import json

import pytest

from sha_claim.adapters.wire.error_translator import raise_for_status
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


def envelope(
    status: int, message: str = "boom", trace: str | None = "t-1", headers: dict[str, str] | None = None
) -> WireResponse:
    body = {"error": "Err", "message": message}
    if trace:
        body["trace_id"] = trace
    return WireResponse(status, headers or {}, json.dumps(body).encode())


@pytest.mark.parametrize(
    ("status", "cls"),
    [
        (400, BadRequestError),
        (401, AuthenticationError),
        (403, PermissionDeniedError),
        (404, NotFoundError),
        (409, ServerError),
    ],
)
def test_4xx_maps_by_status_and_keeps_trace_id(status: int, cls: type[ServerError]) -> None:
    with pytest.raises(cls) as exc:
        raise_for_status(envelope(status))
    assert exc.value.status == status and exc.value.trace_id == "t-1" and "boom" in str(exc.value)


def test_5xx_is_transport_error_with_trace_fallback_to_request_id() -> None:
    with pytest.raises(TransportError) as exc:
        raise_for_status(envelope(502, trace=None, headers={"x-request-id": "req-9"}))
    assert exc.value.trace_id == "req-9"


def test_429_carries_retry_after() -> None:
    with pytest.raises(RateLimitedError) as exc:
        raise_for_status(envelope(429, headers={"retry-after": "7"}))
    assert exc.value.retry_after == 7.0


def test_non_json_body_is_tolerated() -> None:
    with pytest.raises(BadRequestError, match="<html>"):
        raise_for_status(WireResponse(400, {}, b"<html>nope</html>"))


def test_2xx_is_silent() -> None:
    raise_for_status(WireResponse(200, {}, b"{}"))
