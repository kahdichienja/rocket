"""The virtual claim as the server reports it, and the commands that change it.

Read models (`VirtualClaim`, `ClaimLine`, …) carry derived behaviour only — the server owns the
state. Commands (`NewClaimLine`) validate what the server would certainly reject.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sha_claim.domain.codes import Icd11Code, InterventionCode, SchemeCode
from sha_claim.domain.enums import PaymentMechanism, ServiceType
from sha_claim.domain.identifiers import AttachmentId, ClaimGuid, ConsentToken, InvoiceNumber, LineGuid
from sha_claim.domain.money import Money


@dataclass(frozen=True, slots=True)
class ClaimIntervention:
    code: InterventionCode
    name: str
    payment_mechanism: PaymentMechanism | None
    needs_preauth: bool
    preauth_exists: bool
    workflow_state: str
    sub_benefit_code: str = ""
    fund: str = ""
    overall_tariff: Money | None = None
    applicable_document_types: tuple[str, ...] = ()
    required_preauth_document_types: tuple[str, ...] = ()
    bill_from: datetime | None = None
    bill_to: datetime | None = None
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def preauth_outstanding(self) -> bool:
        return self.needs_preauth and not self.preauth_exists


@dataclass(frozen=True, slots=True)
class ClaimDiagnosis:
    code: Icd11Code | None
    name: str
    intervention_code: InterventionCode | None
    record_id: int | None = None
    is_flagged: bool = False
    recorded_on: datetime | None = None
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class ClaimLine:
    guid: LineGuid | None
    intervention_code: InterventionCode | None
    item_code: str
    item_name: str
    quantity: Decimal
    unit_price: Money | None
    total_amount: Money | None
    net_amount: Money | None
    copay: Money | None = None
    scheme_code: str = ""
    charge_date: date | None = None
    is_active: bool = True
    doctor_name: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class ClaimAttachment:
    attachment_id: AttachmentId | None
    title: str
    attachment_type: str
    intervention_code: InterventionCode | None
    description: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class Invoice:
    """An invoice inside a virtual claim (lines are grouped by invoice on the server side)."""

    invoice_id: str
    invoice_number: InvoiceNumber | None
    invoice_type: str
    workflow_state: str
    dispatch_status: str
    total_amount: Money | None
    net_amount: Money | None
    copay: Money | None = None
    discount: Money | None = None
    lines: tuple[ClaimLine, ...] = ()
    invoice_date: date | None = None
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class VirtualClaim:
    consent_token: ConsentToken
    guid: ClaimGuid | None
    claim_id: int | None
    workflow_state: str
    """Raw server vocabulary; promoted to a LenientStrEnum once UAT recordings reveal its values."""
    claim_auth_status: str
    service_type: ServiceType | None
    patient_name: str
    member_number: str
    payer_name: str
    scheme_name: str
    currency: str
    total_amount: Money | None
    net_amount: Money | None
    total_copay: Money | None = None
    total_discount: Money | None = None
    invoice_number: InvoiceNumber | None = None
    visit_number: str = ""
    visit_start: datetime | None = None
    visit_end: datetime | None = None
    interventions: tuple[ClaimIntervention, ...] = ()
    diagnoses: tuple[ClaimDiagnosis, ...] = ()
    attachments: tuple[ClaimAttachment, ...] = ()
    invoices: tuple[Invoice, ...] = ()
    is_negative: bool = False
    is_zero: bool = False
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def preauth_outstanding(self) -> tuple[ClaimIntervention, ...]:
        return tuple(i for i in self.interventions if i.preauth_outstanding)

    def diagnoses_for(self, intervention: InterventionCode) -> tuple[ClaimDiagnosis, ...]:
        return tuple(d for d in self.diagnoses if d.intervention_code == intervention)

    @property
    def lines(self) -> tuple[ClaimLine, ...]:
        return tuple(line for invoice in self.invoices for line in invoice.lines)


@dataclass(frozen=True, slots=True)
class NewClaimLine:
    """Command for `POST /claims/lines`."""

    intervention_code: InterventionCode
    unit_price: Money
    quantity: Decimal | int
    scheme_code: SchemeCode | None = None
    charge_date: date | None = None
    diagnoses: tuple[Icd11Code, ...] = ()

    def __post_init__(self) -> None:
        if Decimal(self.quantity) <= 0:
            raise ValueError("quantity must be positive")
        if self.unit_price.is_negative:
            raise ValueError("unit_price cannot be negative")

    @property
    def total(self) -> Money:
        return self.unit_price * Decimal(self.quantity)


@dataclass(frozen=True, slots=True)
class LineEdit:
    """Command for `PATCH /claims/lines/edit` (after payer review)."""

    line: LineGuid
    quantity: int | None = None
    unit_price: Money | None = None
    scheme_code: SchemeCode | None = None

    def __post_init__(self) -> None:
        if self.quantity is None and self.unit_price is None and self.scheme_code is None:
            raise ValueError("an edit must change at least one of quantity, unit_price, scheme_code")
        if self.quantity is not None and self.quantity <= 0:
            raise ValueError("quantity must be positive")


@dataclass(frozen=True, slots=True)
class PayerClaimRecord:
    """A row from `GET /claims/preview/payer` — the claim as the payer's system sees it (camelCase on the wire)."""

    guid: str
    provider_claim_no: str
    tracking_number: str
    workflow_state: str
    workflow_display_name: str
    claim_type: str
    is_inpatient: bool
    proposed_value: Money | None
    proposed_value_less_copays: Money | None
    total_copay: Money | None
    member_name: str = ""
    member_number: str = ""
    scheme_name: str = ""
    created: datetime | None = None
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def status(self) -> str:
        return self.workflow_display_name or self.workflow_state
