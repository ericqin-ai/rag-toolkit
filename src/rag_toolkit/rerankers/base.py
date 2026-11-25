from abc import ABC, abstractmethod


class BaseReranker(ABC):
    @abstractmethod
    def rerank(self, query, chunks, top_k=10):
        """Score and rank chunks against a query."""
