"""Discharging a member SHA will not send an OTP to.

SHA restricts some beneficiaries to biometric discharge at a given facility and refuses their discharge
OTP outright — *"This beneficiary (…) is restricted to biometric discharge at (…). If you need to use OTP
for discharge submit a whitelist request for this beneficiary."* (production, 2026-10-28). DHA's
biometrics flow answers it in one line: authorize with eKYC exactly as a visit does, then call discharge
"removing the `otp` field and replacing it with `auth_guid`".

The replacement is the contract, so these pin it from both sides: the guid goes out alone, and the OTP
goes out alone. A body carrying both would be a request that contradicts itself about who consented.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from sha_claim import ConsentToken, Discharge, DischargeReason, InvoiceNumber, Otp, Submission
from sha_claim.adapters.wire import requests

TOKEN = ConsentToken("CR1-ABCDEFGHIJ")
WHEN = datetime(2026, 10, 28, 10, 30, tzinfo=UTC)


def _discharge(**kwargs: object) -> Discharge:
    return Discharge(WHEN, DischargeReason.RECOVERED, InvoiceNumber("INV-1"), **kwargs)  # type: ignore[arg-type]


def test_a_biometric_discharge_sends_the_guid_and_no_otp() -> None:
    body = requests.discharge(TOKEN, _discharge(auth_guid="auth-guid-123")).json
    assert body == {
        "consent_token": "CR1-ABCDEFGHIJ",
        "discharge_date": "2026-10-28T10:30:00+00:00",
        "discharge_reason": "RECOVERED",
        "invoice_number": "INV-1",
        "auth_guid": "auth-guid-123",
    }
    assert "otp" not in body


def test_an_otp_discharge_is_unchanged() -> None:
    """The existing path must not acquire a stray field — every inpatient claim goes through here."""
    body = requests.discharge(TOKEN, _discharge(otp=Otp("123456"))).json
    assert body["otp"] == "123456"
    assert "auth_guid" not in body


def test_submit_swaps_the_same_way() -> None:
    """`submit` carries the discharge OTP too (undocumented, required on UAT), so it swaps identically."""
    body = requests.submit(
        TOKEN, Submission(InvoiceNumber("INV-1"), DischargeReason.RECOVERED, auth_guid="auth-guid-123")
    ).json
    assert body["auth_guid"] == "auth-guid-123"
    assert "otp" not in body


def test_the_guid_is_trimmed_so_whitespace_is_not_consent() -> None:
    assert (
        requests.discharge(TOKEN, _discharge(auth_guid="  auth-guid-123  ")).json["auth_guid"]
        == "auth-guid-123"
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {},  # neither
        {"auth_guid": "   "},  # blank is not a guid
        {"otp": Otp("123456"), "auth_guid": "auth-guid-123"},  # both
    ],
)
def test_a_discharge_must_carry_exactly_one_proof(kwargs: dict[str, object]) -> None:
    """Refused where it is built, not silently resolved by field order at the wire.

    Letting one win would decide a consent question — *who proved this discharge* — by the order the
    body happens to be assembled in, and that answer ends up in SHA's record of the claim.
    """
    with pytest.raises(ValueError, match="either otp or auth_guid"):
        _discharge(**kwargs)


def test_submit_refuses_both_proofs_too() -> None:
    with pytest.raises(ValueError, match="either otp or auth_guid"):
        Submission(InvoiceNumber("INV-1"), DischargeReason.RECOVERED, Otp("123456"), "auth-guid-123")
