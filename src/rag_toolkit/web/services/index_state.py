"""Index identity excludes query-time options and authentication secrets."""

import hashlib
import json

from rag_toolkit.web.services.configuration import redact, sensitive_key


def index_fingerprint(config):
    defaults = {
        "splitter": {"type": "fixed", "chunk_size": 512, "chunk_overlap": 64},
        "tokenizer": {"type": "builtin"},
        "store": {"type": "faiss", "dimension": None},
        "embedding": {"provider": "local", "model_name": "BAAI/bge-small-zh-v1.5"},
    }
    identity = {}
    for name, default in defaults.items():
        values = dict(config.get(name, {}))
        if name == "embedding" and values.get("provider") == "hash_stub":
            default = {"provider": "hash_stub", "dimension": 256}
        elif name == "embedding":
            if values.get("provider", "local") == "local":
                default = {**default, "device": "cpu"}
            else:
                default = {**default, "base_url": "https://api.openai.com/v1", "batch_size": 64}
        if name == "store" and values.get("type") == "elasticsearch":
            default = {
                "type": "elasticsearch",
                "dimension": 256,
                "index_name": "rag-toolkit",
                "url": "http://localhost:9200",
            }
        identity[name] = redact(
            {k: v for k, v in {**default, **values}.items() if not sensitive_key(k)}
        )
    return hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()


def requires_rebuild(service):
    return service.index_fingerprint != index_fingerprint(service.config)
