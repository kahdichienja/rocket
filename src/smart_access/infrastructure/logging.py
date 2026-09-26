"""Structured logging and secret redaction filter."""

from __future__ import annotations

import logging
import re

LOGGER = logging.getLogger("smart_access")

_SECRET_PATTERNS = [
    re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),
    re.compile(r"(password=)[^&]+", re.IGNORECASE),
    re.compile(r'("password":\s*")[^"]+(")', re.IGNORECASE),
    re.compile(r'("client_secret":\s*")[^"]+(")', re.IGNORECASE),
]


def redact_secrets(text: str) -> str:
    """Masks tokens and passwords in log messages."""
    result = text
    for pattern in _SECRET_PATTERNS:
        result = pattern.sub(r"\1***REDACTED***", result)
    return result


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_secrets(record.msg)
        return True


LOGGER.addFilter(RedactingFilter())
