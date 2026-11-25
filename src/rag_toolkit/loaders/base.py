from abc import ABC, abstractmethod
from pathlib import Path

from rag_toolkit.schemas import Document


class BaseLoader(ABC):
    @abstractmethod
    def load(self, path: str | Path) -> list[Document]:
        """Load documents from a file."""
