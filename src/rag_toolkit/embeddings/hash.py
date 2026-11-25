import hashlib
from collections.abc import Sequence

import numpy as np

from rag_toolkit.embeddings.base import BaseEmbedder
from rag_toolkit.utils import tokenize


class HashEmbedder(BaseEmbedder):
    """Deterministic normalized bag-of-token hashes for offline tests, not a semantic model."""

    def __init__(self, dimension: int = 256):
        if not isinstance(dimension, int) or dimension <= 0:
            raise ValueError("dimension must be a positive integer")
        self.dimension = dimension

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        output = np.zeros((len(texts), self.dimension), dtype=np.float32)
        for row, text in enumerate(texts):
            for token in tokenize(text):
                digest = hashlib.sha256(token.encode()).digest()
                output[row, int.from_bytes(digest[:8], "little") % self.dimension] += 1
        norms = np.linalg.norm(output, axis=1, keepdims=True)
        return (output / np.maximum(norms, 1e-12)).tolist()
