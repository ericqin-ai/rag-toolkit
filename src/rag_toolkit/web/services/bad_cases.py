"""Trace-based diagnostic hints, not causal claims."""


def infer_bad_case(response, relevant):
    if not relevant:
        return "unjudged"
    if any(r.doc_id in relevant for r in response.results):
        return "hit"
    stages = {t.stage: {c.doc_id for c in t.candidates} for t in response.traces}
    if not (stages.get("bm25", set()) | stages.get("dense", set())) & set(relevant):
        return "retrieval_miss"
    if "fusion" in stages and not stages["fusion"] & set(relevant):
        return "fusion_drop"
    if "rerank" in stages:
        return "rerank_or_candidate_cutoff"
    return "final_cutoff"
