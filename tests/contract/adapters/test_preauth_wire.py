import json
from datetime import UTC, datetime

from sha_claim.adapters.wire import mappers, requests
from sha_claim.adapters.wire.schemas.preauth import PreauthorizationWire
from sha_claim.adapters.wire.transport import TimeoutKind
from sha_claim.domain.attachments import Attachment
from sha_claim.domain.codes import DocumentType, Icd11Code, InterventionCode, RegulationBody
from sha_claim.domain.enums import DoctorConsentRequestType, IdentificationType, ServiceType
from sha_claim.domain.identifiers import ConsentToken
from sha_claim.domain.money import Money
from sha_claim.domain.practitioner import PractitionerRef
from sha_claim.domain.preauth import DoctorConsentRequest, PreauthItem, PreauthRequest

TOKEN = ConsentToken("CR1-ABCDEFGHIJ")
CODE = InterventionCode("SHA-08-006")
START = datetime(2026, 9, 20, 8, tzinfo=UTC)


def request(**overrides: object) -> PreauthRequest:
    base: dict[str, object] = dict(
        intervention_code=CODE,
        service_start=START,
        service_end=START.replace(hour=12),
        items=(PreauthItem("CS", "Cesarean section", 1, Money.kes("30000")),),
        diagnoses=(Icd11Code("JB0Z"),),
        doctors=(PractitionerRef.registered("A1234", RegulationBody.KMPDC),),
        provider_notification_email="claims@facility.example",
    )
    return PreauthRequest(**{**base, **overrides})  # type: ignore[arg-type]


def test_create_preauth_multipart_encoding() -> None:
    r = requests.create_preauth(TOKEN, request())
    assert r.method == "POST" and r.path == "/preauths" and r.multipart and r.timeout is TimeoutKind.UPLOAD
    assert r.form is not None
    assert r.form["consent_token"] == "CR1-ABCDEFGHIJ"
    assert r.form["service_start"] == "2026-09-20T08:00:00+00:00"
    # The shape Postman sends: an item is its price, a diagnosis repeats the token, a doctor names the
    # intervention. The previous expectations here were guesses against an unpublished schema.
    assert json.loads(r.form["items"]) == [{"unit_price": "30000.00"}]
    assert json.loads(r.form["diagnoses"]) == [{"consent_token": "CR1-ABCDEFGHIJ", "icd_code": "JB0Z"}]
    assert json.loads(r.form["doctors"]) == [
        {
            "identification_type": "registration_number",
            "identification_number": "A1234",
            "regulation_body": "KMPDC",
            "practitioner_registration_number": "A1234",
            "intervention_code": "SHA-08-006",
        }
    ]
    assert json.loads(r.form["attachments"]) == []
    assert r.files is None


def test_create_preauth_attachments_reference_file_parts() -> None:
    files = (
        Attachment("form.pdf", b"%PDF-1", DocumentType.PREAUTH_FORM, "application/pdf"),
        Attachment("scan.png", b"\x89PNG", DocumentType.CT_SCAN, "image/png"),
    )
    r = requests.create_preauth(TOKEN, request(attachments=files))
    # `file_field_name` must name a part that is actually on the form — it named `attachment_0`, which was
    # never sent, so SHA silently received a pre-auth with no supporting documents at all.
    assert r.files == {
        "attachments_0_file_blob": ("form.pdf", b"%PDF-1", "application/pdf"),
        "attachments_1_file_blob": ("scan.png", b"\x89PNG", "image/png"),
    }
    assert r.form is not None
    meta = json.loads(r.form["attachments"])
    assert meta == [
        {
            "document_title": "form.pdf",
            "document_type": "PREAUTH_FORM",
            "file_field_name": "attachments_0_file_blob",
        },
        {
            "document_title": "scan.png",
            "document_type": "CT_SCAN",
            "file_field_name": "attachments_1_file_blob",
        },
    ]
    for entry in meta:
        assert entry["file_field_name"] in r.files


def test_preauth_maintenance_requests() -> None:
    assert requests.list_preauths(TOKEN).params == {"consent_token": "CR1-ABCDEFGHIJ"}
    rd = requests.remove_preauth_diagnosis(TOKEN, Icd11Code("JB0Z"), CODE)
    assert rd.method == "DELETE" and rd.path == "/preauths/diagnoses/JB0Z"
    assert rd.json == {
        "consent_token": "CR1-ABCDEFGHIJ",
        "icd_code": "JB0Z",
        "intervention_code": "SHA-08-006",
    }
    rr = requests.remove_preauth_doctor(TOKEN, CODE, "A1234")
    assert rr.method == "DELETE" and rr.json["practitioner_registration_number"] == "A1234"
    assert requests.cancel_preauth(TOKEN, CODE).json == {
        "consent_token": "CR1-ABCDEFGHIJ",
        "intervention_code": "SHA-08-006",
    }


def test_doctor_consent_request_body() -> None:
    by_national_id = PractitionerRef("12345678", IdentificationType.NATIONAL_ID, RegulationBody.NCK)
    r = requests.doctor_consent(
        TOKEN,
        DoctorConsentRequest(
            CODE,
            DoctorConsentRequestType.EMERGENCY_CLAIM_DOCTOR_APPROVAL,
            by_national_id,
            ServiceType.INPATIENT,
            "E-9",
        ),
    )
    assert r.json == {
        "consent_token": "CR1-ABCDEFGHIJ",
        "intervention_code": "SHA-08-006",
        "request_type": "EMERGENCY_CLAIM_DOCTOR_APPROVAL_REQUEST",
        "identification_type": "National ID",
        "identification_number": "12345678",
        "regulation_body": "NCK",
        "service_type": "INPATIENT",
        "emergency_claim_id": "E-9",
    }
    assert "practitioner_registration_number" not in r.json


def test_preauthorization_maps_from_documented_camel_case() -> None:
    w = PreauthorizationWire.model_validate(
        {
            "id": 9,
            "guid": "g",
            "token": "t",
            "interventionCode": "SHA-08-006",
            "status": "PENDING_DOCTOR",
            "doctorReviewStatus": "AWAITING",
            "needsDoctorApproval": True,
            "doctorApproved": False,
            "numberOfPreauthDoctorsRequired": 2,
            "isRequestPhase": True,
            "isResponsePhase": False,
            "totalEstimatedAmountForPreauth": 30000,
            "finalApprovedAmount": None,
            "serviceStart": "2026-09-20T08:00:00+03:00",
            "providerCurrency": "KES",
            "preauthItems": [{"x": 1}],
            "memberIsVip": False,
        }
    )
    p = mappers.to_preauthorization(w)
    assert p.intervention_code == CODE and p.status == "PENDING_DOCTOR"
    assert p.awaiting_doctor and not p.decided and p.doctors_required == 2
    assert p.total_estimated == Money.kes(30000) and p.final_approved is None
    assert p.service_start is not None and p.service_start.utcoffset() is not None
    assert p.extra["preauthItems"] == [{"x": 1}]
