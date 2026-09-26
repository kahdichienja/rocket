"""Domain models for Smart Member, Benefit Pools, and Copayments."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from smart_access.domain.enums import CopayType
from smart_access.domain.identifiers import (
    CardSerialNumber,
    GlobalId,
    InvoiceNumber,
    MedicalAidCode,
    MemberNumber,
    PolicyId,
    SchemeCode,
    SpId,
)


@dataclass(frozen=True)
class BenefitGroup:
    """Sub-service or category group covered under a benefit pool."""

    code: str
    name: str


@dataclass(frozen=True)
class BenefitPool:
    """An insurance benefit pool/fund (e.g. Outpatient, Optical, Dental)."""

    id: int
    amount: Decimal
    claimable: bool
    pool_desc: str
    pool_nr: str
    sp_id: SpId
    groups: tuple[BenefitGroup, ...] = ()

    @property
    def has_balance(self) -> bool:
        return self.claimable and self.amount > 0

    def covers(self, required_amount: Decimal) -> bool:
        return self.claimable and self.amount >= required_amount


@dataclass(frozen=True)
class CopayInfo:
    """Copayment parameters associated with member's scheme."""

    has_copay: bool
    amount: Decimal = Decimal(0)


@dataclass(frozen=True)
class SmartMember:
    """Patient demographic, card, and scheme benefit details retrieved from Smart."""

    admit_id: str
    global_id: GlobalId
    medicalaid_code: MedicalAidCode
    medicalaid_number: MemberNumber
    medicalaid_scheme_name: str
    patient_surname: str
    patient_forenames: str
    patient_dob: str
    benefits: tuple[BenefitPool, ...] = ()
    card_serial_number: CardSerialNumber | None = None
    has_copay: bool = False
    copay_amount: Decimal = Decimal(0)
    medicalaid_name: str | None = None
    medicalaid_scheme_code: SchemeCode | None = None
    medicalaid_plan: str | None = None
    patient_gender: str | None = None
    policy_id: PolicyId | None = None
    policy_currency: str | None = "KES"
    vip_message: str | None = None
    session_type: str | None = None

    @property
    def full_name(self) -> str:
        parts = [self.patient_forenames.strip(), self.patient_surname.strip()]
        return " ".join(p for p in parts if p)

    def find_pool(self, pool_nr: str | int) -> BenefitPool | None:
        target = str(pool_nr).strip()
        for pool in self.benefits:
            if pool.pool_nr.strip() == target:
                return pool
        return None


@dataclass(frozen=True)
class CopaymentRule:
    """Specific copayment rule fetched from `/api/copayment`."""

    benefit_id: int
    amount: Decimal
    is_copay_per_visit: bool
    paid_amount: Decimal
    type: CopayType
    invoice_number: InvoiceNumber | None = None
    receipt_number: str | None = None
