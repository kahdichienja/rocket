import pytest

from sha_claim.domain.identifiers import ConsentToken, PatientId


def test_identifier_strips_whitespace() -> None:
    assert PatientId("  CR123 ").value == "CR123"


@pytest.mark.parametrize("raw", ["", "   "])
def test_identifier_rejects_empty(raw: str) -> None:
    with pytest.raises(ValueError, match="PatientId"):
        PatientId(raw)


def test_of_accepts_str_or_instance() -> None:
    a = PatientId.of("CR1")
    assert PatientId.of(a) is a
    assert a == PatientId("CR1")


def test_distinct_identifier_types_are_not_equal() -> None:
    assert PatientId("X") != ConsentToken("X")  # type: ignore[comparison-overlap]


def test_consent_token_is_redacted_in_repr_and_str() -> None:
    token = ConsentToken("abcdefghijklmnop")
    assert token.value == "abcdefghijklmnop"
    assert "abcdefghijklmnop" not in repr(token)
    assert "abcdefghijklmnop" not in str(token)
    assert str(ConsentToken("short")) == "•••••"
