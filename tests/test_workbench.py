import json
from dataclasses import replace

import pytest

from rag_toolkit.schemas import Document
from rag_toolkit.web.services.comparison import compare
from rag_toolkit.web.services.configuration import safe_json
from rag_toolkit.web.services.query import QueryOptions, run_query
from rag_toolkit.web.session import create_session_service


def test_independent_recall_paths():
    from rag_toolkit.web.charts import ranking_figure
    from rag_toolkit.web.inspector import ranking_rows

    service = create_session_service()
    service.add_documents([Document(id="a", text="apple"), Document(id="b", text="pear")])
    response = run_query(service, "apple", QueryOptions(rerank=True))
    assert all(row["dense_rank_change"] is None for row in ranking_rows(response))
    fig = ranking_figure(response)
    for trace in fig.data:
        assert not ("bm25" in trace.x and "dense" in trace.x)
    assert "dense" not in fig.layout.xaxis.categoryarray
    assert "bm25" not in fig.layout.xaxis2.categoryarray


def test_workbench_language_compare_and_reset():
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "src/rag_toolkit/web/app.py"), default_timeout=30
    ).run()
    app.sidebar.radio[0].set_value("Datasets").run()
    next(b for b in app.button if b.label == "加载样例数据").click().run()
    app.sidebar.selectbox[0].set_value("English").run()
    assert app.sidebar.radio[0].value == "Datasets"
    app.sidebar.radio[0].set_value("Search").run()
    assert app.text_input[0].label == "Query"
    app.text_input[0].set_value("FAISS CPU")
    app.button[0].click().run()
    assert not app.exception
    app.sidebar.radio[0].set_value("Compare").run()
    app.text_input[0].set_value("FAISS CPU")
    next(b for b in app.button if b.label == "Run comparison").click().run()
    assert not app.exception
    assert len(app.session_state["last_comparison"]["variants"]) == 5
    app.sidebar.radio[0].set_value("Inspector").run()
    assert not app.exception


def test_safe_export_recursively_removes_credentials():
    result = safe_json(
        {
            "embedding": {"API_KEY": "secret"},
            "items": [
                {"Authorization": "Bearer hidden", "url": "https://user:pass@host/v1?token=abc"}
            ],
        }
    )
    for secret in ("secret", "hidden", "user:pass", "abc"):
        assert secret not in result
    assert json.loads(result)["embedding"]["API_KEY"] == "[REDACTED]"


def test_safe_export_handles_url_scheme_case_and_auth_aliases():
    result = safe_json(
        {
            "endpoint": "HTTPS://user:password@host/v1?api_key=hidden",
            "headers": {"X-Auth": "auth-value"},
            "passwd": "passwd-value",
        }
    )
    assert "password" not in result
    assert "hidden" not in result
    assert "auth-value" not in result
    assert "passwd-value" not in result


def test_query_views_are_independent_and_real():
    service = create_session_service()
    service.add_documents([Document(id="a", text="apple"), Document(id="b", text="pear")])
    original = service.pipeline.mode
    response = run_query(service, "apple", QueryOptions(mode="bm25", rerank=False))
    assert [t.stage for t in response.traces] == ["bm25"]
    assert response.results[0].doc_id == "a"
    assert service.pipeline.mode == original
    report = compare(service, ["apple"], QueryOptions(), {"apple": {"a"}})
    assert len(report["variants"]) == 5
    for row in report["variants"]:
        assert row["status"] == "ok"
        assert row["metrics"]["hit@5"] == 1
        assert row["latency"]["samples"] == 1
    assert [t["stage"] for t in report["variants"][-1]["responses"][0]["traces"]][-1] == "rerank"


def test_embedding_change_blocks_old_vectors_even_same_dimension():
    service = create_session_service()
    service.add_documents([Document(id="a", text="apple")])
    service.config["embedding"]["model_name"] = "different-model"
    with pytest.raises(ValueError, match="rebuild"):
        run_query(service, "apple", QueryOptions())


def test_invalid_options_and_empty_query():
    with pytest.raises(ValueError):
        QueryOptions(bm25_weight=0, dense_weight=0)
    with pytest.raises(ValueError):
        replace(QueryOptions(), top_k=0)
    with pytest.raises(ValueError):
        run_query(create_session_service(), " ", QueryOptions())


def test_rebuild_atomic_and_bad_case_hints(monkeypatch):
    from copy import deepcopy

    from rag_toolkit.web.services.bad_cases import infer_bad_case
    from rag_toolkit.web.session import rebuild_service

    service = create_session_service()
    service.add_documents([Document(id="a", text="apple")])
    config = deepcopy(service.config)
    config["embedding"]["dimension"] = 128
    new = rebuild_service(service, config)
    assert new.pipeline.dense.embedder.dimension == 128
    assert service.pipeline.dense.embedder.dimension == 256
    response = run_query(new, "apple", QueryOptions())
    assert infer_bad_case(response, {"a"}) == "hit"
    assert infer_bad_case(response, {"absent"}) == "retrieval_miss"
    assert infer_bad_case(response, None) == "unjudged"
    monkeypatch.setattr(
        "rag_toolkit.web.session.RetrievalService",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("secret")),
    )
    with pytest.raises(ValueError):
        rebuild_service(service, config)
    assert run_query(service, "apple", QueryOptions()).results[0].doc_id == "a"


def test_missing_models_are_not_substituted():
    from rag_toolkit.api import RetrievalService
    from rag_toolkit.web.services.index_state import index_fingerprint

    service = RetrievalService(config={"retriever": {"mode": "bm25"}})
    service.config = {"retriever": {"mode": "bm25"}}
    service.index_fingerprint = index_fingerprint(service.config)
    service.add_documents([Document(id="a", text="apple")])
    report = compare(service, ["apple"], QueryOptions())
    assert report["variants"][0]["status"] == "ok"
    assert report["variants"][0]["metrics"] is None
    assert all(v["status"] == "unavailable" for v in report["variants"][1:])


def test_model_draft_disables_search_until_rebuild():
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "src/rag_toolkit/web/app.py"), default_timeout=30
    ).run()
    app.number_input(key="embedding_dimension").set_value(128).run()
    assert next(b for b in app.button if b.label == "搜索").disabled
    next(b for b in app.button if b.label == "重建索引").click().run()
    assert not app.exception
    assert not next(b for b in app.button if b.label == "搜索").disabled
    assert app.session_state["service"].pipeline.dense.embedder.dimension == 128


@pytest.mark.parametrize(
    "changes",
    [
        {"rrf_k": -1},
        {"bm25_top_k": True},
        {"mode": "unknown"},
        {"dense_weight": float("nan")},
        {"bm25_weight": -1},
        {"rerank_top_k": 0},
    ],
)
def test_rejects_invalid_query_options(changes):
    with pytest.raises(ValueError):
        QueryOptions(**changes)


def test_query_settings_do_not_invalidate_index_and_secrets_do_not_define_vectors():
    from copy import deepcopy

    from rag_toolkit.web.services.index_state import index_fingerprint

    service = create_session_service()
    changed = deepcopy(service.config)
    changed["retriever"]["bm25_top_k"] = 3
    changed["fusion"] = {"method": "weighted"}
    assert index_fingerprint(changed) == service.index_fingerprint
    changed["embedding"]["api_key"] = "one"
    first = index_fingerprint(changed)
    changed["embedding"]["api_key"] = "two"
    assert index_fingerprint(changed) == first


def test_bad_case_inference_uses_actual_branch_candidates():
    from rag_toolkit.schemas import SearchResponse, StageCandidate, StageTrace
    from rag_toolkit.web.services.bad_cases import infer_bad_case

    candidate = StageCandidate(doc_id="a", chunk_id="a", score=1, rank=1)
    response = SearchResponse(
        query="apple",
        total_latency_ms=1,
        traces=[
            StageTrace(stage="dense", latency_ms=0, candidates=[candidate]),
            StageTrace(stage="fusion", latency_ms=0, candidates=[]),
        ],
    )
    assert infer_bad_case(response, {"a"}) == "fusion_drop"
    response.traces[1].candidates = [candidate]
    assert infer_bad_case(response, {"a"}) == "final_cutoff"
    response.traces.append(StageTrace(stage="rerank", latency_ms=0, candidates=[]))
    assert infer_bad_case(response, {"a"}) == "rerank_or_candidate_cutoff"


def test_batch_metrics_only_include_judged_queries():
    service = create_session_service()
    service.add_documents([Document(id="a", text="apple"), Document(id="b", text="pear")])
    report = compare(service, ["apple", "pear"], QueryOptions(top_k=1), {"apple": {"a"}})
    assert report["purpose"] == "Offline Pipeline Sanity Check"
    for row in report["variants"]:
        assert row["judged_queries"] == 1
        assert row["metrics"]["recall@1"] == 1
        assert row["metrics"]["ndcg@1"] == 1
        assert row["latency"]["samples"] == 2
        assert row["latency"]["avg_ms"] <= row["latency"]["p95_ms"]


def test_ui_modes_configuration_security_and_data_invalidation(monkeypatch):
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "src/rag_toolkit/web/app.py"), default_timeout=30
    ).run()
    app.sidebar.radio[0].set_value("Datasets").run()
    next(b for b in app.button if b.label == "加载样例数据").click().run()
    app.sidebar.radio[0].set_value("Search").run()
    app.text_input[0].set_value("FAISS CPU")
    app.selectbox(key="search_mode").set_value("bm25")
    app.checkbox(key="search_rerank").uncheck()
    app.button[0].click().run()
    assert [t.stage for t in app.session_state["last_search"].traces] == ["bm25"]
    app.sidebar.radio[0].set_value("Compare").run()
    app.text_input[0].set_value("FAISS CPU")
    app.button[0].click().run()
    next(b for b in app.button if b.label == "保存配置").click().run()
    assert "saved_comparison_config" in app.session_state
    app.session_state["service"].config["embedding"]["api_key"] = "never-show-this"
    app.sidebar.radio[0].set_value("Settings").run()
    assert "never-show-this" not in str([j.value for j in app.json])
    app.sidebar.radio[0].set_value("Datasets").run()
    next(b for b in app.button if b.label == "清空当前会话数据").click().run()
    assert "last_comparison" not in app.session_state
    assert "last_search" not in app.session_state
    app.sidebar.radio[0].set_value("Search").run()
    monkeypatch.setattr(
        "rag_toolkit.web.search.run_query",
        lambda *args: (_ for _ in ()).throw(RuntimeError("never-show-this")),
    )
    app.text_input[0].set_value("anything")
    app.button[0].click().run()
    assert not app.exception
    assert "never-show-this" not in str([e.value for e in app.error])


def test_startup_query_configuration_initializes_controls(monkeypatch, tmp_path):
    from pathlib import Path

    import yaml
    from streamlit.testing.v1 import AppTest

    path = tmp_path / "config.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "retriever": {"mode": "bm25", "bm25_top_k": 7, "dense_top_k": 9},
                "fusion": {
                    "method": "weighted",
                    "rrf_k": 12,
                    "weights": {"bm25": 0.7, "dense": 0.3},
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("RAG_TOOLKIT_CONFIG", str(path))
    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "src/rag_toolkit/web/app.py"), default_timeout=30
    ).run()
    assert app.selectbox(key="search_mode").value == "bm25"
    assert app.selectbox(key="search_fusion").value == "weighted"
    assert app.number_input(key="search_bm25").value == 7
    assert app.number_input(key="search_dw").value == 0.3
    app.text_input[0].set_value("apple")
    app.button[0].click().run()
    assert not app.exception
    assert not app.error
