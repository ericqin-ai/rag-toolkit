from rag_toolkit.evaluation.metrics import _unique, hit_at_k, mrr, ndcg_at_k, recall_at_k
from rag_toolkit.schemas import EvalReport
from rag_toolkit.utils import positive_k


class Evaluator:
    def evaluate(self, responses, qrels, ks=(1, 5, 10)):
        ks = sorted(set(ks))
        for k in ks:
            positive_k(k)
        per_query = []
        names = ["mrr"] + [f"{name}@{k}" for k in ks for name in ("hit", "recall", "ndcg")]
        for response in responses:
            if response.query not in qrels:
                raise ValueError(f"missing relevance judgments for {response.query!r}")
            relevant = qrels[response.query]
            ranking = [item.doc_id for item in sorted(response.results, key=lambda r: r.rank)]
            metrics = {"mrr": mrr(ranking, relevant)}
            for k in ks:
                metrics.update(
                    {
                        f"hit@{k}": hit_at_k(ranking, relevant, k),
                        f"recall@{k}": recall_at_k(ranking, relevant, k),
                        f"ndcg@{k}": ndcg_at_k(ranking, relevant, k),
                    }
                )
            per_query.append(
                {"query": response.query, "ranking": _unique(ranking), "metrics": metrics}
            )
        aggregate = {
            name: (
                sum(row["metrics"][name] for row in per_query) / len(per_query)
                if per_query
                else 0.0
            )
            for name in names
        }
        return EvalReport(metrics=aggregate, num_queries=len(per_query), per_query=per_query)
