from collections.abc import Sequence

from rag_toolkit.embeddings.base import BaseEmbedder
from rag_toolkit.utils import vectors


class LocalSentenceTransformerEmbedder(BaseEmbedder):
    def __init__(self, model_name: str, device: str = "cpu", model=None):
        if model is None:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(model_name, device=device)
        self.model = model

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        encoded = self.model.encode(
            list(texts), normalize_embeddings=True, show_progress_bar=False, convert_to_numpy=True
        )
        return vectors(encoded, count=len(texts)).tolist()
