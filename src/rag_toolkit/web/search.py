import streamlit as st


def render(service):
    st.header("Search")
    st.caption("检索当前会话中的文档；在 Datasets 中加载或上传数据。")
    with st.form("search_form"):
        query = st.text_input("查询", placeholder="例如：FAISS CPU 向量")
        top_k = st.number_input("返回数量", min_value=1, max_value=1000, value=5)
        submitted = st.form_submit_button("搜索")
    if submitted:
        st.session_state.pop("last_search", None)
        if not query.strip():
            st.warning("请输入查询。")
        else:
            try:
                st.session_state["last_search"] = service.search(query, int(top_k))
            except Exception:
                st.error("检索失败，请检查模型与服务配置。")
    response = st.session_state.get("last_search")
    if response is not None:
        st.caption(f"结果查询：{response.query}")
        st.metric("总耗时（ms）", f"{response.total_latency_ms:.3f}")
        if not response.results:
            st.info("没有检索结果，请检查数据集和查询。")
        for result in response.results:
            with st.expander(
                f"#{result.rank} · {result.doc_id} · score={result.score:.4f}", expanded=True
            ):
                st.text(result.text)
                st.json(
                    {
                        "chunk_id": result.chunk_id,
                        "metadata": result.metadata,
                        "stage_ranks": result.stage_ranks,
                        "stage_scores": result.stage_scores,
                    }
                )
        st.download_button(
            "下载搜索结果",
            response.model_dump_json(indent=2),
            file_name="search.json",
            mime="application/json",
        )
