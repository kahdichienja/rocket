import httpx
import pytest
import respx

from sha_claim import AsyncSHAClient, IdentificationType
from sha_claim.domain.money import Money
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
        session = await sha.claims.open_visit(
            "CR0000000000000-0", ServiceType.CAPITATION, ["SHA-12-001"], Otp("123456")
        )
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


@respx.mock
async def test_prescription_get_tolerates_object_list_page_and_empty(settings: SHASettings) -> None:
    root = settings.api_root
    respx.post(f"{root}/tenants/token").mock(
        return_value=httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
    )
    route = respx.get(f"{root}/prescriptions").mock(
        side_effect=[
            httpx.Response(200, json={"guid": "a", "status": "ACTIVE"}),
            httpx.Response(200, json=[{"guid": "b"}]),
            httpx.Response(200, json={"pageSize": 25, "results": [{"guid": "c"}]}),
            httpx.Response(200, json={"pageSize": 25, "results": []}),
            httpx.Response(200, json=[]),
            httpx.Response(200, content=b""),
        ]
    )
    async with AsyncSHAClient(settings) as sha:
        session = sha.claims.resume("CR0-TOKEN12345")
        seen = [await session.prescription() for _ in range(6)]
    assert [p.guid if p else None for p in seen] == ["a", "b", "c", None, None, None]
    assert route.call_count == 6


@respx.mock
async def test_prescribe_and_dispense_over_http(settings: SHASettings) -> None:
    from datetime import date

    from sha_claim import DispensedProduct, MedicationOrder, Money, PractitionerRef, RegulationBody

    root = settings.api_root
    respx.post(f"{root}/tenants/token").mock(
        return_value=httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
    )
    create = respx.post(f"{root}/prescriptions").mock(
        return_value=httpx.Response(
            200,
            json={"guid": "rx", "code": "RX-1", "status": "ACTIVE", "intervention": {"code": "SHA-12-004"}},
        )
    )
    respx.post(f"{root}/prescriptions/dispenses").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 7,
                "status": "DISPENSED",
                "dispenseDosages": [
                    {"medication": "Amoxicillin", "doseQuantity": 1, "medicationPrice": "12.5"}
                ],
            },
        )
    )
    respx.delete(f"{root}/prescriptions/doctors").mock(return_value=httpx.Response(200, json={}))

    doctor = PractitionerRef.registered("A1", RegulationBody.KMPDC)
    async with AsyncSHAClient(settings) as sha:
        session = sha.claims.resume("CR0-TOKEN12345")
        rx = await session.prescribe(
            "SHA-12-004",
            [MedicationOrder("AMOX500", 1, "TABLET", 3, "DAY", 5, "DAY", date(2026, 9, 20))],
            prescriber=doctor,
        )
        dispensed = await session.dispense(
            "SHA-12-004", [DispensedProduct("AMOX500-GEN", 15, Money.kes("12.50"))], [doctor]
        )
        await session.remove_prescription_doctor("SHA-12-004", "A1")

    assert (
        rx.code == "RX-1" and rx.intervention_code is not None and rx.intervention_code.value == "SHA-12-004"
    )
    assert dispensed.dosages[0].price == Money.kes("12.50") and dispensed.dosages[0].dose_quantity == 1
    sent = create.calls[0].request.content
    assert b'"generic_concept_code":"AMOX500"' in sent and b'"regulation_body":"KMPDC"' in sent


@respx.mock
async def test_emergency_case_over_http(settings: SHASettings) -> None:
    from sha_claim import BroughtBy, ModeOfArrival, Money, PractitionerRef, RegulationBody

    root = settings.api_root
    respx.post(f"{root}/tenants/token").mock(
        return_value=httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
    )
    respx.post(f"{root}/claims/emergency").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "E",
                "authorization_code": "CR0-EMERG12345",
                "workflow_state": "OPEN",
                "service_type": "EMERGENCY",
            },
        )
    )
    respx.get(f"{root}/claims/emergency/protocols").mock(
        return_value=httpx.Response(
            200, json={"results": [{"protocolCode": "EP-1", "name": "Resus", "applicableTariff": "5000"}]}
        )
    )
    protocol = respx.post(f"{root}/claims/emergency/protocols").mock(
        return_value=httpx.Response(
            200, json={"id": "L1", "item_code": "EP-1", "quantity": 1, "unit_price": 5000}
        )
    )

    doctor = PractitionerRef.registered("A1", RegulationBody.KMPDC)
    async with AsyncSHAClient(settings) as sha:
        protocols = await sha.emergency.protocols("SHA-19-001")
        session = await sha.emergency.open_case(
            doctor, "REF-1", BroughtBy.PARAMEDICS, ModeOfArrival.AMBULANCE, ["SHA-19-001"], notes="RTA"
        )
        line = await session.add_protocol(
            protocols[0].code, "SHA-19-001", protocols[0].tariff or Money.kes(0)
        )

    assert session.consent_token.value == "CR0-EMERG12345" and session.claim is not None
    assert protocols[0].tariff == Money.kes(5000) and line.unit_price == Money.kes(5000)
    assert protocol.calls[0].request.headers["content-type"].startswith("multipart/form-data")


@respx.mock
async def test_files_and_occupancy_over_http(settings: SHASettings) -> None:
    root = settings.api_root
    respx.post(f"{root}/tenants/token").mock(
        return_value=httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
    )
    up = respx.post(f"{root}/uploads").mock(
        return_value=httpx.Response(200, json={"file_id": "f1", "path": "p"})
    )
    respx.get(f"{root}/uploads/f1").mock(
        return_value=httpx.Response(200, json={"message": "ok", "data": {"url": "https://signed"}})
    )
    respx.get(f"{root}/facilities/FID-1/beds/occupancy").mock(
        return_value=httpx.Response(
            200, json={"name": "H", "bed_occupancy_rate": {"total_number_of_bed": 10, "total_ip_visits": 5}}
        )
    )
    respx.get(f"{root}/patients/pomsf-balances").mock(
        return_value=httpx.Response(200, json={"memberNumber": "M1"})
    )

    async with AsyncSHAClient(settings) as sha:
        stored = await sha.files.upload("x.pdf", b"%PDF", "application/pdf")
        link = await sha.files.download_link(stored.file_id or "f1")
        beds = await sha.eligibility.bed_occupancy("FID-1")
        pomsf = await sha.eligibility.pomsf_balances("CR1111111111111-1", "2026")

    assert stored.file_id is not None and link.url == "https://signed"
    assert beds.occupancy_rate == 0.5 and pomsf["memberNumber"] == "M1"
    assert b'filename="x.pdf"' in up.calls[0].request.content


@respx.mock
async def test_consent_list_filters_out_other_beneficiaries(settings: SHASettings) -> None:
    """DHA returns the facility's authorizations regardless of beneficiary_code (observed on UAT)."""
    root = settings.api_root
    respx.post(f"{root}/tenants/token").mock(
        return_value=httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
    )
    mine = load_fixture("authorization_pending.json")
    other = {
        **mine,
        "id": 99,
        "guid": "other-guid",
        "token": "OTHERTOKEN",
        "beneficiaryCode": "CR-SOMEONE-ELSE",
    }
    respx.get(f"{root}/claims/authorizations").mock(return_value=httpx.Response(200, json=[other, mine]))
    async with AsyncSHAClient(settings) as sha:
        listed = await sha.consent.list("CR0000000000000-0")
    assert [a.guid for a in listed] == [mine["guid"]]


@respx.mock
async def test_utilization_accepts_list_page_and_bare_object(settings: SHASettings) -> None:
    """UAT (2026-09-22) answers with a bare list, one record per limit scope; the portal documents one object."""
    respx.post(f"{settings.api_root}/tenants/token").mock(
        return_value=httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
    )
    record = {
        "code": "SHA-18-003",
        "crId": "CR1111111111111-1",
        "limitScope": "INDIVIDUAL",
        "individualMaxLimit": 5000,
    }
    route = respx.get(f"{settings.api_root}/patients/benefits/utilization")
    for payload, expected in (
        ([record, {**record, "limitScope": "HOUSEHOLD"}], 2),
        ({"pageSize": 1, "results": [record]}, 1),
        (record, 1),
    ):
        route.mock(return_value=httpx.Response(200, json=payload))
        async with AsyncSHAClient(settings) as sha:
            balances = await sha.eligibility.utilization("CR1111111111111-1", "SHA-18-003")
        assert len(balances) == expected
        assert balances[0].individual_max == Money.kes(5000)
    assert [b.limit_scope for b in balances] == ["INDIVIDUAL"]


@respx.mock
async def test_registry_lookup_and_contactability(settings: SHASettings) -> None:
    """The cheapest pre-flight there is: no phone contact → `send_otp` cannot work, whatever cover says."""
    respx.post(f"{settings.api_root}/tenants/token").mock(
        return_value=httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
    )
    patient = respx.get(f"{settings.api_root}/patients").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "CR-2026-000256",
                "resourceType": "Patient",
                "first_name": "JANE",
                "middle_name": "G",
                "last_name": "CHEBET",
                "date_of_birth": "1945-08-16",
                "identification_type": "National ID",
                "identification_number": "1000000256",
                "other_identifications": [
                    {"identification_type": "SHA Number", "identification_number": "SHA-9"}
                ],
                "dependants": [{"relationship": "Child", "total": 1, "result": [{"id": "CR-2026-000258"}]}],
            },
        )
    )
    contacts = respx.get(f"{settings.api_root}/patients/contacts")

    async with AsyncSHAClient(settings) as sha:
        record = await sha.registries.find_patient("1000000256")
        assert record is not None
        assert record.patient_id is not None and record.patient_id.value == "CR-2026-000256"
        assert record.full_name == "JANE G CHEBET" and record.identification("SHA Number") == "SHA-9"
        assert [d.value for d in record.dependant_ids] == ["CR-2026-000258"]

        contacts.mock(
            return_value=httpx.Response(
                200,
                json={
                    "count": 1,
                    "results": [
                        {
                            "id": 982843,
                            "contactValue": "+254710***256",
                            "contactType": "PHO",
                            "isConfirmed": True,
                            "active": True,
                            "isMainContact": True,
                        }
                    ],
                },
            )
        )
        assert await sha.registries.can_consent_by_otp("CR-2026-000256") is True

        contacts.mock(return_value=httpx.Response(200, json={"count": 0, "results": []}))
        assert await sha.registries.can_consent_by_otp("CR5274957287918-1") is False

    assert patient.calls[0].request.url.params["identification_type"] == "National ID"
