"""Run with: uv run streamlit run src/rag_toolkit/web/app.py."""

import streamlit as st

from rag_toolkit.web import compare, data_view, evaluation, inspection, overview, search, settings
from rag_toolkit.web.i18n import t
from rag_toolkit.web.model_controls import pending_rebuild
from rag_toolkit.web.services.configuration import redact
from rag_toolkit.web.session import create_session_service


def main():
    st.set_page_config(page_title="Retrieval Workbench", layout="wide")
    st.sidebar.selectbox("语言 / Language", ["中文", "English"], key="language")
    st.title("Retrieval Workbench")
    if "service" not in st.session_state:
        try:
            st.session_state["service"] = create_session_service()
        except Exception:
            st.error(t("无法初始化检索服务，请检查 RAG_TOOLKIT_CONFIG。"))
            st.stop()
    service = st.session_state["service"]
    view = st.sidebar.radio(
        t("视图"),
        ["Search", "Inspector", "Compare", "Overview", "Evaluation", "Datasets", "Settings"],
        key="navigation",
    )
    stats = service.stats()
    st.sidebar.caption(f"Documents: {stats['num_documents']} · Chunks: {stats['num_chunks']}")
    embedding = service.config.get("embedding", {})
    st.sidebar.text(str(redact(embedding.get("model_name", embedding.get("provider", "none")))))
    if embedding.get("provider") == "hash_stub" or (
        service.config.get("reranker", {}).get("provider") == "token_overlap"
    ):
        st.sidebar.warning("Offline Pipeline Sanity Check")
    renderers = {
        "Search": search.render,
        "Inspector": inspection.render,
        "Compare": compare.render,
        "Evaluation": evaluation.render,
        "Datasets": data_view.render,
        "Overview": overview.render,
        "Settings": settings.render,
    }
    if view in ("Compare", "Inspector", "Evaluation") and pending_rebuild(service):
        st.warning(t("模型配置已改变，请重建索引后查询。"))
        return
    renderers[view](service)


if __name__ == "__main__":
    main()
