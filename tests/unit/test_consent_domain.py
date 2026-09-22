import pytest


def test_authorization_acts_as_consent_proof() -> None:
    """No phone on record → authorize() still yields a guid, and that guid opens the visit (UAT 2026-09-22)."""
    from sha_claim.domain.consent import Authorization, BiometricGuid

    def auth(guid: str) -> Authorization:
        return Authorization(guid, "tok", "code", None, "", True, "OUTPATIENT", None, "", "", ())

    assert auth("G-9").proof == BiometricGuid("G-9")
    with pytest.raises(ValueError, match="guid"):
        _ = auth("").proof
