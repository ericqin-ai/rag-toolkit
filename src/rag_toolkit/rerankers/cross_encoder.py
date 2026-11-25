import numpy as np

from rag_toolkit.rerankers.base import BaseReranker
from rag_toolkit.utils import positive_k, ranked


class CrossEncoderReranker(BaseReranker):
    def __init__(self, model_name: str, device: str = "cpu", model=None):
        if model is None:
            from sentence_transformers import CrossEncoder

            model = CrossEncoder(model_name, device=device)
        self.model = model

    def rerank(self, query, chunks, top_k=10):
        positive_k(top_k)
        if not chunks:
            return []
        values = np.asarray(
            self.model.predict([(query, c.text) for c in chunks], show_progress_bar=False)
        )
        if values.shape != (len(chunks),) or not np.isfinite(values).all():
            raise ValueError("cross encoder must return one finite score per chunk")
        return ranked(
            {(c.doc_id, c.chunk_id): float(s) for c, s in zip(chunks, values, strict=True)}, top_k
        )
