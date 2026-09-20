from __future__ import annotations

from pydantic import Field

from sha_claim.adapters.wire.schemas.common import WireModel


class PolicyWire(WireModel):
    start_date: str = ""
    end_date: str = ""
    number: str = ""


class CoverageWire(WireModel):
    start_date: str = ""
    end_date: str = ""
    message: str = ""
    reason: str = ""
    status: str = ""


class SchemeWire(WireModel):
    scheme_name: str = ""
    scheme_id: int | None = None
    member_type: str = ""
    policy: PolicyWire = PolicyWire()
    coverage: CoverageWire = CoverageWire()


class EligibilityWire(WireModel):
    request_id_type: int | None = None
    request_id_number: str = ""
    date_of_birth: str = ""
    gender: str = ""
    age: int | None = None
    is_alive: bool | None = None
    whitelisted_for_otp: bool = Field(False, alias="whitelistedForOTP")
    facility_biometrics_enforced: bool = False
    member_cr_number: str = ""
    full_name: str = ""
    status_code: str = ""
    status_desc: str = ""
    schemes: list[SchemeWire] = Field(default_factory=list)
