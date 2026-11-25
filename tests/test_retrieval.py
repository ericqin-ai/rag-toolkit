import math

import httpx
import numpy as np
import pytest

from rag_toolkit.embeddings import (
    HashEmbedder,
    LocalSentenceTransformerEmbedder,
    OpenAICompatibleEmbedder,
)
from rag_toolkit.fusion import RRFFusion, WeightedFusion
from rag_toolkit.rerankers import CrossEncoderReranker, TokenOverlapReranker
from rag_toolkit.retrievers import BM25Retriever, DenseRetriever, HybridRetriever
from rag_toolkit.schemas import Chunk, StageCandidate
from rag_toolkit.stores import ElasticsearchStoreAdapter, FAISSVectorStore


def chunk(key, text="apple"):
    return Chunk(doc_id=key, chunk_id=key, text=text)


def candidate(key, score, rank):
    return StageCandidate(doc_id=key, chunk_id=key, score=score, rank=rank)


def test_hash_normalized_deterministic():
    a, b = HashEmbedder(64), HashEmbedder(64)
    assert a.embed_query("苹果 apple") == b.embed_query("苹果 apple")
    assert np.linalg.norm(a.embed_query("apple")) == pytest.approx(1)
    assert a.embed_documents([]) == []
    assert a.embed_query("") == [0.0] * 64
    with pytest.raises(ValueError):
        HashEmbedder(0)


def test_local_model_injected():
    class Encoder:
        def encode(self, texts, **kwargs):
            return np.array([[1.0, 0.0] for _ in texts])

    model = LocalSentenceTransformerEmbedder("unused", model=Encoder())
    assert model.embed_documents(["a", "b"]) == [[1, 0], [1, 0]]
    assert model.embed_query("a") == [1, 0]


def test_openai_batch_order_and_error():
    def handler(request):
        assert request.url.path == "/v1/embeddings"
        return httpx.Response(
            200,
            json={"data": [{"index": 1, "embedding": [0, 1]}, {"index": 0, "embedding": [1, 0]}]},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    model = OpenAICompatibleEmbedder("model", "https://local/v1", client=client)
    assert model.embed_documents(["a", "b"]) == [[1, 0], [0, 1]]
    bad = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(401)))
    with pytest.raises(httpx.HTTPStatusError):
        OpenAICompatibleEmbedder("m", "https://local/v1", client=bad).embed_query("a")


def test_faiss_cosine_upsert_and_validation():
    store = FAISSVectorStore()
    store.upsert([chunk("a"), chunk("b")], [[3, 0], [0, 4]])
    assert store.search([2, 0], 2)[0].chunk_id == "a"
    assert store.search([2, 0], 2)[0].score == pytest.approx(1)
    store.upsert([chunk("a", "updated")], [[0, 2]])
    assert len(store.chunks) == 2
    assert store.chunks["a"].text == "updated"
    with pytest.raises(ValueError):
        store.upsert([chunk("c")], [[1, 2, 3]])
    with pytest.raises(ValueError):
        store.upsert([chunk("c")], [[float("nan"), 1]])
    with pytest.raises(ValueError):
        store.upsert([chunk("c")], [])
    assert len(store.chunks) == 2
    assert store.search([1, 0], 0) == []


def test_bm25_hand_calculation_and_dense():
    docs = [chunk("a", "apple apple"), chunk("b", "pear pear")]
    bm = BM25Retriever(docs)
    expected = math.log(2) * (2 * 2.5 / (2 + 1.5))
    assert bm.retrieve("apple", 2)[0].score == pytest.approx(expected)
    assert bm.retrieve("absent", 2) == []
    assert BM25Retriever([]).retrieve("apple", 2) == []
    dense = DenseRetriever(HashEmbedder(128), FAISSVectorStore())
    dense.add_chunks(docs)
    assert dense.retrieve("apple", 1)[0].doc_id == "a"
    hybrid = HybridRetriever(bm, dense, RRFFusion())
    assert hybrid.retrieve("apple", 1)[0].doc_id == "a"


def test_fusion_manual_and_dedup():
    lists = {"bm25": [candidate("a", 5, 1), candidate("b", 1, 2)], "dense": [candidate("b", 3, 1)]}
    rrf = RRFFusion(60).fuse(lists, 10)
    assert rrf[0].chunk_id == "b"
    assert rrf[0].score == pytest.approx(1 / 62 + 1 / 61)
    weighted = WeightedFusion({"bm25": 0.4, "dense": 0.6}).fuse(lists, 10)
    assert weighted[0].chunk_id == "b"
    assert weighted[0].score == pytest.approx(0.6)
    duplicated = {"bm25": [candidate("a", 5, 1), candidate("a", 5, 2)]}
    assert RRFFusion().fuse(duplicated, 2)[0].score == pytest.approx(1 / 61)
    with pytest.raises(ValueError):
        WeightedFusion({"bm25": -1})


def test_rerankers():
    docs = [chunk("a", "pear"), chunk("b", "apple")]
    assert TokenOverlapReranker().rerank("apple", docs, 1)[0].doc_id == "b"

    class Encoder:
        def predict(self, pairs, **kwargs):
            return np.array([0.1, 0.9])

    assert CrossEncoderReranker("unused", model=Encoder()).rerank("apple", docs, 1)[0].doc_id == "b"


def test_elasticsearch_adapter_offline():
    class Indices:
        def exists(self, **kwargs):
            return False

        def create(self, **kwargs):
            assert kwargs["mappings"]["properties"]["vector"]["dims"] == 2

    class Client:
        indices = Indices()

        def index(self, **kwargs):
            assert kwargs["document"]["chunk_id"] == "a"

        def search(self, **kwargs):
            assert kwargs["knn"]["query_vector"] == [1, 0]
            return {
                "hits": {"hits": [{"_source": {"doc_id": "a", "chunk_id": "a"}, "_score": 0.75}]}
            }

    store = ElasticsearchStoreAdapter(client=Client(), dimension=2)
    store.upsert([chunk("a")], [[1, 0]])
    assert store.search([1, 0], 1)[0].doc_id == "a"
    assert store.search([1, 0], 1)[0].score == pytest.approx(0.5)


def test_cross_encoder_rejects_negative_limit_even_when_empty():
    with pytest.raises(ValueError):
        CrossEncoderReranker("unused", model=object()).rerank("q", [], -1)


@pytest.mark.parametrize(
    "payload",
    [
        {"data": [{"index": 1, "embedding": [1, 0]}]},
        {"data": [{"index": 0, "embedding": [float("inf"), 0]}]},
    ],
)
def test_openai_rejects_malformed_payload(payload):
    # Bytes permit non-finite JSON, as may be returned by a broken compatible endpoint.
    import json

    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, content=json.dumps(payload).encode())
        )
    )
    with pytest.raises(ValueError):
        OpenAICompatibleEmbedder("m", "https://local/v1", client=client).embed_query("x")


def test_faiss_delete_and_ties():
    store = FAISSVectorStore()
    store.upsert([chunk("b"), chunk("a")], [[1, 0], [1, 0]])
    assert [c.doc_id for c in store.search([1, 0], 2)] == ["a", "b"]
    store.delete(["a", "b"])
    assert store.search([1, 0], 2) == []


def test_elasticsearch_rejects_wrong_existing_similarity():
    class Indices:
        def exists(self, **kwargs):
            return True

        def get_mapping(self, **kwargs):
            return {
                "rag-toolkit": {
                    "mappings": {"properties": {"vector": {"dims": 2, "similarity": "l2_norm"}}}
                }
            }

    class Client:
        indices = Indices()

        def index(self, **kwargs):
            raise AssertionError("must validate mapping before writing")

    with pytest.raises(ValueError, match="cosine"):
        ElasticsearchStoreAdapter(client=Client(), dimension=2).upsert([chunk("a")], [[1, 0]])
