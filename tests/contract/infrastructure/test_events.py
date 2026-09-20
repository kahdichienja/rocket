import httpx
import pytest
import respx

from sha_claim import AsyncSHAClient, SDKEvent
from sha_claim.settings import SHASettings


@respx.mock
async def test_events_are_emitted_per_attempt_with_redaction(settings: SHASettings) -> None:
    root = settings.api_root
    respx.post(f"{root}/tenants/token").mock(
        return_value=httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
    )
    respx.get(f"{root}/patients/benefits").mock(
        side_effect=[httpx.Response(503), httpx.Response(200, json={"results": []})]
    )
    respx.post(f"{root}/claims/preview").mock(
        return_value=httpx.Response(400, json={"error": "Bad Request", "message": "nope", "trace_id": "tr-1"})
    )
    respx.post(f"{root}/claims/submit").mock(side_effect=httpx.ReadTimeout("slow"))

    events: list[SDKEvent] = []
    async with AsyncSHAClient(settings, on_event=events.append) as sha:
        await sha.eligibility.benefits("CR1111111111111-1")
        session = sha.claims.resume("CR0-TOKEN12345")
        with pytest.raises(Exception):  # noqa: B017 — BadRequestError; the point is the events
            await session.preview()
        with pytest.raises(Exception):  # noqa: B017 — SubmissionOutcomeUnknownError
            await session.submit("INV-1")

    ops = [(e.operation, e.status, e.attempt, e.error) for e in events]
    assert ops == [
        ("POST /tenants/token", 200, 1, None),
        ("GET /patients/benefits", 503, 1, None),
        ("GET /patients/benefits", 200, 2, None),
        ("POST /claims/preview", 400, 1, None),
        ("POST /claims/submit", None, 1, "ReadTimeout"),
    ]
    preview = events[3]
    assert preview.trace_id == "tr-1" and not preview.ok
    assert preview.consent_token == "CR0-…45" and "TOKEN12345" not in str(events)
    assert all(e.duration_ms >= 0 for e in events) and events[0].occurred_at.tzinfo is not None


@respx.mock
async def test_broken_hook_never_breaks_a_call(settings: SHASettings) -> None:
    root = settings.api_root
    respx.post(f"{root}/tenants/token").mock(
        return_value=httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
    )
    respx.get(f"{root}/patients/benefits").mock(return_value=httpx.Response(200, json={"results": []}))

    def explode(_: SDKEvent) -> None:
        raise RuntimeError("observer bug")

    async with AsyncSHAClient(settings, on_event=explode) as sha:
        assert await sha.eligibility.benefits("CR1111111111111-1") == ()
