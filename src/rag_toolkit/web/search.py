import streamlit as st

from rag_toolkit.web import model_controls
from rag_toolkit.web.activity import record_event
from rag_toolkit.web.controls import options, query_controls
from rag_toolkit.web.i18n import t
from rag_toolkit.web.services.configuration import redact, safe_json
from rag_toolkit.web.services.query import run_query


def render(service):
    st.header("Search")
    st.caption(t("模型配置变更后必须重建索引。"))
    if not service.documents:
        st.info(t("暂无文档，请在 Datasets 加载数据。"))
    stale = model_controls.pending_rebuild(service)
    if stale:
        st.warning(t("模型配置已改变，请重建索引后查询。"))
    with st.form("search_form"):
        query = st.text_input(t("查询"), placeholder="FAISS CPU")
        top_k = st.number_input(
            t("返回数量"), 1, 1000, service.config.get("retriever", {}).get("final_top_k", 5)
        )
        values = query_controls("search_", service)
        submitted = st.form_submit_button(t("搜索"), disabled=stale)
    if submitted:
        st.session_state.pop("last_search", None)
        if not query.strip():
            st.warning(t("请输入查询。"))
        else:
            try:
                with st.spinner(t("加载中…")):
                    st.session_state["last_search"] = run_query(
                        service, query, options(values, top_k)
                    )
                response = st.session_state["last_search"]
                record_event(
                    "search",
                    {
                        "query": response.query,
                        "results": len(response.results),
                        "latency_ms": response.total_latency_ms,
                    },
                )
            except Exception:
                st.error(t("检索失败，请检查模型与服务配置。"))
    model_controls.render(service)
    response = st.session_state.get("last_search")
    if response is None or stale:
        return
    st.text(response.query)
    st.metric(t("总耗时（ms）"), f"{response.total_latency_ms:.3f}")
    if not response.results:
        st.info(t("没有检索结果，请检查数据集和查询。"))
    for result in response.results:
        with st.expander(
            f"#{result.rank} · {result.doc_id} · score={result.score:.4f}", expanded=True
        ):
            st.text(result.text)
            st.json(
                redact(
                    {
                        "chunk_id": result.chunk_id,
                        "metadata": result.metadata,
                        "stage_ranks": result.stage_ranks,
                        "stage_scores": result.stage_scores,
                    }
                )
            )
    st.download_button(
        t("下载搜索结果"),
        safe_json(response.model_dump()),
        file_name="search.json",
        mime="application/json",
    )
