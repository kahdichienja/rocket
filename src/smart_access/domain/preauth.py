"""Domain models for Smart Pre-Authorization requests and status tracking."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from smart_access.domain.enums import HospitalizationType, PreauthStatus
from smart_access.domain.identifiers import (
    GlobalId,
    InvoiceNumber,
    LocationCode,
    MedicalAidCode,
    MemberNumber,
    PatientNumber,
    PolicyId,
    PreauthRequestId,
    VisitNumber,
)


@dataclass(frozen=True)
class PreauthAttachment:
    """Document attachment accompanying a preauth request (e.g. PDF in base64)."""

    attachment: str
    type: str = "pdf"


@dataclass(frozen=True)
class PreauthContact:
    """Hospital contact person responsible for this preauth."""

    contact_person_name: str
    email_address: str
    phone_number: str


@dataclass(frozen=True)
class PreauthItem:
    """Specific line item submitted under a preauth rule."""

    item_code: str
    item_name: str
    quantity: Decimal | int
    unit_amount: Decimal
    total_amount: Decimal
    discount: Decimal = Decimal(0)
    prov_comment: str = ""


@dataclass(frozen=True)
class PreauthRule:
    """Pre-authorization rule and its itemized breakdown."""

    rule_code: str
    request_amount: Decimal
    items: tuple[PreauthItem, ...]


@dataclass(frozen=True)
class OpticalRequest:
    """Optional optical specs when preauthorizing optical frames/lenses."""

    frame_brand: str = ""
    frame_color: str = ""
    frame_model: str = ""
    frame_rim_type: int = 0
    frame_size: str = ""
    frame_type: int = 0
    is_new_frames: bool = True
    lens_type: int = 0
    spectacles_reason: str = ""


@dataclass(frozen=True)
class PreauthRequest:
    """Full request payload for `/api/preauth-request`."""

    admit_id: int
    condition_diagnosis_date: str
    copay_amount: Decimal
    copay_type: str
    diagnosis_code: str
    doctor_name: str
    global_id: GlobalId
    invoice_number: InvoiceNumber
    medical_aid_code: MedicalAidCode
    medical_aid_number: MemberNumber
    medical_aid_plan: str
    patient_file_no: PatientNumber
    phone_number: str
    policy_id: PolicyId
    pool_number: int
    location_code: LocationCode
    rules: tuple[PreauthRule, ...]
    treatment_cost_estimate: Decimal
    treatment_date: str
    visit_number: VisitNumber
    attachments: tuple[PreauthAttachment, ...] = ()
    contact_details: tuple[PreauthContact, ...] = ()
    doctor_phone_no: str | None = None
    estimated_stay: int | None = None
    first_diag_date: str | None = None
    hospitalization_type: HospitalizationType | None = HospitalizationType.PLANNED
    is_congenital: bool = False
    is_integrated: bool = True
    is_optical: bool = False
    preauth_notes: str | None = None
    preauth_type: str = "ZERO"
    presenting_complaints: str | None = None
    provider_comments: str | None = None
    provider_key: str | None = None
    treatment_line: str | None = None
    optical_request: OpticalRequest | None = None


@dataclass(frozen=True)
class PreauthResponse:
    """Initial response acknowledging preauth receipt."""

    preauth_request_id: PreauthRequestId
    visit_number: VisitNumber
    status: PreauthStatus

    @property
    def is_approved(self) -> bool:
        return self.status == PreauthStatus.APPROVED


@dataclass(frozen=True)
class PreauthStatusItem:
    """Line item status returned from preauth query."""

    item_code: str
    item_name: str
    approved_amount: Decimal
    balance_amount: Decimal
    declined_amount: Decimal
    requested_amount: Decimal
    rule_code: str


@dataclass(frozen=True)
class PreauthStatusFeedback:
    """Detailed feedback from the insurer on a processed preauth request."""

    id: int
    preauth_request_code: PreauthRequestId
    preauth_amount: Decimal
    consumed_amount: Decimal
    preauth_switch_status: str
    invoice_number: InvoiceNumber
    patient_number: PatientNumber
    visit_number: VisitNumber
    items: tuple[PreauthStatusItem, ...] = ()
    diagnosis_code: str = ""
    operation_name: str = ""
    preauth_notes: str = ""
