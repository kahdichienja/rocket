from __future__ import annotations

from pydantic import Field

from sha_claim.adapters.wire.schemas.common import WireModel


class BenefitPackageWire(WireModel):
    parent_benefit: str = ""
    parent_benefit_code: str = ""


class SubBenefitWire(WireModel):
    id: int | None = None
    code: str = ""
    name: str = ""
    access_point: str = ""
    fund: str = ""
    parent_benefit: str = ""
    parent_benefit_code: str = ""


class InterventionWire(WireModel):
    id: int | None = None
    code: str = ""
    name: str = ""
    access_point: str = ""
    payment_mechanism: str = ""
    needs_preauth: bool = False
    needs_manual_preauth_approval: bool = False
    needs_doctor_authorization: bool = False
    overall_tariff: str | None = None
    fund: str = ""
    sub_benefit_code: str = ""
    applicable_schemes: list[str] = Field(default_factory=list)
    number_of_doctors_required: int = 0
