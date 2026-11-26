from pathlib import Path

import streamlit as st

from rag_toolkit.web.datasets import parse_documents, parse_queries
from rag_toolkit.web.i18n import t
from rag_toolkit.web.services.configuration import redact, safe_json
from rag_toolkit.web.services.status import overview_status
from rag_toolkit.web.session import clear_session_service

ROOT = Path(__file__).resolve().parents[3]


def clear_results():
    for key in ("last_search", "last_report", "last_comparison", "evaluation_report"):
        st.session_state.pop(key, None)


def render(service):
    st.header("Datasets")
    st.caption(t("仅修改当前会话的内存索引；同 ID 文档会被替换，服务重启后数据不保留。"))
    st.json(service.stats())
    st.caption(t("示例为仓库公开样例（MIT），离线加载，不代表真实模型基准。"))
    if st.button(t("加载样例数据")):
        try:
            docs = parse_documents(
                (ROOT / "datasets/documents.jsonl").read_bytes(), "documents.jsonl"
            )
            queries = parse_queries((ROOT / "datasets/queries.jsonl").read_bytes())
            service.add_documents(docs)
            st.session_state["queries"] = queries
            st.session_state.pop("dataset_labels_editor", None)
            clear_results()
            st.success(
                t("已加载 {docs} 篇文档、{queries} 条查询。", docs=len(docs), queries=len(queries))
            )
        except (ValueError, OSError):
            st.error(t("无法加载样例数据。"))
        except Exception:
            st.error(t("样例导入失败，请检查模型与服务配置。"))
    upload = st.file_uploader(
        t("上传文档（TXT / Markdown / JSONL）"), type=["txt", "md", "markdown", "jsonl"]
    )
    if upload is not None:
        try:
            docs = parse_documents(upload.getvalue(), upload.name)
            st.dataframe(redact([doc.model_dump() for doc in docs]), hide_index=True)
            if st.button(t("导入文档")):
                service.add_documents(docs)
                clear_results()
                st.success(t("已导入 {count} 篇文档。", count=len(docs)))
        except ValueError as exc:
            st.error(t("文档格式无效。") + " " + str(exc))
        except Exception:
            st.error(t("导入失败，请检查配置与数据。"))
    labels = st.file_uploader(t("上传标注查询 JSONL"), type=["jsonl"], key="labels_upload")
    if labels is not None:
        try:
            queries = parse_queries(labels.getvalue())
            if st.button(t("导入标注查询")):
                st.session_state["queries"] = queries
                st.session_state.pop("dataset_labels_editor", None)
                clear_results()
                st.success(t("已导入 {count} 条查询。", count=len(queries)))
        except ValueError as exc:
            st.error(t("查询格式无效。") + " " + str(exc))
    if service.documents:
        docs = list(service.documents.values())
        st.subheader(t("当前文档"))
        st.dataframe(redact([doc.model_dump() for doc in docs]), hide_index=True, width="stretch")
        st.subheader(t("Chunk 预览"))
        doc_id = st.selectbox(t("按文档筛选"), ["all"] + list(service.documents))
        st.dataframe(
            redact(
                [
                    c.model_dump()
                    for c in service.pipeline.chunks.values()
                    if doc_id == "all" or c.doc_id == doc_id
                ]
            ),
            hide_index=True,
            width="stretch",
        )
        st.download_button(
            t("导出文档 JSONL"),
            "\n".join(safe_json(d.model_dump()).replace("\n", "") for d in docs),
            file_name="documents.jsonl",
            mime="application/x-ndjson",
        )
    queries = st.session_state.get("queries", [])
    if queries:
        st.subheader(t("当前标注查询"))
        st.dataframe([q.model_dump() for q in queries], hide_index=True, width="stretch")
        st.download_button(
            t("导出标注查询"),
            "\n".join(safe_json(q.model_dump()).replace("\n", "") for q in queries),
            file_name="queries.jsonl",
            mime="application/x-ndjson",
        )
    with st.expander(t("管理 Query 标注")):
        text = st.text_area(
            t("标注 JSONL（编辑后替换）"),
            value="\n".join(q.model_dump_json() for q in queries),
            key="dataset_labels_editor",
        )
        if st.button(t("保存标注")):
            try:
                st.session_state["queries"] = parse_queries(text.encode())
                clear_results()
                st.rerun()
            except ValueError as exc:
                st.error(t("查询格式无效。") + " " + str(exc))
        if st.button(t("清空标注")):
            st.session_state["queries"] = []
            st.session_state.pop("dataset_labels_editor", None)
            clear_results()
            st.rerun()
    st.subheader(t("当前数据集与索引状态"))
    st.json(overview_status(service, st.session_state.get("pending_config")))
    with st.expander(t("粘贴导入文档")):
        filename = st.selectbox(t("文档格式"), ["documents.jsonl", "document.txt", "document.md"])
        pasted = st.text_area(t("文档内容"), key="dataset_documents_text")
        if st.button(t("导入粘贴文档")):
            try:
                docs = parse_documents(pasted.encode(), filename)
                service.add_documents(docs)
                clear_results()
                st.rerun()
            except ValueError as exc:
                st.error(t("文档格式无效。") + " " + str(exc))
            except Exception:
                st.error(t("导入失败，请检查配置与数据。"))
    if st.button(t("清空当前会话数据")):
        try:
            service = clear_session_service(service)
        except Exception:
            st.error(t("无法重置检索服务，请检查配置。"))
            return
        st.session_state["service"] = service
        for key in (
            "pending_config",
            "embedding_provider",
            "embedding_model",
            "embedding_dimension",
        ):
            st.session_state.pop(key, None)
        st.session_state["queries"] = []
        st.session_state.pop("dataset_labels_editor", None)
        clear_results()
        st.rerun()
