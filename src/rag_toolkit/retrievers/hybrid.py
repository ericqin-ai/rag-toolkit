from rag_toolkit.retrievers.base import BaseRetriever
from rag_toolkit.utils import positive_k


class HybridRetriever(BaseRetriever):
    def __init__(self, bm25, dense, fusion, bm25_top_k=20, dense_top_k=20):
        self.bm25, self.dense, self.fusion = bm25, dense, fusion
        self.bm25_top_k = positive_k(bm25_top_k)
        self.dense_top_k = positive_k(dense_top_k)

    def retrieve(self, query, top_k=10):
        return self.fusion.fuse(
            {
                "bm25": self.bm25.retrieve(query, self.bm25_top_k),
                "dense": self.dense.retrieve(query, self.dense_top_k),
            },
            top_k,
        )
