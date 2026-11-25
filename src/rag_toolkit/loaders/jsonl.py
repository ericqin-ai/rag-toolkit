import hashlib
import json
from pathlib import Path

from rag_toolkit.loaders.text import TextLoader
from rag_toolkit.schemas import Document


class JSONLLoader(TextLoader):
    def load(self, path: str | Path) -> list[Document]:
        path = Path(path).resolve()
        docs, seen = [], set()
        for number, line in enumerate(path.read_text(encoding=self.encoding).splitlines(), 1):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                if not isinstance(data, dict):
                    raise ValueError("record must be an object")
                data.setdefault("id", hashlib.sha256(f"{path}:{number}".encode()).hexdigest())
                doc = Document.model_validate(data, strict=True)
                if doc.id in seen:
                    raise ValueError("duplicate document id")
                seen.add(doc.id)
                doc.metadata.update(source=str(path), loader="JSONLLoader", line_number=number)
                docs.append(doc)
            except (ValueError, TypeError) as exc:
                raise ValueError(f"{path}:{number}: {exc}") from exc
        return docs
