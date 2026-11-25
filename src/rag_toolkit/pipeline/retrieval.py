from collections.abc import Mapping, Sequence
from pathlib import Path
from time import perf_counter

import yaml

from rag_toolkit.embeddings import (
    HashEmbedder,
    LocalSentenceTransformerEmbedder,
    OpenAICompatibleEmbedder,
)
from rag_toolkit.fusion import RRFFusion, WeightedFusion
from rag_toolkit.rerankers import CrossEncoderReranker, TokenOverlapReranker
from rag_toolkit.retrievers import BM25Retriever, DenseRetriever
from rag_toolkit.schemas import Document, SearchResponse, SearchResult, StageTrace
from rag_toolkit.splitters import FixedLengthSplitter, MarkdownHeaderSplitter
from rag_toolkit.stores import ElasticsearchStoreAdapter, FAISSVectorStore
from rag_toolkit.utils import positive_k


class RetrievalPipeline:
    def __init__(
        self,
        splitter,
        embedder=None,
        store=None,
        mode="hybrid",
        fusion=None,
        reranker=None,
        bm25_top_k=20,
        dense_top_k=20,
        rerank_top_k=10,
    ):
        if mode not in {"bm25", "dense", "hybrid"}:
            raise ValueError("unknown retrieval mode")
        if mode != "bm25" and (embedder is None or store is None):
            raise ValueError("dense/hybrid mode requires embedder and store")
        self.splitter, self.mode = splitter, mode
        self.bm25 = BM25Retriever()
        self.dense = DenseRetriever(embedder, store) if mode != "bm25" else None
        self.fusion = fusion if fusion is not None else RRFFusion()
        self.reranker = reranker
        self.bm25_top_k = positive_k(bm25_top_k)
        self.dense_top_k = positive_k(dense_top_k)
        self.rerank_top_k = positive_k(rerank_top_k)
        self.chunks = {}
        self._document_chunks = {}

    @classmethod
    def from_config(cls, config: Mapping | str | Path, *, embedder=None, store=None, reranker=None):
        """Load YAML or a mapping. Injectable components override configured providers."""
        if not isinstance(config, Mapping):
            with Path(config).open(encoding="utf-8") as stream:
                config = yaml.safe_load(stream)
        if not isinstance(config, Mapping):
            raise ValueError("configuration must be a mapping")
        allowed = {"splitter", "embedding", "store", "retriever", "fusion", "reranker"}
        if set(config) - allowed:
            raise ValueError(f"unknown configuration sections: {set(config) - allowed}")
        for name, value in config.items():
            if not isinstance(value, Mapping):
                raise ValueError(f"{name} must be a mapping")
        split = dict(config.get("splitter", {}))
        emb = dict(config.get("embedding", {}))
        storage = dict(config.get("store", {}))
        retrieval = dict(config.get("retriever", {}))
        fusion = dict(config.get("fusion", {}))
        rerank = dict(config.get("reranker", {}))
        if type(rerank.get("enabled", False)) is not bool:
            raise ValueError("reranker.enabled must be a boolean")
        choices = [
            (split.get("type", "fixed"), {"fixed", "markdown_header"}),
            (emb.get("provider", "local"), {"local", "openai_compatible", "hash_stub"}),
            (storage.get("type", "faiss"), {"faiss", "elasticsearch"}),
            (retrieval.get("mode", "hybrid"), {"bm25", "dense", "hybrid"}),
            (fusion.get("method", "rrf"), {"rrf", "weighted"}),
            (rerank.get("provider", "cross_encoder"), {"cross_encoder", "token_overlap"}),
        ]
        for value, options in choices:
            if value not in options:
                raise ValueError(f"unknown component {value!r}; expected one of {sorted(options)}")
        mode = retrieval.get("mode", "hybrid")
        # Validate numerical settings before constructing any network-capable provider.
        for key in ("bm25_top_k", "dense_top_k"):
            positive_k(retrieval.get(key, 20))
        positive_k(rerank.get("top_k", 10))
        splitter_cls = (
            FixedLengthSplitter if split.pop("type", "fixed") == "fixed" else MarkdownHeaderSplitter
        )
        splitter = splitter_cls(**split)
        fuser = (
            RRFFusion(fusion.get("rrf_k", 60))
            if fusion.get("method", "rrf") == "rrf"
            else WeightedFusion(fusion.get("weights"))
        )
        if mode != "bm25":
            if embedder is None:
                provider = emb.pop("provider", "local")
                if provider == "hash_stub":
                    emb.pop("model_name", None)
                    embedder = HashEmbedder(**emb)
                else:
                    emb.setdefault("model_name", "BAAI/bge-small-zh-v1.5")
                    embedder = (
                        LocalSentenceTransformerEmbedder(**emb)
                        if provider == "local"
                        else OpenAICompatibleEmbedder(**emb)
                    )
            if store is None:
                kind = storage.pop("type", "faiss")
                store = (
                    FAISSVectorStore(**storage)
                    if kind == "faiss"
                    else ElasticsearchStoreAdapter(**storage)
                )
        if rerank.get("enabled", False) and reranker is None:
            provider = rerank.pop("provider", "cross_encoder")
            rerank.pop("enabled", None)
            rerank.pop("top_k", None)
            if provider == "token_overlap":
                rerank.pop("model_name", None)
                reranker = TokenOverlapReranker(**rerank)
            else:
                rerank.setdefault("model_name", "BAAI/bge-reranker-base")
                reranker = CrossEncoderReranker(**rerank)
        return cls(
            splitter,
            embedder,
            store,
            mode,
            fuser,
            reranker,
            retrieval.get("bm25_top_k", 20),
            retrieval.get("dense_top_k", 20),
            config.get("reranker", {}).get("top_k", 10),
        )

    def add_documents(self, documents: Sequence[Document]) -> int:
        """Replace existing documents by ID, removing all obsolete chunks."""
        documents = list(documents)
        if len({d.id for d in documents}) != len(documents):
            raise ValueError("duplicate document IDs in batch")
        new_chunks = [c for doc in documents for c in self.splitter.split(doc)]
        if len({c.chunk_id for c in new_chunks}) != len(new_chunks):
            raise ValueError("duplicate generated chunk IDs")
        old_ids = {key for doc in documents for key in self._document_chunks.get(doc.id, [])}
        obsolete = old_ids - {c.chunk_id for c in new_chunks}
        # Validate/embed before mutating local BM25 state. Remote stores are not transactional.
        if self.dense:
            self.dense.add_chunks(new_chunks)
            self.dense.store.delete(sorted(obsolete))
        self.bm25.delete(old_ids)
        self.bm25.add_chunks(new_chunks)
        for key in old_ids:
            self.chunks.pop(key, None)
        for chunk in new_chunks:
            self.chunks[chunk.chunk_id] = chunk.model_copy(deep=True)
        for doc in documents:
            self._document_chunks[doc.id] = [c.chunk_id for c in new_chunks if c.doc_id == doc.id]
        return len(new_chunks)

    def search(self, query: str, top_k: int = 10) -> SearchResponse:
        positive_k(top_k)
        started = perf_counter()
        traces = []

        def run(stage, operation):
            start = perf_counter()
            candidates = operation()
            traces.append(
                StageTrace(
                    stage=stage, latency_ms=(perf_counter() - start) * 1000, candidates=candidates
                )
            )
            return candidates

        active = bool(query.strip() and top_k and self.chunks)
        lists = {}
        if self.mode in {"bm25", "hybrid"}:
            lists["bm25"] = run(
                "bm25", lambda: self.bm25.retrieve(query, self.bm25_top_k) if active else []
            )
        if self.mode in {"dense", "hybrid"}:
            lists["dense"] = run(
                "dense",
                lambda: (
                    self.dense.retrieve(query, self.dense_top_k, chunk_ids=self.chunks)
                    if active
                    else []
                ),
            )
        if self.mode == "hybrid":
            candidates = run(
                "fusion",
                lambda: (
                    self.fusion.fuse(
                        lists,
                        max(
                            self.bm25_top_k,
                            self.dense_top_k,
                            top_k,
                            self.rerank_top_k if self.reranker is not None else 0,
                        ),
                    )
                    if active
                    else []
                ),
            )
        else:
            candidates = lists[self.mode]
        if self.reranker is not None:
            pool = candidates[: self.rerank_top_k]
            candidates = run(
                "rerank",
                lambda: (
                    self.reranker.rerank(query, [self.chunks[c.chunk_id] for c in pool], top_k)
                    if active
                    else []
                ),
            )
        lookups = {trace.stage: {c.chunk_id: c for c in trace.candidates} for trace in traces}
        results = []
        for rank, candidate in enumerate(candidates[:top_k], 1):
            chunk = self.chunks[candidate.chunk_id]
            stage_ranks, stage_scores = {}, {}
            for stage, lookup in lookups.items():
                item = lookup.get(candidate.chunk_id)
                stage_ranks[stage] = item.rank if item else None
                stage_scores[stage] = item.score if item else None
            results.append(
                SearchResult(
                    doc_id=chunk.doc_id,
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                    score=candidate.score,
                    rank=rank,
                    metadata=chunk.model_copy(deep=True).metadata,
                    stage_ranks=stage_ranks,
                    stage_scores=stage_scores,
                )
            )
        return SearchResponse(
            query=query,
            results=results,
            traces=traces,
            total_latency_ms=(perf_counter() - started) * 1000,
        )
