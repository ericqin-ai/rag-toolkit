import re


def tokenize(text: str) -> list[str]:
    """Latin words/numbers and individual CJK characters; no downloaded tokenizer."""
    return re.findall(r"[a-z0-9_]+|[\u3400-\u9fff]", text.lower())


def whitespace_tokenize(text: str) -> list[str]:
    return text.lower().split()
