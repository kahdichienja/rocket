import httpx
import pytest
import respx

from sha_claim import AsyncSHAClient, IdentificationType
from sha_claim.settings import SHASettings
from tests.conftest import load_fixture


@respx.mock
async def test_end_to_end_eligibility_through_facade(settings: SHASettings) -> None:
    respx.post(f"{settings.api_root}/tenants/token").mock(
        return_value=httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
    )
    respx.get(f"{settings.api_root}/patients/eligibility").mock(
        return_value=httpx.Response(200, json=load_fixture("eligibility_member_found.json"))
    )

    async with AsyncSHAClient(settings) as sha:
        e = await sha.eligibility.check("00000000", IdentificationType.NATIONAL_ID)
    assert e.member_found and e.schemes[0].name == "UHC"


@respx.mock
async def test_consent_and_visit_through_facade(settings: SHASettings) -> None:
    from sha_claim import Otp, ServiceType

    respx.post(f"{settings.api_root}/tenants/token").mock(
        return_value=httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
    )
    respx.get(f"{settings.api_root}/patients/benefits/interventions").mock(
        return_value=httpx.Response(200, json=load_fixture("interventions.json"))
    )
    respx.post(f"{settings.api_root}/claims/authorize").mock(
        return_value=httpx.Response(200, json=load_fixture("authorization_pending.json"))
    )
    visit = respx.post(f"{settings.api_root}/claims/visit").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "g",
                "claim_id": 1,
                "authorization_code": "CR0-TOKEN12345",
                "workflow_state": "OPEN",
                "service_type": "CAPITATION",
            },
        )
    )

    async with AsyncSHAClient(settings) as sha:
        coverage = await sha.eligibility.interventions("CR0000000000000-0", "SHA-12-SC-01")
        consultation = next(c for c in coverage if c.name == "Consultation")
        auth = await sha.consent.authorize(
            "CR0000000000000-0", consultation.service_type_for_authorization, [consultation.code]
        )
        assert auth.is_pending
        claim = await sha.claims.open_visit(
            "CR0000000000000-0", ServiceType.CAPITATION, [consultation.code], Otp("123456")
        )

    assert claim.consent_token.value == "CR0-TOKEN12345"
    assert "CR0-TOKEN12345" not in repr(claim)  # ConsentToken is redacted
    assert (
        visit.calls[0].request.content
        == b'{"patient_id":"CR0000000000000-0","service_type":"CAPITATION","intervention_codes":["SHA-12-001"],"otp":"123456"}'
    )


@respx.mock
async def test_claim_session_end_to_end_over_http(settings: SHASettings) -> None:
    from sha_claim import DocumentType, Money, Otp, ServiceType
    from sha_claim.domain.attachments import Attachment

    root = settings.api_root
    respx.post(f"{root}/tenants/token").mock(
        return_value=httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
    )
    respx.post(f"{root}/claims/visit").mock(
        return_value=httpx.Response(
            200,
            json={"id": "G", "claim_id": 1, "authorization_code": "CR0-TOKEN12345", "workflow_state": "OPEN"},
        )
    )
    respx.post(f"{root}/claims/diagnoses").mock(
        return_value=httpx.Response(
            200, json={"claim_diagnosis_id": 1, "diagnosis_code": "1A00", "intervention_code": "SHA-12-001"}
        )
    )
    lines = respx.post(f"{root}/claims/lines").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "L1",
                "intervention_code": "SHA-12-001",
                "quantity": 1,
                "unit_price": 1500,
                "line_total_amount": 1500,
            },
        )
    )
    attach = respx.post(f"{root}/claims/attachments").mock(
        return_value=httpx.Response(200, json={"id": "A1", "title": "inv.pdf", "attachment_type": "INVOICE"})
    )
    respx.post(f"{root}/claims/preview").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "G",
                "authorization_code": "CR0-TOKEN12345",
                "workflow_state": "OPEN",
                "total_claim_amount": 1500,
            },
        )
    )
    submit = respx.post(f"{root}/claims/submit").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "G",
                "authorization_code": "CR0-TOKEN12345",
                "workflow_state": "SUBMITTED",
                "invoice_number": "INV-1",
            },
        )
    )
    respx.get(f"{root}/claims/preview/payer").mock(
        return_value=httpx.Response(
            200,
            json={
                "pageSize": 25,
                "results": [{"guid": "G", "providerClaimNo": "INV-1", "workflowState": "RECEIVED"}],
            },
        )
    )

    async with AsyncSHAClient(settings) as sha:
        session = await sha.claims.open_visit("CR0", ServiceType.CAPITATION, ["SHA-12-001"], Otp("123456"))
        await session.add_diagnosis("1A00", "SHA-12-001")
        await session.add_line("SHA-12-001", Money.kes(1500), diagnoses=["1A00"])
        await session.attach(
            Attachment("inv.pdf", b"%PDF", DocumentType.INVOICE, "application/pdf"), "SHA-12-001"
        )
        preview = await session.preview()
        submitted = await session.submit("INV-1")
        status = await session.payer_status("INV-1")

        resumed = sha.claims.resume("CR0-TOKEN12345")
        assert resumed.claim is None and resumed.consent_token == session.consent_token

    assert preview.total_amount == Money.kes(1500)
    assert submitted.workflow_state == "SUBMITTED" and submitted.invoice_number is not None
    assert status[0].status == "RECEIVED"
    # multipart without a file still goes out as multipart/form-data, with the token as a plain part
    line_req = lines.calls[0].request
    assert line_req.headers["content-type"].startswith("multipart/form-data")
    assert b'name="consent_token"\r\n\r\nCR0-TOKEN12345' in line_req.content
    assert b'name="diagnoses"\r\n\r\n["1A00"]' in line_req.content
    assert b'filename="inv.pdf"' in attach.calls[0].request.content
    assert submit.calls[0].request.content == b'{"consent_token":"CR0-TOKEN12345","invoice_number":"INV-1"}'


@respx.mock
async def test_submit_timeout_surfaces_as_outcome_unknown_and_is_not_retried(settings: SHASettings) -> None:
    from sha_claim import SubmissionOutcomeUnknownError

    root = settings.api_root
    respx.post(f"{root}/tenants/token").mock(
        return_value=httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
    )
    submit = respx.post(f"{root}/claims/submit").mock(side_effect=httpx.ReadTimeout("slow"))
    async with AsyncSHAClient(settings) as sha:
        session = sha.claims.resume("CR0-TOKEN12345")
        with pytest.raises(SubmissionOutcomeUnknownError):
            await session.submit("INV-1")
    assert submit.call_count == 1


@respx.mock
async def test_preauth_over_http_is_multipart_with_attachment_parts(settings: SHASettings) -> None:
    from datetime import UTC, datetime

    from sha_claim import Attachment, DocumentType, Money, PractitionerRef, PreauthItem, RegulationBody

    root = settings.api_root
    respx.post(f"{root}/tenants/token").mock(
        return_value=httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
    )
    create = respx.post(f"{root}/preauths").mock(
        return_value=httpx.Response(
            200, json={"guid": "pg", "token": "pt", "status": "PENDING", "needsDoctorApproval": True}
        )
    )
    respx.get(f"{root}/preauths").mock(
        return_value=httpx.Response(
            200, json={"pageSize": 25, "results": [{"guid": "pg", "status": "PENDING"}]}
        )
    )

    start = datetime(2026, 9, 20, 8, tzinfo=UTC)
    async with AsyncSHAClient(settings) as sha:
        session = sha.claims.resume("CR0-TOKEN12345")
        created = await session.request_preauth(
            "SHA-08-006",
            service_start=start,
            service_end=start.replace(hour=12),
            items=[PreauthItem("CS", "Cesarean", 1, Money.kes(30000))],
            diagnoses=["JB0Z"],
            doctors=[PractitionerRef.registered("A1", RegulationBody.KMPDC)],
            notification_email="claims@facility.example",
            attachments=[Attachment("form.pdf", b"%PDF", DocumentType.PREAUTH_FORM, "application/pdf")],
        )
        listed = await session.preauths()

    assert created.guid == "pg" and created.awaiting_doctor
    assert listed[0].guid == "pg"
    body = create.calls[0].request.content
    assert create.calls[0].request.headers["content-type"].startswith("multipart/form-data")
    assert b'name="attachment_0"; filename="form.pdf"' in body
    assert b'name="items"\r\n\r\n[{"item_code": "CS"' in body
