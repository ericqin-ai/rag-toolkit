from abc import ABC, abstractmethod
from collections.abc import Sequence


class BaseEmbedder(ABC):
    @abstractmethod
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Encode a batch in input order."""

    def embed_query(self, query: str) -> list[float]:
        return self.embed_documents([query])[0]
