"""Run with: uv run streamlit run src/rag_toolkit/web/app.py."""

import streamlit as st

from rag_toolkit.web import data_view, evaluation, inspection, search
from rag_toolkit.web.session import create_session_service


def main():
    st.set_page_config(page_title="RAG Inspector", page_icon="🔎", layout="wide")
    st.title("RAG Inspector")
    if "service" not in st.session_state:
        try:
            st.session_state["service"] = create_session_service()
        except Exception:
            st.error("无法初始化检索服务，请检查 RAG_TOOLKIT_CONFIG。")
            st.stop()
    service = st.session_state["service"]
    view = st.sidebar.radio("视图", ["Search", "Inspector", "Evaluation", "Datasets"])
    stats = service.stats()
    st.sidebar.caption(f"{stats['num_documents']} 篇文档 · {stats['num_chunks']} 个 chunk")
    pipeline = service.pipeline
    st.sidebar.caption(
        f"模式：{pipeline.mode} · "
        f"嵌入：{type(pipeline.dense.embedder).__name__ if pipeline.dense else '未使用'} · "
        f"重排：{type(pipeline.reranker).__name__ if pipeline.reranker else '关闭'}"
    )
    renderers = {
        "Search": search.render,
        "Inspector": inspection.render,
        "Evaluation": evaluation.render,
        "Datasets": data_view.render,
    }
    renderers[view](service)


if __name__ == "__main__":
    main()
