import math

import pytest
import yaml

from rag_toolkit.evaluation import Evaluator, hit_at_k, mrr, ndcg_at_k, recall_at_k
from rag_toolkit.pipeline import RetrievalPipeline
from rag_toolkit.schemas import Document


def config(mode="hybrid", rerank=False):
    return {
        "embedding": {"provider": "hash_stub", "dimension": 64},
        "splitter": {"type": "fixed", "chunk_size": 16, "chunk_overlap": 2},
        "store": {"type": "faiss"},
        "retriever": {"mode": mode, "bm25_top_k": 10, "dense_top_k": 10},
        "reranker": {"enabled": rerank, "provider": "token_overlap", "top_k": 5},
    }


@pytest.mark.parametrize(
    "mode, stages",
    [("bm25", ["bm25"]), ("dense", ["dense"]), ("hybrid", ["bm25", "dense", "fusion"])],
)
def test_modes_and_trace(mode, stages):
    pipeline = RetrievalPipeline.from_config(config(mode))
    assert pipeline.search("apple").results == []
    pipeline.add_documents(
        [Document(id="a", text="apple fruit"), Document(id="b", text="pear fruit")]
    )
    response = pipeline.search("apple", top_k=2)
    assert response.results[0].doc_id == "a"
    assert [t.stage for t in response.traces] == stages
    assert all(t.latency_ms >= 0 for t in response.traces)
    assert response.total_latency_ms >= sum(t.latency_ms for t in response.traces)
    for result in response.results:
        for trace in response.traces:
            candidate = next((c for c in trace.candidates if c.chunk_id == result.chunk_id), None)
            assert result.stage_ranks[trace.stage] == (candidate.rank if candidate else None)
            assert result.stage_scores[trace.stage] == (candidate.score if candidate else None)


def test_rerank_and_document_replacement(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config(rerank=True)), encoding="utf8")
    pipeline = RetrievalPipeline.from_config(path)
    pipeline.add_documents([Document(id="a", text="apple fruit " * 10)])
    old = set(pipeline.chunks)
    pipeline.add_documents([Document(id="a", text="pear")])
    assert not old.intersection(pipeline.chunks)
    assert len(pipeline.chunks) == 1
    response = pipeline.search("pear")
    assert response.results[0].text == "pear"
    assert response.traces[-1].stage == "rerank"
    pipeline.add_documents([Document(id="a", text="")])
    assert pipeline.search("pear").results == []


def test_config_validation_and_input():
    for section, key, value in [
        ("embedding", "provider", "bad"),
        ("retriever", "mode", "bad"),
        ("store", "type", "bad"),
        ("fusion", "method", "bad"),
        ("splitter", "type", "bad"),
    ]:
        cfg = config()
        cfg.setdefault(section, {})[key] = value
        with pytest.raises(ValueError):
            RetrievalPipeline.from_config(cfg)
    pipeline = RetrievalPipeline.from_config(config())
    with pytest.raises(ValueError):
        pipeline.search("x", -1)
    with pytest.raises(ValueError):
        pipeline.add_documents([Document(id="a", text="x"), Document(id="a", text="y")])
    assert pipeline.search("").results == []
    assert pipeline.search("apple", 0).results == []


def test_hand_computed_metrics_and_duplicates():
    ranked = ["x", "a", "a", "b"]
    relevant = {"a", "b", "c"}
    assert hit_at_k(ranked, relevant, 1) == 0
    assert hit_at_k(ranked, relevant, 2) == 1
    assert recall_at_k(ranked, relevant, 3) == pytest.approx(2 / 3)
    assert mrr(ranked, relevant) == 0.5
    expected = (1 / math.log2(3) + 1 / math.log2(4)) / (1 + 1 / math.log2(3) + 1 / math.log2(4))
    assert ndcg_at_k(ranked, relevant, 3) == pytest.approx(expected)
    for metric in [hit_at_k, recall_at_k, ndcg_at_k]:
        assert metric([], set(), 3) == 0
        with pytest.raises(ValueError):
            metric([], set(), -1)
    assert mrr([], set()) == 0


def test_evaluator_and_empty_report():
    pipeline = RetrievalPipeline.from_config(config())
    pipeline.add_documents([Document(id="a", text="apple"), Document(id="b", text="pear")])
    response = pipeline.search("apple", 2)
    report = Evaluator().evaluate([response], {"apple": {"a"}}, ks=[1, 2])
    assert report.num_queries == 1
    assert report.metrics["hit@1"] == report.metrics["mrr"] == 1
    assert report.per_query[0]["query"] == "apple"
    assert Evaluator().evaluate([], {}, ks=[1]).metrics["mrr"] == 0
    with pytest.raises(ValueError):
        Evaluator().evaluate([response], {}, ks=[1])


def test_embedding_failure_preserves_document_state():
    from rag_toolkit.embeddings import HashEmbedder

    class FailingEmbedder(HashEmbedder):
        def embed_documents(self, texts):
            if "broken" in texts:
                raise RuntimeError("encoding failed")
            return super().embed_documents(texts)

    pipeline = RetrievalPipeline.from_config(config(), embedder=FailingEmbedder(64))
    pipeline.add_documents([Document(id="a", text="apple")])
    before = dict(pipeline.chunks)
    with pytest.raises(RuntimeError, match="encoding failed"):
        pipeline.add_documents([Document(id="a", text="broken")])
    assert pipeline.chunks == before
    assert pipeline.search("apple").results[0].text == "apple"


def test_bm25_only_does_not_load_local_model():
    pipeline = RetrievalPipeline.from_config({"retriever": {"mode": "bm25"}})
    pipeline.add_documents([Document(id="x", text="apple")])
    assert pipeline.search("apple").results[0].doc_id == "x"


@pytest.mark.parametrize("enabled", ["false", "true", 0, 1, None])
def test_reranker_requires_boolean(enabled):
    cfg = config("bm25")
    cfg["reranker"] = {"enabled": enabled, "provider": "token_overlap"}
    with pytest.raises(ValueError, match="boolean"):
        RetrievalPipeline.from_config(cfg)


def test_hybrid_preserves_configured_reranking_pool(monkeypatch):
    from rag_toolkit.schemas import StageCandidate

    cfg = config(rerank=True)
    cfg["retriever"].update(bm25_top_k=2, dense_top_k=2)
    cfg["reranker"]["top_k"] = 4
    pipeline = RetrievalPipeline.from_config(cfg)
    pipeline.add_documents([Document(id=str(i), text=f"item {i}") for i in range(4)])
    chunks = list(pipeline.chunks.values())
    candidates = [
        StageCandidate(doc_id=c.doc_id, chunk_id=c.chunk_id, score=1, rank=i % 2 + 1)
        for i, c in enumerate(chunks)
    ]
    monkeypatch.setattr(pipeline.bm25, "retrieve", lambda *a, **kw: candidates[:2])
    monkeypatch.setattr(pipeline.dense, "retrieve", lambda *a, **kw: candidates[2:])

    class Reranker:
        def rerank(self, query, pool, top_k):
            assert len(pool) == 4
            chosen = next(c for c in pool if c.doc_id == "3")
            return [StageCandidate(doc_id=chosen.doc_id, chunk_id=chosen.chunk_id, score=1, rank=1)]

    pipeline.reranker = Reranker()
    assert pipeline.search("item", 1).results[0].doc_id == "3"


def test_pipeline_excludes_stale_remote_candidates():
    from rag_toolkit.stores import ElasticsearchStoreAdapter

    class Indices:
        def exists(self, **kwargs):
            return False

        def create(self, **kwargs):
            return None

    class Client:
        indices = Indices()

        def __init__(self):
            self.current = None

        def index(self, **kwargs):
            self.current = kwargs["document"]

        def search(self, **kwargs):
            scope = kwargs["knn"].get("filter", {}).get("terms", {}).get("chunk_id", [])
            assert scope == [self.current["chunk_id"]]
            return {"hits": {"hits": [{"_source": self.current, "_score": 1}]}}

    store = ElasticsearchStoreAdapter(dimension=64, client=Client())
    pipeline = RetrievalPipeline.from_config(config(), store=store)
    pipeline.add_documents([Document(id="current", text="apple")])
    assert pipeline.search("apple", 1).results[0].doc_id == "current"
