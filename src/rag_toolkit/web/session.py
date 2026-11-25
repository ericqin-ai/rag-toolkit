"""Create session-local pipelines, including isolated remote index names."""

import os
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from uuid import uuid4

import yaml

from rag_toolkit.api import RetrievalService


def create_session_service():
    path = os.environ.get("RAG_TOOLKIT_CONFIG")
    if path is None:
        return RetrievalService()
    config = yaml.safe_load(Path(path).read_text(encoding="utf8"))
    if not isinstance(config, Mapping):
        raise ValueError("configuration must be a mapping")
    config = deepcopy(config)
    store = config.get("store", {})
    if isinstance(store, Mapping) and store.get("type") == "elasticsearch":
        store["index_name"] = f"{store.get('index_name', 'rag-toolkit')}-session-{uuid4().hex}"
    return RetrievalService(config=config)
