"""Validated public data contracts."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

StageName = Literal["bm25", "dense", "fusion", "rerank"]


class Schema(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Document(Schema):
    id: str = Field(min_length=1)
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class Chunk(Schema):
    chunk_id: str = Field(min_length=1)
    doc_id: str = Field(min_length=1)
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class StageCandidate(Schema):
    doc_id: str
    chunk_id: str
    score: float
    rank: int = Field(ge=1)


class StageTrace(Schema):
    stage: StageName
    latency_ms: float = Field(ge=0)
    candidates: list[StageCandidate] = Field(default_factory=list)


class SearchResult(Schema):
    doc_id: str
    chunk_id: str
    text: str
    score: float
    rank: int = Field(ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    stage_ranks: dict[str, int | None] = Field(default_factory=dict)
    stage_scores: dict[str, float | None] = Field(default_factory=dict)


class SearchResponse(Schema):
    query: str
    results: list[SearchResult] = Field(default_factory=list)
    traces: list[StageTrace] = Field(default_factory=list)
    total_latency_ms: float = Field(ge=0)


class EvalReport(Schema):
    metrics: dict[str, float]
    num_queries: int = Field(ge=0)
    per_query: list[dict[str, Any]] = Field(default_factory=list)
