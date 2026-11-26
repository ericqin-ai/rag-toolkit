"""Unified configuration UI: credentials never enter widgets or export payloads."""

from copy import deepcopy

import streamlit as st

from rag_toolkit.web.i18n import t
from rag_toolkit.web.services.configuration import redact, safe_json
from rag_toolkit.web.services.settings import apply_config, import_config, rebuild_needed


def activate(service, config):
    try:
        with st.spinner(t("加载中…")):
            replacement = apply_config(service, config)
        st.session_state["service"] = replacement
        st.session_state["_reset_settings_widgets"] = True
        for key in list(st.session_state):
            if key in (
                "pending_config",
                "last_search",
                "last_report",
                "last_comparison",
                "evaluation_report",
            ) or key.startswith(("search_", "compare_", "embedding_")):
                st.session_state.pop(key, None)
        st.session_state["_settings_applied"] = True
        st.rerun()
    except Exception:
        st.error(t("配置无效或重建失败，原服务保持不变。"))


def render(service):
    st.header("Settings")
    if st.session_state.pop("_reset_settings_widgets", False):
        for key in list(st.session_state):
            if key.startswith("set_"):
                st.session_state.pop(key, None)
    if st.session_state.pop("_settings_applied", False):
        st.success(t("配置已应用。"))
    st.caption(t("配置已脱敏，凭据通过环境变量管理。"))
    cfg = service.config
    emb, rr = cfg.get("embedding", {}), cfg.get("reranker", {})
    store, split = cfg.get("store", {}), cfg.get("splitter", {})
    retrieval, fusion = cfg.get("retriever", {}), cfg.get("fusion", {})
    with st.form("settings_form"):
        with st.expander("Embedding / Reranker", expanded=True):
            providers = ["hash_stub", "local", "openai_compatible"]
            ep = st.selectbox(
                "Embedding Provider",
                providers,
                index=providers.index(emb.get("provider", "local")),
                key="set_ep",
            )
            em = st.text_input(
                t("Embedding 模型"), emb.get("model_name", "BAAI/bge-small-zh-v1.5"), key="set_em"
            )
            ed = st.text_input("Embedding device", emb.get("device", "cpu"), key="set_ed")
            dimension = st.number_input(
                "Hash dimension", 1, 65536, emb.get("dimension", 256), key="set_dim"
            )
            endpoint = st.text_input(
                "API endpoint (no credentials)",
                redact(emb.get("base_url", "https://api.openai.com/v1")),
                key="set_endpoint",
            )
            batch_size = st.number_input(
                "API batch size", 1, 1000000, emb.get("batch_size", 64), key="set_batch"
            )
            enabled = st.checkbox(t("启用重排"), rr.get("enabled", False), key="set_enabled")
            rps = ["token_overlap", "cross_encoder"]
            rp = st.selectbox(
                "Reranker Provider",
                rps,
                index=rps.index(rr.get("provider", "cross_encoder")),
                key="set_rp",
            )
            rm = st.text_input(
                "Reranker model", rr.get("model_name", "BAAI/bge-reranker-base"), key="set_rm"
            )
            rd = st.text_input("Reranker device", rr.get("device", "cpu"), key="set_rd")
            rk = st.number_input(t("重排候选数"), 1, 10000, rr.get("top_k", 10), key="set_rk")
        with st.expander(t("向量库与分块")):
            stores = ["faiss", "elasticsearch"]
            kind = st.selectbox(
                "Vector store",
                stores,
                index=stores.index(store.get("type", "faiss")),
                key="set_store",
            )
            url = st.text_input(
                "Elasticsearch URL (no credentials)",
                redact(store.get("url", "http://localhost:9200")),
                key="set_url",
            )
            index = st.text_input(
                "Index name", store.get("index_name", "rag-toolkit"), key="set_index"
            )
            sd = st.number_input(
                "Store dimension (0 = FAISS auto)",
                0,
                65536,
                store.get("dimension") or 0,
                key="set_sd",
            )
            splits = ["fixed", "markdown_header"]
            sp = st.selectbox(
                "Splitter", splits, index=splits.index(split.get("type", "fixed")), key="set_split"
            )
            size = st.number_input(
                "Chunk size", 1, 1000000, split.get("chunk_size", 512), key="set_size"
            )
            overlap = st.number_input(
                "Chunk overlap", 0, 1000000, split.get("chunk_overlap", 64), key="set_overlap"
            )
            tokenizers = ["builtin", "whitespace"]
            tokenizer = st.selectbox(
                "BM25 Tokenizer",
                tokenizers,
                index=tokenizers.index(cfg.get("tokenizer", {}).get("type", "builtin")),
                key="set_tokenizer",
            )
            st.caption(t("Tokenizer 仅用于 BM25；Embedding 使用模型自身的分词器。"))
        with st.expander(t("默认检索参数")):
            modes = ["bm25", "dense", "hybrid"]
            mode = st.selectbox(
                t("召回模式"),
                modes,
                index=modes.index(retrieval.get("mode", "hybrid")),
                key="set_mode",
            )
            bk = st.number_input(
                "BM25 Top K", 1, 10000, retrieval.get("bm25_top_k", 20), key="set_bk"
            )
            dk = st.number_input(
                "Dense Top K", 1, 10000, retrieval.get("dense_top_k", 20), key="set_dk"
            )
            final_k = st.number_input(
                t("返回数量"), 1, 1000, retrieval.get("final_top_k", 5), key="set_fk"
            )
            methods = ["rrf", "weighted"]
            method = st.selectbox(
                t("融合方式"),
                methods,
                index=methods.index(fusion.get("method", "rrf")),
                key="set_fusion",
            )
            rrf = st.number_input("RRF K", 0, 100000, fusion.get("rrf_k", 60), key="set_rrf")
            weights = fusion.get("weights", {"bm25": 0.4, "dense": 0.6})
            bw = st.number_input(
                "BM25 weight", min_value=0.0, value=float(weights.get("bm25", 0.4)), key="set_bw"
            )
            dw = st.number_input(
                "Dense weight", min_value=0.0, value=float(weights.get("dense", 0.6)), key="set_dw"
            )
        st.caption(t("索引相关变更将重建；仅查询参数变更直接生效。"))
        submitted = st.form_submit_button(t("应用配置"))
    if submitted:
        config = deepcopy(cfg)
        if ep == "hash_stub":
            config["embedding"] = {"provider": ep, "dimension": int(dimension)}
        elif ep == "local":
            config["embedding"] = {"provider": ep, "model_name": em, "device": ed}
        else:
            config["embedding"] = {
                "provider": ep,
                "model_name": em,
                "base_url": endpoint,
                "batch_size": int(batch_size),
            }
            if ep == emb.get("provider") and endpoint == redact(
                emb.get("base_url", "https://api.openai.com/v1")
            ):
                config["embedding"]["base_url"] = emb.get("base_url", endpoint)
                if "api_key" in emb:
                    config["embedding"]["api_key"] = emb["api_key"]
        config["reranker"] = {"enabled": enabled, "provider": rp, "top_k": int(rk)}
        if rp == "cross_encoder":
            config["reranker"].update(model_name=rm, device=rd)
        config["store"] = {"type": kind}
        if kind == "elasticsearch":
            config["store"].update(
                url=store.get("url", url) if url == redact(store.get("url", "")) else url,
                index_name=index,
                dimension=int(sd or dimension),
            )
        elif sd:
            config["store"]["dimension"] = int(sd)
        config["splitter"] = {"type": sp, "chunk_size": int(size), "chunk_overlap": int(overlap)}
        config["tokenizer"] = {"type": tokenizer}
        config["retriever"] = {"mode": mode, "bm25_top_k": int(bk), "dense_top_k": int(dk)}
        config["retriever"]["final_top_k"] = int(final_k)
        config["fusion"] = {
            "method": method,
            "rrf_k": int(rrf),
            "weights": {"bm25": bw, "dense": dw},
        }
        activate(service, config)
        service = st.session_state["service"]
    upload = st.file_uploader(
        t("导入配置 YAML / JSON（仅脱敏配置）"), type=["yaml", "yml", "json"], key="config_upload"
    )
    if upload is not None:
        try:
            imported = import_config(upload.getvalue(), service.config)
            st.json(redact(imported))
            st.caption(
                t("需要重建索引") if rebuild_needed(service, imported) else t("仅查询参数变更")
            )
            if st.button(t("应用导入配置")):
                activate(service, imported)
        except ValueError:
            st.error(t("配置无效或包含凭据；请使用环境变量。"))
    st.json(redact(st.session_state["service"].config))
    st.download_button(
        t("下载配置"),
        safe_json(st.session_state["service"].config),
        file_name="config.json",
        mime="application/json",
    )
