"""Member and benefit pool wire schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class BenefitGroupWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    code: str
    name: str


class BenefitPoolWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    amount: float = 0.0
    claimable: bool = True
    pool_desc: str = ""
    pool_nr: str | int = "0"
    sp_id: int = 0
    groups: list[BenefitGroupWire] = []


class SmartMemberWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    admit_id: str
    global_id: str
    medicalaid_code: str
    medicalaid_number: str
    medicalaid_scheme_name: str
    patient_surname: str
    patient_forenames: str = ""
    patient_dob: str = ""
    benefits: list[BenefitPoolWire] = []
    card_serial_number: str | None = None
    has_copay: bool = False
    co_pay_amount: float = 0.0
    medicalaid_name: str | None = None
    medicalaid_scheme_code: str | None = None
    medicalaid_plan: str | None = None
    patient_gender: str | None = None
    policy_id: int | str | None = None
    policy_currency: str | None = "KES"
    vip_message: str | None = None
    session_type: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalise(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        d = dict(data)
        if "admit_id" not in d and "policy_id" in d:
            d["admit_id"] = str(d["policy_id"])
        elif "admit_id" in d:
            d["admit_id"] = str(d["admit_id"])

        copay_info = d.get("copay_info")
        if isinstance(copay_info, dict):
            d["has_copay"] = copay_info.get("has_copay", d.get("has_copay", False))
            d["co_pay_amount"] = copay_info.get("amount", d.get("co_pay_amount", 0.0))

        if "patient_surname" not in d and "member_name" in d:
            d["patient_surname"] = str(d["member_name"])

        return d


class CopaymentRuleWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    amount: float = 0.0
    invoice_number: str | None = None
    is_copay_per_visit: bool = True
    paid_amount: float = 0.0
    receipt_number: str | None = None
    type: str = "PERCENTAGE"
