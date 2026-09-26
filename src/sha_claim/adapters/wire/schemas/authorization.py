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


class ElectivePreauthWire(WireModel):
    """The summary of an earlier, elective pre-auth, as it rides on a later authorization.

    Deliberately thin — SHA sends only enough to recognise the approval, not the pre-auth itself. The full
    record is still fetched with `GET /preauths`.
    """

    is_elective: bool = False
    status: str = ""
    doctor_review_status: str = ""
    preauth_type: str = ""
    member_name: str = ""
    service_start: str = ""
    service_end: str = ""


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
    #: Set when this visit is being opened against a pre-auth raised at an earlier one.
    is_elective: bool = False
    needs_preauth: bool = False
    #: The earlier pre-auth itself, summarised. This is how an approval granted on Monday is found again
    #: on Friday: it arrives on the *new* authorization rather than being looked up by anything NaCare holds.
    elective_preauth: ElectivePreauthWire | None = None
