from pathlib import Path

import streamlit as st

from rag_toolkit.web.datasets import parse_documents, parse_queries
from rag_toolkit.web.session import create_session_service

ROOT = Path(__file__).resolve().parents[3]


def clear_results():
    for key in ("last_search", "last_report"):
        st.session_state.pop(key, None)


def render(service):
    st.header("Datasets")
    st.caption("仅修改当前会话的内存索引；同 ID 文档会被替换，服务重启后数据不保留。")
    st.json(service.stats())
    if st.button("加载样例数据"):
        try:
            docs = parse_documents(
                (ROOT / "datasets/documents.jsonl").read_bytes(), "documents.jsonl"
            )
            queries = parse_queries((ROOT / "datasets/queries.jsonl").read_bytes())
            service.add_documents(docs)
            st.session_state["queries"] = queries
            clear_results()
            st.success(f"已加载 {len(docs)} 篇文档、{len(queries)} 条查询。")
        except (ValueError, OSError) as exc:
            st.error(f"无法加载样例数据：{exc}")
        except Exception:
            st.error("样例导入失败，请检查模型与服务配置。")
    upload = st.file_uploader(
        "上传文档（TXT / Markdown / JSONL）", type=["txt", "md", "markdown", "jsonl"]
    )
    if upload is not None:
        try:
            docs = parse_documents(upload.getvalue(), upload.name)
            st.dataframe([doc.model_dump() for doc in docs], hide_index=True)
            if st.button("导入文档"):
                service.add_documents(docs)
                clear_results()
                st.success(f"已导入 {len(docs)} 篇文档。")
        except ValueError as exc:
            st.error(f"文档格式无效：{exc}")
        except Exception:
            st.error("导入失败，请检查配置与数据。")
    labels = st.file_uploader("上传标注查询 JSONL", type=["jsonl"], key="labels_upload")
    if labels is not None:
        try:
            queries = parse_queries(labels.getvalue())
            if st.button("导入标注查询"):
                st.session_state["queries"] = queries
                clear_results()
                st.success(f"已导入 {len(queries)} 条查询。")
        except ValueError as exc:
            st.error(f"查询格式无效：{exc}")
    if service.documents:
        docs = list(service.documents.values())
        st.subheader("当前文档")
        st.dataframe([doc.model_dump() for doc in docs], hide_index=True, width="stretch")
        st.download_button(
            "导出文档 JSONL",
            "\n".join(d.model_dump_json() for d in docs),
            file_name="documents.jsonl",
            mime="application/x-ndjson",
        )
    queries = st.session_state.get("queries", [])
    if queries:
        st.subheader("当前标注查询")
        st.dataframe([q.model_dump() for q in queries], hide_index=True, width="stretch")
        st.download_button(
            "导出标注查询",
            "\n".join(q.model_dump_json() for q in queries),
            file_name="queries.jsonl",
            mime="application/x-ndjson",
        )
    if st.button("清空当前会话数据"):
        try:
            service = create_session_service()
        except Exception:
            st.error("无法重置检索服务，请检查配置。")
            return
        st.session_state["service"] = service
        st.session_state["queries"] = []
        clear_results()
        st.rerun()
