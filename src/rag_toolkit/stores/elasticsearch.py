from collections.abc import Sequence

import numpy as np

from rag_toolkit.schemas import StageCandidate
from rag_toolkit.stores.base import BaseVectorStore
from rag_toolkit.utils import positive_k, vectors


class ElasticsearchStoreAdapter(BaseVectorStore):
    """Cosine kNN adapter; caller may inject an Elasticsearch-compatible client."""

    def __init__(
        self,
        index_name: str = "rag-toolkit",
        dimension: int = 256,
        url: str = "http://localhost:9200",
        client=None,
    ):
        if dimension <= 0:
            raise ValueError("dimension must be positive")
        if client is None:
            from elasticsearch import Elasticsearch

            client = Elasticsearch(url)
        self.client, self.index_name, self.dimension = client, index_name, dimension
        self._ready = False

    def _ensure_index(self):
        if self._ready:
            return
        if not self.client.indices.exists(index=self.index_name):
            self.client.indices.create(
                index=self.index_name,
                mappings={
                    "properties": {
                        "chunk_id": {"type": "keyword"},
                        "doc_id": {"type": "keyword"},
                        "text": {"type": "text"},
                        "metadata": {"type": "object", "enabled": False},
                        "vector": {
                            "type": "dense_vector",
                            "dims": self.dimension,
                            "index": True,
                            "similarity": "cosine",
                        },
                    }
                },
            )
        else:
            mappings = self.client.indices.get_mapping(index=self.index_name)
            field = mappings[self.index_name]["mappings"]["properties"]["vector"]
            if field["dims"] != self.dimension:
                raise ValueError("existing Elasticsearch index dimension mismatch")
            if field.get("similarity", "cosine") != "cosine":
                raise ValueError("existing Elasticsearch index must use cosine similarity")
        self._ready = True

    def upsert(self, chunks, vectors_):
        if not chunks and len(vectors_) == 0:
            return
        matrix = vectors(vectors_, self.dimension, len(chunks))
        if len({c.chunk_id for c in chunks}) != len(chunks):
            raise ValueError("duplicate chunk IDs in batch")
        if np.any(np.linalg.norm(matrix, axis=1) == 0):
            raise ValueError("Elasticsearch cosine vectors must be nonzero")
        self._ensure_index()
        for chunk, vector in zip(chunks, matrix, strict=True):
            self.client.index(
                index=self.index_name,
                id=chunk.chunk_id,
                document={**chunk.model_dump(), "vector": vector.tolist()},
                refresh="wait_for",
            )

    def delete(self, chunk_ids: Sequence[str]):
        for key in chunk_ids:
            self.client.delete(index=self.index_name, id=key, refresh="wait_for")

    def search(self, vector, top_k):
        return self._search(vector, top_k)

    def search_scoped(self, vector, top_k, chunk_ids):
        """Restrict kNN to chunks owned by the current pipeline instance."""
        positive_k(top_k)
        if not chunk_ids:
            return []
        return self._search(vector, top_k, chunk_ids)

    def _search(self, vector, top_k, chunk_ids=None):
        positive_k(top_k)
        matrix = vectors([vector], self.dimension, 1)
        if top_k == 0:
            return []
        if not np.linalg.norm(matrix):
            raise ValueError("Elasticsearch cosine query must be nonzero")
        self._ensure_index()
        knn = {
            "field": "vector",
            "query_vector": matrix[0].tolist(),
            "k": top_k,
            "num_candidates": max(100, top_k * 2),
        }
        if chunk_ids is not None:
            knn["filter"] = {"terms": {"chunk_id": sorted(chunk_ids)}}
        response = self.client.search(index=self.index_name, size=top_k, knn=knn)
        return [
            StageCandidate(
                doc_id=hit["_source"]["doc_id"],
                chunk_id=hit["_source"]["chunk_id"],
                score=2 * hit["_score"] - 1,
                rank=i,
            )
            for i, hit in enumerate(response["hits"]["hits"], 1)
        ]
