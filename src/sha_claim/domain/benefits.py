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
class RequiredClaimDocument:
    """One document a claim for this intervention must carry. `any_of` lists the types that satisfy it."""

    key: str
    label: str
    any_of: tuple[str, ...] = ()


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
    required_preauth_document_types: tuple[str, ...] = ()
    """What SHA wants attached to the pre-auth — known at selection time, before a visit exists.

    Worth surfacing where the service is chosen rather than where the pre-auth is filed: the documents are
    gathered by the ward, and a desk that learns of them at submission is a desk that submits without them.
    """
    required_claim_documents: tuple[RequiredClaimDocument, ...] = ()
    """A different list, for the claim itself. Varies by intervention — an inpatient one wants a discharge
    summary, an outpatient one wants the prescription."""
    requires_surgical_preauth: bool = False
    requires_renal_preauth: bool = False
    requires_oncology_preauth: bool = False
    requires_radiology_preauth: bool = False
    requires_optical_preauth: bool = False
    is_multisession: bool = False
    """Renal and oncology courses: priced per session rather than per visit."""
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def preauth_kind(self) -> str:
        """Which specialised form SHA expects: SURGICAL | RENAL | ONCOLOGY | OPTICAL | IMAGING | NORMAL.

        Read from SHA's own flags rather than inferred from the code family. A guess off `SHA-19-…` is right
        often enough to be dangerous — it would put a surgeon in front of the wrong form on the day.
        """
        for flag, kind in (
            (self.requires_surgical_preauth, "SURGICAL"),
            (self.requires_renal_preauth, "RENAL"),
            (self.requires_oncology_preauth, "ONCOLOGY"),
            (self.requires_optical_preauth, "OPTICAL"),
            (self.requires_radiology_preauth, "IMAGING"),
        ):
            if flag:
                return kind
        return "NORMAL"

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
