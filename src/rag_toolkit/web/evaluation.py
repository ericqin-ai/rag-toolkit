import plotly.graph_objects as go
import streamlit as st

from rag_toolkit.schemas import EvalReport
from rag_toolkit.web.activity import record_event
from rag_toolkit.web.datasets import parse_queries
from rag_toolkit.web.i18n import t
from rag_toolkit.web.services.configuration import redact, safe_json
from rag_toolkit.web.services.evaluation import STRATEGIES, evaluate_strategies, export_report


def render(service):
    st.header("Evaluation")
    queries = st.session_state.get("queries", [])
    st.caption(t("二元相关性、文档去重、宏平均；Hash 与词项重排只用于离线链路验证。"))
    if not queries:
        st.info(t("请导入标注 Query，或在 Datasets 加载样例。"))
    top_k = st.number_input(t("检索数量"), 1, 1000, 10, key="eval_top_k")
    ks_text = st.text_input(t("评测 K（逗号分隔）"), value="1,3,5")
    strategies = st.multiselect(
        t("评测策略"), STRATEGIES, default=["Current"], key="eval_strategies"
    )
    if st.button(t("运行评测"), disabled=not queries):
        st.session_state.pop("last_report", None)
        st.session_state.pop("evaluation_report", None)
        try:
            ks = [int(k.strip()) for k in ks_text.split(",")]
            with st.spinner(t("加载中…")):
                report = evaluate_strategies(service, queries, strategies, int(top_k), ks)
            st.session_state["evaluation_report"] = report
            first = next((s for s in report["strategies"] if s["status"] == "ok"), None)
            if first:
                st.session_state["last_report"] = EvalReport(
                    metrics=first["metrics"],
                    num_queries=first["num_queries"],
                    per_query=[
                        {k: v for k, v in q.items() if k in ("query", "ranking", "metrics")}
                        for q in first["per_query"]
                    ],
                )
            record_event(
                "evaluation",
                {
                    "queries": len(queries),
                    "strategies": ", ".join(strategies),
                    "metrics": safe_json(
                        {s["name"]: s.get("metrics", {}) for s in report["strategies"]}
                    ),
                },
            )
        except ValueError:
            st.error(t("评测参数无效。"))
        except Exception:
            st.error(t("评测失败，请检查模型与服务配置。"))
    report = st.session_state.get("evaluation_report")
    if report:
        st.caption(report["purpose"])
        st.warning(t("以下诊断仅为 StageTrace 规则推断线索，不是已确认根因。"))
        summary = [
            {
                "strategy": s["name"],
                "status": s["status"],
                "num_queries": s.get("num_queries", 0),
                **s.get("metrics", {}),
                "avg_ms": s.get("avg_ms"),
                "p95_ms": s.get("p95_ms"),
            }
            for s in report["strategies"]
        ]
        st.dataframe(summary, hide_index=True, width="stretch")
        figure = go.Figure()
        for strategy in report["strategies"]:
            if strategy["status"] == "ok":
                figure.add_bar(
                    name=strategy["name"],
                    x=list(strategy["metrics"]),
                    y=list(strategy["metrics"].values()),
                )
        figure.update_layout(
            barmode="group",
            yaxis_range=[0, 1],
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(figure, theme="streamlit", width="stretch")
        failures = st.checkbox(t("仅显示失败案例"), key="eval_failures")
        query_filter = st.text_input(t("筛选 Query"), key="eval_filter")
        clues = [
            "all",
            "recall_omission",
            "fusion_demotion",
            "candidate_truncation",
            "rerank_deviation",
            "final_truncation",
        ]
        clue = st.selectbox(t("诊断线索筛选"), clues)
        rows = [
            {
                "strategy": s["name"],
                "query": q["query"],
                **q["metrics"],
                "hit": q["diagnosis"]["hit"],
                "rule_based_clues": ", ".join(q["diagnosis"]["clues"]),
            }
            for s in report["strategies"]
            for q in s["per_query"]
            if (not failures or not q["diagnosis"]["hit"])
            and query_filter in q["query"]
            and (clue == "all" or clue in q["diagnosis"]["clues"])
        ]
        st.dataframe(rows, hide_index=True, width="stretch")
        with st.expander(t("逐 Query StageTrace 与诊断证据")):
            items = [(s["name"], q) for s in report["strategies"] for q in s["per_query"]]
            if items:
                idx = st.selectbox(
                    t("选择 Query 记录"),
                    list(range(len(items))),
                    format_func=lambda i: f"{items[i][0]} · {items[i][1]['query']}",
                )
                st.json(redact(items[idx][1]))
        for fmt, suffix, mime in [
            ("json", "json", "application/json"),
            ("csv", "csv", "text/csv"),
            ("markdown", "md", "text/markdown"),
        ]:
            st.download_button(
                t("下载评测报告") + " · " + fmt.upper(),
                export_report(report, fmt),
                file_name=f"evaluation.{suffix}",
                mime=mime,
                key="eval_export_" + fmt,
            )
    with st.expander(t("导入标注 Query")):
        upload = st.file_uploader(t("上传标注查询 JSONL"), type=["jsonl"], key="eval_labels")
        text = st.text_area(t("或粘贴标注 JSONL"), key="eval_labels_text")
        if st.button(t("导入/替换标注"), key="eval_import"):
            try:
                labels = parse_queries(upload.getvalue() if upload else text.encode())
                st.session_state["queries"] = labels
                for key in ("last_report", "evaluation_report", "last_comparison"):
                    st.session_state.pop(key, None)
                st.rerun()
            except ValueError as exc:
                st.error(t("查询格式无效。") + " " + str(exc))
    if queries:
        st.caption(t("已加载 {count} 条标注查询", count=len(queries)))
