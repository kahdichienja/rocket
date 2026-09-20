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
class AuthorizedIntervention:
    code: InterventionCode
    name: str
    needs_preauth: bool
    payment_mechanism: PaymentMechanism | None
    sub_benefit_code: str = ""


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
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def is_pending(self) -> bool:
        return self.status == AuthorizationStatus.PENDING

    @property
    def needs_preauth(self) -> bool:
        return any(i.needs_preauth for i in self.interventions)

    def as_biometric_proof(self) -> BiometricGuid:
        return BiometricGuid(self.guid)
