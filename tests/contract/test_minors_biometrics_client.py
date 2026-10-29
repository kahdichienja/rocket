"""The minors fingerprint calls, as they go on the wire and come back.

Pinned field by field against DHA's published request bodies, because every one of these has a `400` that
names a field, and the fields are *not* spelled the way the eKYC endpoints spell them.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
import respx

from sha_claim import AsyncSHAClient, CaptureStation
from sha_claim.settings import SHASettings

CHILD = "CR7678914660684-5"
MATCH = "4b0f2f8e-7a6c-4d1b-9f3a-0c2d6e8a1b47"
STATION = CaptureStation(workstation_id="WS-1", device_id="DEV-9", agent_id="12345678")


def _token(settings: SHASettings) -> None:
    respx.post(f"{settings.api_root}/tenants/token").mock(
        return_value=httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
    )


def _sent(route: respx.Route, call: int = 0) -> dict[str, Any]:
    """The JSON body of one call, so an assertion reads as the body DHA was sent."""
    body: dict[str, Any] = json.loads(route.calls[call].request.content)
    return body


@respx.mock
async def test_enrolment_sends_what_dha_documents(settings: SHASettings) -> None:
    _token(settings)
    route = respx.post(f"{settings.api_root}/biometrics/enrollments").mock(
        return_value=httpx.Response(202, json={"job_id": "job-1", "next_action": "await_callback"})
    )

    async with AsyncSHAClient(settings) as sha:
        job = await sha.biometrics.enrol(CHILD, 3, station=STATION)

    assert _sent(route) == {
        "beneficiary_code": CHILD,
        "position": 3,
        "workstation_id": "WS-1",
        "device_id": "DEV-9",
        "agent_id": "12345678",
    }
    assert job.job_id is not None and job.job_id.value == "job-1"
    assert job.awaits_callback, "202 means dispatched, not done"


@respx.mock
async def test_verification_goes_to_its_own_path(settings: SHASettings) -> None:
    _token(settings)
    route = respx.post(f"{settings.api_root}/biometrics/enrollments/verify").mock(
        return_value=httpx.Response(202, json={"job_id": "job-2", "next_action": "await_callback"})
    )

    async with AsyncSHAClient(settings) as sha:
        job = await sha.biometrics.verify(CHILD, 3, station=STATION)

    assert _sent(route)["position"] == 3
    assert job.job_id is not None and job.job_id.value == "job-2"


@respx.mock
async def test_a_match_sends_health_id_not_beneficiary_code(settings: SHASettings) -> None:
    """The one field name that differs between the match and the enrolment calls, and the one DHA compares
    against `patient_id` later — a mismatch is refused as a subject mismatch."""
    _token(settings)
    route = respx.post(f"{settings.api_root}/biometrics/matches").mock(
        return_value=httpx.Response(202, json={"match_id": MATCH, "next_action": "await_callback"})
    )

    async with AsyncSHAClient(settings) as sha:
        attempt = await sha.biometrics.match(CHILD, station=STATION)

    body = _sent(route)
    assert body["health_id"] == CHILD
    assert "beneficiary_code" not in body
    assert body["position"] == 0, "any enrolled finger, which is what a point-of-care capture wants"
    assert attempt.match_id is not None and attempt.match_id.value == MATCH


@respx.mock
async def test_a_match_can_target_one_finger(settings: SHASettings) -> None:
    _token(settings)
    route = respx.post(f"{settings.api_root}/biometrics/matches").mock(
        return_value=httpx.Response(202, json={"match_id": MATCH})
    )

    async with AsyncSHAClient(settings) as sha:
        await sha.biometrics.match(CHILD, station=STATION, position=7)

    assert _sent(route)["position"] == 7


@respx.mock
async def test_deadline_seconds_is_omitted_unless_asked_for(settings: SHASettings) -> None:
    """DHA: "Leave it unset unless you have a reason to widen or narrow the window." An explicit default
    would be us overriding a platform default we have no information about."""
    _token(settings)
    route = respx.post(f"{settings.api_root}/biometrics/matches").mock(
        return_value=httpx.Response(202, json={"match_id": MATCH})
    )

    async with AsyncSHAClient(settings) as sha:
        await sha.biometrics.match(CHILD, station=STATION)
        await sha.biometrics.match(CHILD, station=STATION, deadline_seconds=45)

    assert "deadline_seconds" not in _sent(route)
    assert _sent(route, call=1)["deadline_seconds"] == 45


@respx.mock
async def test_enrollment_status_reads_the_positions(settings: SHASettings) -> None:
    _token(settings)
    respx.get(f"{settings.api_root}/biometrics/enrollment-status").mock(
        return_value=httpx.Response(
            200,
            json={
                "beneficiary_code": CHILD,
                "enrollment_status": "partially_enrolled",
                "verified": [5, 2],
                "non_verified": [3],
                "total": 3,
            },
        )
    )

    async with AsyncSHAClient(settings) as sha:
        status = await sha.biometrics.enrollment_status(CHILD)

    assert status.verified == (2, 5), "sorted, so two reads of the same fingers compare equal"
    assert status.non_verified == (3,)
    assert status.total == 3
    assert status.state == "partially_enrolled"
    assert status.can_consent


@respx.mock
async def test_a_beneficiary_with_no_prints_reads_as_needing_enrolment(settings: SHASettings) -> None:
    """DHA: "A beneficiary with no stored prints returns total 0 and an empty enrollment_status"."""
    _token(settings)
    respx.get(f"{settings.api_root}/biometrics/enrollment-status").mock(
        return_value=httpx.Response(200, json={"enrollment_status": "", "total": 0})
    )

    async with AsyncSHAClient(settings) as sha:
        status = await sha.biometrics.enrollment_status(CHILD)

    assert status.needs_enrollment and not status.can_consent
    assert status.beneficiary is not None and status.beneficiary.value == CHILD, (
        "the subject is carried through even when DHA does not echo it back"
    )


@respx.mock
async def test_the_status_query_names_the_beneficiary(settings: SHASettings) -> None:
    _token(settings)
    route = respx.get(f"{settings.api_root}/biometrics/enrollment-status").mock(
        return_value=httpx.Response(200, json={"total": 0})
    )

    async with AsyncSHAClient(settings) as sha:
        await sha.biometrics.enrollment_status(CHILD)

    assert route.calls[0].request.url.params["beneficiary_code"] == CHILD


@respx.mock
async def test_the_reconciliation_read_returns_a_verdict(settings: SHASettings) -> None:
    _token(settings)
    respx.get(f"{settings.api_root}/biometrics/matches/{MATCH}").mock(
        return_value=httpx.Response(200, json={"match_id": MATCH, "status": "matched"})
    )

    async with AsyncSHAClient(settings) as sha:
        result = await sha.biometrics.match_status(MATCH)

    assert result.is_matched
    assert result.proof().value == MATCH, "and only now is it consent"


@respx.mock
async def test_a_failed_capture_carries_its_reason(settings: SHASettings) -> None:
    _token(settings)
    respx.get(f"{settings.api_root}/biometrics/matches/{MATCH}").mock(
        return_value=httpx.Response(
            200, json={"match_id": MATCH, "status": "failed", "error_code": "deadline_exceeded"}
        )
    )

    async with AsyncSHAClient(settings) as sha:
        result = await sha.biometrics.match_status(MATCH)

    assert result.is_terminal and result.deadline_exceeded and not result.is_matched
    with pytest.raises(ValueError, match="cannot prove consent"):
        result.proof()


@respx.mock
async def test_a_bad_position_never_reaches_the_network(settings: SHASettings) -> None:
    """DHA would answer 400 naming the field. Refusing here saves the round trip and, more to the point,
    gives the desk a sentence instead of a server error."""
    _token(settings)
    route = respx.post(f"{settings.api_root}/biometrics/enrollments")

    async with AsyncSHAClient(settings) as sha:
        with pytest.raises(ValueError, match="finger position"):
            await sha.biometrics.enrol(CHILD, 0, station=STATION)

    assert not route.calls, "nothing was dispatched"
