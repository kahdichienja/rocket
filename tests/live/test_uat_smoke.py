"""Hits the DHA UAT environment. Run with: RUN_LIVE=1 pytest -m live"""

import os
from datetime import date

import pytest

from sha_claim import AsyncSHAClient, BadRequestError, IdentificationType

pytestmark = [pytest.mark.live, pytest.mark.skipif(not os.getenv("RUN_LIVE"), reason="set RUN_LIVE=1")]


@pytest.fixture(autouse=True)
def _load_dotenv() -> None:
    from dotenv import load_dotenv

    load_dotenv()


async def test_eligibility_synthetic_member() -> None:
    async with AsyncSHAClient.from_env() as sha:
        e = await sha.eligibility.check("00000000", IdentificationType.NATIONAL_ID)
    assert e.member_found
    assert e.is_covered_on(date.today())


async def test_server_validation_error_is_typed() -> None:
    """Bypass local validation on purpose: we want the *server's* 400 envelope translated."""
    from sha_claim.adapters.wire.error_translator import raise_for_status
    from sha_claim.adapters.wire.transport import WireRequest

    async with AsyncSHAClient.from_env() as sha:
        response = await sha._transport.send(
            WireRequest(
                "GET",
                "/patients/eligibility",
                params={"identification_number": "1", "identification_type": "garbage"},
            )
        )
        with pytest.raises(BadRequestError) as exc:
            raise_for_status(response)
    assert exc.value.trace_id
    assert "identification type" in str(exc.value)


SYNTHETIC_PATIENT = "CR7678914660684-5"  # UAT member behind identification_number 00000000


async def test_benefit_hierarchy_reads() -> None:
    async with AsyncSHAClient.from_env() as sha:
        packages = await sha.eligibility.benefits(SYNTHETIC_PATIENT)
        subs = await sha.eligibility.sub_benefits(SYNTHETIC_PATIENT)
        outpatient = next(s for s in subs if s.code == "SHA-12-SC-01")
        coverage = await sha.eligibility.interventions(SYNTHETIC_PATIENT, outpatient.code)
    assert {p.code for p in packages} >= {"SHA-12"}
    assert any(c.name == "Consultation" for c in coverage)


async def test_authorize_then_reject_round_trip() -> None:
    """Creates a PENDING authorization on UAT (this is what sends the beneficiary an OTP) and closes it."""
    from sha_claim import ServiceType

    async with AsyncSHAClient.from_env() as sha:
        auth = await sha.consent.authorize(SYNTHETIC_PATIENT, ServiceType.CAPITATION, ["SHA-12-001"])
        try:
            assert auth.is_pending
            assert auth.is_open
            again = await sha.consent.get(auth.token, auth.guid, SYNTHETIC_PATIENT)
            assert again is not None
            assert again.guid == auth.guid
        finally:
            await sha.consent.reject(auth.token)


async def test_capitation_intervention_under_outpatient_is_a_typed_business_error() -> None:
    from sha_claim import ServiceType

    async with AsyncSHAClient.from_env() as sha:
        with pytest.raises(BadRequestError) as exc:
            await sha.consent.authorize(SYNTHETIC_PATIENT, ServiceType.OUTPATIENT, ["SHA-12-001"])
    assert "not supported for service type OUTPATIENT" in str(exc.value)
    assert exc.value.trace_id
