import streamlit as st

from rag_toolkit.web.i18n import t
from rag_toolkit.web.model_controls import pending_rebuild
from rag_toolkit.web.services.status import overview_status


def render(service):
    st.header("Overview")
    status = overview_status(service)
    if pending_rebuild(service):
        status["index_state"] = "rebuild_required"
    left, right = st.columns(2)
    left.metric(t("文档数"), status["num_documents"])
    right.metric("Chunks", status["num_chunks"])
    st.subheader(t("当前模型与索引状态"))
    st.json(status)
    st.caption(t("远程连接未主动探测；ready 表示当前会话索引已构建，不代表远程服务健康。"))
    st.subheader(t("检索流水线"))
    p = service.pipeline
    edges = ["digraph { rankdir=LR; Documents -> Splitter;"]
    if p.mode in ("bm25", "hybrid"):
        edges += ["Splitter -> BM25; Query -> BM25;"]
    if p.mode in ("dense", "hybrid"):
        edges += [
            "Splitter -> Embedding -> VectorStore; Query -> EmbeddingQuery -> Dense;",
            "VectorStore -> Dense;",
        ]
    source = "Fusion" if p.mode == "hybrid" else ("BM25" if p.mode == "bm25" else "Dense")
    if p.mode == "hybrid":
        edges += ["BM25 -> Fusion; Dense -> Fusion;"]
    edges += [f"{source} -> Reranker -> Results;" if p.reranker else f"{source} -> Results;", "}"]
    st.graphviz_chart(" ".join(edges))
    st.subheader(t("最近检索与评测记录"))
    events = st.session_state.get("activity", [])
    if events:
        st.dataframe(list(reversed(events)), hide_index=True, width="stretch")
    else:
        st.info(t("暂无记录，请先运行 Search 或 Evaluation。"))
