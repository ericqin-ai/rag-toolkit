"""HTTP request/response contracts, shared with the Inspector."""

from pydantic import Field, StrictInt, field_validator, model_validator

from rag_toolkit.schemas import Document, Schema


class SearchRequest(Schema):
    query: str = Field(min_length=1, max_length=10000)
    top_k: StrictInt = Field(default=10, ge=1, le=1000)

    @field_validator("query")
    @classmethod
    def nonblank_query(cls, value):
        if not value.strip():
            raise ValueError("query must not be blank")
        return value


class DocumentsRequest(Schema):
    documents: list[Document] = Field(min_length=1, max_length=1000)

    @field_validator("documents")
    @classmethod
    def unique_documents(cls, value):
        if len({d.id for d in value}) != len(value):
            raise ValueError("duplicate document IDs")
        return value


class EvaluationQuery(Schema):
    id: str | None = None
    query: str = Field(min_length=1, max_length=10000)
    relevant_doc_ids: list[str]

    @field_validator("query")
    @classmethod
    def nonblank_query(cls, value):
        if not value.strip():
            raise ValueError("query must not be blank")
        return value


class EvaluateRequest(Schema):
    queries: list[EvaluationQuery] = Field(min_length=1, max_length=1000)
    top_k: StrictInt = Field(default=10, ge=1, le=1000)
    ks: list[StrictInt] = Field(default_factory=lambda: [1, 3, 5], min_length=1)

    @model_validator(mode="after")
    def validate_evaluation(self):
        if len({q.query for q in self.queries}) != len(self.queries):
            raise ValueError("duplicate query text")
        if any(k <= 0 or k > self.top_k for k in self.ks):
            raise ValueError("ks must be positive and not exceed top_k")
        return self


class HealthResponse(Schema):
    status: str = "ok"
    num_documents: int
    num_chunks: int


class DocumentsResponse(Schema):
    num_documents: int
    num_chunks: int
    added_chunks: int


class ErrorBody(Schema):
    code: str
    message: str
    details: list[dict] = Field(default_factory=list)


class ErrorResponse(Schema):
    error: ErrorBody
