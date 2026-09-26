"""Translates HTTP error codes and Smart error envelopes into typed domain exceptions."""

from __future__ import annotations

from typing import Any

from smart_access.errors import (
    SmartAccessError,
    SmartAuthenticationError,
    SmartBadRequestError,
    SmartNotFoundError,
    SmartPermissionDeniedError,
    SmartRateLimitedError,
    SmartTransportError,
)


def translate_error(status_code: int, body: Any = None) -> SmartAccessError:
    """Translates an HTTP status code and response payload into a SmartAccessError."""
    msg = ""
    if isinstance(body, dict):
        msg = body.get("message") or body.get("error") or ""
        if not msg and isinstance(body.get("content"), dict):
            msg = body["content"].get("message", "")
    elif isinstance(body, str):
        msg = body

    if not msg:
        msg = f"HTTP {status_code} error from Smart API"

    if status_code == 400:
        return SmartBadRequestError(msg, status_code=status_code, response_body=body)
    if status_code == 401:
        return SmartAuthenticationError(msg, status_code=status_code, response_body=body)
    if status_code == 403:
        return SmartPermissionDeniedError(msg, status_code=status_code, response_body=body)
    if status_code == 404:
        return SmartNotFoundError(msg, status_code=status_code, response_body=body)
    if status_code == 429:
        return SmartRateLimitedError(msg, status_code=status_code, response_body=body)

    return SmartTransportError(msg, status_code=status_code, response_body=body)
