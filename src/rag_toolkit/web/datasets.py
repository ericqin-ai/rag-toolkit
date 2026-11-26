"""Parse uploaded bytes without trusting filenames as filesystem paths."""

import hashlib
import json
from pathlib import PurePath

from rag_toolkit.api.models import DocumentsRequest, EvaluateRequest, EvaluationQuery
from rag_toolkit.schemas import Document


def _records(content):
    try:
        text = content.decode("utf-8-sig")
    except UnicodeError:
        raise ValueError("invalid UTF-8 encoding") from None
    for number, line in enumerate(text.splitlines(), 1):
        if line.strip():
            try:
                data = json.loads(line)
                if not isinstance(data, dict):
                    raise ValueError("record must be an object")
                yield number, data
            except ValueError:
                raise ValueError(f"line {number}: invalid JSON object") from None


def parse_documents(content: bytes, filename: str) -> list[Document]:
    suffix = PurePath(filename).suffix.lower()
    if suffix in {".txt", ".md", ".markdown"}:
        try:
            text = content.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
            return [
                Document(
                    id=hashlib.sha256(filename.encode()).hexdigest(),
                    text=text,
                    metadata={"source": filename},
                )
            ]
        except (UnicodeError, ValueError):
            raise ValueError("invalid UTF-8 text document") from None
    if suffix != ".jsonl":
        raise ValueError("supported document formats: TXT, Markdown, JSONL")
    documents = []
    ids = set()
    for number, data in _records(content):
        data.setdefault("id", hashlib.sha256(f"{filename}:{number}".encode()).hexdigest())
        try:
            documents.append(Document.model_validate(data, strict=True))
        except ValueError:
            raise ValueError(f"line {number}: invalid document fields") from None
        if documents[-1].id in ids:
            raise ValueError(f"line {number}: duplicate document ID")
        ids.add(documents[-1].id)
    try:
        return DocumentsRequest(documents=documents).documents
    except ValueError:
        raise ValueError("document count must be between 1 and 1000") from None


def parse_queries(content: bytes) -> list[EvaluationQuery]:
    queries = []
    seen = set()
    for number, data in _records(content):
        try:
            queries.append(EvaluationQuery.model_validate(data, strict=True))
        except ValueError:
            raise ValueError(f"line {number}: invalid query fields") from None
        if queries[-1].query in seen:
            raise ValueError(f"line {number}: duplicate query text")
        seen.add(queries[-1].query)
    try:
        return EvaluateRequest(queries=queries, ks=[1], top_k=1).queries
    except ValueError:
        raise ValueError("query count must be between 1 and 1000") from None
