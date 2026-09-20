"""HTTP status + `{error, message, trace_id}` → SDK exceptions."""

from __future__ import annotations

from pydantic import ValidationError

from sha_claim.adapters.wire.schemas.common import ErrorEnvelope
from sha_claim.adapters.wire.transport import WireResponse
from sha_claim.errors import (
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitedError,
    ServerError,
    TransportError,
)

_BY_STATUS: dict[int, type[ServerError]] = {
    400: BadRequestError,
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: NotFoundError,
}


def envelope_of(response: WireResponse) -> ErrorEnvelope:
    try:
        payload = response.json()
        if isinstance(payload, dict):
            return ErrorEnvelope.model_validate(payload)
    except (ValueError, ValidationError):
        pass
    return ErrorEnvelope(error="", message=response.body[:200].decode("utf-8", "replace"))


def raise_for_status(response: WireResponse) -> None:
    if response.status < 400:
        return
    env = envelope_of(response)
    trace = env.trace_id or response.request_id
    if response.status == 429:
        retry_after = response.headers.get("retry-after")
        raise RateLimitedError(
            env.message or "rate limited",
            retry_after=float(retry_after) if retry_after and retry_after.isdigit() else None,
            trace_id=trace,
        )
    if response.status >= 500:
        raise TransportError(f"{response.status} {env.error}: {env.message}", trace_id=trace)
    cls = _BY_STATUS.get(response.status, ServerError)
    raise cls(env.message, status=response.status, error=env.error, trace_id=trace)
