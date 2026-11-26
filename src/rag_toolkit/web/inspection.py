import streamlit as st

from rag_toolkit.web.charts import latency_figure, ranking_figure
from rag_toolkit.web.i18n import t
from rag_toolkit.web.inspector import latency_rows, ranking_rows
from rag_toolkit.web.services.configuration import redact, safe_json


def render(service):
    st.header("Inspector")
    response = st.session_state.get("last_search")
    if response is None:
        st.info(t("请先在 Search 中执行检索。"))
        return
    st.text(response.query)
    final = {(r.doc_id, r.chunk_id) for r in response.results}
    for trace in response.traces:
        st.subheader(trace.stage.upper())
        st.dataframe(
            [
                {
                    **c.model_dump(),
                    "status": "retained" if (c.doc_id, c.chunk_id) in final else "dropped",
                }
                for c in trace.candidates
            ],
            hide_index=True,
            width="stretch",
        )
    st.subheader(t("保留与淘汰候选"))
    st.dataframe(ranking_rows(response), hide_index=True, width="stretch")
    st.subheader(t("阶段排名变化"))
    st.caption(t("独立召回通道分别进入融合；空值表示未进入该阶段。"))
    st.plotly_chart(ranking_figure(response), theme="streamlit", width="stretch")
    st.subheader(t("阶段耗时"))
    st.dataframe(latency_rows(response), hide_index=True, width="stretch")
    st.plotly_chart(latency_figure(response), theme="streamlit", width="stretch")
    st.metric(t("总耗时（ms）"), f"{response.total_latency_ms:.3f}")
    raw = [trace.model_dump() for trace in response.traces]
    with st.expander(t("原始 StageTrace")):
        st.json(redact(raw))
    st.download_button(
        t("下载 StageTrace"), safe_json(raw), file_name="traces.json", mime="application/json"
    )
