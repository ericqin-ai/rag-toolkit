"""Actual multi-strategy evaluation and portable, credential-safe reports."""

import csv
import io
from dataclasses import replace

import numpy as np

from rag_toolkit.evaluation import Evaluator
from rag_toolkit.web.services.configuration import redact, safe_json
from rag_toolkit.web.services.query import QueryOptions, run_query

STRATEGIES = ["Current", "BM25", "Dense", "Hybrid RRF", "Hybrid Weighted", "Hybrid + Reranker"]


def diagnose(response, relevant, pool_size):
    relevant = set(relevant)
    stages = {t.stage: {c.chunk_id: c for c in t.candidates} for t in response.traces}
    clues = []
    recalled = [
        c for s in ("bm25", "dense") for c in stages.get(s, {}).values() if c.doc_id in relevant
    ]
    fused = [c for c in stages.get("fusion", {}).values() if c.doc_id in relevant]
    final_hit = any(r.doc_id in relevant for r in response.results)
    if relevant and not recalled:
        clues.append("recall_omission")
    if recalled and "fusion" in stages:
        if not fused or any(c.rank > min(r.rank for r in recalled) for c in fused):
            clues.append("fusion_demotion")
    source = list(stages.get("fusion", stages.get("bm25", stages.get("dense", {}))).values())
    if "rerank" in stages:
        pool = [c for c in source if c.rank <= pool_size and c.doc_id in relevant]
        if any(c.doc_id in relevant and c.rank > pool_size for c in source):
            clues.append("candidate_truncation")
        if pool and not final_hit:
            clues.append("rerank_deviation")
    elif recalled and not final_hit:
        clues.append("final_truncation")
    return {
        "kind": "rule_based_clues",
        "confirmed_root_cause": None,
        "clues": clues,
        "hit": final_hit,
        "relevant_doc_ids": sorted(relevant),
    }


def evaluate_strategies(service, labels, strategies, top_k, ks):
    if not labels or not strategies or set(strategies) - set(STRATEGIES):
        raise ValueError("queries and supported strategies are required")
    if any(type(k) is not int or k < 1 or k > top_k for k in ks) or not ks:
        raise ValueError("invalid evaluation K")
    config = service.config
    p = service.pipeline
    fusion = config.get("fusion", {})
    weights = fusion.get("weights", {"bm25": 0.4, "dense": 0.6})
    base = QueryOptions(
        mode=p.mode,
        bm25_top_k=p.bm25_top_k,
        dense_top_k=p.dense_top_k,
        top_k=top_k,
        fusion=fusion.get("method", "rrf"),
        rrf_k=fusion.get("rrf_k", 60),
        bm25_weight=weights.get("bm25", 0.4),
        dense_weight=weights.get("dense", 0.6),
        rerank=p.reranker is not None,
        rerank_top_k=p.rerank_top_k,
    )
    choices = {
        "Current": base,
        "BM25": replace(base, mode="bm25", rerank=False),
        "Dense": replace(base, mode="dense", rerank=False),
        "Hybrid RRF": replace(base, mode="hybrid", fusion="rrf", rerank=False),
        "Hybrid Weighted": replace(base, mode="hybrid", fusion="weighted", rerank=False),
        "Hybrid + Reranker": replace(base, mode="hybrid", fusion="rrf", rerank=True),
    }
    rows = []
    qrels = {q.query: set(q.relevant_doc_ids) for q in labels}
    if len(qrels) != len(labels):
        raise ValueError("duplicate queries")
    for name in strategies:
        options = choices[name]
        if (options.mode != "bm25" and p.dense is None) or (options.rerank and p.reranker is None):
            rows.append({"name": name, "status": "unavailable", "per_query": []})
            continue
        responses = [run_query(service, q.query, options) for q in labels]
        report = Evaluator().evaluate(responses, qrels, ks)
        latency = [r.total_latency_ms for r in responses]
        rows.append(
            {
                "name": name,
                "status": "ok",
                "config": options.to_dict(),
                "metrics": report.metrics,
                "num_queries": report.num_queries,
                "avg_ms": float(np.mean(latency)),
                "p95_ms": float(np.percentile(latency, 95)),
                "per_query": [
                    {
                        **row,
                        "response": response.model_dump(),
                        "diagnosis": diagnose(
                            response, qrels[response.query], options.rerank_top_k
                        ),
                    }
                    for row, response in zip(report.per_query, responses)
                ],
            }
        )
    offline = (
        config.get("embedding", {}).get("provider") == "hash_stub"
        or config.get("reranker", {}).get("provider") == "token_overlap"
    )
    return {
        "strategies": rows,
        "purpose": "Offline Pipeline Sanity Check" if offline else "Retrieval evaluation",
        "ks": ks,
        "top_k": top_k,
        "index_fingerprint": service.index_fingerprint,
        "diagnosis_notice": "Rule-based clues only; no confirmed root causes.",
    }


def flat_rows(report):
    summaries = [
        {
            "row_type": "summary",
            "strategy": s["name"],
            "query": "",
            **s.get("metrics", {}),
            "num_queries": s.get("num_queries", 0),
            "avg_ms": s.get("avg_ms"),
            "p95_ms": s.get("p95_ms"),
            "status": s["status"],
            "purpose": report["purpose"],
        }
        for s in report["strategies"]
    ]
    queries = [
        {
            "strategy": s["name"],
            "row_type": "query",
            "query": q["query"],
            **q["metrics"],
            "latency_ms": q["response"]["total_latency_ms"],
            "clues": ", ".join(q["diagnosis"]["clues"]),
            "confirmed_root_cause": "",
            "purpose": report["purpose"],
        }
        for s in report["strategies"]
        for q in s["per_query"]
    ]
    return summaries + queries


def export_report(report, fmt):
    report = redact(report)
    if fmt == "json":
        return safe_json(report)
    rows = flat_rows(report)
    if not rows:
        return report["diagnosis_notice"]
    headers = list(dict.fromkeys(k for row in rows for k in row))
    if fmt == "csv":
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    k: "'" + v
                    if isinstance(v, str) and v.lstrip().startswith(("=", "+", "-", "@"))
                    else v
                    for k, v in row.items()
                }
            )
        return stream.getvalue()
    if fmt != "markdown":
        raise ValueError("unsupported report format")

    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")

    lines = [
        "# Retrieval Evaluation",
        report["purpose"],
        report["diagnosis_notice"],
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines += ["| " + " | ".join(cell(row.get(k, "")) for k in headers) + " |" for row in rows]
    lines += [
        "",
        "## Summary",
        safe_json([{k: v for k, v in s.items() if k != "per_query"} for s in report["strategies"]]),
    ]
    return "\n".join(lines)
