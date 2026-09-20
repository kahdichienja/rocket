from __future__ import annotations

from typing import Protocol

from sha_claim.domain.eligibility import Eligibility
from sha_claim.domain.enums import IdentificationType


class EligibilityGateway(Protocol):
    async def check(
        self, identification_number: str, identification_type: IdentificationType
    ) -> Eligibility: ...
