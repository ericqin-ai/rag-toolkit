from abc import ABC, abstractmethod


class BaseFusion(ABC):
    @abstractmethod
    def fuse(self, candidates, top_k=10):
        """Fuse named ranked candidate lists."""
