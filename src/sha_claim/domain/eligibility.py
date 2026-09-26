"""Beneficiary eligibility as reported by `GET /patients/eligibility`. Read model: derived behaviour only."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
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


class ConsentRoute(StrEnum):
    """How this member proves consent for a visit."""

    OTP = "OTP"
    BIOMETRIC = "BIOMETRIC"


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
    """False means SHA holds no phone contact for the member: `send_otp` will fail, whatever else is true."""
    facility_biometrics_enforced: bool = False
    facility_contracts: tuple[str, ...] = ()
    """Scheme names the acting facility is contracted for (UHC, SHIF, POMSF …). Empty when SHA sent none."""
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)
    """Server fields the SDK does not model yet. Read-only escape hatch; never rely on it in domain logic."""

    @property
    def member_found(self) -> bool:
        return self.status == EligibilityStatus.MEMBER_FOUND and self.patient_id is not None

    def can_consent_by_otp(self) -> bool:
        """Whether `send_otp` can work at all: SHA must hold a phone contact for this member."""
        return self.whitelisted_for_otp

    def consent_route(self) -> ConsentRoute:
        """Which way this member proves consent — the payer's decision, not ours.

        Both flags come back on the eligibility check and between them they settle it:

        * `facility_biometrics_enforced` — SHA has put this facility on biometrics. It decides first,
          because an enforced facility may not fall back to an OTP even for a member who has a phone.
        * `whitelisted_for_otp` — SHA holds a confirmed phone contact. False means `send_otp` will fail
          whatever else is true, so the biometric path is the only one left.

        A member who can do neither is not represented here: biometrics is what remains, and if it fails the
        desk files an OTP whitelist request. That is the documented remedy, not a dead end.
        """
        if self.facility_biometrics_enforced:
            return ConsentRoute.BIOMETRIC
        return ConsentRoute.OTP if self.whitelisted_for_otp else ConsentRoute.BIOMETRIC

    def contracted_schemes_on(self, day: date) -> tuple[Scheme, ...]:
        """Active schemes the acting facility may actually bill — the intersection SHA enforces at `open_visit`."""
        active = self.active_schemes_on(day)
        if not self.facility_contracts:
            return active
        allowed = {c.strip().upper() for c in self.facility_contracts}
        return tuple(s for s in active if s.name.strip().upper() in allowed)

    def active_schemes_on(self, day: date) -> tuple[Scheme, ...]:
        return tuple(s for s in self.schemes if s.is_active_on(day))

    def is_covered_on(self, day: date) -> bool:
        return self.member_found and bool(self.active_schemes_on(day))
