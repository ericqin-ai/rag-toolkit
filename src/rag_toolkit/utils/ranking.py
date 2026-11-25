from rag_toolkit.schemas import StageCandidate

from .validation import positive_k


def ranked(scores, top_k):
    positive_k(top_k)
    ordered = sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))
    return [
        StageCandidate(doc_id=key[0], chunk_id=key[1], score=float(score), rank=i)
        for i, (key, score) in enumerate(ordered[:top_k], 1)
    ]
