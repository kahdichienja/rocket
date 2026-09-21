import json
from datetime import UTC, date, datetime

from sha_claim.adapters.wire import requests
from sha_claim.adapters.wire.transport import TimeoutKind
from sha_claim.domain.attachments import Attachment
from sha_claim.domain.claim import Discharge, LineEdit, NewClaimLine, NextOfKin, Submission
from sha_claim.domain.codes import DocumentType, Icd11Code, InterventionCode, SchemeCode
from sha_claim.domain.consent import Otp
from sha_claim.domain.enums import CancelReason, DischargeReason, NextOfKinIdType
from sha_claim.domain.identifiers import (
    AttachmentId,
    ClaimGuid,
    ConsentToken,
    InvoiceNumber,
    LineGuid,
    PatientId,
)
from sha_claim.domain.money import Money

TOKEN = ConsentToken("CR1-ABCDEFGHIJ")
CODE = InterventionCode("SHA-12-001")


def test_add_line_is_multipart_with_json_encoded_diagnoses() -> None:
    line = NewClaimLine(
        CODE,
        Money.kes("1500"),
        2,
        scheme_code=SchemeCode("UHC"),
        charge_date=date(2026, 9, 20),
        diagnoses=(Icd11Code("1a00"), Icd11Code("BA00")),
    )
    r = requests.add_line(TOKEN, line)
    assert r.method == "POST" and r.path == "/claims/lines"
    assert r.multipart is True and r.files is None and r.json is None
    assert r.form == {
        "consent_token": "CR1-ABCDEFGHIJ",
        "intervention_code": "SHA-12-001",
        "unit_price": "1500.00",
        "quantity": "2",
        "scheme_code": "UHC",
        "charge_date": "2026-09-20",
        "diagnoses": json.dumps(["1A00", "BA00"]),
    }
    minimal = requests.add_line(TOKEN, NewClaimLine(CODE, Money.kes(1), 1))
    assert minimal.form is not None
    assert set(minimal.form) == {"consent_token", "intervention_code", "unit_price", "quantity"}


def test_attachment_is_multipart_with_file_and_upload_timeout() -> None:
    r = requests.add_attachment(
        TOKEN, Attachment("dis.pdf", b"%PDF", DocumentType.DISCHARGE_SUMMARY, "application/pdf"), CODE
    )
    assert r.files == {"file_blob": ("dis.pdf", b"%PDF", "application/pdf")}
    assert r.form is not None and r.form["document_type"] == "DISCHARGE_SUMMARY"
    assert r.timeout is TimeoutKind.UPLOAD
    assert not r.idempotent


def test_json_mutations_carry_token_and_codes() -> None:
    assert requests.add_diagnosis(TOKEN, Icd11Code("1A00"), CODE).json == {
        "consent_token": "CR1-ABCDEFGHIJ",
        "icd_code": "1A00",
        "intervention_code": "SHA-12-001",
    }
    assert requests.remove_diagnosis(TOKEN, Icd11Code("1A00"), CODE).method == "PATCH"
    assert requests.remove_line(TOKEN, LineGuid("L")).json == {
        "consent_token": "CR1-ABCDEFGHIJ",
        "line_guid": "L",
    }
    assert requests.remove_attachment(TOKEN, AttachmentId("A"), CODE).json["attachment_id"] == "A"
    assert requests.retire_intervention(TOKEN, CODE).path == "/claims/interventions/retire"
    assert requests.restore_intervention(TOKEN, CODE).path == "/claims/interventions/restore"


def test_edit_line_sends_only_changed_fields() -> None:
    assert requests.edit_line(LineEdit(LineGuid("L"), quantity=2)).json == {"line_id": "L", "quantity": 2}
    assert requests.edit_line(LineEdit(LineGuid("L"), unit_price=Money.kes("9.5"))).json == {
        "line_id": "L",
        "unit_price": "9.50",
    }


def test_preview_is_retry_safe_but_submit_and_close_are_not() -> None:
    assert requests.preview(TOKEN).idempotent
    assert requests.preview(TOKEN).method == "POST"
    s = requests.submit(TOKEN, Submission(InvoiceNumber("INV-1")))
    assert not s.idempotent and s.json == {"consent_token": "CR1-ABCDEFGHIJ", "invoice_number": "INV-1"}
    assert requests.submit(TOKEN, Submission(reason_for_unknown_patient="unconscious")).json == {
        "consent_token": "CR1-ABCDEFGHIJ",
        "reason_for_unknown_patient": "unconscious",
    }
    full = requests.submit(
        TOKEN, Submission(InvoiceNumber("INV-1"), DischargeReason.RECOVERED, Otp("123456"))
    ).json
    assert full == {
        "consent_token": "CR1-ABCDEFGHIJ",
        "invoice_number": "INV-1",
        "discharge_reason": "RECOVERED",
        "otp": "123456",
    }
    c = requests.close(TOKEN, CancelReason.WRONG_PATIENT, "typo")
    assert not c.idempotent and c.json["cancel_reason_type"] == "WRONG_PATIENT"


def test_payer_status_query() -> None:
    r = requests.payer_status(ClaimGuid("G"), "INV-1")
    assert r.idempotent and r.params == {"guid": "G", "provider_claim_no": "INV-1"}


def test_discharge_and_next_of_kin_requests() -> None:
    assert requests.send_discharge_otp(TOKEN, PatientId("CR1111111111111-1")).json == {
        "consent_token": "CR1-ABCDEFGHIJ",
        "patient_id": "CR1111111111111-1",
    }
    d = requests.discharge(
        TOKEN,
        Discharge(
            datetime(2026, 9, 21, 10, 30, tzinfo=UTC),
            DischargeReason.REFERRED,
            InvoiceNumber("INV-1"),
            Otp("123456"),
        ),
    )
    assert d.json == {
        "consent_token": "CR1-ABCDEFGHIJ",
        "discharge_date": "2026-09-21T10:30:00+00:00",
        "discharge_reason": "REFERRED",
        "invoice_number": "INV-1",
        "otp": "123456",
    }
    assert not d.idempotent
    n = requests.add_next_of_kin(
        TOKEN, NextOfKin(" Jane Doe ", "1", NextOfKinIdType.BIRTH_CERTIFICATE, "+254700000000")
    )
    assert n.json == {
        "consent_token": "CR1-ABCDEFGHIJ",
        "next_of_kin_full_name": "Jane Doe",
        "next_of_kin_id_number": "1",
        "next_of_kin_id_number_type": "Birth Certificate",
        "contact_value": "+254700000000",
    }
    assert requests.resubmit_lines(TOKEN).json == {"consent_token": "CR1-ABCDEFGHIJ"}


def test_switch_intervention_request() -> None:
    from datetime import UTC, datetime

    r = requests.switch_intervention(
        TOKEN, CODE, InterventionCode("SHA-12-002"), True, datetime(2026, 9, 20, tzinfo=UTC), None
    )
    assert r.json == {
        "consent_token": "CR1-ABCDEFGHIJ",
        "existing_intervention_code": "SHA-12-001",
        "new_intervention_code": "SHA-12-002",
        "retain_bill_items": True,
        "bill_from": "2026-09-20T00:00:00+00:00",
    }


def test_list_authorizations_request() -> None:
    r = requests.list_authorizations(PatientId("CR1111111111111-1"))
    assert r.idempotent and r.params == {"beneficiary_code": "CR1111111111111-1"}


def test_combined_billing_line_carries_label_practitioner_diagnoses_and_files() -> None:
    from sha_claim.domain.claim import LineAttachment
    from sha_claim.domain.codes import RegulationBody
    from sha_claim.domain.practitioner import PractitionerRef

    line = NewClaimLine(
        CODE,
        Money.kes("2600"),
        1,
        diagnoses=(Icd11Code("1A00"),),
        service_name=" Anti-rabies vaccine ",
        service_identifier="CHG-42",
        practitioner=PractitionerRef.registered("A1234", RegulationBody.KMPDC),
        attachments=(
            LineAttachment(
                "Lab report", Attachment("lab.pdf", b"%PDF", DocumentType.LAB_RESULTS, "application/pdf")
            ),
            LineAttachment("Photo", Attachment("w.jpg", b"\xff\xd8", DocumentType.OTHER, "image/jpeg")),
        ),
    )
    r = requests.add_line(TOKEN, line)
    assert r.form is not None and r.files is not None
    assert r.form["service_name"] == "Anti-rabies vaccine" and r.form["service_identifier"] == "CHG-42"
    assert r.form["practitioner_identification_type"] == "registration_number"
    assert r.form["practitioner_identification_number"] == "A1234"
    assert r.form["practitioner_regulation_body"] == "KMPDC"
    meta = json.loads(r.form["attachments"])
    assert [m["file_field_name"] for m in meta] == ["attachment_0", "attachment_1"]
    assert meta[0] == {
        "document_title": "Lab report",
        "document_type": "LAB_RESULTS",
        "file_field_name": "attachment_0",
    }
    assert r.files["attachment_0"] == ("lab.pdf", b"%PDF", "application/pdf")
    assert r.timeout is TimeoutKind.UPLOAD
    plain = requests.add_line(TOKEN, NewClaimLine(CODE, Money.kes(1), 1))
    assert (
        plain.files is None
        and plain.timeout is TimeoutKind.DEFAULT
        and "attachments" not in (plain.form or {})
    )


def test_set_coverage_request() -> None:
    from sha_claim.domain.claim import CoverageSelection

    r = requests.set_coverage(TOKEN, CoverageSelection(PatientId("CR1111111111111-1"), " POMSF-123 "))
    assert r.method == "POST" and r.path == "/authorizations/covers"
    assert r.json == {
        "principal_cr_id": "CR1111111111111-1",
        "consent_token": "CR1-ABCDEFGHIJ",
        "policy_number": "POMSF-123",
    }
