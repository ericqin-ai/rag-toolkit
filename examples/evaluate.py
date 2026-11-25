"""Run a reproducible CPU-only sample evaluation from any working directory."""

import argparse
import json
from pathlib import Path

from rag_toolkit.evaluation import Evaluator
from rag_toolkit.loaders import JSONLLoader
from rag_toolkit.pipeline import RetrievalPipeline

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/offline.yaml")
    parser.add_argument("--documents", type=Path, default=ROOT / "datasets/documents.jsonl")
    parser.add_argument("--queries", type=Path, default=ROOT / "datasets/queries.jsonl")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    pipeline = RetrievalPipeline.from_config(args.config)
    count = pipeline.add_documents(JSONLLoader().load(args.documents))
    records = [
        json.loads(line)
        for line in args.queries.read_text(encoding="utf8").splitlines()
        if line.strip()
    ]
    qrels = {}
    for row in records:
        if row["query"] in qrels:
            raise ValueError("duplicate query text in evaluation dataset")
        qrels[row["query"]] = set(row["relevant_doc_ids"])
    responses = [pipeline.search(row["query"], args.top_k) for row in records]
    report = Evaluator().evaluate(responses, qrels, ks=[1, 3, 5])
    print(f"Indexed {count} chunks; evaluated {report.num_queries} queries.")
    print(json.dumps(report.metrics, indent=2, sort_keys=True))
    if args.output:
        args.output.write_text(report.model_dump_json(indent=2), encoding="utf8")


if __name__ == "__main__":
    main()
