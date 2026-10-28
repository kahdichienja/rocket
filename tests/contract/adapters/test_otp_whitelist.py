"""Asking SHA to accept an OTP for a member biometrics will not match.

SHA's published remedy when the reader fails, and the only route left for a beneficiary it restricts
to biometric discharge whose finger will not match.

NaCare sent this through a legacy proxy aimed at `{DHA_BASE_URL}/patients/otp-whitelists`, where
`DHA_BASE_URL` carried no `/api/v1` — so DHA answered `404 page not found` and the desk saw "DHA Auth
API Error" with nothing to do about it (prod, 2026-10-28). Probed directly, the two paths answer:

    404  …/middleware/patients/otp-whitelists          page not found
    401  …/middleware/api/v1/patients/otp-whitelists   Unauthorized   ← exists; only the token was missing

The SDK prepends `/api/v1` itself, so the request below lands on the second. The body is pinned field
by field against DHA's published Postman collection, because `attachments` is a **JSON string inside a
form field** naming the form field each file arrives under — an indirection no one would guess.
"""

from __future__ import annotations

import json

import pytest

from sha_claim import Attachment, PatientId
from sha_claim.adapters.wire import requests
from sha_claim.domain.consent import OtpWhitelistRequest

CR = PatientId("CR9664407984618-9")
FACILITY = "FID-46-110269-6"


def _request(**kwargs: object) -> OtpWhitelistRequest:
    defaults: dict[str, object] = {
        "beneficiary": CR,
        "reason_type": "BIOMETRIC_FAILURE",
        "reason": "Reader would not match after ten attempts",
        "biometric_attempts": 10,
        "attachments": (Attachment("invoice.pdf", b"%PDF-1.4", "SUPPORT_DOCUMENT", "application/pdf"),),
        "facility_fr_code": FACILITY,
    }
    return OtpWhitelistRequest(**{**defaults, **kwargs})  # type: ignore[arg-type]


def test_the_request_matches_dhas_published_form() -> None:
    r = requests.create_otp_whitelist(_request())

    assert (r.method, r.path) == ("POST", "/patients/otp-whitelists")
    assert r.multipart
    assert r.form == {
        "reason_type": "BIOMETRIC_FAILURE",
        "reason": "Reader would not match after ten attempts",
        "beneficiary_cr_id": "CR9664407984618-9",
        "biometric_attempts": "10",
        "attachments": json.dumps(
            [
                {
                    "document_title": "invoice.pdf",
                    "document_type": "SUPPORT_DOCUMENT",
                    "file_field_name": "attachments_file_blob",
                }
            ]
        ),
        "facility_fr_code": FACILITY,
    }
    assert r.files is not None and list(r.files) == ["attachments_file_blob"]


def test_each_file_is_named_by_the_field_the_manifest_points_at() -> None:
    """The manifest and the parts must agree, or DHA receives a document it cannot place."""
    r = requests.create_otp_whitelist(
        _request(
            attachments=(
                Attachment("a.pdf", b"a", "SUPPORT_DOCUMENT", "application/pdf"),
                Attachment("b.pdf", b"b", "SUPPORT_DOCUMENT", "application/pdf"),
            )
        )
    )

    assert r.form is not None
    named = [a["file_field_name"] for a in json.loads(r.form["attachments"])]
    assert named == ["attachments_file_blob", "attachments_file_blob_1"]
    assert r.files is not None and list(r.files) == named


def test_a_request_with_no_evidence_still_goes_but_says_zero() -> None:
    """SHA may refuse it; that is SHA's call, and the count must not be quietly inflated to hide it."""
    r = requests.create_otp_whitelist(_request(biometric_attempts=0, attachments=()))

    assert r.form is not None
    assert r.form["biometric_attempts"] == "0"
    assert r.form["attachments"] == "[]"
    assert r.files is None


def test_reading_the_verdict_is_a_plain_idempotent_get() -> None:
    r = requests.get_otp_whitelist(CR, FACILITY)

    assert (r.method, r.path) == ("GET", "/patients/otp-whitelists/callback")
    assert dict(r.params) == {"beneficiary_cr_id": CR.value, "facility_fr_code": FACILITY}
    assert r.idempotent


@pytest.mark.parametrize(("field", "value"), [("reason_type", "  "), ("reason", "")])
def test_an_unexplained_request_is_refused_here(field: str, value: str) -> None:
    """An officer reads these. Sending a blank wastes a review and comes back refused."""
    with pytest.raises(ValueError):
        _request(**{field: value})
