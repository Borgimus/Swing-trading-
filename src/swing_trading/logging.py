from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit, urlunsplit

_SENSITIVE_KEY_PARTS = (
    "authorization",
    "proxyauthorization",
    "apikey",
    "secret",
    "password",
    "token",
    "cookie",
    "sessionid",
    "signedurl",
)
_BEARER = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")
_ASSIGNMENT = re.compile(r"(?i)\b(api[_-]?key|secret|password|token|authorization)=([^\s&]+)")


def _normalized_key(key: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): (
                "[REDACTED]"
                if any(part in _normalized_key(key) for part in _SENSITIVE_KEY_PARTS)
                else redact(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    if isinstance(value, str):
        cleaned = _BEARER.sub("Bearer [REDACTED]", value)
        cleaned = _ASSIGNMENT.sub(lambda match: f"{match.group(1)}=[REDACTED]", cleaned)
        if "://" in cleaned:
            try:
                parsed = urlsplit(cleaned)
                if parsed.query or parsed.username or parsed.password:
                    safe_host = parsed.hostname or ""
                    if parsed.port:
                        safe_host = f"{safe_host}:{parsed.port}"
                    cleaned = urlunsplit((parsed.scheme, safe_host, parsed.path, "", ""))
            except ValueError:
                return "[REDACTED_URL]"
        return cleaned
    return value


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = record.msg
        if isinstance(message, dict):
            context = redact(message)
            event = str(context.pop("event", record.name))
        else:
            event = str(redact(record.getMessage()))
            context = {}
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "component": record.name,
            "event": event,
            **context,
        }
        if record.exc_info and record.exc_info[0] is not None:
            payload["exception_class"] = record.exc_info[0].__name__
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def configure_json_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
