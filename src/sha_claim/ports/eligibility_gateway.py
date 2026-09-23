from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from sha_claim.domain.benefits import (
    BedOccupancy,
    BenefitPackage,
    InterventionCoverage,
    SubBenefit,
    UtilizationBalance,
)
from sha_claim.domain.codes import InterventionCode
from sha_claim.domain.eligibility import Eligibility
from sha_claim.domain.enums import IdentificationType
from sha_claim.domain.identifiers import FacilityCode, PatientId


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

    async def utilization(
        self, patient: PatientId, intervention: InterventionCode
    ) -> tuple[UtilizationBalance, ...]: ...

    async def pomsf_balances(
        self, patient: PatientId, policy_year: str, principal_member_number: str | None
    ) -> Mapping[str, Any]: ...

    async def bed_occupancy(self, facility: FacilityCode) -> BedOccupancy: ...
