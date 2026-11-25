# rag-toolkit 开发规范与核心契约

## 项目目标
构建轻量、可配置、可评测、可解释的通用 RAG 检索工具箱（Python 3.11+，`uv` + `pyproject.toml`）。
英文简介：A lightweight and modular retrieval toolkit for hybrid search, reranking, retrieval evaluation, and RAG applications.

## 工程红线
1. **从零干净实现**：仅使用通用开源算法思想独立实现，不包含任何敏感信息或硬编码凭据。
2. **禁止伪实现**：所有 P0 模块必须有真实可运行的实现，不允许空函数、Mock 评测分数或硬编码演示结果。
3. **CPU 优先与离线可测**：`pytest` 单元测试禁止依赖外网下载大模型或连接外部 Elasticsearch/GPU；测试中使用轻量确定性本地 Embedder/Reranker 替身验证算法与链路，真实模型（BGE/Qwen）通过配置加载。
4. **每步必验**：每完成一个阶段必须执行 `uv run pytest` 和 `uv run ruff check .` 并展示真实终端输出。
5. **包入口保持轻量**：禁止在 `__init__.py` 中编写业务逻辑实现；包入口只允许导入转发与 `__all__` 导出，具体类、函数和算法按职责放入独立子模块，跨模块共享工具统一放入 `src/rag_toolkit/utils/`。

## 核心数据结构契约 (`src/rag_toolkit/schemas/`)
- `Document`: `id: str`, `text: str`, `metadata: dict[str, Any]`
- `Chunk`: `chunk_id: str`, `doc_id: str`, `text: str`, `metadata: dict[str, Any]`
- `StageCandidate`: `doc_id: str`, `chunk_id: str`, `score: float`, `rank: int`
- `StageTrace`: `stage: str` (`bm25` | `dense` | `fusion` | `rerank`), `latency_ms: float`, `candidates: list[StageCandidate]`
- `SearchResult`: `doc_id: str`, `chunk_id: str`, `text: str`, `score: float`, `rank: int`, `metadata: dict[str, Any]`, `stage_ranks: dict[str, int | None]`, `stage_scores: dict[str, float | None]`
- `SearchResponse`: `query: str`, `results: list[SearchResult]`, `traces: list[StageTrace]`, `total_latency_ms: float`
- `EvalReport`: `metrics: dict[str, float]` (`hit@k`, `recall@k`, `mrr`, `ndcg@k`), `num_queries: int`, `per_query: list[dict]`

## 配置文件契约 (`configs/default.yaml`)
```yaml
splitter:
  type: fixed # fixed | markdown_header
  chunk_size: 512
  chunk_overlap: 64
embedding:
  provider: local # local | openai_compatible | hash_stub
  model_name: BAAI/bge-small-zh-v1.5
store:
  type: faiss # faiss | elasticsearch
retriever:
  mode: hybrid # bm25 | dense | hybrid
  bm25_top_k: 20
  dense_top_k: 20
fusion:
  method: rrf # rrf | weighted
  rrf_k: 60
  weights: { bm25: 0.4, dense: 0.6 }
reranker:
  enabled: false
  model_name: BAAI/bge-reranker-base
  top_k: 10
