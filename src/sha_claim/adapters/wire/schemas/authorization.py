from __future__ import annotations

from pydantic import Field

from sha_claim.adapters.wire.schemas.common import WireModel


class AuthorizedInterventionWire(WireModel):
    id: int | None = None
    code: str = ""
    name: str = ""
    needs_preauth: bool = False
    payment_mechanism: str = ""
    sub_benefit_code: str = ""


class VerificationRequestWire(WireModel):
    """`shaVerificationRequest` — the eKYC capture handoff on a biometric authorization."""

    embed_expiry: int | None = None
    embeded_token: str = ""  # SHA's spelling
    request_id: str = ""
    request_url: str = ""


class AuthorizationWire(WireModel):
    id: int | None = None
    guid: str = ""
    token: str = ""
    auth_code: str = ""
    status: str = ""
    label: str = ""
    is_open: bool = False
    benefit_type: str = ""
    beneficiary_code: str = ""
    beneficiary_name: str = ""
    provider_fid: str = ""
    expiry: str = ""
    overall_preauth_finalised: bool = False
    interventions: list[AuthorizedInterventionWire] = Field(default_factory=list)
    ekyc_token: str = ""
    sha_verification_request: VerificationRequestWire | None = None
