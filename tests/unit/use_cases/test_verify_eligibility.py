import pytest

from sha_claim.domain.eligibility import Eligibility
from sha_claim.domain.enums import EligibilityStatus, IdentificationType
from sha_claim.domain.identifiers import PatientId
from sha_claim.errors import RequestValidationError
from sha_claim.use_cases.verify_eligibility import VerifyEligibility


class FakeGateway:
    def __init__(self) -> None:
        self.calls: list[tuple[str, IdentificationType]] = []

    async def check(self, identification_number: str, identification_type: IdentificationType) -> Eligibility:
        self.calls.append((identification_number, identification_type))
        return Eligibility(PatientId("CR1"), "T", EligibilityStatus.MEMBER_FOUND, "", ())


async def test_trims_and_delegates() -> None:
    gw = FakeGateway()
    result = await VerifyEligibility(gw).execute(" 123 ", IdentificationType.NATIONAL_ID)
    assert result.member_found
    assert gw.calls == [("123", IdentificationType.NATIONAL_ID)]


async def test_rejects_empty_number_and_practitioner_type_without_calling_gateway() -> None:
    gw = FakeGateway()
    with pytest.raises(RequestValidationError) as exc:
        await VerifyEligibility(gw).execute("  ", IdentificationType.REGISTRATION_NUMBER)
    assert {v.field for v in exc.value.violations} == {"identification_number", "identification_type"}
    assert gw.calls == []
