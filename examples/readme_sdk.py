"""Exact README SDK example: Offline Pipeline Sanity Check, no model downloads."""

from rag_toolkit.pipeline import RetrievalPipeline
from rag_toolkit.schemas import Document

pipeline = RetrievalPipeline.from_config(
    {
        "embedding": {"provider": "hash_stub", "dimension": 256},
        "retriever": {"mode": "hybrid"},
        "reranker": {"enabled": True, "provider": "token_overlap", "top_k": 10},
    }
)
pipeline.add_documents(
    [
        Document(id="intro", text="FAISS supports vector search."),
        Document(id="lexical", text="BM25 supports lexical search."),
    ]
)
response = pipeline.search("vector search", top_k=2)
assert response.results[0].doc_id == "intro"
print("Offline Pipeline Sanity Check")
print(response.model_dump_json(indent=2))
