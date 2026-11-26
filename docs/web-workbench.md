# Retrieval Workbench

## RAG Inspector

```sh
uv run streamlit run src/rag_toolkit/web/app.py --server.address 127.0.0.1
```

Open [the Inspector](http://127.0.0.1:8501), select **Datasets**, and explicitly load
the sample dataset or upload your own:

- **Search:** BM25/Dense/Hybrid, recall/final top-k, RRF/weighted fusion,
  reranker controls, chunk text, metadata, stage scores and JSON download.
  Embedding drafts disable queries until a fresh index has been built successfully.
- **Inspector:** all stage candidates including dropped chunks, rank changes,
  independent BM25/Dense Plotly paths into fusion/reranking, stage durations and
  orchestration overhead, raw trace viewing and export.
- **Compare:** execute BM25, Dense, Hybrid RRF, Hybrid Weighted and Hybrid +
  Reranker on the same indexed data. Inspect candidates, rankings, scores and
  query latency; labeled queries add Hit/Recall/MRR/NDCG and Avg/P95 with sample
  counts. Unavailable models are explicit. Save session configurations or download
  redacted configurations/reports. Hash/token results remain labeled as offline
  sanity checks, including exported reports.
- **Overview:** document/chunk counts, active models, store/index status, the actual
  retrieval architecture and bounded session-local search/evaluation history.
- **Evaluation:** import judgments, choose current or multiple retrieval strategies
  and K values, compare real aggregate/per-query metrics with Plotly, filter failures
  and inspect their StageTrace. Diagnosis labels are rule-based clues, never
  automatically confirmed root causes. Export JSON, CSV (summary and per-query
  rows) or Markdown; CSV formula-like query values are escaped.
- **Datasets:** import TXT/Markdown/document JSONL and query-label JSONL;
  preview documents/chunks, edit/replace/clear judgments, inspect safe validation
  line numbers and index status, export data or clear it while preserving settings.
  Public repository samples are bundled under the repository's MIT license and
  load without a network request.
- **Settings:** configure supported embedding/reranker providers, models/devices,
  vector stores, splitter, lexical BM25 tokenizer and default retrieval parameters.
  Query-only changes reuse vectors; index/model changes build a replacement before
  activation. YAML/JSON imports reject plaintext credentials; redacted exports can
  round-trip existing credentials for the same provider/endpoint. Use environment
  variables for OpenAI-compatible API keys. No credential input fields are exposed.

The sidebar offers Chinese/English and seven navigation entries. Light/Dark follows
Streamlit's native theme menu; Plotly uses the Streamlit theme, with no global CSS
overrides. See [Round 1 design](v02-round1-design.md) and [Round 2 plan](v02-round2-plan.md).
The optional `tokenizer: {type: builtin | whitespace}` selects only BM25 lexical
tokenization. Real embedding models keep their own internal tokenizer; existing
configurations retain the original CJK/Latin tokenizer by default. Remote store
connectivity is not actively probed on Overview: local index readiness is distinct
from remote service health.

Web sessions have independent pipelines. The Web UI runs retrieval directly and
has a separate index from the API. Dataset changes and failed submissions clear
outdated results. Elasticsearch-backed Web sessions use unique index suffixes;
old remote session indexes need an external cleanup/lifecycle policy.


[Documentation index](index.md)
