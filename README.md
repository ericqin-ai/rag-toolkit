<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/banner-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="docs/assets/banner-light.svg">
  <img alt="rag-toolkit — Build. Inspect. Compare. Evaluate." src="docs/assets/banner-light.svg" width="1200">
</picture>

[![CI](https://github.com/ericqin-ai/rag-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/ericqin-ai/rag-toolkit/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-6366F1)](pyproject.toml)
[![MIT License](https://img.shields.io/badge/license-MIT-6366F1)](LICENSE)

**English** | [简体中文](README.zh-CN.md)

# rag-toolkit

**An open-source workbench for retrieval engineering.**

Build hybrid retrieval pipelines, inspect candidate rankings, compare strategies,
and evaluate retrieval quality with a Python SDK and a visual workbench.
Designed for retrieval engineers working with their own documents and relevance labels.

[Quick start](#quick-start) · [Documentation](docs/index.md) · [Screenshots](docs/screenshots.md)

## Product Preview

![Inspector ranking paths: independent BM25 and Dense recall feed fusion and reranking](docs/assets/screenshots/inspector-chart-desktop.png)

**Visual Inspector** — follow candidates from independent recall through fusion and reranking.
Actual application capture using bundled sample data and **Offline Pipeline Sanity Check**
providers. Displayed timings describe one run, not production performance.
[Browse the full gallery and capture recipe](docs/screenshots.md).

## Features

| Capability | What you can do |
|---|---|
| **Hybrid Retrieval** | Combine BM25 and Dense with RRF or weighted fusion; add an optional reranker. |
| **Visual Inspector** | Inspect candidate ranks, scores, dropped candidates and stage timings. |
| **Strategy Comparison** | Compare retrieval configurations on the same documents and relevance labels. |
| **Evaluation** | Measure Hit@K, Recall@K, MRR and NDCG; inspect query timings and export reports. |

Import TXT, Markdown or JSONL. Start offline with FAISS, then configure learned
embeddings, rerankers or an Elasticsearch adapter. [Providers and configuration](docs/configuration.md).

## Quick Start

With **Python 3.11+** and [uv](https://docs.astral.sh/uv/getting-started/installation/)
installed, run from the repository root:

```sh
uv sync --locked
uv run python examples/readme_sdk.py
uv run streamlit run src/rag_toolkit/web/app.py --server.address 127.0.0.1 --server.port 8507 --server.headless true
```

Open [localhost:8507](http://127.0.0.1:8507), choose **Datasets → Load sample data**,
run a Search, then open Inspector or Compare.

The default pipeline uses offline sanity providers and needs no model downloads.
Dependency installation may access the network. `configs/default.yaml` instead
requests real local models; see the [configuration guide](docs/configuration.md).

## Python SDK Example

This **Offline Pipeline Sanity Check** uses hash embeddings and token-overlap
reranking. It validates the chain, not learned semantic retrieval quality.
The executable source is [examples/readme_sdk.py](examples/readme_sdk.py).

```python
from rag_toolkit.pipeline import RetrievalPipeline
from rag_toolkit.schemas import Document

pipeline = RetrievalPipeline.from_config("configs/offline.yaml")
pipeline.add_documents(
    [
        Document(id="intro", text="FAISS supports vector search."),
        Document(id="lexical", text="BM25 supports lexical search."),
    ]
)
response = pipeline.search("vector search", top_k=2)
assert response.results[0].doc_id == "intro"
print("Offline Pipeline Sanity Check")
print(response.model_dump_json(indent=2))
```

## Architecture

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/architecture-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="docs/assets/architecture-light.svg">
  <img alt="Query → independent BM25 / Dense → Fusion → Optional Reranker → Results + StageTrace → Inspector / Evaluation" src="docs/assets/architecture-light.svg" width="680">
</picture>

BM25 and Dense recall independently; the current implementation executes them
sequentially. The diagram shows the hybrid path; reranking can be bypassed.
[Algorithms, data contracts and index ownership](docs/architecture.md).

## Benchmark Status

Real-model/public-dataset benchmarks are **not yet completed**.
Offline sanity reports validate the pipeline only.
[Benchmark status, recorded report and planned protocol](docs/benchmarks.md).

## Documentation

| Guide | Start here for |
|---|---|
| [Documentation index](docs/index.md) | All guides and project notes |
| [Web workbench](docs/web-workbench.md) | Inspector, Compare and Evaluation workflows |
| [Configuration](docs/configuration.md) | Providers, parameters and index rebuilds |
| [Architecture](docs/architecture.md) | Retrieval strategies and data contracts |
| [HTTP API](docs/api.md) | Routes, schemas and request examples |
| [Development](docs/development.md) | Contribution, tests, CI and Docker |
| [Known limits](docs/limitations.md) | In-memory state, scale and integration boundaries |

## Roadmap

- [x] Hybrid retrieval, stage traces, comparison and evaluation workbench.
- [x] Offline verification and real application screenshots.
- [ ] Reproducible real-model/public-dataset benchmarks with raw results.
- [ ] Durable index restore, shared worker state and deployment authentication.
- [ ] Concrete PDF loading and semantic splitting extensions.

## License

[MIT](LICENSE), including the original brand SVGs. Optional model weights and
third-party dependencies retain their own licenses.
