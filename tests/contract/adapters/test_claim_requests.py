import json
from datetime import date

from sha_claim.adapters.wire import requests
from sha_claim.adapters.wire.transport import TimeoutKind
from sha_claim.domain.attachments import Attachment
from sha_claim.domain.claim import Discharge, LineEdit, NewClaimLine, NextOfKin
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
    s = requests.submit(TOKEN, InvoiceNumber("INV-1"), None)
    assert not s.idempotent and s.json == {"consent_token": "CR1-ABCDEFGHIJ", "invoice_number": "INV-1"}
    assert requests.submit(TOKEN, None, "unconscious").json == {
        "consent_token": "CR1-ABCDEFGHIJ",
        "reason_for_unknown_patient": "unconscious",
    }
    c = requests.close(TOKEN, CancelReason.WRONG_PATIENT, "typo")
    assert not c.idempotent and c.json["cancel_reason_type"] == "WRONG_PATIENT"


def test_payer_status_query() -> None:
    r = requests.payer_status(ClaimGuid("G"), "INV-1")
    assert r.idempotent and r.params == {"guid": "G", "provider_claim_no": "INV-1"}


def test_discharge_and_next_of_kin_requests() -> None:
    assert requests.send_discharge_otp(TOKEN, PatientId("CR1")).json == {
        "consent_token": "CR1-ABCDEFGHIJ",
        "patient_id": "CR1",
    }
    d = requests.discharge(
        TOKEN, Discharge(date(2026, 9, 21), DischargeReason.REFERRED, InvoiceNumber("INV-1"), Otp("123456"))
    )
    assert d.json == {
        "consent_token": "CR1-ABCDEFGHIJ",
        "discharge_date": "2026-09-21",
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
