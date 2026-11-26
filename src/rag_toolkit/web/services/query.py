"""Independent query views share indexed components, never mutable query settings."""

from copy import copy
from dataclasses import asdict, dataclass
from math import isfinite

from rag_toolkit.fusion import RRFFusion, WeightedFusion
from rag_toolkit.web.services.index_state import requires_rebuild


@dataclass(frozen=True)
class QueryOptions:
    mode: str = "hybrid"
    bm25_top_k: int = 20
    dense_top_k: int = 20
    top_k: int = 5
    fusion: str = "rrf"
    rrf_k: int = 60
    bm25_weight: float = 0.4
    dense_weight: float = 0.6
    rerank: bool = False
    rerank_top_k: int = 20

    def __post_init__(self):
        if self.mode not in ("bm25", "dense", "hybrid") or self.fusion not in ("rrf", "weighted"):
            raise ValueError("invalid retrieval options")
        for k in (self.bm25_top_k, self.dense_top_k, self.top_k, self.rerank_top_k):
            if type(k) is not int or k < 1:
                raise ValueError("K must be a positive integer")
        if type(self.rrf_k) is not int or self.rrf_k < 0:
            raise ValueError("RRF K must be nonnegative")
        weights = (self.bm25_weight, self.dense_weight)
        if any(not isfinite(w) or w < 0 for w in weights) or sum(weights) <= 0:
            raise ValueError("weights must be finite, nonnegative, with positive sum")

    def to_dict(self):
        return asdict(self)


def run_query(service, query, options):
    if not query.strip():
        raise ValueError("query is empty")
    with service.lock:
        if requires_rebuild(service):
            raise ValueError("index configuration changed; rebuild required")
        pipeline = copy(service.pipeline)
        if options.mode != "bm25" and pipeline.dense is None:
            raise ValueError("dense model unavailable")
        if options.rerank and pipeline.reranker is None:
            raise ValueError("reranker unavailable")
        pipeline.mode = options.mode
        pipeline.bm25_top_k, pipeline.dense_top_k = options.bm25_top_k, options.dense_top_k
        pipeline.rerank_top_k = options.rerank_top_k
        if not options.rerank:
            pipeline.reranker = None
        pipeline.fusion = (
            RRFFusion(options.rrf_k)
            if options.fusion == "rrf"
            else WeightedFusion({"bm25": options.bm25_weight, "dense": options.dense_weight})
        )
        return pipeline.search(query, options.top_k)
