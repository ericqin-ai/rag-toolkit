import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


def test_example_evaluates_dataset_and_writes_report(tmp_path):
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "report.json"
    completed = subprocess.run(
        [sys.executable, str(root / "examples/evaluate.py"), "--output", str(output)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(output.read_text(encoding="utf8"))
    assert report["num_queries"] == 8
    assert len(report["per_query"]) == 8
    assert report["metrics"]["recall@1"] == 0.875
    assert "Indexed 6 chunks" in completed.stdout


def test_default_configuration_contract():
    root = Path(__file__).resolve().parents[1]
    config = yaml.safe_load((root / "configs/default.yaml").read_text(encoding="utf8"))
    assert config == {
        "splitter": {"type": "fixed", "chunk_size": 512, "chunk_overlap": 64},
        "embedding": {"provider": "local", "model_name": "BAAI/bge-small-zh-v1.5"},
        "store": {"type": "faiss"},
        "retriever": {"mode": "hybrid", "bm25_top_k": 20, "dense_top_k": 20},
        "fusion": {"method": "rrf", "rrf_k": 60, "weights": {"bm25": 0.4, "dense": 0.6}},
        "reranker": {"enabled": False, "model_name": "BAAI/bge-reranker-base", "top_k": 10},
    }


@pytest.mark.parametrize(
    "example, stages",
    [
        ("basic_search.py", ["bm25"]),
        ("hybrid_search.py", ["bm25", "dense", "fusion"]),
        ("rerank_search.py", ["bm25", "dense", "fusion", "rerank"]),
    ],
)
def test_search_examples_are_runnable_from_other_directory(tmp_path, example, stages):
    root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [sys.executable, str(root / "examples" / example), "--query", "FAISS CPU 向量"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf8",
        check=True,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    response = json.loads(completed.stdout)
    assert response["results"][0]["doc_id"] == "faiss"
    assert [t["stage"] for t in response["traces"]] == stages
