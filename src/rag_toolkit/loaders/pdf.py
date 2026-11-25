from abc import ABC

from rag_toolkit.loaders.base import BaseLoader


class PDFLoader(BaseLoader, ABC):
    """Extension point for a future PDF parser."""
