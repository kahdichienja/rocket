"""Beneficiary eligibility as reported by `GET /patients/eligibility`. Read model: derived behaviour only."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from sha_claim.domain.enums import CoverageStatus, EligibilityStatus
from sha_claim.domain.identifiers import PatientId


@dataclass(frozen=True, slots=True)
class DateRange:
    start: date | None
    end: date | None

    def contains(self, day: date) -> bool:
        return (self.start is None or self.start <= day) and (self.end is None or day <= self.end)


@dataclass(frozen=True, slots=True)
class Coverage:
    status: CoverageStatus | None
    message: str
    reason: str
    period: DateRange

    def is_active_on(self, day: date) -> bool:
        return self.status == CoverageStatus.COVERED and self.period.contains(day)


@dataclass(frozen=True, slots=True)
class Scheme:
    name: str
    scheme_id: int | None
    member_type: str
    policy_number: str
    policy_period: DateRange
    coverage: Coverage

    def is_active_on(self, day: date) -> bool:
        return self.coverage.is_active_on(day) and self.policy_period.contains(day)


@dataclass(frozen=True, slots=True)
class Eligibility:
    patient_id: PatientId | None
    full_name: str
    status: EligibilityStatus | None
    status_description: str
    schemes: tuple[Scheme, ...]
    date_of_birth: date | None = None
    gender: str = ""
    age: int | None = None
    is_alive: bool | None = None
    whitelisted_for_otp: bool = False
    facility_biometrics_enforced: bool = False
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)
    """Server fields the SDK does not model yet. Read-only escape hatch; never rely on it in domain logic."""

    @property
    def member_found(self) -> bool:
        return self.status == EligibilityStatus.MEMBER_FOUND and self.patient_id is not None

    def active_schemes_on(self, day: date) -> tuple[Scheme, ...]:
        return tuple(s for s in self.schemes if s.is_active_on(day))

    def is_covered_on(self, day: date) -> bool:
        return self.member_found and bool(self.active_schemes_on(day))
