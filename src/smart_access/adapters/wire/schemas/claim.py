"""Claim submission and status feedback wire schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class ClaimDiagnosisWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    code: str
    name: str
    coding_standard: str = "ICD10"
    is_added_with_claim: bool = True
    primary: bool = True

    @model_validator(mode="before")
    @classmethod
    def normalise(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        d = dict(data)
        if "primary" not in d and "is_primary" in d:
            d["primary"] = d["is_primary"]
        return d


class PreauthReferenceWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    code: str
    amount: float
    authorized_by: str
    message: str


class ClaimInvoiceLineWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    item_code: str
    item_name: str
    quantity: float | int
    unit_price: float
    amount: float
    service_group: str
    charge_date: str
    charge_time: str
    additional_info: str = ""
    pre_authorization_code: str = ""


class ClaimInvoiceWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    amount: float
    gross_amount: float
    invoice_date: str
    invoice_number: str
    invoice_ref_number: str
    lines: list[ClaimInvoiceLineWire]
    etims_number: str | None = None
    etims_qrcode: str | None = None


class PaymentModifierWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    amount: float
    reference_number: str
    nhif_contributor_nr: str | None = None
    nhif_employer_code: str | None = None
    nhif_member_nr: str | None = None
    nhif_patient_relation: str | None = None
    nhif_site_nr: str | None = None


class PreauthOverrideWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    override_reason: str
    preauth_overides_types: str = "1"
    preauth_request_code: str = ""
    preauth_request_rule_code: str = ""
    username: str = ""


class AdmissionWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    admission_date: str
    admission_number: str
    discharge_date: str | None = None
    discharge_summary: str | None = None
    additional_info: str | None = None


class SmartClaimRequestWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    claim_code: str
    payer_code: str
    payer_name: str
    medicalaid_code: str
    amount: float
    gross_amount: float
    batch_number: str
    dispatch_date: str
    patient_number: str
    patient_name: str
    location_code: str
    location_name: str
    scheme_code: str
    scheme_name: str
    member_number: str
    visit_number: str
    session_id: int
    visit_start: str
    visit_end: str
    sp_id: int
    currency: str = "KES"
    doctor_name: str = ""
    pool_number: int | None = None
    diagnosis: list[ClaimDiagnosisWire] = []
    pre_authorization: list[PreauthReferenceWire] = []
    invoices: list[ClaimInvoiceWire] = []
    payment_modifiers: list[PaymentModifierWire] = []
    preauth_overrides: list[PreauthOverrideWire] = []
    admission: list[AdmissionWire] = []


class ClaimStatusResponseWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    session_id: int
    claim_status: str = "Pending"
    payer_name: str = ""
    patient_number: str = ""
    visit_number: str = ""
    scheme_name: str = ""
    amount: float = 0.0
    invoice_number: str = ""
