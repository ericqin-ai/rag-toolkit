import hashlib
from copy import deepcopy

from rag_toolkit.schemas import Chunk, Document
from rag_toolkit.splitters.base import BaseSplitter


class FixedLengthSplitter(BaseSplitter):
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        if type(chunk_size) is not int or type(chunk_overlap) is not int:
            raise ValueError("chunk_size and chunk_overlap must be integers")
        if chunk_size <= 0 or not 0 <= chunk_overlap < chunk_size:
            raise ValueError("require chunk_size > 0 and 0 <= overlap < size")
        self.chunk_size, self.chunk_overlap = chunk_size, chunk_overlap

    def _chunks(self, doc, start, end, headers=None):
        chunks = []
        while start < end:
            stop = min(start + self.chunk_size, end)
            signature = (
                f"{doc.id}:{type(self).__name__}:{self.chunk_size}:"
                f"{self.chunk_overlap}:{start}:{stop}"
            )
            metadata = deepcopy(doc.metadata)
            metadata.update(start_char=start, end_char=stop)
            if headers is not None:
                metadata["headers"] = dict(headers)
            chunks.append(
                Chunk(
                    chunk_id=hashlib.sha256(signature.encode()).hexdigest(),
                    doc_id=doc.id,
                    text=doc.text[start:stop],
                    metadata=metadata,
                )
            )
            if stop == end:
                break
            start = stop - self.chunk_overlap
        return chunks

    def split(self, document: Document) -> list[Chunk]:
        chunks = self._chunks(document, 0, len(document.text))
        for index, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = index
        return chunks
