# Configuration reference

Configuration is a YAML path or mapping passed to `RetrievalPipeline.from_config`.
`configs/default.yaml` requests local BGE embeddings; `configs/offline.yaml` is an
explicit **Offline Pipeline Sanity Check** using hash/token implementations.
API/Web startup without `RAG_TOOLKIT_CONFIG` uses offline providers for a working
CPU-only first run. Paths are relative to the launch directory.

## Parameters

Defaults below describe `from_config`, unless marked Web-only. Provider-specific
parameters apply only to the named provider; do not pass devices to hash/API models.

| Section / key | Type / choices | Default | Scope |
|---|---|---|---|
| splitter.type | fixed / markdown_header | fixed | Rebuild chunks/index |
| splitter.chunk_size | positive integer, characters | 512 | Rebuild |
| splitter.chunk_overlap | integer, 0 <= overlap < size | 64 | Rebuild |
| tokenizer.type | builtin / whitespace | builtin | Rebuild BM25; Web rebuilds replacement index |
| embedding.provider | local / openai_compatible / hash_stub | local | Rebuild vectors |
| embedding.model_name | string | BAAI/bge-small-zh-v1.5 | Rebuild; ignored by hash_stub |
| embedding.device | string, local only | cpu | Model setup; Web replacement |
| embedding.dimension | positive integer, hash_stub only | 256 | Rebuild vectors |
| embedding.base_url | HTTP(S) URL, API provider only | https://api.openai.com/v1 | Endpoint identity; rebuild |
| embedding.batch_size | positive integer, API provider only | 64 | API request batch size |
| embedding.api_key | optional secret, API provider only | OPENAI_API_KEY environment | Never display/export plaintext; prefer environment |
| store.type | faiss / elasticsearch | faiss | New index |
| store.dimension | positive integer / FAISS auto | FAISS: auto; ES: 256 | Must match embedder |
| store.url | HTTP(S) URL, ES only | http://localhost:9200 | New isolated Web index |
| store.index_name | string, ES only | rag-toolkit | Web adds session-specific names |
| retriever.mode | bm25 / dense / hybrid | hybrid | Query-time if required components are loaded |
| retriever.bm25_top_k | positive integer | 20 | BM25 candidate budget |
| retriever.dense_top_k | positive integer | 20 | Dense candidate budget |
| retriever.final_top_k | integer 1..1000 | 5 | Optional Web Search default only; SDK/API accept top_k per call |
| fusion.method | rrf / weighted | rrf | Query-time |
| fusion.rrf_k | nonnegative integer | 60 | Query-time |
| fusion.weights | nonnegative bm25/dense values, positive sum | bm25: 0.4, dense: 0.6 | Weighted only; normalized by sum |
| reranker.enabled | boolean | false | Use loaded model, or load via Settings replacement |
| reranker.provider | cross_encoder / token_overlap | cross_encoder | Model setup |
| reranker.model_name | string | BAAI/bge-reranker-base | Model setup; ignored by token_overlap |
| reranker.device | string, CrossEncoder only | cpu | Model setup |
| reranker.top_k | positive integer | 10 | Query-time reranking candidate pool |

`builtin` tokenization uses lowercase Latin words/numbers and individual CJK
characters. `whitespace` uses lowercase whitespace-separated tokens. This setting
only affects BM25; real embedding models retain their internal tokenizer.

## Applying settings safely

Search controls affect that query. Settings manage startup-style defaults and
model/index configuration. A compatible query-only update reuses indexed vectors.
Index/model changes build a fresh service before replacing the active service;
failure keeps the old service. Changed model drafts block searches against the old
vectors. Effective defaults are normalized when comparing index identities.

Settings do not offer an API-key input. Exported JSON is redacted, including URL
credentials and sensitive query parameters. YAML/JSON import rejects plaintext
credentials. A redacted round trip may reuse the current secret only for the same
provider/endpoint; a fresh session should use environment-provided credentials.
Never paste credentials into model names, document text or connection widgets.

## Optional integrations

Install `local` extras for Sentence Transformers / CrossEncoder or `elasticsearch`
extras for a separately running Elasticsearch service. First local model loading
may download weights. These live integrations and model quality have not been
verified in this release's offline acceptance. See [limits](limitations.md).
Set `RAG_TOOLKIT_CONFIG` to the desired YAML path before starting the API/Web;
keep `OPENAI_API_KEY` outside source control. The SDK also accepts injected clients
and models for advanced integration/testing.

[Documentation index](index.md)


## Web theme

`.streamlit/config.toml` leaves the base theme unset and supplies native
`theme.light` / `theme.dark` accent colors. The locked Streamlit version was
browser-checked in both modes. Plotly receives `theme="streamlit"` and transparent
figure backgrounds; no global CSS theme replacement is used.
