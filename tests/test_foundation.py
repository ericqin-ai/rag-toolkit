import json

import pytest

from rag_toolkit.loaders import JSONLLoader, MarkdownLoader, TextLoader
from rag_toolkit.schemas import Document, StageCandidate, StageTrace
from rag_toolkit.splitters import FixedLengthSplitter, MarkdownHeaderSplitter


def test_schema_validation_and_isolation():
    a = Document(id="a", text="")
    b = Document(id="b", text="")
    a.metadata["x"] = 1
    assert not b.metadata
    assert Document.model_validate_json(a.model_dump_json()) == a
    with pytest.raises(ValueError):
        StageCandidate(doc_id="a", chunk_id="c", score=float("nan"), rank=1)
    with pytest.raises(ValueError):
        StageTrace(stage="bad", latency_ms=0)


def test_loaders(tmp_path):
    path = tmp_path / "a.txt"
    path.write_bytes(b"\xef\xbb\xbfhello\r\nworld")
    assert TextLoader().load(path)[0].text == "hello\nworld"
    assert MarkdownLoader().load(path)[0].id == TextLoader().load(path)[0].id
    path.write_text("\n" + json.dumps({"text": "hello"}) + "\n", encoding="utf8")
    doc = JSONLLoader().load(path)[0]
    assert doc.metadata["line_number"] == 2
    path.write_text('{"text": 3}', encoding="utf8")
    with pytest.raises(ValueError, match="1"):
        JSONLLoader().load(path)


def test_fixed_offsets_and_no_redundant_tail():
    doc = Document(id="a", text="abcdefghij", metadata={"nested": []})
    chunks = FixedLengthSplitter(6, 2).split(doc)
    assert [c.text for c in chunks] == ["abcdef", "efghij"]
    assert all(
        c.text == doc.text[c.metadata["start_char"] : c.metadata["end_char"]] for c in chunks
    )
    assert FixedLengthSplitter().split(Document(id="a", text="")) == []
    with pytest.raises(ValueError):
        FixedLengthSplitter(2, 2)


def test_markdown_fences_and_headers():
    doc = Document(id="a", text="intro\n# One\n```\n## fake\n```\n## Two\nbody")
    chunks = MarkdownHeaderSplitter().split(doc)
    assert len(chunks) == 3
    assert chunks[-1].metadata["headers"] == {"h1": "One", "h2": "Two"}
    assert "## fake" in chunks[1].text
    assert "".join(c.text for c in chunks) == doc.text


@pytest.mark.parametrize("size, overlap", [(2.5, 0), (3, 0.5), (True, 0)])
def test_splitter_rejects_noninteger_bounds(size, overlap):
    with pytest.raises(ValueError):
        FixedLengthSplitter(size, overlap)
