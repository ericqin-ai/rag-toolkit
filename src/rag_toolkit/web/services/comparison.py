"""Run actual retrieval variants; no synthetic scores or substitute models."""

from dataclasses import replace

import numpy as np

from rag_toolkit.evaluation import Evaluator
from rag_toolkit.web.services.bad_cases import infer_bad_case
from rag_toolkit.web.services.query import run_query


def compare(service, queries, options, qrels=None):
    variants = [
        ("BM25", replace(options, mode="bm25", rerank=False)),
        ("Dense", replace(options, mode="dense", rerank=False)),
        ("Hybrid RRF", replace(options, mode="hybrid", fusion="rrf", rerank=False)),
        ("Hybrid Weighted", replace(options, mode="hybrid", fusion="weighted", rerank=False)),
        ("Hybrid + Reranker", replace(options, mode="hybrid", fusion="rrf", rerank=True)),
    ]
    rows = []
    for name, settings in variants:
        row = {"name": name, "config": settings.to_dict()}
        if (settings.mode != "bm25" and service.pipeline.dense is None) or (
            settings.rerank and service.pipeline.reranker is None
        ):
            rows.append({**row, "status": "unavailable"})
            continue
        responses = [run_query(service, q, settings) for q in queries]
        latencies = [r.total_latency_ms for r in responses]
        judged = [r for r in responses if qrels and r.query in qrels]
        metrics = Evaluator().evaluate(judged, qrels, [options.top_k]).metrics if judged else None
        rows.append(
            {
                **row,
                "status": "ok",
                "metrics": metrics,
                "judged_queries": len(judged),
                "latency": {
                    "avg_ms": float(np.mean(latencies)) if latencies else None,
                    "p95_ms": float(np.percentile(latencies, 95)) if latencies else None,
                    "samples": len(latencies),
                },
                "responses": [r.model_dump() for r in responses],
                "diagnostics": [infer_bad_case(r, (qrels or {}).get(r.query)) for r in responses],
            }
        )
    offline = (
        service.config.get("embedding", {}).get("provider") == "hash_stub"
        or service.config.get("reranker", {}).get("provider") == "token_overlap"
    )
    return {
        "variants": rows,
        "index_build_included": False,
        "purpose": "Offline Pipeline Sanity Check" if offline else "Retrieval comparison",
        "index_fingerprint": service.index_fingerprint,
    }
