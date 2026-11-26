"""Draft model configuration never becomes active before a successful rebuild."""

from copy import deepcopy

import streamlit as st

from rag_toolkit.web.i18n import t
from rag_toolkit.web.services.index_state import index_fingerprint, requires_rebuild
from rag_toolkit.web.session import rebuild_service


def pending_rebuild(service):
    desired = st.session_state.get("pending_config", service.config)
    return requires_rebuild(service) or index_fingerprint(desired) != service.index_fingerprint


def update_draft():
    config = deepcopy(st.session_state["service"].config)
    embedding = dict(config.get("embedding", {}))
    provider = st.session_state["embedding_provider"]
    if provider != embedding.get("provider", "local"):
        embedding = {}
    embedding["provider"] = provider
    if provider == "hash_stub":
        embedding.pop("model_name", None)
        embedding["dimension"] = st.session_state["embedding_dimension"]
    else:
        embedding.pop("dimension", None)
        embedding["model_name"] = st.session_state["embedding_model"]
    config["embedding"] = embedding
    st.session_state["pending_config"] = config
    for key in ("last_search", "last_report", "last_comparison", "evaluation_report"):
        st.session_state.pop(key, None)


def render(service):
    config = st.session_state.get("pending_config", service.config)
    embedding = config.get("embedding", {})
    with st.expander(t("模型配置（需重建）")):
        st.caption(t("模型配置变更后必须重建索引。"))
        providers = ["hash_stub", "local", "openai_compatible"]
        st.selectbox(
            "Embedding provider",
            providers,
            index=providers.index(embedding.get("provider", "local")),
            key="embedding_provider",
            on_change=update_draft,
        )
        st.text_input(
            t("Embedding 模型"),
            value=embedding.get("model_name", "BAAI/bge-small-zh-v1.5"),
            key="embedding_model",
            on_change=update_draft,
            disabled=embedding.get("provider") == "hash_stub",
        )
        st.number_input(
            "Hash dimension",
            1,
            65536,
            embedding.get("dimension", 256),
            key="embedding_dimension",
            on_change=update_draft,
            disabled=embedding.get("provider") != "hash_stub",
        )
        if st.button(t("重建索引"), disabled=not pending_rebuild(service)):
            try:
                with st.spinner(t("加载中…")):
                    replacement = rebuild_service(service, config)
                st.session_state["service"] = replacement
                st.session_state.pop("pending_config", None)
                for key in ("last_search", "last_report", "last_comparison", "evaluation_report"):
                    st.session_state.pop(key, None)
                st.rerun()
            except Exception:
                st.error(t("重建失败，原服务保持不变。"))
