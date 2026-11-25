from abc import ABC, abstractmethod
from collections.abc import Sequence

from rag_toolkit.schemas import Chunk, StageCandidate


class BaseVectorStore(ABC):
    @abstractmethod
    def upsert(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> None:
        """Insert or replace chunks by chunk_id."""

    @abstractmethod
    def delete(self, chunk_ids: Sequence[str]) -> None:
        """Remove chunks by ID."""

    @abstractmethod
    def search(self, vector: Sequence[float], top_k: int) -> list[StageCandidate]:
        """Return ranked neighbors."""
