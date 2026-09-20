from datetime import UTC, date, datetime

import pytest

from sha_claim.adapters.wire.parsing import parse_date, parse_datetime
from sha_claim.domain.codes import RegulationBody
from sha_claim.domain.enums import IdentificationType
from sha_claim.domain.practitioner import PractitionerRef
from sha_claim.infrastructure.logging import redact


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2024-10-01", date(2024, 10, 1)),
        ("2024-10-01T10:00:00Z", date(2024, 10, 1)),
        ("", None),
        (None, None),
        ("not-a-date", None),
    ],
)
def test_parse_date_is_tolerant(raw: str | None, expected: date | None) -> None:
    assert parse_date(raw) == expected


def test_parse_datetime_assumes_utc_when_naive() -> None:
    assert parse_datetime("2024-10-01T10:00:00Z") == datetime(2024, 10, 1, 10, tzinfo=UTC)
    assert parse_datetime("2024-10-01T10:00:00") == datetime(2024, 10, 1, 10, tzinfo=UTC)
    assert parse_datetime("garbage") is None
    assert parse_datetime("") is None


def test_redaction_hides_bearer_tokens_and_long_digit_runs() -> None:
    out = redact("Authorization: Bearer eyJabc.def-ghi id=37161876 otp=123456 code=12")
    assert "eyJabc" not in out
    assert "37161876" not in out
    assert "123456" not in out
    assert "code=12" in out


def test_practitioner_ref() -> None:
    ref = PractitionerRef.registered(" A1234 ", RegulationBody.KMPDC)
    assert ref.identification_number == "A1234"
    assert ref.identification_type is IdentificationType.REGISTRATION_NUMBER
    with pytest.raises(ValueError, match="empty"):
        PractitionerRef(" ", IdentificationType.NATIONAL_ID, RegulationBody.NCK)
