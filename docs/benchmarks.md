# Benchmark status

**Real-model/public-dataset benchmarks have not been completed.**

## Offline Pipeline Sanity Check

Executed on 2026-11-26 with Python 3.12.9 on Windows:

```sh
uv run python examples/evaluate.py --output datasets/evaluation-report.json
```

Actual output: **6 indexed chunks, 8 evaluated queries**. Configuration:
`configs/offline.yaml` (HashEmbedder, FAISS, hybrid RRF, TokenOverlapReranker),
search top_k=5, evaluation K=1/3/5. Inputs: `datasets/documents.jsonl` and
`datasets/queries.jsonl`. Full per-query output: [recorded report](../datasets/evaluation-report.json).

| Metric | Measured value |
|---|---|
| hit@1 | 1.000 |
| hit@3 | 1.000 |
| hit@5 | 1.000 |
| mrr | 1.000 |
| ndcg@1 | 1.000 |
| ndcg@3 | 1.000 |
| ndcg@5 | 1.000 |
| recall@1 | 0.875 |
| recall@3 | 1.000 |
| recall@5 | 1.000 |

This tiny synthetic set validates the retrieval/evaluation chain. These are not
production benchmarks, real-model scores, throughput measurements, or latency claims.
Evaluation deduplicates document IDs before computing binary relevance metrics,
macro-averages across queries, and scores empty relevance sets as zero. MRR is
computed over the returned ranking and therefore depends on retrieval truncation.


[Documentation index](index.md)

## Future real-model benchmark protocol

Before publishing scores, identify the public dataset/license, exact split/qrels,
model revisions, hardware/device, dependencies, recall/final K, fusion and rerank
parameters. Commit the executable runner and raw per-query outputs. Separate index
build time, warmed repeated query latency and quality metrics. The Web's actual
Avg/P95 samples are useful diagnostics, not a substitute for that protocol.

The offline command and metrics above were re-executed during Round 3 on 2026-11-26
with Python 3.12.9; `datasets/evaluation-report.json` was refreshed from that run.
No real-model quality or production speed claim is implied.
