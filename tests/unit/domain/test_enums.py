from sha_claim.domain.enums import EligibilityStatus, ServiceType


def test_lenient_enum_known_value() -> None:
    assert EligibilityStatus("10") is EligibilityStatus.MEMBER_FOUND
    assert EligibilityStatus.MEMBER_FOUND.is_known


def test_lenient_enum_unknown_value_degrades_instead_of_raising() -> None:
    s = EligibilityStatus("99")
    assert s == "99"
    assert not s.is_known
    assert s != EligibilityStatus.MEMBER_FOUND


def test_lenient_enum_parse_empty_is_none() -> None:
    assert EligibilityStatus.parse(None) is None
    assert EligibilityStatus.parse("") is None


def test_documented_enums_are_strict() -> None:
    import pytest

    with pytest.raises(ValueError):
        ServiceType("DAYCARE")
