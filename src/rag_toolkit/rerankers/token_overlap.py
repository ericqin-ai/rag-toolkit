from rag_toolkit.rerankers.base import BaseReranker
from rag_toolkit.utils import ranked, tokenize


class TokenOverlapReranker(BaseReranker):
    """Lightweight deterministic test substitute; not a learned model."""

    def rerank(self, query, chunks, top_k=10):
        terms = set(tokenize(query))
        return ranked(
            {
                (c.doc_id, c.chunk_id): len(terms & set(tokenize(c.text))) / max(1, len(terms))
                for c in chunks
            },
            top_k,
        )
