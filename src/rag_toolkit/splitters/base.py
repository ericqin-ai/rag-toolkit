from abc import ABC, abstractmethod

from rag_toolkit.schemas import Chunk, Document


class BaseSplitter(ABC):
    @abstractmethod
    def split(self, document: Document) -> list[Chunk]:
        """Split into chunks with source offsets."""
