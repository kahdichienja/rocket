"""HTTP status + `{error, message, trace_id, details}` → SDK exceptions."""

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


#: What an upstream crash looks like when DHA wraps it instead of passing the status through.
#:
#: Seen on a live claim submission: DHA answered **400** whose body was its own upstream's HTML error page
#: — `<title>Server Error (500)</title>`. A 400 means *we* sent something wrong and the claim was refused;
#: a 500 means SHA broke and the claim's fate is unknown. Believing the status line turned "SHA crashed,
#: we do not know whether the claim went through" into "SHA rejected your claim", which invites a desk to
#: edit a perfectly good claim and submit it again — and a resubmitted claim that did land the first time
#: is a duplicate on a national system.
#:
#: The API answers JSON for everything, so an HTML body is not an answer at all; it is a web server's
#: error page that reached us by accident.
_UPSTREAM_CRASH_MARKERS = ("<!doctype html", "<html", "server error (5")


def looks_like_upstream_crash(body: bytes) -> bool:
    """Whether this body is somebody's HTML error page rather than an answer from the API."""
    head = body[:400].decode("utf-8", "replace").strip().lower()
    return any(marker in head for marker in _UPSTREAM_CRASH_MARKERS)


def _crash_summary(body: bytes) -> str:
    """One line for a desk, instead of a page of markup.

    The raw HTML is not withheld — it stays on the exception's `technical` — but it is useless as a
    headline and unreadable in a toast.
    """
    text = body[:400].decode("utf-8", "replace")
    start = text.lower().find("<title>")
    if start != -1:
        end = text.lower().find("</title>", start)
        if end != -1:
            title = text[start + len("<title>") : end].strip()
            if title:
                return f"SHA's own server failed ({title})"
    return "SHA's own server returned an error page"


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
    detail = env.detail()
    if response.status == 429:
        retry_after = response.headers.get("retry-after")
        raise RateLimitedError(
            detail or "rate limited",
            retry_after=float(retry_after) if retry_after and retry_after.isdigit() else None,
            trace_id=trace,
        )
    if response.status >= 500 or looks_like_upstream_crash(response.body):
        # A TransportError, not a rejection: the request may or may not have been acted on. `SubmitClaim`
        # turns this into `SubmissionOutcomeUnknownError`, which parks the journey in SUBMIT_UNKNOWN for
        # `preview` to resolve — instead of telling a desk the claim was refused and letting them resend.
        summary = _crash_summary(response.body) if looks_like_upstream_crash(response.body) else detail
        raise TransportError(f"{response.status} {env.status_text}: {summary}".strip(), trace_id=trace)
    cls = _BY_STATUS.get(response.status, ServerError)
    raise cls(detail, status=response.status, error=env.status_text, trace_id=trace)
