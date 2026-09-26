"""Domain models for Smart Claims submission and status feedback."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from smart_access.domain.enums import (
    ClaimStatus,
    CodingStandard,
    PaymentModifierType,
    SmartResponseType,
)
from smart_access.domain.identifiers import (
    ClaimCode,
    InvoiceNumber,
    LocationCode,
    MedicalAidCode,
    MemberNumber,
    PatientNumber,
    SchemeCode,
    SessionId,
    SpId,
    VisitNumber,
)


@dataclass(frozen=True)
class ClaimDiagnosis:
    """Diagnostic coding associated with the claim."""

    code: str
    name: str
    coding_standard: CodingStandard | str = CodingStandard.ICD10
    is_added_with_claim: bool = True
    primary: bool = True


@dataclass(frozen=True)
class PreauthReference:
    """Pre-authorization approval reference attached to the claim."""

    code: str
    amount: Decimal
    authorized_by: str
    message: str


@dataclass(frozen=True)
class ClaimInvoiceLine:
    """Detailed billed service line under an invoice."""

    item_code: str
    item_name: str
    quantity: Decimal | int
    unit_price: Decimal
    amount: Decimal
    service_group: str
    charge_date: str
    charge_time: str
    additional_info: str = ""
    pre_authorization_code: str = ""


@dataclass(frozen=True)
class ClaimInvoice:
    """Invoice container grouping billed items and eTIMS fiscal tags."""

    amount: Decimal
    gross_amount: Decimal
    invoice_date: str
    invoice_number: InvoiceNumber
    invoice_ref_number: InvoiceNumber
    lines: tuple[ClaimInvoiceLine, ...]
    etims_number: str | None = None
    etims_qrcode: str | None = None


@dataclass(frozen=True)
class PaymentModifier:
    """Payment split details (e.g. Copay, NHIF/SHIF, Cash excess)."""

    type: PaymentModifierType | str
    amount: Decimal
    reference_number: str
    nhif_contributor_nr: str | None = None
    nhif_employer_code: str | None = None
    nhif_member_nr: str | None = None
    nhif_patient_relation: str | None = None
    nhif_site_nr: str | None = None


@dataclass(frozen=True)
class PreauthOverride:
    """Justification details when pre-authorization requirement was bypassed."""

    override_reason: str
    preauth_overides_types: str = "1"
    preauth_request_code: str = ""
    preauth_request_rule_code: str = ""
    username: str = ""


@dataclass(frozen=True)
class Admission:
    """Inpatient admission details linked to the claim."""

    admission_date: str
    admission_number: str
    discharge_date: str | None = None
    discharge_summary: str | None = None
    additional_info: str | None = None


@dataclass(frozen=True)
class SmartClaim:
    """Complete claim representation posted to `POST /api/claims`."""

    claim_code: ClaimCode
    payer_code: MedicalAidCode
    payer_name: str
    medicalaid_code: MedicalAidCode
    amount: Decimal
    gross_amount: Decimal
    batch_number: str
    dispatch_date: str
    patient_number: PatientNumber
    patient_name: str
    location_code: LocationCode
    location_name: str
    scheme_code: SchemeCode
    scheme_name: str
    member_number: MemberNumber
    visit_number: VisitNumber
    session_id: SessionId
    visit_start: str
    visit_end: str
    sp_id: SpId
    currency: str = "KES"
    doctor_name: str = ""
    pool_number: int | None = None
    diagnosis: tuple[ClaimDiagnosis, ...] = ()
    pre_authorization: tuple[PreauthReference, ...] = ()
    invoices: tuple[ClaimInvoice, ...] = ()
    payment_modifiers: tuple[PaymentModifier, ...] = ()
    preauth_overrides: tuple[PreauthOverride, ...] = ()
    admission: tuple[Admission, ...] = ()


@dataclass(frozen=True)
class ClaimSubmissionResult:
    """Outcome of posting claim to Smart."""

    success: bool
    code: str
    message: str
    response_type: SmartResponseType


@dataclass(frozen=True)
class ClaimStatusFeedback:
    """Insurer claim processing/settlement status returned from `/api/claim-status`."""

    session_id: SessionId
    claim_status: ClaimStatus
    payer_name: str
    patient_number: PatientNumber
    visit_number: VisitNumber
    scheme_name: str
    amount: Decimal
    invoice_number: InvoiceNumber

    @property
    def is_billed(self) -> bool:
        return self.claim_status.is_billed

    @property
    def is_pending(self) -> bool:
        return self.claim_status == ClaimStatus.PENDING

    @property
    def is_terminal_failure(self) -> bool:
        return self.claim_status.is_terminal_failure
