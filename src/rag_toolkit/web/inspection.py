import pandas as pd
import streamlit as st

from rag_toolkit.web.inspector import latency_rows, ranking_rows


def render(service):
    st.header("Inspector")
    response = st.session_state.get("last_search")
    if response is None:
        st.info("请先在 Search 中执行检索。")
        return
    st.caption(f"查询：{response.query}")
    ranks = ranking_rows(response)
    st.subheader("阶段排名变化")
    st.caption(
        "包含后续被淘汰的候选；空值表示未进入该阶段。rank_change 正值表示名次提升。"
        "BM25 与 Dense 是并行召回，二者排名差异表示比较，不代表处理先后。"
    )
    st.dataframe(ranks, hide_index=True, width="stretch")
    if ranks:
        frame = pd.DataFrame(ranks).set_index("chunk_id")
        columns = [f"{trace.stage}_rank" for trace in response.traces]
        st.line_chart(frame[columns].T, y_label="排名（越小越好）")
    st.subheader("阶段耗时")
    times = latency_rows(response)
    st.dataframe(times, hide_index=True, width="stretch")
    st.bar_chart(pd.DataFrame(times).set_index("stage")[["latency_ms"]])
    st.metric("总耗时（ms）", f"{response.total_latency_ms:.3f}")
    with st.expander("原始 StageTrace"):
        st.json([trace.model_dump() for trace in response.traces])
