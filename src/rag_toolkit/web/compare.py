import streamlit as st

from rag_toolkit.web.controls import options, query_controls
from rag_toolkit.web.i18n import t
from rag_toolkit.web.services.comparison import compare
from rag_toolkit.web.services.configuration import redact, safe_json


def render(service):
    st.header("Compare")
    st.caption(t("查询耗时不含建索引；单样本 P95 不代表稳定基准。"))
    with st.form("compare_form"):
        query = st.text_input(t("查询"), key="compare_query")
        top_k = st.number_input(t("返回数量"), 1, 1000, 5, key="compare_top_k")
        batch = st.checkbox(t("使用已加载标注批量对比"))
        values = query_controls("compare_", service)
        submitted = st.form_submit_button(t("运行对比"))
    if submitted:
        st.session_state.pop("last_comparison", None)
        labels = st.session_state.get("queries", [])
        queries = [q.query for q in labels] if batch else [query]
        if not queries or any(not q.strip() for q in queries):
            st.warning(t("请输入查询。"))
        else:
            try:
                with st.spinner(t("加载中…")):
                    report = compare(
                        service,
                        queries,
                        options(values, top_k),
                        {q.query: set(q.relevant_doc_ids) for q in labels},
                    )
                st.session_state["last_comparison"] = report
            except Exception:
                st.error(t("对比失败，请检查模型与配置。"))
    report = st.session_state.get("last_comparison")
    if not report:
        return
    st.caption(report["purpose"])
    summary = []
    for variant in report["variants"]:
        summary.append(
            {
                "variant": variant["name"],
                "status": variant["status"],
                **(variant.get("metrics") or {}),
                **variant.get("latency", {}),
            }
        )
    st.dataframe(summary, hide_index=True, width="stretch")
    if not any(v.get("metrics") for v in report["variants"]):
        st.info(t("没有标注，指标不适用。"))
    for variant in report["variants"]:
        with st.expander(variant["name"]):
            if variant["status"] != "ok":
                st.info("unavailable")
                continue
            for response, hint in zip(variant["responses"], variant["diagnostics"]):
                st.text(response["query"])
                st.caption(f"{response['total_latency_ms']:.3f} ms · {hint}")
                st.dataframe(redact(response["results"]), hide_index=True, width="stretch")
                for trace in response["traces"]:
                    st.caption(trace["stage"])
                    st.dataframe(trace["candidates"], hide_index=True, width="stretch")
    configs = {v["name"]: v["config"] for v in report["variants"]}
    if st.button(t("保存配置")):
        st.session_state["saved_comparison_config"] = configs
        st.success(t("已保存到当前会话。"))
    st.download_button(
        t("下载配置"),
        safe_json(configs),
        file_name="comparison-config.json",
        mime="application/json",
    )
    st.download_button(
        t("下载报告"), safe_json(report), file_name="comparison.json", mime="application/json"
    )
