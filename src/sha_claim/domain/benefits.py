"""What SHA will pay for, for a given beneficiary: packages → sub-benefits → interventions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from sha_claim.domain.codes import InterventionCode
from sha_claim.domain.enums import PaymentMechanism, ServiceType
from sha_claim.domain.money import Money


@dataclass(frozen=True, slots=True)
class BenefitPackage:
    code: str  # e.g. SHA-12
    name: str


@dataclass(frozen=True, slots=True)
class SubBenefit:
    code: str  # e.g. SHA-12-SC-01
    name: str
    parent_code: str
    access_point: str  # "OP", "IP", "OP and IP"


@dataclass(frozen=True, slots=True)
class InterventionCoverage:
    code: InterventionCode
    name: str
    payment_mechanism: PaymentMechanism | None
    needs_preauth: bool
    needs_doctor_authorization: bool
    access_point: str
    overall_tariff: Money | None
    applicable_schemes: tuple[str, ...]
    fund: str = ""
    sub_benefit_code: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def is_emergency(self) -> bool:
        """Payable from the Emergency, Chronic and Critical Illness Fund — the only interventions
        `POST /claims/emergency` accepts (UAT: Consultation "is not supported for service type EMERGENCY")."""
        return "ECCIF" in self.fund.upper()

    @property
    def service_type_for_authorization(self) -> ServiceType:
        """UAT rejects CAPITATION interventions under OUTPATIENT; they must be authorised as CAPITATION."""
        if self.payment_mechanism == PaymentMechanism.CAPITATION:
            return ServiceType.CAPITATION
        return ServiceType.INPATIENT if self.access_point.strip().upper() == "IP" else ServiceType.OUTPATIENT


@dataclass(frozen=True, slots=True)
class FundLimit:
    fund_type: str
    max_amount: Money | None
    utilised_amount: Money | None
    available_amount: Money | None


@dataclass(frozen=True, slots=True)
class UtilizationBalance:
    """`GET /patients/benefits/utilization` — how much of a benefit the member (and household) has left."""

    intervention_code: InterventionCode | None
    patient_id: str
    limit_scope: str
    individual_max: Money | None
    individual_utilised: Money | None
    household_max: Money | None
    household_utilised: Money | None
    available_amount: Money | None
    eligible: bool | None
    next_availability: str = ""
    funds: tuple[FundLimit, ...] = ()
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def individual_remaining(self) -> Money | None:
        if self.individual_max is None or self.individual_utilised is None:
            return self.available_amount
        return self.individual_max - self.individual_utilised


@dataclass(frozen=True, slots=True)
class BedOccupancy:
    facility_name: str
    level: str
    total_beds: int
    total_inpatient_visits: int
    normal_beds: int = 0
    icu_beds: int = 0
    hdu_beds: int = 0
    dialysis_beds: int = 0
    baby_cots: int = 0
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def occupancy_rate(self) -> float | None:
        return None if self.total_beds == 0 else self.total_inpatient_visits / self.total_beds
