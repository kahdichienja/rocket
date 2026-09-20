"""Structured-ish logging with PII/secret redaction. Consumers configure handlers; we only emit."""

from __future__ import annotations

import logging
import re

logger = logging.getLogger("sha_claim")

_BEARER = re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*")
_LONG_DIGITS = re.compile(r"\b\d{6,}\b")  # national IDs, phone numbers, OTPs


def redact(text: str) -> str:
    text = _BEARER.sub(r"\1[redacted]", text)
    return _LONG_DIGITS.sub("[digits]", text)


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(str(record.msg))
        if record.args:
            record.args = tuple(redact(str(a)) for a in record.args)
        return True


logger.addFilter(RedactingFilter())
