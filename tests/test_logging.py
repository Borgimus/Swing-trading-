from __future__ import annotations

import json
import logging

from swing_trading.logging import JsonFormatter, redact


def test_nested_credentials_and_signed_urls_are_redacted() -> None:
    sensitive_value = "super-sensitive-value"
    value = {
        "Authorization": f"Bearer {sensitive_value}",
        "nested": {
            "api_key": sensitive_value,
            "safe": "kept",
            "url": f"https://example.test/path?token={sensitive_value}&expires=1",
        },
    }

    redacted = redact(value)

    assert sensitive_value not in json.dumps(redacted)
    assert redacted["nested"]["safe"] == "kept"
    assert redacted["nested"]["url"] == "https://example.test/path"


def test_json_formatter_emits_structured_safe_record() -> None:
    record = logging.LogRecord(
        name="swing.importer",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg={"event": "import_rejected", "token": "hidden", "error_code": "STALE_BATCH"},
        args=(),
        exc_info=None,
    )

    encoded = JsonFormatter().format(record)
    payload = json.loads(encoded)

    assert payload["event"] == "import_rejected"
    assert payload["token"] == "[REDACTED]"
    assert payload["error_code"] == "STALE_BATCH"
    assert payload["component"] == "swing.importer"
