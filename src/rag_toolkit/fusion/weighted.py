import math

from rag_toolkit.fusion.base import BaseFusion
from rag_toolkit.utils import ranked


class WeightedFusion(BaseFusion):
    """Per-stage min-max normalization; constant lists map to one, missing items to zero."""

    def __init__(self, weights=None):
        self.weights = dict(weights if weights is not None else {"bm25": 0.4, "dense": 0.6})
        if (
            not self.weights
            or any(not math.isfinite(w) or w < 0 for w in self.weights.values())
            or sum(self.weights.values()) <= 0
        ):
            raise ValueError("weights must be finite, nonnegative, with positive sum")

    def fuse(self, candidates, top_k=10):
        scores = {}
        total = sum(self.weights.values())
        for stage, items in candidates.items():
            if stage not in self.weights:
                raise ValueError(f"missing weight for stage {stage}")
            unique = {}
            for item in items:
                key = (item.doc_id, item.chunk_id)
                unique[key] = max(unique.get(key, -math.inf), item.score)
            if not unique:
                continue
            low, high = min(unique.values()), max(unique.values())
            for key, score in unique.items():
                norm = (score - low) / (high - low) if high > low else 1
                scores[key] = scores.get(key, 0) + self.weights[stage] / total * norm
        return ranked(scores, top_k)
