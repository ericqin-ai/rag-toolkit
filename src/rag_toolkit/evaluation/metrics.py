import math

from rag_toolkit.utils import positive_k


def _unique(ranking):
    return list(dict.fromkeys(ranking))


def hit_at_k(ranking, relevant, k):
    positive_k(k)
    return float(bool(set(_unique(ranking)[:k]) & set(relevant)))


def recall_at_k(ranking, relevant, k):
    positive_k(k)
    relevant = set(relevant)
    return len(set(_unique(ranking)[:k]) & relevant) / len(relevant) if relevant else 0.0


def mrr(ranking, relevant):
    relevant = set(relevant)
    return next(
        (1 / rank for rank, doc_id in enumerate(_unique(ranking), 1) if doc_id in relevant), 0.0
    )


def ndcg_at_k(ranking, relevant, k):
    positive_k(k)
    relevant = set(relevant)
    dcg = sum(
        1 / math.log2(rank + 1)
        for rank, doc_id in enumerate(_unique(ranking)[:k], 1)
        if doc_id in relevant
    )
    ideal = sum(1 / math.log2(rank + 1) for rank in range(1, min(k, len(relevant)) + 1))
    return dcg / ideal if ideal else 0.0
