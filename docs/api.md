# HTTP API

## API

```sh
uv run uvicorn rag_toolkit.api.app:create_app --factory --host 127.0.0.1 --port 8000 --workers 1
```

Open [interactive API docs](http://127.0.0.1:8000/docs).

| Endpoint | Request | Response |
|---|---|---|
| GET /health | none | status, document/chunk counts |
| POST /documents | documents: Document list | counts and added_chunks |
| POST /search | query, top_k (default 10) | SearchResponse with traces |
| POST /evaluate | queries, top_k, ks | EvalReport from executed searches |

Example request bodies, in the same order as the three POST endpoints:

```json
{"documents": [{"id": "intro", "text": "FAISS supports vector search.", "metadata": {}}]}
```

```json
{"query": "FAISS", "top_k": 5}
```

```json
{"queries": [{"query": "FAISS", "relevant_doc_ids": ["intro"]}], "top_k": 5, "ks": [1, 3, 5]}
```

Requests reject unknown fields and duplicate document IDs/query text. API top_k
must be an integer from 1 to 1000; evaluation K values must be positive and no
larger than top_k. Invalid requests return 422 with
`{"error": {"code": "validation_error", "message": "Invalid request", "details": [...]}}`.
Unhandled backend errors return a generic 500. Application logs contain the method, path and exception class, without raw provider exceptions or tracebacks.
Health reports application availability, not external-provider readiness.

The API starts empty. Use one worker: separate workers do not share their indexes.
Restarting loses the in-memory index; existing external vectors alone cannot restore
local chunks or BM25 state. Elasticsearch searches are scoped to the chunks
added to the current pipeline. Use separate indexes for independent writers.


[Documentation index](index.md)

## Response schemas

| Object | Fields |
|---|---|
| Document | `id`, `text`, `metadata` (defaults to an empty mapping) |
| SearchResult | `doc_id`, `chunk_id`, `text`, `score`, `rank`, `metadata`, `stage_ranks`, `stage_scores` |
| StageTrace | `stage` (bm25/dense/fusion/rerank), `latency_ms`, `candidates` |
| StageCandidate | `doc_id`, `chunk_id`, `score`, `rank` |
| SearchResponse | `query`, `results`, `traces`, `total_latency_ms` |
| EvalReport | `metrics`, `num_queries`, `per_query` |

Ranks are one-based; absent stage ranks/scores are null. Results carry chunk text,
while evaluation deduplicates document IDs. The complete machine-readable schema
is `/openapi.json`; interactive documentation is `/docs`. Application exception
middleware consumes handled endpoint failures before the server's exception logger,
so raw provider messages do not propagate for these non-streaming endpoints.
External HTTP/debug logging and provider startup failures are separate operational
concerns; never enable verbose third-party logs with secrets in URLs.
