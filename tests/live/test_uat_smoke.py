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


async def test_full_outpatient_claim_lifecycle_on_uat() -> None:
    """send OTP (UAT returns it) → open visit → diagnosis → line → preview → blockers → submit → payer status.

    Creates and submits a real sandbox claim for the synthetic member. This is the certification path.
    The OTP path must NOT be preceded by `authorize` — a pending authorization blocks it.
    """
    import re

    from sha_claim import Money, Otp

    async with AsyncSHAClient.from_env() as sha:
        coverage = await sha.eligibility.interventions(SYNTHETIC_PATIENT, "SHA-12-SC-01")
        consultation = next(c for c in coverage if c.name == "Consultation")
        service_type = consultation.service_type_for_authorization

        message = await sha.consent.send_otp(SYNTHETIC_PATIENT, [consultation.code])
        match = re.search(r"\b(\d{4,8})\b", message)
        assert match, f"UAT did not return an OTP in the message: {message!r}"

        session = await sha.claims.open_visit(
            SYNTHETIC_PATIENT, service_type, [consultation.code], Otp(match.group(1))
        )
        claim = session.claim
        assert claim is not None and claim.consent_token.value
        assert claim.workflow_state == "DRAFT" and claim.claim_auth_status == "AUTHORIZED"
        assert claim.interventions[0].code == consultation.code
        print("\nvisit opened:", claim.guid, claim.invoice_number)

        diagnosis = await session.add_diagnosis("1A00", consultation.code)
        assert diagnosis.intervention_code == consultation.code
        line = await session.add_line(consultation.code, Money.kes("500"), quantity=1, diagnoses=["1A00"])
        print("line:", line.guid, line.total_amount)

        preview = await session.preview()
        print(
            "preview:",
            preview.workflow_state,
            preview.total_amount,
            [str(b) for b in preview.submission_blockers()],
        )
        assert preview.diagnoses_for(consultation.code)
        assert preview.submission_blockers() == ()

        invoice = preview.invoice_number.value if preview.invoice_number else f"INV-UAT-{preview.guid}"

        # Observed on UAT: submit is refused until the visit is discharged — even for CAPITATION/outpatient.
        from sha_claim import DischargeReason

        otp_message = await session.send_discharge_otp(SYNTHETIC_PATIENT)
        discharge_match = re.search(r"\b(\d{4,8})\b", otp_message)
        assert discharge_match, f"no discharge OTP in message: {otp_message!r}"
        discharged = await session.discharge(
            reason=DischargeReason.RECOVERED,
            invoice_number=invoice,
            otp=discharge_match.group(1),
        )
        print("discharged:", discharged.workflow_state, discharged.visit_end)

        submitted = await session.submit(invoice)
        print("submitted:", submitted.workflow_state, submitted.invoice_number, submitted.guid)
        assert submitted.workflow_state and submitted.workflow_state != "DRAFT"

        if submitted.guid:
            payer = await session.payer_status(invoice)
            print("payer:", [(p.status, p.workflow_state, p.tracking_number) for p in payer])
