"""Safe status snapshots, including only locally known connection/index facts."""

from rag_toolkit.web.services.configuration import redact
from rag_toolkit.web.services.index_state import index_fingerprint, requires_rebuild


def overview_status(service, pending_config=None):
    p = service.pipeline
    invalid = requires_rebuild(service) or (
        pending_config is not None
        and index_fingerprint(pending_config) != service.index_fingerprint
    )
    return redact(
        {
            **service.stats(),
            "retrieval_mode": p.mode,
            "embedding": {
                "config": service.config.get("embedding", {}),
                "implementation": type(p.dense.embedder).__name__ if p.dense else None,
                "state": "loaded" if p.dense else "not_active",
            },
            "reranker": {
                "config": service.config.get("reranker", {}),
                "implementation": type(p.reranker).__name__ if p.reranker else None,
                "state": "loaded" if p.reranker else "disabled",
            },
            "store": service.config.get("store", {"type": "faiss"}),
            "store_state": "active" if p.dense else "not_active",
            "index_state": "rebuild_required" if invalid else ("ready" if p.chunks else "empty"),
            "vector_dimension": getattr(p.dense.store, "dimension", None) if p.dense else None,
            "remote_connectivity": "not_probed",
            "index_fingerprint": service.index_fingerprint,
        }
    )
