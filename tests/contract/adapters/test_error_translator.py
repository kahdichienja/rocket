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


def test_an_html_body_is_an_upstream_crash_not_a_rejection() -> None:
    """A JSON API answering HTML is not answering at all — it is somebody's error page.

    Seen on a live claim submission: DHA returned **400** whose body was its own upstream's
    `<title>Server Error (500)</title>` page. Believing the status line turns "SHA crashed and we do not
    know whether the claim went through" into "SHA rejected your claim" — which invites a desk to edit a
    good claim and send it again, and a resubmission of one that *did* land is a duplicate on a national
    system.

    As a `TransportError` it becomes `SubmissionOutcomeUnknownError`, which parks the journey in
    SUBMIT_UNKNOWN for `preview` to resolve.
    """
    with pytest.raises(TransportError):
        raise_for_status(WireResponse(400, {}, b"<html>nope</html>"))


def test_the_headline_is_a_sentence_not_a_page_of_markup() -> None:
    body = b"<!doctype html><html><head><title>Server Error (500)</title></head><body></body></html>"
    with pytest.raises(TransportError) as caught:
        raise_for_status(WireResponse(400, {}, body))
    assert "Server Error (500)" in str(caught.value)
    assert "<html" not in str(caught.value), "raw markup must not reach a headline"


def test_html_wrapped_inside_dhas_json_envelope_is_caught_too() -> None:
    """The real one arrived as JSON with the page inside `message`, not as a bare HTML body.

    Built with `json.dumps` rather than written out, so the escaping is the same as DHA's.
    """
    body = json.dumps(
        {
            "message": (
                "failed to perform requested claim operation: \n<!doctype html>\n"
                '<html lang="en">\n<head>\n  <title>Server Error (500)</title>\n</head>\n</html>'
            ),
            "trace_id": "t-1",
        }
    ).encode()
    with pytest.raises(TransportError) as caught:
        raise_for_status(WireResponse(400, {}, body))
    assert caught.value.trace_id == "t-1", "the trace id must survive — it is what support asks for"
    assert "<html" not in str(caught.value)


def test_an_ordinary_rejection_is_still_a_rejection() -> None:
    """The point is not to reclassify everything: a real refusal must stay one, or a desk stops
    believing the difference."""
    with pytest.raises(BadRequestError):
        raise_for_status(WireResponse(400, {}, b'{"message": "Beneficiary is not eligible"}'))


def test_2xx_is_silent() -> None:
    raise_for_status(WireResponse(200, {}, b"{}"))


def test_a_crashed_submit_becomes_an_unknown_outcome_not_a_refusal() -> None:
    """The whole point of the reclassification, end to end.

    `SubmitClaim` turns a transport-level failure into `SubmissionOutcomeUnknownError`, which the backend
    uses to park the journey in SUBMIT_UNKNOWN. Left as a rejection, the desk is told the claim was
    refused and resends it — and a claim that *did* land the first time becomes a duplicate.
    """
    import asyncio

    from sha_claim.domain.claim import Submission, VirtualClaim
    from sha_claim.domain.identifiers import ConsentToken, InvoiceNumber
    from sha_claim.errors import SubmissionOutcomeUnknownError
    from sha_claim.use_cases.submit_claim import SubmitClaim

    crash = WireResponse(400, {}, b"<!doctype html><html><title>Server Error (500)</title></html>")

    class _Gateway:
        async def submit(self, token: ConsentToken, submission: Submission) -> VirtualClaim:
            raise_for_status(crash)
            raise AssertionError("unreachable")

    with pytest.raises(SubmissionOutcomeUnknownError):
        asyncio.run(
            SubmitClaim(_Gateway()).execute(
                ConsentToken("tok-1"), Submission(invoice_number=InvoiceNumber("INV-1"))
            )
        )
