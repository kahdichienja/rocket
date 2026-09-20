"""Answer: is this person an SHA beneficiary, and under which schemes?"""

from __future__ import annotations

from sha_claim.domain.eligibility import Eligibility
from sha_claim.domain.enums import IdentificationType
from sha_claim.errors import RequestValidationError, Violation
from sha_claim.ports.eligibility_gateway import EligibilityCheck


class VerifyEligibility:
    def __init__(self, gateway: EligibilityCheck) -> None:
        self._gateway = gateway

    async def execute(
        self, identification_number: str, identification_type: IdentificationType
    ) -> Eligibility:
        number = identification_number.strip()
        violations = []
        if not number:
            violations.append(Violation("identification_number", "cannot be empty"))
        if identification_type is IdentificationType.REGISTRATION_NUMBER:
            violations.append(
                Violation("identification_type", "registration_number identifies practitioners, not patients")
            )
        if violations:
            raise RequestValidationError(violations)
        return await self._gateway.check(number, identification_type)
