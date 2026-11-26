"""Create session-local pipelines, including isolated remote index names."""

import os
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from uuid import uuid4

import yaml

from rag_toolkit.api import RetrievalService
from rag_toolkit.pipeline import RetrievalPipeline
from rag_toolkit.web.services.index_state import index_fingerprint

DEFAULT_CONFIG = {
    "embedding": {"provider": "hash_stub", "dimension": 256},
    "retriever": {"mode": "hybrid", "bm25_top_k": 20, "dense_top_k": 20},
    "reranker": {"enabled": True, "provider": "token_overlap", "top_k": 20},
}


def create_session_service():
    path = os.environ.get("RAG_TOOLKIT_CONFIG")
    config = (
        yaml.safe_load(Path(path).read_text(encoding="utf8")) if path else deepcopy(DEFAULT_CONFIG)
    )
    if not isinstance(config, Mapping):
        raise ValueError("configuration must be a mapping")
    config = deepcopy(config)
    store = config.get("store", {})
    if isinstance(store, Mapping) and store.get("type") == "elasticsearch":
        store["index_name"] = f"{store.get('index_name', 'rag-toolkit')}-session-{uuid4().hex}"
    service = RetrievalService(config=config)
    service.config = config
    service.index_fingerprint = index_fingerprint(config)
    return service


def rebuild_service(service, config, *, documents=None):
    """Build separately; callers replace session service only after successful indexing."""
    config = deepcopy(config)
    store = config.get("store", {})
    if store.get("type") == "elasticsearch":
        store["index_name"] = f"rag-toolkit-session-{uuid4().hex}"
    replacement = RetrievalService(config=config)
    source = list(service.documents.values()) if documents is None else documents
    if source:
        replacement.add_documents(source)
    replacement.config = config
    replacement.index_fingerprint = index_fingerprint(config)
    return replacement


def clear_session_service(service):
    """Empty indexes while retaining loaded models and active configuration."""
    config = deepcopy(service.config)
    store = config.get("store", {})
    if store.get("type") == "elasticsearch":
        store["index_name"] = f"rag-toolkit-session-{uuid4().hex}"
    pipeline = RetrievalPipeline.from_config(
        config,
        embedder=service.pipeline.dense.embedder if service.pipeline.dense else None,
        reranker=service.pipeline.reranker,
    )
    replacement = RetrievalService(pipeline=pipeline)
    replacement.config = config
    replacement.index_fingerprint = index_fingerprint(config)
    return replacement
