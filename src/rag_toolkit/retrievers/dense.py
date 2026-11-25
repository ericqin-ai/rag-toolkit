from rag_toolkit.retrievers.base import BaseRetriever
from rag_toolkit.utils import positive_k


class DenseRetriever(BaseRetriever):
    def __init__(self, embedder, store):
        self.embedder, self.store = embedder, store

    def add_chunks(self, chunks):
        self.store.upsert(chunks, self.embedder.embed_documents([c.text for c in chunks]))

    def retrieve(self, query, top_k=10, *, chunk_ids=None):
        positive_k(top_k)
        if top_k == 0 or not query.strip():
            return []
        vector = self.embedder.embed_query(query)
        scoped_search = getattr(self.store, "search_scoped", None)
        if chunk_ids is not None and scoped_search is not None:
            candidates = scoped_search(vector, top_k, chunk_ids)
        else:
            candidates = self.store.search(vector, top_k)
        if chunk_ids is not None:
            candidates = [c for c in candidates if c.chunk_id in chunk_ids]
            candidates = [c.model_copy(update={"rank": i}) for i, c in enumerate(candidates, 1)]
        return candidates
