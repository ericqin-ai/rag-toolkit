import streamlit as st

from rag_toolkit.api.models import EvaluateRequest


def render(service):
    st.header("Evaluation")
    queries = st.session_state.get("queries", [])
    st.caption("二元相关性、文档去重、宏平均；Hash 与词项重排只用于离线链路验证。")
    if not queries:
        st.info("请在 Datasets 中加载相关性标注查询。")
        return
    st.write(f"已加载 {len(queries)} 条标注查询")
    top_k = st.number_input("检索数量", min_value=1, max_value=1000, value=10)
    ks_text = st.text_input("评测 K（逗号分隔）", value="1,3,5")
    if st.button("运行评测"):
        st.session_state.pop("last_report", None)
        try:
            request = EvaluateRequest(
                queries=queries, top_k=int(top_k), ks=[int(k.strip()) for k in ks_text.split(",")]
            )
            st.session_state["last_report"] = service.evaluate(request)
        except ValueError as exc:
            st.error(f"评测参数无效：{exc}")
        except Exception:
            st.error("评测失败，请检查模型与服务配置。")
    report = st.session_state.get("last_report")
    if report is not None:
        st.dataframe(
            [{"metric": name, "value": score} for name, score in report.metrics.items()],
            hide_index=True,
            width="stretch",
        )
        st.dataframe(
            [{"query": row["query"], **row["metrics"]} for row in report.per_query],
            hide_index=True,
            width="stretch",
        )
        st.download_button(
            "下载评测报告",
            report.model_dump_json(indent=2),
            file_name="evaluation.json",
            mime="application/json",
        )
