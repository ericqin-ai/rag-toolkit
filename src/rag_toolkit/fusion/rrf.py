from rag_toolkit.fusion.base import BaseFusion
from rag_toolkit.utils import ranked


class RRFFusion(BaseFusion):
    def __init__(self, rrf_k: int = 60):
        if rrf_k < 0:
            raise ValueError("rrf_k must be nonnegative")
        self.rrf_k = rrf_k

    def fuse(self, candidates, top_k=10):
        scores = {}
        for items in candidates.values():
            seen = set()
            for item in sorted(items, key=lambda c: c.rank):
                key = (item.doc_id, item.chunk_id)
                if key not in seen:
                    scores[key] = scores.get(key, 0) + 1 / (self.rrf_k + item.rank)
                    seen.add(key)
        return ranked(scores, top_k)
