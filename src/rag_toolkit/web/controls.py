"""Shared query controls for Search and Compare."""

import streamlit as st

from rag_toolkit.web.i18n import t
from rag_toolkit.web.services.query import QueryOptions


def query_controls(prefix, service):
    pipeline = service.pipeline
    fusion_config = service.config.get("fusion", {})
    weights = fusion_config.get("weights", {"bm25": 0.4, "dense": 0.6})
    modes = ["hybrid", "bm25", "dense"] if pipeline.dense else ["bm25"]
    methods = ["rrf", "weighted"]
    with st.expander(t("高级查询参数")):
        mode = st.selectbox(
            t("召回模式"), modes, index=modes.index(pipeline.mode), key=prefix + "mode"
        )
        bm25_k = st.number_input(
            "BM25 Top K",
            1,
            max(1000, pipeline.bm25_top_k),
            pipeline.bm25_top_k,
            key=prefix + "bm25",
        )
        dense_k = st.number_input(
            "Dense Top K",
            1,
            max(1000, pipeline.dense_top_k),
            pipeline.dense_top_k,
            key=prefix + "dense",
            disabled=pipeline.dense is None,
        )
        fusion = st.selectbox(
            t("融合方式"),
            methods,
            index=methods.index(fusion_config.get("method", "rrf")),
            key=prefix + "fusion",
        )
        rrf_default = fusion_config.get("rrf_k", 60)
        rrf_k = st.number_input(
            "RRF K", 0, max(10000, rrf_default), rrf_default, key=prefix + "rrf"
        )
        bm25_weight = st.number_input(
            "BM25 weight", min_value=0.0, value=float(weights.get("bm25", 0.4)), key=prefix + "bw"
        )
        dense_weight = st.number_input(
            "Dense weight", min_value=0.0, value=float(weights.get("dense", 0.6)), key=prefix + "dw"
        )
        st.caption(t("权重仅用于 Weighted Fusion；RRF 使用排名与 RRF K。"))
        if service.pipeline.reranker is None:
            st.caption(t("未配置 Reranker，请通过启动配置加载模型。"))
        rerank = st.checkbox(
            t("启用重排"),
            value=service.pipeline.reranker is not None,
            disabled=service.pipeline.reranker is None,
            key=prefix + "rerank",
        )
        rerank_k = st.number_input(
            t("重排候选数"),
            1,
            max(1000, pipeline.rerank_top_k),
            pipeline.rerank_top_k,
            key=prefix + "rk",
        )
    return dict(
        mode=mode,
        bm25_top_k=int(bm25_k),
        dense_top_k=int(dense_k),
        fusion=fusion,
        rrf_k=int(rrf_k),
        bm25_weight=bm25_weight,
        dense_weight=dense_weight,
        rerank=rerank,
        rerank_top_k=int(rerank_k),
    )


def options(values, top_k):
    return QueryOptions(**values, top_k=int(top_k))
