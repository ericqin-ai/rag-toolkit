"""Offline hybrid search with deterministic token-overlap reranking."""

from search_common import run

if __name__ == "__main__":
    run("hybrid", rerank=True)
