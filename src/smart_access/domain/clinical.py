"""Domain models for clinical records, orders, admissions, discharges, and item mapping."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from smart_access.domain.claim import ClaimDiagnosis
from smart_access.domain.enums import AdmissionType, DoctorType
from smart_access.domain.identifiers import (
    InvoiceNumber,
    MemberNumber,
    PatientNumber,
    PreauthRequestId,
    SessionId,
    VisitNumber,
)


@dataclass(frozen=True)
class ClinicalRecord:
    """Clinical diagnostic record posted to `/api/clinic-record`."""

    invoice_number: InvoiceNumber
    member_number: MemberNumber
    patient_number: PatientNumber
    session_id: SessionId
    visit_number: VisitNumber
    diagnosis: tuple[ClaimDiagnosis, ...]


@dataclass(frozen=True)
class PrescriptionItem:
    """Prescription line item under clinical requests."""

    item_code: str
    item_name: str
    dosage: str
    duration: str
    frequency: str
    price: Decimal
    quantity: Decimal | int
    amount: Decimal
    route: str = ""


@dataclass(frozen=True)
class ClinicalOrder:
    """Diagnostic or procedural order under clinical requests."""

    item_code: str
    item_name: str
    price: Decimal
    quantity: Decimal | int
    amount: Decimal
    request_type: str = ""


@dataclass(frozen=True)
class ClinicalRequests:
    """Collection of clinical requests posted to `/api/requests`."""

    member_number: MemberNumber
    patient_number: PatientNumber
    visit_number: VisitNumber
    preauth_request_id: PreauthRequestId | None = None
    prescription: tuple[PrescriptionItem, ...] = ()
    laboratory: tuple[ClinicalOrder, ...] = ()
    radiology: tuple[ClinicalOrder, ...] = ()
    procedure: tuple[ClinicalOrder, ...] = ()
    other: tuple[ClinicalOrder, ...] = ()


@dataclass(frozen=True)
class AdmissionDetails:
    """Inpatient admission record posted to `/api/admission`."""

    admission_number: str
    visit_number: VisitNumber
    patient_number: PatientNumber
    admission_type: AdmissionType | str
    admission_date: str
    admitting_doctor: str
    admitting_doctor_type: DoctorType | str
    ward_name: str
    ward_number: str
    bed_type: str
    bed_number: str
    inpatient_number: str
    admission_notes: str
    preauth_request_id: PreauthRequestId | None = None
    additional_info: str = ""


@dataclass(frozen=True)
class DischargeDetails:
    """Inpatient discharge record posted to `/api/discharge`."""

    admission_number: str
    patient_number: PatientNumber
    discharge_date: str
    discharging_doctor: str
    discharge_summary: str = ""


@dataclass(frozen=True)
class ItemMapping:
    """Service or Item mapped to Smart Master List via `/api/new-mapping`."""

    group_code: str
    group_name: str
    item_code: str
    item_name: str
    provider_key: str = ""
