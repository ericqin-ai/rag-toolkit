"""Configuration validation/import/application without Streamlit or credential reflection."""

from copy import copy, deepcopy
from urllib.parse import parse_qsl, urlsplit

import yaml

from rag_toolkit.fusion import RRFFusion, WeightedFusion
from rag_toolkit.pipeline import RetrievalPipeline
from rag_toolkit.web.services.configuration import redact, sensitive_key
from rag_toolkit.web.services.index_state import index_fingerprint
from rag_toolkit.web.session import rebuild_service

FIELDS = {
    "embedding": {
        "provider",
        "model_name",
        "dimension",
        "device",
        "base_url",
        "api_key",
        "batch_size",
    },
    "reranker": {"provider", "model_name", "device", "enabled", "top_k"},
    "store": {"type", "url", "dimension", "index_name"},
    "splitter": {"type", "chunk_size", "chunk_overlap"},
    "tokenizer": {"type"},
    "retriever": {"mode", "bm25_top_k", "dense_top_k", "final_top_k"},
    "fusion": {"method", "rrf_k", "weights"},
}


def validate_config(config):
    if not isinstance(config, dict) or set(config) - set(FIELDS):
        raise ValueError("invalid configuration sections")
    for section, values in config.items():
        if not isinstance(values, dict) or set(values) - FIELDS[section]:
            raise ValueError("invalid configuration fields")
    emb = config.get("embedding", {})
    for key in ("dimension", "batch_size"):
        if key in emb and (type(emb[key]) is not int or emb[key] <= 0):
            raise ValueError("invalid embedding dimensions or batch size")
    provider = emb.get("provider", "local")
    final_k = config.get("retriever", {}).get("final_top_k", 5)
    if type(final_k) is not int or not 1 <= final_k <= 1000:
        raise ValueError("invalid final top K")
    allowed = {
        "hash_stub": {"provider", "dimension", "model_name"},
        "local": {"provider", "model_name", "device"},
        "openai_compatible": {"provider", "model_name", "base_url", "api_key", "batch_size"},
    }
    if provider not in allowed or set(emb) - allowed[provider]:
        raise ValueError("invalid embedding provider options")
    store = config.get("store", {})
    kind = store.get("type", "faiss")
    allowed_store = {
        "faiss": {"type", "dimension"},
        "elasticsearch": {"type", "url", "dimension", "index_name"},
    }
    if kind not in allowed_store or set(store) - allowed_store[kind]:
        raise ValueError("invalid store options")
    if store.get("dimension") is not None and (
        type(store["dimension"]) is not int or store["dimension"] < 1
    ):
        raise ValueError("invalid store dimension")
    rr = config.get("reranker", {})
    if rr.get("provider") == "token_overlap" and "device" in rr:
        raise ValueError("token overlap does not accept a device")
    f = config.get("fusion", {})
    if type(f.get("rrf_k", 60)) is not int or f.get("rrf_k", 60) < 0:
        raise ValueError("invalid RRF K")
    if "weights" in f and (
        not isinstance(f["weights"], dict) or set(f["weights"]) != {"bm25", "dense"}
    ):
        raise ValueError("weights require both recall channels")
    for section in ("embedding", "reranker"):
        values = config.get(section, {})
        for key in ("device", "model_name"):
            if key in values and (not isinstance(values[key], str) or not values[key].strip()):
                raise ValueError("model and device must not be blank")
    for url in (emb.get("base_url"), config.get("store", {}).get("url")):
        if url is not None:
            parsed = urlsplit(url)
            if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
                raise ValueError("invalid endpoint")
    # Validate existing splitter/fusion rules without loading models or contacting stores.
    RetrievalPipeline.from_config(config, embedder=object(), store=object(), reranker=object())
    return deepcopy(config)


def import_config(content, current):
    try:
        config = yaml.safe_load(content.decode("utf-8-sig"))
        if not isinstance(config, dict):
            raise ValueError
        # Never transfer a redacted credential to a different provider or endpoint.
        incoming = config.get("embedding", {})
        previous_embedding = current.get("embedding", {})
        if isinstance(incoming, dict) and "[REDACTED]" in str(incoming):
            if incoming.get("provider", "local") != previous_embedding.get(
                "provider", "local"
            ) or incoming.get("base_url", "https://api.openai.com/v1") != redact(
                previous_embedding.get("base_url", "https://api.openai.com/v1")
            ):
                raise ValueError

        def sanitize(value, previous):
            if isinstance(value, dict):
                result = {}
                for key, item in value.items():
                    old = previous.get(key) if isinstance(previous, dict) else None
                    if sensitive_key(key):
                        if item != "[REDACTED]":
                            raise ValueError
                        if old is not None:
                            result[key] = old
                    else:
                        result[key] = sanitize(item, old)
                return result
            if isinstance(value, list):
                return [sanitize(v, None) for v in value]
            if isinstance(value, str) and value.lower().startswith(("http://", "https://")):
                parsed = urlsplit(value)
                if "[REDACTED]" in value or "%5BREDACTED%5D" in value:
                    if isinstance(previous, str) and redact(previous) == value:
                        return previous
                    raise ValueError
                if (
                    parsed.username
                    or parsed.password
                    or any(sensitive_key(k) for k, _ in parse_qsl(parsed.query))
                ):
                    raise ValueError
            return value

        return validate_config(sanitize(config, current))
    except Exception:
        raise ValueError(
            "invalid configuration or embedded credentials; use environment variables"
        ) from None


def rebuild_needed(service, config):
    if index_fingerprint(config) != service.index_fingerprint:
        return True

    def signature(values):
        defaults = {
            "enabled": False,
            "provider": "cross_encoder",
            "model_name": "BAAI/bge-reranker-base",
            "device": "cpu",
        }
        if values.get("provider") == "token_overlap":
            defaults = {"enabled": False, "provider": "token_overlap"}
        return {k: v for k, v in {**defaults, **values}.items() if k != "top_k"}

    old = signature(service.config.get("reranker", {}))
    new = signature(config.get("reranker", {}))
    return old != new or (
        service.pipeline.dense is None
        and config.get("retriever", {}).get("mode", "hybrid") != "bm25"
    )


def apply_config(service, config):
    config = validate_config(config)
    with service.lock:
        if rebuild_needed(service, config):
            return rebuild_service(service, config)
        replacement = copy(service)
        replacement.config = deepcopy(config)
        replacement.pipeline = copy(service.pipeline)
        p = replacement.pipeline
        retrieval, fusion = config.get("retriever", {}), config.get("fusion", {})
        p.mode = retrieval.get("mode", "hybrid")
        p.bm25_top_k = retrieval.get("bm25_top_k", 20)
        p.dense_top_k = retrieval.get("dense_top_k", 20)
        p.rerank_top_k = config.get("reranker", {}).get("top_k", 10)
        p.fusion = (
            RRFFusion(fusion.get("rrf_k", 60))
            if fusion.get("method", "rrf") == "rrf"
            else WeightedFusion(fusion.get("weights"))
        )
        replacement.index_fingerprint = index_fingerprint(config)
        return replacement
