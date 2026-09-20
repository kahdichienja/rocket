from datetime import date

from sha_claim.domain.eligibility import Coverage, DateRange, Eligibility, Scheme
from sha_claim.domain.enums import CoverageStatus, EligibilityStatus
from sha_claim.domain.identifiers import PatientId


def scheme(status: CoverageStatus | None, start: date, end: date) -> Scheme:
    period = DateRange(start, end)
    return Scheme("UHC", 1, "PRIMARY", "UHC-1", period, Coverage(status, "", "", period))


def test_covered_when_member_found_and_scheme_active() -> None:
    e = Eligibility(
        PatientId("CR1"),
        "X",
        EligibilityStatus.MEMBER_FOUND,
        "",
        (scheme(CoverageStatus.COVERED, date(2024, 1, 1), date(2030, 1, 1)),),
    )
    assert e.member_found
    assert e.is_covered_on(date(2026, 9, 20))
    assert not e.is_covered_on(date(2031, 1, 1))


def test_not_covered_when_status_not_covered_or_member_missing() -> None:
    inactive = Eligibility(
        PatientId("CR1"),
        "X",
        EligibilityStatus.MEMBER_FOUND,
        "",
        (scheme(CoverageStatus("0"), date(2024, 1, 1), date(2030, 1, 1)),),
    )
    assert not inactive.is_covered_on(date(2026, 9, 20))
    no_member = Eligibility(None, "", EligibilityStatus("20"), "not found", ())
    assert not no_member.member_found and not no_member.is_covered_on(date(2026, 9, 20))


def test_open_ended_range() -> None:
    assert DateRange(None, None).contains(date(2000, 1, 1))
    assert not DateRange(date(2025, 1, 1), None).contains(date(2024, 12, 31))
