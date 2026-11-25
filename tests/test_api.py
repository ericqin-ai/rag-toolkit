import pytest
from fastapi.testclient import TestClient

from rag_toolkit.api import create_app
from rag_toolkit.pipeline import RetrievalPipeline


@pytest.fixture
def client():
    with TestClient(create_app()) as client:
        yield client


def test_health_ingestion_search_and_evaluation(client):
    assert client.get("/health").json() == {"status": "ok", "num_documents": 0, "num_chunks": 0}
    response = client.post(
        "/documents",
        json={
            "documents": [
                {"id": "a", "text": "apple fruit", "metadata": {"source": "test"}},
                {"id": "b", "text": "pear fruit"},
            ]
        },
    )
    assert response.status_code == 200
    assert response.json() == {"num_documents": 2, "num_chunks": 2, "added_chunks": 2}
    result = client.post("/search", json={"query": "apple", "top_k": 2})
    assert result.status_code == 200
    data = result.json()
    assert data["results"][0]["doc_id"] == "a"
    assert data["results"][0]["metadata"]["source"] == "test"
    assert [t["stage"] for t in data["traces"]] == ["bm25", "dense", "fusion", "rerank"]
    assert all(t["latency_ms"] >= 0 for t in data["traces"])
    report = client.post(
        "/evaluate",
        json={
            "queries": [{"query": "apple", "relevant_doc_ids": ["a"]}],
            "ks": [1, 2],
            "top_k": 2,
        },
    )
    assert report.status_code == 200
    assert report.json()["metrics"]["hit@1"] == 1
    assert report.json()["num_queries"] == 1
    assert client.get("/health").json()["num_chunks"] == 2


def test_replacement_empty_index_and_instance_isolation(client):
    assert client.post("/search", json={"query": "apple"}).json()["results"] == []
    client.post("/documents", json={"documents": [{"id": "a", "text": "apple"}]})
    client.post("/documents", json={"documents": [{"id": "a", "text": "pear"}]})
    assert client.post("/search", json={"query": "pear"}).json()["results"][0]["text"] == "pear"
    with TestClient(create_app()) as other:
        assert other.get("/health").json()["num_chunks"] == 0


@pytest.mark.parametrize(
    "path, payload",
    [
        ("/documents", {"documents": []}),
        ("/documents", {"documents": [{"id": "a", "text": "x"}, {"id": "a", "text": "y"}]}),
        ("/search", {"query": "  "}),
        ("/search", {"query": "x", "top_k": -1}),
        ("/search", {"query": "x", "top_k": True}),
        ("/search", {"query": "x", "unknown": 1}),
        ("/evaluate", {"queries": []}),
        ("/evaluate", {"queries": [{"query": "x", "relevant_doc_ids": []}], "ks": [0]}),
        ("/evaluate", {"queries": [{"query": "x", "relevant_doc_ids": []}], "ks": [5], "top_k": 1}),
        ("/evaluate", {"queries": [{"query": "x", "relevant_doc_ids": []}] * 2}),
    ],
)
def test_invalid_requests_have_standard_error(client, path, payload):
    response = client.post(path, json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["error"]["details"]


def test_backend_exception_is_sanitized():
    class BrokenPipeline(RetrievalPipeline):
        def search(self, query, top_k=10):
            raise RuntimeError("secret-provider-key")

    pipeline = BrokenPipeline.from_config({"retriever": {"mode": "bm25"}})
    with TestClient(create_app(pipeline=pipeline), raise_server_exceptions=False) as client:
        response = client.post("/search", json={"query": "apple"})
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "internal_error"
        assert "secret-provider-key" not in response.text


def test_openapi_documents_response_contracts(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert paths["/search"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert client.get("/missing").json()["error"]["code"] == "http_error"
