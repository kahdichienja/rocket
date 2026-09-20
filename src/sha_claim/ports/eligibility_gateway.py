from __future__ import annotations

from typing import Protocol

from sha_claim.domain.benefits import BenefitPackage, InterventionCoverage, SubBenefit
from sha_claim.domain.eligibility import Eligibility
from sha_claim.domain.enums import IdentificationType
from sha_claim.domain.identifiers import PatientId


class EligibilityCheck(Protocol):
    """Role interface for the use case that only needs the eligibility lookup."""

    async def check(
        self, identification_number: str, identification_type: IdentificationType
    ) -> Eligibility: ...


class EligibilityGateway(EligibilityCheck, Protocol):
    async def benefits(self, patient: PatientId) -> tuple[BenefitPackage, ...]: ...

    async def sub_benefits(self, patient: PatientId) -> tuple[SubBenefit, ...]: ...

    async def interventions(
        self, patient: PatientId, sub_benefit_code: str
    ) -> tuple[InterventionCoverage, ...]: ...
