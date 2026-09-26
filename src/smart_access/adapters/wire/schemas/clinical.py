"""Clinical and mapping wire schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from smart_access.adapters.wire.schemas.claim import ClaimDiagnosisWire


class ClinicalRecordWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    invoice_number: str
    member_number: str
    patient_number: str
    session_id: int | str
    visit_number: str
    diagnosis: list[ClaimDiagnosisWire]


class PrescriptionItemWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    item_code: str
    item_name: str
    dosage: str
    duration: str
    frequency: str
    price: float
    quantity: float | int
    amount: float
    route: str = ""


class ClinicalOrderWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    item_code: str
    item_name: str
    price: float
    quantity: float | int
    amount: float
    request_type: str = ""


class ClinicalRequestsWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    member_number: str
    patient_number: str
    visit_number: str
    preauth_request_id: str | None = None
    prescription: list[PrescriptionItemWire] = []
    laboratory: list[ClinicalOrderWire] = []
    radiology: list[ClinicalOrderWire] = []
    procedure: list[ClinicalOrderWire] = []
    other: list[ClinicalOrderWire] = []


class AdmissionDetailsWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    admission_number: str
    visit_number: str
    patient_number: str
    admission_type: str
    admission_date: str
    admitting_doctor: str
    admitting_doctor_type: str
    ward_name: str
    ward_number: str
    bed_type: str
    bed_number: str
    inpatient_number: str
    admission_notes: str
    preauth_request_id: str | None = None
    additional_info: str = ""


class DischargeDetailsWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    admission_number: str
    patient_number: str
    discharge_date: str
    discharging_doctor: str
    discharge_summary: str = ""


class ItemMappingWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    group_code: str
    group_name: str
    item_code: str
    item_name: str
    provider_key: str = ""
