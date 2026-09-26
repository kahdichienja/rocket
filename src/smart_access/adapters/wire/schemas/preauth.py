"""Pre-authorization wire schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class PreauthAttachmentWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    attachment: str
    type: str = "pdf"


class PreauthContactWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    contact_person_name: str
    email_address: str
    phone_number: str


class PreauthItemWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    item_code: str
    item_name: str
    quantity: float | int
    unit_amount: float
    total_amount: float
    discount: float = 0.0
    prov_comment: str = ""


class PreauthRuleWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    rule_code: str
    request_amount: float
    items: list[PreauthItemWire]


class OpticalRequestWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    frame_brand: str = ""
    frame_color: str = ""
    frame_model: str = ""
    frame_rim_type: int = 0
    frame_size: str = ""
    frame_type: int = 0
    is_new_frames: bool = True
    lens_type: int = 0
    spectacles_reason: str = ""


class PreauthRequestWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    admit_id: int
    condition_diganosis_date: str
    copay_amount: float
    copay_type: str
    diagnosis_code: str
    doctor_name: str
    global_id: str
    invoice_number: str
    medical_aid_code: str
    medical_aid_number: str
    medical_aid_plan: str
    patient_file_no: str
    phone_number: str
    policy_id: int | str
    pool_number: int
    location_code: str | int
    rules: list[PreauthRuleWire]
    treatment_cost_estimate: float | str
    treatment_date: str
    visit_number: str
    attachments: list[PreauthAttachmentWire] = []
    contact_details: list[PreauthContactWire] = []
    doctor_phone_no: str | None = None
    estimated_stay: int | None = None
    first_diag_date: str | None = None
    hospitalization_type: str | None = "Planned"
    is_congenital: bool = False
    is_integrated: bool = True
    is_optical: bool = False
    preauth_notes: str | None = None
    preauth_type: str = "ZERO"
    presenting_complaints: str | None = None
    provider_comments: str | None = None
    provider_key: str | None = None
    treatment_line: str | None = None
    preauth_optical_request: OpticalRequestWire | None = None


class PreauthResponseWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    preauth_request_id: str
    visit_number: str
    status: str = "Pending"


class PreauthStatusItemWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    item_code: str = ""
    item_name: str = ""
    approved_amount: float = 0.0
    balance_amount: float = 0.0
    declined_amount: float = 0.0
    requested_amount: float = 0.0
    rule_code: str = ""


class PreauthStatusFeedbackWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int = 0
    preauth_request_code: str = ""
    preauth_amount: float = 0.0
    consumed_amount: float = 0.0
    preauth_switch_status: str = "PENDING"
    invoice_number: str = ""
    patient_number: str = ""
    visit_number: str = ""
    diagnosis_code: str = ""
    operation_name: str = ""
    preauth_notes: str = ""
    rules: list[dict[str, Any]] = []

    @model_validator(mode="before")
    @classmethod
    def normalise(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        d = dict(data)
        if "preauth_request_code" not in d and "preauth_request_id" in d:
            d["preauth_request_code"] = d["preauth_request_id"]
        return d
