"""Parse uploaded bytes without trusting filenames as filesystem paths."""

import hashlib
import json
from pathlib import PurePath

from rag_toolkit.api.models import DocumentsRequest, EvaluateRequest, EvaluationQuery
from rag_toolkit.schemas import Document


def _records(content):
    text = content.decode("utf-8-sig")
    for number, line in enumerate(text.splitlines(), 1):
        if line.strip():
            try:
                data = json.loads(line)
                if not isinstance(data, dict):
                    raise ValueError("record must be an object")
                yield number, data
            except ValueError as exc:
                raise ValueError(f"line {number}: {exc}") from exc


def parse_documents(content: bytes, filename: str) -> list[Document]:
    suffix = PurePath(filename).suffix.lower()
    if suffix in {".txt", ".md", ".markdown"}:
        text = content.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        return [
            Document(
                id=hashlib.sha256(filename.encode()).hexdigest(),
                text=text,
                metadata={"source": filename},
            )
        ]
    if suffix != ".jsonl":
        raise ValueError("supported document formats: TXT, Markdown, JSONL")
    documents = []
    for number, data in _records(content):
        data.setdefault("id", hashlib.sha256(f"{filename}:{number}".encode()).hexdigest())
        try:
            documents.append(Document.model_validate(data, strict=True))
        except ValueError as exc:
            raise ValueError(f"line {number}: {exc}") from exc
    return DocumentsRequest(documents=documents).documents


def parse_queries(content: bytes) -> list[EvaluationQuery]:
    queries = []
    for number, data in _records(content):
        try:
            queries.append(EvaluationQuery.model_validate(data, strict=True))
        except ValueError as exc:
            raise ValueError(f"line {number}: {exc}") from exc
    return EvaluateRequest(queries=queries, ks=[1], top_k=1).queries
