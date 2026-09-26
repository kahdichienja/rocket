"""Visit session wire schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class VisitSessionWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    patient_number: str
    sessionStatus: str = "PENDING"  # noqa: N815
    sp_id: int = 0
    location_code: str | None = None
    payer_code: str | None = None
    payer_name: str | None = None
    schemecode: str | None = None
    scheme_name: str | None = None
    visit_number: str | None = None
    member_number: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalise(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        d = dict(data)
        if "id" not in d and "session_id" in d:
            d["id"] = d["session_id"]
        if "patient_number" not in d and "patientNumber" in d:
            d["patient_number"] = d["patientNumber"]
        if "sessionStatus" not in d and "status" in d:
            d["sessionStatus"] = d["status"]
        if "member_number" not in d and "memberNumber" in d:
            d["member_number"] = d["memberNumber"]
        if "payer_code" not in d and "payerCode" in d:
            d["payer_code"] = d["payerCode"]
        if "payer_name" not in d and "payerName" in d:
            d["payer_name"] = d["payerName"]
        if "schemecode" not in d:
            d["schemecode"] = d.get("scheme_code") or d.get("schemeCode")
        if "scheme_name" not in d and "schemeName" in d:
            d["scheme_name"] = d["schemeName"]
        if "visit_number" not in d and "visitNumber" in d:
            d["visit_number"] = d["visitNumber"]
        return d


class SessionActionResponseWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    code: str | int = "200"
    message: str = ""
    response_type: str = "SUCCESS"
