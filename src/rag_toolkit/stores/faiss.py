import faiss
import numpy as np

from rag_toolkit.schemas import Chunk
from rag_toolkit.stores.base import BaseVectorStore
from rag_toolkit.utils import positive_k, ranked, vectors


class FAISSVectorStore(BaseVectorStore):
    """Exact cosine search. Upserts rebuild the index to avoid duplicate vector IDs."""

    def __init__(self, dimension: int | None = None):
        if dimension is not None and dimension <= 0:
            raise ValueError("dimension must be positive")
        self.dimension = dimension
        self.chunks: dict[str, Chunk] = {}
        self._vectors = {}
        self._ids = []
        self.index = None

    def upsert(self, chunks, vectors_):
        if not chunks and len(vectors_) == 0:
            return
        arr = vectors(vectors_, self.dimension, len(chunks))
        if len({c.chunk_id for c in chunks}) != len(chunks):
            raise ValueError("duplicate chunk IDs in batch")
        self.dimension = arr.shape[1]
        for chunk, vector in zip(chunks, arr, strict=True):
            self.chunks[chunk.chunk_id] = chunk.model_copy(deep=True)
            self._vectors[chunk.chunk_id] = vector.copy()
        self._rebuild()

    def _rebuild(self):
        self._ids = sorted(self.chunks)
        if self.dimension is None:
            return
        self.index = faiss.IndexFlatIP(self.dimension)
        if self._ids:
            matrix = np.stack([self._vectors[key] for key in self._ids])
            faiss.normalize_L2(matrix)
            self.index.add(matrix)

    def delete(self, chunk_ids):
        for key in chunk_ids:
            self.chunks.pop(key, None)
            self._vectors.pop(key, None)
        self._rebuild()

    def search(self, vector, top_k):
        positive_k(top_k)
        arr = vectors([vector], self.dimension, 1)
        if not self._ids or top_k == 0:
            return []
        faiss.normalize_L2(arr)
        # Fetch all for a stable lexical tie-break at the top-k boundary.
        scores, indices = self.index.search(arr, len(self._ids))
        values = {}
        for score, index in zip(scores[0], indices[0], strict=True):
            chunk = self.chunks[self._ids[index]]
            values[(chunk.doc_id, chunk.chunk_id)] = float(score)
        return ranked(values, top_k)
