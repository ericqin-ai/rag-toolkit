"""Package exports must remain identical to their implementation-module classes."""

from importlib import import_module

import pytest


@pytest.mark.parametrize(
    "package, module, name",
    [
        ("loaders", "jsonl", "JSONLLoader"),
        ("splitters", "markdown", "MarkdownHeaderSplitter"),
        ("embeddings", "local", "LocalSentenceTransformerEmbedder"),
        ("stores", "faiss", "FAISSVectorStore"),
        ("retrievers", "bm25", "BM25Retriever"),
        ("fusion", "rrf", "RRFFusion"),
        ("rerankers", "cross_encoder", "CrossEncoderReranker"),
        ("pipeline", "retrieval", "RetrievalPipeline"),
        ("evaluation", "evaluator", "Evaluator"),
        ("schemas", "models", "Document"),
        ("utils", "ranking", "ranked"),
    ],
)
def test_public_import_matches_implementation(package, module, name):
    public = import_module(f"rag_toolkit.{package}")
    implementation = import_module(f"rag_toolkit.{package}.{module}")
    assert getattr(public, name) is getattr(implementation, name)
    assert name in public.__all__
