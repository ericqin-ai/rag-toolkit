import math
from collections import Counter

from rag_toolkit.retrievers.base import BaseRetriever
from rag_toolkit.utils import positive_k, ranked, tokenize


class BM25Retriever(BaseRetriever):
    def __init__(self, chunks=(), k1: float = 1.5, b: float = 0.75):
        if not math.isfinite(k1) or k1 <= 0 or not 0 <= b <= 1:
            raise ValueError("invalid BM25 parameters")
        self.k1, self.b = k1, b
        self.chunks = {}
        self.add_chunks(chunks)

    def add_chunks(self, chunks):
        self.chunks.update({c.chunk_id: c.model_copy(deep=True) for c in chunks})
        self._rebuild()

    def delete(self, chunk_ids):
        for key in chunk_ids:
            self.chunks.pop(key, None)
        self._rebuild()

    def _rebuild(self):
        self.terms = {key: Counter(tokenize(c.text)) for key, c in self.chunks.items()}
        self.df = Counter(term for tf in self.terms.values() for term in tf)
        self.lengths = {key: sum(tf.values()) for key, tf in self.terms.items()}
        self.avgdl = sum(self.lengths.values()) / max(1, len(self.chunks))

    def retrieve(self, query, top_k=10):
        positive_k(top_k)
        if not self.avgdl:
            return []
        scores = {}
        for key, tf in self.terms.items():
            score = 0
            for term in set(tokenize(query)):
                count = tf[term]
                if not count:
                    continue
                idf = math.log(1 + (len(self.chunks) - self.df[term] + 0.5) / (self.df[term] + 0.5))
                score += (
                    idf
                    * count
                    * (self.k1 + 1)
                    / (count + self.k1 * (1 - self.b + self.b * self.lengths[key] / self.avgdl))
                )
            if score > 0:
                scores[(self.chunks[key].doc_id, key)] = score
        return ranked(scores, top_k)
