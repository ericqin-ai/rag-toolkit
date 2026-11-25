from abc import ABC

from rag_toolkit.splitters.base import BaseSplitter


class SemanticSplitter(BaseSplitter, ABC):
    """Extension point for semantic segmentation."""
