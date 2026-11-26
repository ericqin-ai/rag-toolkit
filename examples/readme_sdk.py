from rag_toolkit.pipeline import RetrievalPipeline
from rag_toolkit.schemas import Document

pipeline = RetrievalPipeline.from_config("configs/offline.yaml")
pipeline.add_documents(
    [
        Document(id="intro", text="FAISS supports vector search."),
        Document(id="lexical", text="BM25 supports lexical search."),
    ]
)
response = pipeline.search("vector search", top_k=2)
assert response.results[0].doc_id == "intro"
print("Offline Pipeline Sanity Check")
print(response.model_dump_json(indent=2))
