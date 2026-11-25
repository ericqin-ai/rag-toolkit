import hashlib
from pathlib import Path

from rag_toolkit.loaders.base import BaseLoader
from rag_toolkit.schemas import Document


class TextLoader(BaseLoader):
    def __init__(self, encoding: str = "utf-8-sig"):
        self.encoding = encoding

    def load(self, path: str | Path) -> list[Document]:
        path = Path(path).resolve()
        return [
            Document(
                id=hashlib.sha256(str(path).encode()).hexdigest(),
                text=path.read_text(encoding=self.encoding),
                metadata={"source": str(path), "loader": type(self).__name__},
            )
        ]
