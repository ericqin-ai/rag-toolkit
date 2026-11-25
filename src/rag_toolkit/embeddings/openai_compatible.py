import os
from collections.abc import Sequence

import httpx

from rag_toolkit.embeddings.base import BaseEmbedder
from rag_toolkit.utils import vectors


class OpenAICompatibleEmbedder(BaseEmbedder):
    def __init__(
        self,
        model_name: str,
        base_url: str = "https://api.openai.com/v1",
        api_key: str | None = None,
        client: httpx.Client | None = None,
        batch_size: int = 64,
    ):
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        self.model_name, self.base_url = model_name, base_url.rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.client = client
        self.batch_size = batch_size

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        result = []
        # Own short-lived clients; injected clients remain owned by their caller.
        if not texts:
            return result
        if self.client is None:
            with httpx.Client(timeout=60) as client:
                return self._encode(texts, client)
        return self._encode(texts, self.client)

    def _encode(self, texts, client):
        result, dimension = [], None
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        for start in range(0, len(texts), self.batch_size):
            batch = list(texts[start : start + self.batch_size])
            response = client.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json={"model": self.model_name, "input": batch},
            )
            response.raise_for_status()
            data = sorted(response.json()["data"], key=lambda item: item["index"])
            if [item["index"] for item in data] != list(range(len(batch))):
                raise ValueError("embedding response indices do not match input")
            matrix = vectors([item["embedding"] for item in data], dimension, len(batch))
            dimension = matrix.shape[1]
            result.extend(matrix.tolist())
        return result
