"""Rules engine wire schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class RulesCheckItemWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    item_net_amount: float
    pool_number: int
    provider_item_code: str


class RulesCheckRequestWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    items: list[RulesCheckItemWire]
    medical_aid_code: str
    medical_aid_number: str
    medical_aid_plan: str
    policy_id: int | str


class RulesItemResponseWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    item_code: str
    item_name: str = ""
    preauth_required: bool = False
    preauth_amount: float = 0.0
    preauth_rule_code: str = ""
    excluded: bool = False
    price_amount: float = 0.0

    @model_validator(mode="before")
    @classmethod
    def normalise(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        d = dict(data)
        raw_exc = d.get("excluded", False)
        if isinstance(raw_exc, str):
            d["excluded"] = raw_exc.strip().lower() in ("true", "1", "yes")
        return d


class RulesContentWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    items: list[RulesItemResponseWire] = []


class RulesResponseWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    code: str | int = "200"
    content: list[RulesContentWire] = []
