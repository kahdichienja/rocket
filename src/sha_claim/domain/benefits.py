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
    def service_type_for_authorization(self) -> ServiceType:
        """UAT rejects CAPITATION interventions under OUTPATIENT; they must be authorised as CAPITATION."""
        if self.payment_mechanism == PaymentMechanism.CAPITATION:
            return ServiceType.CAPITATION
        return ServiceType.INPATIENT if self.access_point.strip().upper() == "IP" else ServiceType.OUTPATIENT
