import re

from rag_toolkit.schemas import Chunk, Document
from rag_toolkit.splitters.fixed import FixedLengthSplitter


class MarkdownHeaderSplitter(FixedLengthSplitter):
    def split(self, document: Document) -> list[Chunk]:
        boundaries, headers, fence = [(0, {})], {}, None
        offset = 0
        for line in document.text.splitlines(keepends=True):
            marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
            if marker:
                chars, tail = marker.groups()
                if fence is None:
                    fence = chars
                elif chars[0] == fence[0] and len(chars) >= len(fence) and not tail.strip():
                    fence = None
            elif fence is None:
                heading = re.match(r"^ {0,3}(#{1,6})[ \t]+(.+?)\s*$", line)
                if heading:
                    level = len(heading[1])
                    headers = {k: v for k, v in headers.items() if int(k[1:]) < level}
                    headers[f"h{level}"] = re.sub(r"\s+#+\s*$", "", heading[2]).strip()
                    if offset == 0:
                        boundaries[0] = (0, dict(headers))
                    else:
                        boundaries.append((offset, dict(headers)))
            offset += len(line)
        chunks = []
        for index, (start, section_headers) in enumerate(boundaries):
            end = boundaries[index + 1][0] if index + 1 < len(boundaries) else len(document.text)
            chunks.extend(self._chunks(document, start, end, section_headers))
        for index, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = index
        return chunks
