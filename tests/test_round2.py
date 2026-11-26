from copy import deepcopy

import pytest

from rag_toolkit.schemas import Document
from rag_toolkit.web.services.evaluation import evaluate_strategies, export_report
from rag_toolkit.web.services.settings import apply_config, import_config, validate_config
from rag_toolkit.web.services.status import overview_status
from rag_toolkit.web.session import create_session_service


def test_settings_query_defaults_reuse_vectors_and_index_changes_rebuild():
    service = create_session_service()
    service.add_documents([Document(id="a", text="apple fruit")])
    cfg = deepcopy(service.config)
    cfg["retriever"]["bm25_top_k"] = 7
    updated = apply_config(service, cfg)
    assert updated.pipeline.dense is service.pipeline.dense
    assert updated.pipeline.bm25_top_k == 7
    cfg["tokenizer"] = {"type": "whitespace"}
    rebuilt = apply_config(updated, cfg)
    assert rebuilt.pipeline.dense is not service.pipeline.dense
    assert rebuilt.pipeline.bm25.retrieve("apple")[0].doc_id == "a"


def test_config_import_is_safe_and_validates_before_models():
    service = create_session_service()
    with pytest.raises(ValueError):
        import_config(b"embedding: {api_key: do-not-echo}", service.config)
    with pytest.raises(ValueError):
        validate_config({"splitter": {"chunk_size": 2, "chunk_overlap": 3}})
    with pytest.raises(ValueError):
        import_config(b'store: {url: "HTTPS://user:secret@host"}', service.config)
    service.config["embedding"] = {"provider": "openai_compatible", "api_key": "private"}
    cfg = import_config(
        b'embedding: {provider: openai_compatible, api_key: "[REDACTED]"}', service.config
    )
    assert cfg["embedding"]["api_key"] == "private"


def test_real_evaluation_reports_and_clues():
    from rag_toolkit.api.models import EvaluationQuery

    service = create_session_service()
    service.add_documents([Document(id="a", text="apple")])
    labels = [
        EvaluationQuery(query="apple", relevant_doc_ids=["a"]),
        EvaluationQuery(query="absent", relevant_doc_ids=["missing"]),
    ]
    report = evaluate_strategies(service, labels, ["BM25", "Hybrid RRF"], 5, [1, 5])
    assert len(report["strategies"]) == 2
    assert report["strategies"][0]["metrics"]["hit@1"] == 0.5
    row = report["strategies"][0]["per_query"][1]
    assert row["diagnosis"]["confirmed_root_cause"] is None
    assert row["diagnosis"]["clues"]
    for fmt in ["json", "csv", "markdown"]:
        assert export_report(report, fmt)
    status = overview_status(service)
    assert status["num_chunks"] == 1
    assert status["index_state"] == "ready"


def app_test():
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    return AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "src/rag_toolkit/web/app.py"), default_timeout=30
    ).run()


def button(app, name):
    return next(b for b in app.button if b.label == name)


def load_sample(app):
    app.sidebar.radio[0].set_value("Datasets").run()
    button(app, "加载样例数据").click().run()
    assert not app.exception


def test_overview_history_and_pipeline():
    app = app_test()
    app.sidebar.radio[0].set_value("Overview").run()
    assert [m.value for m in app.metric] == ["0", "0"]
    load_sample(app)
    app.sidebar.radio[0].set_value("Search").run()
    app.text_input[0].set_value("FAISS CPU")
    button(app, "搜索").click().run()
    app.sidebar.radio[0].set_value("Overview").run()
    assert not app.exception
    assert app.metric[0].value == "6"
    assert app.session_state["activity"][-1]["kind"] == "search"
    assert "ready" in str([j.value for j in app.json])


def test_evaluation_import_strategies_failure_filters_and_exports():
    app = app_test()
    load_sample(app)
    app.sidebar.radio[0].set_value("Evaluation").run()
    app.text_area(key="eval_labels_text").set_value(
        '{"query":"FAISS CPU","relevant_doc_ids":["faiss"]}\n'
        '{"query":"nothingmatcheszz","relevant_doc_ids":["missing"]}'
    )
    button(app, "导入/替换标注").click().run()
    app.multiselect(key="eval_strategies").set_value(["BM25", "Hybrid RRF"]).run()
    button(app, "运行评测").click().run()
    assert not app.exception
    report = app.session_state["evaluation_report"]
    assert len(report["strategies"]) == 2
    assert report["strategies"][0]["metrics"]["hit@1"] == 0.5
    app.checkbox(key="eval_failures").check().run()
    assert len(app.dataframe[1].value) == 2
    assert all(
        "confirmed_root_cause" in q["diagnosis"]
        for s in report["strategies"]
        for q in s["per_query"]
    )
    app.text_input(key="eval_filter").set_value("no-such-query").run()
    assert len(app.dataframe[1].value) == 0
    assert len(app.get("download_button")) == 3
    app.sidebar.radio[0].set_value("Overview").run()
    assert app.session_state["activity"][-1]["kind"] == "evaluation"


def test_dataset_validation_chunks_and_label_management():
    app = app_test()
    app.sidebar.radio[0].set_value("Datasets").run()
    app.text_area(key="dataset_documents_text").set_value(
        '{"id":"a","text":"apple fruit"}\n{"text":3}'
    )
    button(app, "导入粘贴文档").click().run()
    assert "line 2" in app.error[0].value
    assert not app.session_state["service"].documents
    app.text_area(key="dataset_documents_text").set_value('{"id":"a","text":"apple fruit"}')
    button(app, "导入粘贴文档").click().run()
    assert not app.exception
    assert len(app.session_state["service"].pipeline.chunks) == 1
    app.text_area(key="dataset_labels_editor").set_value(
        '{"query":"apple","relevant_doc_ids":["a"]}'
    )
    button(app, "保存标注").click().run()
    assert len(app.session_state["queries"]) == 1
    button(app, "清空标注").click().run()
    assert not app.session_state["queries"]
    button(app, "清空当前会话数据").click().run()
    assert not app.session_state["service"].documents


def test_settings_apply_invalid_splitter_and_tokenizer_rebuild():
    app = app_test()
    load_sample(app)
    app.sidebar.radio[0].set_value("Settings").run()
    original = app.session_state["service"].pipeline.dense
    app.number_input(key="set_bk").set_value(7)
    button(app, "应用配置").click().run()
    assert not app.exception
    assert app.session_state["service"].pipeline.dense is original
    assert app.session_state["service"].pipeline.bm25_top_k == 7
    app.number_input(key="set_size").set_value(2)
    app.number_input(key="set_overlap").set_value(3)
    button(app, "应用配置").click().run()
    assert app.error
    assert app.session_state["service"].pipeline.dense is original
    app.number_input(key="set_size").set_value(512)
    app.number_input(key="set_overlap").set_value(64)
    app.selectbox(key="set_tokenizer").set_value("whitespace")
    button(app, "应用配置").click().run()
    assert not app.exception
    assert app.session_state["service"].pipeline.dense is not original
    assert len(app.session_state["service"].documents) == 6


def test_settings_uploaded_config_and_secret_failure(monkeypatch):
    from types import SimpleNamespace

    import streamlit as st

    original_upload = st.file_uploader
    content = [b"embedding: {provider: hash_stub, api_key: dont-print-me}"]

    def upload(label, *args, **kwargs):
        if kwargs.get("key") == "config_upload":
            return SimpleNamespace(getvalue=lambda: content[0], name="config.yaml")
        return original_upload(label, *args, **kwargs)

    monkeypatch.setattr(st, "file_uploader", upload)
    app = app_test()
    app.sidebar.radio[0].set_value("Settings").run()
    assert not app.exception
    assert app.error
    assert "dont-print-me" not in str([e.value for e in app.error])
    content[0] = b"embedding: {provider: hash_stub, dimension: 128}\nretriever: {mode: hybrid}"
    app.run()
    button(app, "应用导入配置").click().run()
    assert not app.exception
    assert app.session_state["service"].pipeline.dense.embedder.dimension == 128
    assert app.number_input(key="set_dim").value == 128


def test_redacted_configuration_roundtrip_preserves_tokenizer_and_rejects_bad_store():
    from rag_toolkit.web.services.configuration import safe_json

    service = create_session_service()
    cfg = deepcopy(service.config)
    cfg["tokenizer"] = {"type": "whitespace"}
    assert import_config(safe_json(cfg).encode(), cfg)["tokenizer"]["type"] == "whitespace"
    with pytest.raises(ValueError):
        validate_config({"store": {"type": "faiss", "dimension": -2}})


@pytest.mark.parametrize(
    "filename, content",
    [
        ("sample.txt", b"apple fruit"),
        ("sample.md", b"# Apple\nfruit"),
        ("sample.jsonl", b'{"id":"a","text":"apple"}'),
    ],
)
def test_all_document_formats(filename, content):
    from rag_toolkit.web.datasets import parse_documents

    assert parse_documents(content, filename)[0].text


def test_safe_error_lines_and_no_echoed_record_values():
    from rag_toolkit.web.datasets import parse_documents, parse_queries

    for function, args in [
        (parse_documents, (b'{"id":"a","text":3,"metadata":{"api_key":"hidden"}}', "a.jsonl")),
        (parse_queries, (b'{"query":3,"relevant_doc_ids":["hidden"]}',)),
    ]:
        with pytest.raises(ValueError) as error:
            function(*args)
        assert "line 1" in str(error.value)
        assert "hidden" not in str(error.value)


def test_effective_defaults_do_not_invalidate_vectors():
    from rag_toolkit.web.services.index_state import index_fingerprint

    left = {"embedding": {"provider": "local"}}
    right = {
        "embedding": {"provider": "local", "model_name": "BAAI/bge-small-zh-v1.5", "device": "cpu"}
    }
    assert index_fingerprint(left) == index_fingerprint(right)


def test_csv_includes_summary_and_neutralizes_formula_queries():
    import csv
    import io

    from rag_toolkit.api.models import EvaluationQuery

    service = create_session_service()
    report = evaluate_strategies(
        service, [EvaluationQuery(query="=1+1", relevant_doc_ids=["a"])], ["BM25"], 1, [1]
    )
    rows = list(csv.DictReader(io.StringIO(export_report(report, "csv"))))
    assert rows[0]["row_type"] == "summary"
    assert rows[1]["query"].startswith("'")
    assert report["diagnosis_notice"] in export_report(report, "markdown")


def test_api_batch_size_survives_query_apply_and_clear_preserves_settings():
    from rag_toolkit.web.services.index_state import index_fingerprint

    app = app_test()
    service = app.session_state["service"]
    # Deterministic local embedder injection; only configuration/UI behavior is under test.
    service.config["embedding"] = {
        "provider": "openai_compatible",
        "model_name": "test-model",
        "base_url": "https://example.invalid/v1",
        "batch_size": 1,
        "api_key": "never-render-this",
    }
    service.index_fingerprint = index_fingerprint(service.config)
    original = service.pipeline.dense
    app.sidebar.radio[0].set_value("Settings").run()
    assert app.number_input(key="set_batch").value == 1
    assert "never-render-this" not in str([j.value for j in app.json])
    app.number_input(key="set_bk").set_value(7)
    button(app, "应用配置").click().run()
    assert not app.exception
    assert app.session_state["service"].pipeline.dense is original
    assert app.session_state["service"].config["embedding"]["batch_size"] == 1
    app.sidebar.radio[0].set_value("Datasets").run()
    button(app, "清空当前会话数据").click().run()
    assert not app.exception
    assert app.session_state["service"].config["embedding"]["batch_size"] == 1
    assert app.session_state["service"].config["embedding"]["provider"] == "openai_compatible"
    assert not app.session_state["service"].documents


def test_settings_failed_model_rebuild_retains_service_and_hides_exception(monkeypatch):
    app = app_test()
    load_sample(app)
    original = app.session_state["service"]

    def fail(*args, **kwargs):
        raise RuntimeError("hidden-api-key-value")

    monkeypatch.setattr("rag_toolkit.web.services.settings.rebuild_service", fail)
    app.sidebar.radio[0].set_value("Settings").run()
    app.selectbox(key="set_ep").set_value("local")
    button(app, "应用配置").click().run()
    assert not app.exception
    assert app.session_state["service"] is original
    assert app.error
    assert "hidden-api-key-value" not in str([e.value for e in app.error])


def test_four_pages_language_switch_and_independent_session():
    app = app_test()
    load_sample(app)
    for page in ["Overview", "Evaluation", "Datasets", "Settings"]:
        app.sidebar.radio[0].set_value(page).run()
        app.sidebar.selectbox[0].set_value("English").run()
        assert app.sidebar.radio[0].value == page
        assert not app.exception
        app.sidebar.selectbox[0].set_value("中文").run()
        assert not app.exception
    other = app_test()
    other.sidebar.radio[0].set_value("Overview").run()
    assert not other.session_state["service"].documents


def test_dataset_upload_error_line_does_not_echo_input(monkeypatch):
    from types import SimpleNamespace

    import streamlit as st

    original = st.file_uploader

    def upload(label, *args, **kwargs):
        if kwargs.get("type") == ["txt", "md", "markdown", "jsonl"]:
            return SimpleNamespace(
                name="bad.jsonl",
                getvalue=lambda: b'{"id":"a","text":"valid"}\n{"text":3,"api_key":"hidden-value"}',
            )
        return original(label, *args, **kwargs)

    monkeypatch.setattr(st, "file_uploader", upload)
    app = app_test()
    app.sidebar.radio[0].set_value("Datasets").run()
    assert not app.exception
    assert "line 2" in app.error[0].value
    assert "hidden-value" not in app.error[0].value
    assert not app.session_state["service"].documents
