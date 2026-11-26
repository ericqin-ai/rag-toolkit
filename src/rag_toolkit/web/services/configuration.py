"""Safe serialization at presentation/export boundaries."""

import json
import re
from collections.abc import Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

SENSITIVE = re.compile(r"key|secret|token|password|passwd|auth|credential|cookie", re.I)


def sensitive_key(key):
    normalized = re.sub(r"[^a-z0-9]", "", str(key).lower())
    return normalized in {"key", "auth", "authorization", "credentials", "cookie", "cookies"} or (
        normalized.endswith(
            (
                "apikey",
                "secret",
                "token",
                "password",
                "passwd",
                "credential",
                "privatekey",
                "authorization",
                "xauth",
            )
        )
    )


def redact(value):
    if isinstance(value, Mapping):
        return {str(k): "[REDACTED]" if sensitive_key(k) else redact(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v) for v in value]
    if isinstance(value, str) and value.lower().startswith(("https://", "http://")):
        try:
            url = urlsplit(value)
        except ValueError:
            return "[REDACTED URL]"
        host = url.netloc.rsplit("@", 1)[-1]
        query = urlencode(
            [(k, "[REDACTED]" if sensitive_key(k) else v) for k, v in parse_qsl(url.query)]
        )
        return urlunsplit((url.scheme, host, url.path, query, ""))
    return value


def safe_json(value):
    return json.dumps(redact(value), ensure_ascii=False, indent=2)
