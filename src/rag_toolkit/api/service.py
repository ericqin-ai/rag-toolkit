"""Serialize access to the in-memory pipeline shared by HTTP request threads."""

import os
from threading import RLock

from rag_toolkit.api.models import EvaluateRequest
from rag_toolkit.evaluation import Evaluator
from rag_toolkit.pipeline import RetrievalPipeline


def create_pipeline(config=None):
    config = config if config is not None else os.environ.get("RAG_TOOLKIT_CONFIG")
    if config is None:
        config = {
            "embedding": {"provider": "hash_stub", "dimension": 256},
            "retriever": {"mode": "hybrid", "bm25_top_k": 20, "dense_top_k": 20},
            "reranker": {"enabled": True, "provider": "token_overlap", "top_k": 20},
        }
    return RetrievalPipeline.from_config(config)


class RetrievalService:
    def __init__(self, pipeline=None, config=None):
        if pipeline is not None and config is not None:
            raise ValueError("provide pipeline or config, not both")
        self.pipeline = pipeline if pipeline is not None else create_pipeline(config)
        self.documents = {}
        self.lock = RLock()

    def stats(self):
        with self.lock:
            ids = set(self.documents) | {c.doc_id for c in self.pipeline.chunks.values()}
            return {"num_documents": len(ids), "num_chunks": len(self.pipeline.chunks)}

    def add_documents(self, documents):
        with self.lock:
            count = self.pipeline.add_documents(documents)
            self.documents.update({d.id: d.model_copy(deep=True) for d in documents})
            return {**self.stats(), "added_chunks": count}

    def search(self, query, top_k=10):
        with self.lock:
            return self.pipeline.search(query, top_k)

    def evaluate(self, request: EvaluateRequest):
        with self.lock:
            responses = [self.pipeline.search(q.query, request.top_k) for q in request.queries]
            return Evaluator().evaluate(
                responses, {q.query: set(q.relevant_doc_ids) for q in request.queries}, request.ks
            )
