"""Patient consent: how it is proven, and the authorization record the server keeps."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sha_claim.domain.codes import InterventionCode
from sha_claim.domain.enums import AuthorizationStatus, PaymentMechanism
from sha_claim.domain.identifiers import Identifier, PatientId


@dataclass(frozen=True, slots=True)
class Otp:
    """One-time password delivered to the beneficiary's registered phone by `authorize`."""

    code: str

    def __post_init__(self) -> None:
        code = self.code.strip()
        if not code.isdigit():
            raise ValueError("OTP must be numeric")
        object.__setattr__(self, "code", code)

    def __repr__(self) -> str:
        return "Otp('••••')"


@dataclass(frozen=True, slots=True)
class BiometricGuid(Identifier):
    """GUID of a biometric authorization that has been verified (eKYC / fingerprint)."""


@dataclass(frozen=True, slots=True)
class MatchId(Identifier):
    """Biometric match identifier accepted by `/claims/visit` as an alternative to OTP."""


ConsentProof = Otp | BiometricGuid | MatchId


@dataclass(frozen=True, slots=True)
class BiometricContext:
    """Who and what is performing a biometric capture, as `POST /claims/authorize` wants it.

    These identify the *workstation and operator*, not the patient: SHA ties a capture to a registered
    device and a registered agent, and rejects one it cannot place. They come from the HealthID hardware
    server where it is deployed, and from configuration where it is not — this type does not care which,
    so adopting the hardware later changes nothing below the call site.

    `factors` selects the method: `SHA` is eKYC through the SHA portal (adults), `fingerprint` the
    under-18 flow. Defaults to eKYC because that is the path this SDK supports end to end.
    """

    agent_id: str
    """National ID of the biometrics agent registered on the hardware server."""
    work_station_id: str
    ekyc_provider_id: str = ""
    """The facility *name* SHA has registered, not its FR code — `provider` carries that."""
    provider: str = ""
    """Facility FR code. Usually left empty so the facility scope in force supplies it."""
    authorizing_device_os: str = "windows"
    factors: tuple[str, ...] = ("SHA",)
    is_integration: bool = True
    """True when the request comes from an integrated HMS rather than the portal — always true here."""
    is_emergency: bool = False
    is_biometrics_discharge_authorization: bool = False
    """Only when authorizing an inpatient discharge; false for every other flow."""

    def __post_init__(self) -> None:
        if not self.agent_id.strip():
            raise ValueError("biometric capture needs the agent's national ID")
        if not self.work_station_id.strip():
            raise ValueError("biometric capture needs a work station id")

    def as_payload(self) -> dict[str, Any]:
        """The biometric half of the authorize body. Empty optional fields are omitted, not sent blank."""
        body: dict[str, Any] = {
            "agent_id": self.agent_id.strip(),
            "work_station_id": self.work_station_id.strip(),
            "authorizing_device_os": self.authorizing_device_os,
            "factors": list(self.factors),
            "is_integration": self.is_integration,
            "is_emergency": self.is_emergency,
            "is_biometrics_discharge_authorization": self.is_biometrics_discharge_authorization,
        }
        if self.ekyc_provider_id.strip():
            body["ekyc_provider_id"] = self.ekyc_provider_id.strip()
        if self.provider.strip():
            body["provider"] = self.provider.strip()
        return body


@dataclass(frozen=True, slots=True)
class VerificationRequest:
    """The eKYC capture handoff on a biometric authorization (`shaVerificationRequest`).

    `POST /claims/authorize` with biometric factors does not verify anybody by itself: it files a PENDING
    authorization and hands back a one-time URL where the beneficiary proves who they are. Without
    `request_url` there is nothing for the integrator to open, and the authorization sits PENDING for ever.

    `embed_expiry` is seconds, and short — 120 on UAT. When it lapses the authorization stays PENDING and
    **blocks a new one for the same context**, so the caller must `reject` it before trying again.
    """

    request_url: str = ""
    embed_expiry: int | None = None
    embeded_token: str = ""
    """SHA's spelling, kept verbatim so the wire and the model read the same."""
    request_id: str = ""

    @property
    def is_usable(self) -> bool:
        return bool(self.request_url)


@dataclass(frozen=True, slots=True)
class AuthorizedIntervention:
    code: InterventionCode
    name: str
    needs_preauth: bool
    payment_mechanism: PaymentMechanism | None
    sub_benefit_code: str = ""


@dataclass(frozen=True, slots=True)
class ElectivePreauth:
    """An earlier pre-auth, as SHA summarises it on a later authorization."""

    is_elective: bool = False
    status: str = ""
    doctor_review_status: str = ""
    preauth_type: str = ""
    member_name: str = ""
    service_start: datetime | None = None
    service_end: datetime | None = None

    @property
    def is_approved(self) -> bool:
        """Approved outright — the only state in which the visit can be billed against it.

        Substring-matched, and anything unrecognised is **not** approved: SHA spells approval several ways
        and the cost of reading a pending one as approved is a refused claim after the operation.
        """
        status = self.status.strip().upper()
        return "APPROV" in status and not any(w in status for w in ("PENDING", "AWAIT", "REQUEST"))


@dataclass(frozen=True, slots=True)
class Authorization:
    """Snapshot of `POST /claims/authorize` / `GET /claims/authorizations`."""

    guid: str
    token: str
    auth_code: str
    status: AuthorizationStatus | None
    label: str
    is_open: bool
    benefit_type: str
    beneficiary: PatientId | None
    beneficiary_name: str
    provider_fid: str
    interventions: tuple[AuthorizedIntervention, ...]
    expiry: datetime | None = None
    overall_preauth_finalised: bool = False
    record_id: int | None = None
    ekyc_token: str = ""
    """Present on the biometric path; the same value as `verification.embeded_token`."""
    verification: VerificationRequest | None = None
    """Where the beneficiary proves who they are. Only the biometric path has one."""
    is_elective: bool = False
    """This visit is being opened against a pre-auth raised at an earlier one."""
    server_needs_preauth: bool = False
    """SHA's own top-level answer, which is not always the one the interventions give.

    Kept separate from the `needs_preauth` property rather than replacing it: that property reads the
    authorized interventions, and an authorization can arrive with none listed while SHA still says a
    pre-auth is wanted. The property takes both and errs towards wanting one.
    """
    elective_preauth: ElectivePreauth | None = None
    """The earlier approval, summarised by SHA.

    This is the whole of the elective mechanism as the API actually offers it. A pre-auth is always raised
    against an *open* visit — `POST /preauths` takes a `consent_token` from `POST /claims/visit` — so there
    is no such thing as raising one before the patient arrives. What makes it elective is that the service
    is dated later; and when the patient does come back, SHA reports the approval **here**, on the new
    authorization, rather than anywhere NaCare could have looked it up.
    """
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def proof(self) -> BiometricGuid:
        """This authorization as consent proof for `open_visit` — the `auth_guid` branch of `/claims/visit`.

        The route out when the beneficiary has no phone on record: `authorize()` still returns a PENDING
        authorization, and its guid opens the visit without an OTP (verified on UAT 2026-09-22).
        """
        if not self.guid:
            raise ValueError("authorization has no guid to use as consent proof")
        return BiometricGuid(self.guid)

    @property
    def is_pending(self) -> bool:
        return self.status == AuthorizationStatus.PENDING

    @property
    def is_verified(self) -> bool:
        """Consent is proven and the visit can be opened.

        `AUTHORIZED_PENDING_VISIT` counts: SHA has matched the beneficiary and is waiting for us to open the
        visit. Treating it as unfinished leaves a verified patient standing at the desk.
        """
        return self.status in (AuthorizationStatus.AUTHORIZED, AuthorizationStatus.AUTHORIZED_PENDING_VISIT)

    @property
    def capture_url(self) -> str:
        """The eKYC page to send the beneficiary to, or empty on the OTP path."""
        return self.verification.request_url if self.verification else ""

    @property
    def needs_preauth(self) -> bool:
        """Either SHA's own flag or any authorized intervention asking for one.

        An `or`, not a choice between them. Reading "no pre-auth needed" when one is lets a line be billed
        that SHA will refuse; the opposite merely prompts for something already in hand.
        """
        return self.server_needs_preauth or any(i.needs_preauth for i in self.interventions)

    def as_biometric_proof(self) -> BiometricGuid:
        return BiometricGuid(self.guid)
