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
    overall_tariff: str | float | int | None = None  # UAT sends "0", the portal example sends 0
    fund: str = ""
    sub_benefit_code: str = ""
    applicable_schemes: list[str] = Field(default_factory=list)
    number_of_doctors_required: int = 0


Number = float | int | str | None


class FundLimitWire(WireModel):
    fund_type: str = ""
    max_amount: Number = None
    utilised_amount: Number = None
    available_amount: Number = None


class UtilizationComputationWire(WireModel):
    eligibility: bool | None = None
    limit_available_amount: Number = None
    next_available_date: str = ""


class UtilizationWire(WireModel):
    code: str = ""
    cr_id: str = ""
    limit_scope: str = ""
    individual_max_limit: Number = None
    individual_utilised_limit: Number = None
    household_max_limit: Number = None
    household_utilised_limit: Number = None
    next_availability: str = ""
    computational_detail: UtilizationComputationWire | None = None
    fund_utilization_limit: list[FundLimitWire] = Field(default_factory=list)


class BedCountsWire(WireModel):
    total_number_of_bed: int = 0
    total_ip_visits: int = 0
    number_of_normal_bed: int = 0
    number_of_icu_bed: int = 0
    number_of_hdu_bed: int = 0
    number_of_dialysis_bed: int = 0
    number_of_baby_cot: int = 0


class BedOccupancyWire(WireModel):
    name: str = ""
    bp_level: str = ""
    bed_occupancy_rate: BedCountsWire = BedCountsWire()
