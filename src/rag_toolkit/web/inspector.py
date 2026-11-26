"""Presentation data derived from actual trace candidates, including dropped chunks."""


def ranking_rows(response):
    stages = [trace.stage for trace in response.traces]
    rows = {}
    for trace in response.traces:
        for item in trace.candidates:
            key = (item.doc_id, item.chunk_id)
            row = rows.setdefault(
                key,
                {
                    "doc_id": item.doc_id,
                    "chunk_id": item.chunk_id,
                    "final_rank": None,
                    **{
                        f"{stage}_{field}": None
                        for stage in stages
                        for field in ("rank", "score", "rank_change")
                    },
                },
            )
            row[f"{trace.stage}_rank"] = item.rank
            row[f"{trace.stage}_score"] = item.score
            previous = (
                row.get("fusion_rank") or row.get("bm25_rank") or row.get("dense_rank")
                if trace.stage == "rerank"
                else None
            )
            if previous is not None:
                row[f"{trace.stage}_rank_change"] = previous - item.rank
            if trace.stage == "fusion":
                for channel in ("bm25", "dense"):
                    rank = row.get(f"{channel}_rank")
                    row[f"fusion_from_{channel}_change"] = rank - item.rank if rank else None
    for result in response.results:
        key = (result.doc_id, result.chunk_id)
        if key in rows:
            rows[key]["final_rank"] = result.rank
    for row in rows.values():
        row["status"] = "retained" if row["final_rank"] is not None else "dropped"
    return sorted(
        rows.values(),
        key=lambda row: (
            row["final_rank"] if row["final_rank"] is not None else float("inf"),
            row["doc_id"],
            row["chunk_id"],
        ),
    )


def latency_rows(response):
    rows = [
        {"stage": trace.stage, "latency_ms": trace.latency_ms, "candidates": len(trace.candidates)}
        for trace in response.traces
    ]
    rows.append(
        {
            "stage": "overhead",
            "latency_ms": max(
                0.0, response.total_latency_ms - sum(t.latency_ms for t in response.traces)
            ),
            "candidates": None,
        }
    )
    return rows
