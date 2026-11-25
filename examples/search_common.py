"""Shared CLI plumbing for the three offline retrieval examples."""

import argparse
from pathlib import Path

from rag_toolkit.api.service import create_pipeline
from rag_toolkit.loaders import JSONLLoader

ROOT = Path(__file__).resolve().parents[1]


def run(mode: str, rerank: bool = False):
    parser = argparse.ArgumentParser(description=f"{mode} retrieval; rerank={rerank}")
    parser.add_argument("--query", default="FAISS CPU 向量")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--documents", type=Path, default=ROOT / "datasets/documents.jsonl")
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error("--top-k must be positive")
    if not args.query.strip():
        parser.error("--query must not be blank")
    pipeline = create_pipeline(
        {
            "embedding": {"provider": "hash_stub", "dimension": 256},
            "retriever": {"mode": mode, "bm25_top_k": 20, "dense_top_k": 20},
            "fusion": {"method": "rrf", "rrf_k": 60},
            "reranker": {"enabled": rerank, "provider": "token_overlap", "top_k": 20},
        }
    )
    pipeline.add_documents(JSONLLoader().load(args.documents))
    # Escaped JSON is portable across Windows terminal code pages.
    import json

    print(json.dumps(pipeline.search(args.query, args.top_k).model_dump(), indent=2))
