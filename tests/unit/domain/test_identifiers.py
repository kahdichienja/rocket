import pytest

from sha_claim.domain.identifiers import ClaimGuid, ConsentToken, PatientId


def test_identifier_strips_whitespace() -> None:
    assert ConsentToken("  abc ").value == "abc"


@pytest.mark.parametrize("raw", ["", "   "])
def test_identifier_rejects_empty(raw: str) -> None:
    with pytest.raises(ValueError, match="ConsentToken"):
        ConsentToken(raw)


@pytest.mark.parametrize("raw", ["CR7678914660684-5", " cr5274957287918-1 "])
def test_patient_id_accepts_client_registry_numbers(raw: str) -> None:
    assert PatientId(raw).value == raw.strip().upper()


@pytest.mark.parametrize(
    "raw", ["12345678", "CR123", "CR7678914660684", "PAT-TEST/00021/26", "SHIF-EJKZZ4R5"]
)
def test_patient_id_rejects_non_cr_numbers(raw: str) -> None:
    with pytest.raises(ValueError, match="Client Registry"):
        PatientId(raw)


def test_of_accepts_str_or_instance() -> None:
    a = PatientId.of("CR7678914660684-5")
    assert PatientId.of(a) is a
    assert a == PatientId("CR7678914660684-5")


def test_distinct_identifier_types_are_not_equal() -> None:
    assert ClaimGuid("X") != ConsentToken("X")  # type: ignore[comparison-overlap]


def test_consent_token_is_redacted_in_repr_and_str() -> None:
    token = ConsentToken("abcdefghijklmnop")
    assert token.value == "abcdefghijklmnop"
    assert "abcdefghijklmnop" not in repr(token)
    assert "abcdefghijklmnop" not in str(token)
    assert str(ConsentToken("short")) == "•••••"


def test_patient_id_accepts_both_live_cr_formats() -> None:
    """UAT 2026-09-23: `CR-2026-000256` alongside `CR7678914660684-5` — the strict form silently dropped members."""
    assert PatientId("CR7678914660684-5").value == "CR7678914660684-5"
    assert PatientId("CR-2026-000256").value == "CR-2026-000256"
    for wrong in ("SHIF-EJKZZ4R5", "1000000256", "CR1", "CRABCDEFGHIJKLM-1", ""):
        with pytest.raises(ValueError):
            PatientId(wrong)
