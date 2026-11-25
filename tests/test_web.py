from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from rag_toolkit.schemas import SearchResponse, StageCandidate, StageTrace
from rag_toolkit.web.datasets import parse_documents, parse_queries
from rag_toolkit.web.inspector import latency_rows, ranking_rows


def test_inspector_keeps_dropped_candidates_and_actual_rank_change():
    response = SearchResponse(
        query="x",
        total_latency_ms=8,
        traces=[
            StageTrace(
                stage="bm25",
                latency_ms=2,
                candidates=[
                    StageCandidate(doc_id="a", chunk_id="a", score=2, rank=1),
                    StageCandidate(doc_id="b", chunk_id="b", score=1, rank=2),
                ],
            ),
            StageTrace(
                stage="rerank",
                latency_ms=3,
                candidates=[StageCandidate(doc_id="b", chunk_id="b", score=0.9, rank=1)],
            ),
        ],
    )
    rows = {r["chunk_id"]: r for r in ranking_rows(response)}
    assert rows["a"]["bm25_rank"] == 1
    assert rows["a"]["rerank_rank"] is None
    assert rows["b"]["rerank_rank_change"] == 1
    assert rows["a"]["final_rank"] is None
    times = latency_rows(response)
    assert [r["latency_ms"] for r in times] == [2, 3, 3]
    assert times[-1]["stage"] == "overhead"


def test_upload_parser_validates_before_indexing():
    docs = parse_documents(b'{"id":"a","text":"apple"}\n', "a.jsonl")
    assert docs[0].text == "apple"
    assert parse_documents(b"\xef\xbb\xbf# Apple\r\nfruit", "a.md")[0].text == "# Apple\nfruit"
    query = parse_queries(b'{"id":"q","query":"apple","relevant_doc_ids":["a"]}')
    assert query[0].relevant_doc_ids == ["a"]
    with pytest.raises(ValueError, match="line 2"):
        parse_documents(b'\n{"text":3}', "bad.jsonl")
    with pytest.raises(ValueError, match="duplicate"):
        parse_documents(b'{"id":"a","text":"x"}\n{"id":"a","text":"y"}', "bad.jsonl")
    with pytest.raises(ValueError):
        parse_queries(b'{"query":"x","relevant_doc_ids":[]}\n' * 2)
    with pytest.raises(ValueError):
        parse_documents(b"file", "file.pdf")


def test_streamlit_datasets_search_inspector_evaluation_flow():
    root = Path(__file__).resolve().parents[1]
    app = AppTest.from_file(str(root / "src/rag_toolkit/web/app.py"), default_timeout=20).run()
    assert not app.exception
    app.sidebar.radio[0].set_value("Datasets").run()
    next(b for b in app.button if b.label == "加载样例数据").click().run()
    assert not app.exception
    assert len(app.session_state["service"].documents) == 6
    app.sidebar.radio[0].set_value("Search").run()
    app.text_input[0].set_value("FAISS CPU 向量")
    app.button[0].click().run()
    assert not app.exception
    assert app.session_state["last_search"].results[0].doc_id == "faiss"
    app.sidebar.radio[0].set_value("Inspector").run()
    assert not app.exception
    assert len(app.dataframe) >= 2
    app.sidebar.radio[0].set_value("Evaluation").run()
    app.button[0].click().run()
    assert not app.exception
    assert app.session_state["last_report"].num_queries == 8
    # Independent sessions must not inherit another user's documents.
    other = AppTest.from_file(str(root / "src/rag_toolkit/web/app.py")).run()
    assert not other.session_state["service"].documents
    app.sidebar.radio[0].set_value("Search").run()
    app.text_input[0].set_value("   ")
    app.button[0].click().run()
    assert "last_search" not in app.session_state
    app.sidebar.radio[0].set_value("Evaluation").run()
    app.text_input[0].set_value("bad")
    app.button[0].click().run()
    assert "last_report" not in app.session_state


def test_web_sessions_namespace_elasticsearch_without_mutating_config(monkeypatch, tmp_path):
    import yaml

    from rag_toolkit.pipeline import RetrievalPipeline
    from rag_toolkit.web.session import create_session_service

    captured = []
    original = RetrievalPipeline.from_config

    def capture(config):
        captured.append(config)
        return original({"retriever": {"mode": "bm25"}})

    monkeypatch.setattr(RetrievalPipeline, "from_config", capture)
    path = tmp_path / "config.yaml"
    config = {"store": {"type": "elasticsearch", "index_name": "demo"}}
    path.write_text(yaml.safe_dump(config), encoding="utf8")
    monkeypatch.setenv("RAG_TOOLKIT_CONFIG", str(path))
    create_session_service()
    create_session_service()
    names = [cfg["store"]["index_name"] for cfg in captured]
    assert names[0].startswith("demo-session-")
    assert names[0] != names[1]
    assert yaml.safe_load(path.read_text(encoding="utf8")) == config
