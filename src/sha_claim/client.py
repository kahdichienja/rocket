"""Composition root and public facade."""

from __future__ import annotations

import base64
import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from types import TracebackType
from typing import Any, Self

import httpx

from sha_claim.adapters.wire.http_gateways import (
    HttpConsentGateway,
    HttpEligibilityGateway,
    HttpEmergencyGateway,
    HttpFileGateway,
    HttpPreauthGateway,
    HttpPrescriptionGateway,
    HttpVirtualClaimGateway,
)
from sha_claim.adapters.wire.transport import Transport
from sha_claim.domain.benefits import (
    BedOccupancy,
    BenefitPackage,
    InterventionCoverage,
    SubBenefit,
    UtilizationBalance,
)
from sha_claim.domain.codes import InterventionCode
from sha_claim.domain.consent import Authorization, ConsentProof, Otp
from sha_claim.domain.eligibility import Eligibility
from sha_claim.domain.emergency import EmergencyCase, EmergencyProtocol
from sha_claim.domain.enums import BroughtBy, IdentificationType, ModeOfArrival, ServiceType
from sha_claim.domain.files import DownloadLink, StoredFile
from sha_claim.domain.identifiers import ConsentToken, FacilityCode, FileId, PatientId
from sha_claim.domain.identity import BearerToken, Identity
from sha_claim.domain.practitioner import PractitionerRef
from sha_claim.errors import RequestValidationError, Violation
from sha_claim.events import EventHook
from sha_claim.facility import FacilityScope
from sha_claim.infrastructure.auth import OAuth2ClientCredentials
from sha_claim.infrastructure.clock import SystemClock
from sha_claim.infrastructure.retry import DEFAULT_RETRY, RetryPolicy
from sha_claim.infrastructure.transport import HttpxTransport
from sha_claim.ports.claim_gateways import ClaimGateways
from sha_claim.ports.clock import Clock
from sha_claim.ports.consent_gateway import ConsentGateway
from sha_claim.ports.eligibility_gateway import EligibilityGateway
from sha_claim.ports.file_gateway import FileGateway
from sha_claim.ports.token_provider import TokenProvider
from sha_claim.session import ClaimSession
from sha_claim.settings import SHASettings
from sha_claim.use_cases.capture_consent import CaptureConsent
from sha_claim.use_cases.open_visit import OpenVisit
from sha_claim.use_cases.verify_eligibility import VerifyEligibility


class AuthResource:
    """Credentials and identity. The SDK authenticates implicitly; this is for health checks and 'which facility am I'."""

    def __init__(self, tokens: TokenProvider) -> None:
        self._tokens = tokens

    async def identity(self) -> Identity:
        """`POST /tenants/token` (cached) → the facility/tenant the credentials belong to. Never returns the token."""
        token = await self._tokens.access_token()
        return _identity_from_jwt(token)

    async def check(self) -> bool:
        """True if a token can be obtained. Raises AuthenticationError/TransportError otherwise."""
        await self._tokens.access_token()
        return True

    async def token(self) -> BearerToken:
        """The raw grant (`access_token`, remaining `expires_in`, `token_type`), from the cache when still valid.

        For callers that must hit the HIE directly (legacy code, bots). Prefer the SDK's own methods:
        they never need the token.
        """
        token = await self._tokens.access_token()
        remaining = _identity_from_jwt(token).seconds_remaining
        return BearerToken(access_token=token, expires_in=remaining if remaining is not None else 0)


def _identity_from_jwt(token: str) -> Identity:
    claims: dict[str, object] = {}
    parts = token.split(".")
    if len(parts) == 3:
        try:
            payload = parts[1] + "=" * (-len(parts[1]) % 4)
            decoded = json.loads(base64.urlsafe_b64decode(payload))
            if isinstance(decoded, dict):
                claims = decoded
        except (ValueError, UnicodeDecodeError):
            claims = {}
    facility = str(claims.get("facility_id") or "").strip()
    return Identity(
        facility=FacilityCode(facility) if facility else None,
        facility_id_type=str(claims.get("facility_id_type") or ""),
        tenant_id=str(claims.get("tenant_id") or ""),
        tenant_name=str(claims.get("tenant_name") or ""),
        issuer=str(claims.get("iss") or ""),
        client_id=str(claims.get("client_id") or claims.get("azp") or ""),
        issued_at=_epoch(claims.get("iat")),
        expires_at=_epoch(claims.get("exp")),
    )


def _epoch(value: object) -> datetime | None:
    return datetime.fromtimestamp(int(value), tz=UTC) if isinstance(value, (int, float)) else None


class EligibilityResource:
    """Who is covered, and for what. All reads; safe to retry."""

    def __init__(self, gateway: EligibilityGateway) -> None:
        self._gateway = gateway
        self._verify = VerifyEligibility(gateway)

    async def check(self, identification_number: str, identification_type: IdentificationType) -> Eligibility:
        """`GET /patients/eligibility` — is this person an SHA beneficiary, and under which schemes?"""
        return await self._verify.execute(identification_number, identification_type)

    async def benefits(self, patient: PatientId | str) -> tuple[BenefitPackage, ...]:
        """`GET /patients/benefits` — top-level packages (SHA-08, SHA-12, …) available to the patient."""
        return await self._gateway.benefits(PatientId.of(patient))

    async def sub_benefits(self, patient: PatientId | str) -> tuple[SubBenefit, ...]:
        """`GET /patients/sub-benefits` — sub-benefit codes (SHA-12-SC-01, …) with access points."""
        return await self._gateway.sub_benefits(PatientId.of(patient))

    async def interventions(
        self, patient: PatientId | str, sub_benefit_code: str
    ) -> tuple[InterventionCoverage, ...]:
        """`GET /patients/benefits/interventions` — billable interventions under a sub-benefit, with tariffs and preauth flags."""
        return await self._gateway.interventions(PatientId.of(patient), sub_benefit_code)

    async def utilization(
        self, patient: PatientId | str, intervention: InterventionCode | str
    ) -> tuple[UtilizationBalance, ...]:
        """`GET /patients/benefits/utilization` — remaining limits for one intervention.

        One record per limit scope (individual, household, fund …); UAT returns a bare list.
        """
        return await self._gateway.utilization(PatientId.of(patient), InterventionCode.of(intervention))

    async def pomsf_balances(
        self, patient: PatientId | str, policy_year: str, *, principal_member_number: str | None = None
    ) -> Mapping[str, Any]:
        """`GET /patients/pomsf-balances` — Public Officers Medical Scheme Fund balances, raw payload."""
        return await self._gateway.pomsf_balances(PatientId.of(patient), policy_year, principal_member_number)

    async def bed_occupancy(self, facility: FacilityCode | str) -> BedOccupancy:
        """`GET /facilities/{code}/beds/occupancy`."""
        return await self._gateway.bed_occupancy(FacilityCode.of(facility))


class FilesResource:
    """Standalone uploads. Claim attachments normally go inline via `ClaimSession.attach`."""

    def __init__(self, gateway: FileGateway) -> None:
        self._gateway = gateway

    async def upload(
        self, filename: str, content: bytes, content_type: str = "application/octet-stream"
    ) -> StoredFile:
        return await self._gateway.upload(filename, content, content_type)

    async def download_link(self, file_id: FileId | str) -> DownloadLink:
        return await self._gateway.download_link(FileId.of(file_id))


class ConsentResource:
    """Patient consent. `authorize` sends the OTP; `open_visit` (on `claims`) consumes it."""

    def __init__(self, gateway: ConsentGateway) -> None:
        self._gateway = gateway
        self._capture = CaptureConsent(gateway)

    async def authorize(
        self,
        patient: PatientId | str,
        service_type: ServiceType,
        interventions: Sequence[InterventionCode | str],
        otp: Otp | None = None,
    ) -> Authorization:
        """`POST /claims/authorize` — creates a PENDING authorization and triggers the OTP to the beneficiary.

        Use `InterventionCoverage.service_type_for_authorization` to pick `service_type`: CAPITATION
        interventions are rejected under OUTPATIENT.
        """
        codes = [InterventionCode.of(c) for c in interventions]
        return await self._capture.execute(PatientId.of(patient), service_type, codes, otp)

    async def send_otp(
        self, patient: PatientId | str, interventions: Sequence[InterventionCode | str]
    ) -> str:
        """`POST /claims/otp` — (re)send the visit OTP to the beneficiary's registered phone.

        `authorize` already triggers the first OTP; use this to resend. On UAT the response message
        contains the OTP itself (sandbox behaviour) — never rely on that in production.
        """
        codes = [InterventionCode.of(c) for c in interventions]
        return await self._gateway.send_otp(PatientId.of(patient), codes)

    async def get(
        self, token: str, guid: str, patient: PatientId | str | None = None
    ) -> Authorization | None:
        """`GET /claims/authorizations` — re-read an authorization; `None` if the server knows nothing."""
        return await self._gateway.get(token, guid, PatientId.of(patient) if patient else None)

    async def list(self, patient: PatientId | str) -> tuple[Authorization, ...]:
        """`GET /claims/authorizations?beneficiary_code=…` — every authorization for a beneficiary (undocumented; live on UAT).

        Use it to find a dangling PENDING authorization (which blocks the OTP path) and `reject` it.
        """
        return await self._gateway.list(PatientId.of(patient))

    async def reject(self, token: str) -> None:
        """`POST /claims/authorizations/{token}/reject` — close a pending authorization."""
        await self._gateway.reject(token)


class ClaimsResource:
    """Virtual claims. `open_visit` starts one; `resume` re-attaches to one you already hold the token for."""

    def __init__(self, gateways: ClaimGateways) -> None:
        self._gateways = gateways
        self._open_visit = OpenVisit(gateways.claims)

    async def open_visit(
        self,
        patient: PatientId | str,
        service_type: ServiceType,
        interventions: Sequence[InterventionCode | str],
        proof: ConsentProof | Authorization,
    ) -> ClaimSession:
        """`POST /claims/visit` — opens the server-side virtual claim and returns a session bound to its consent token.

        `proof` is the OTP the beneficiary read out, a `BiometricGuid`/`MatchId` from the biometric path, or
        the `Authorization` that `consent.authorize()` returned (its guid is used).
        """
        codes = [InterventionCode.of(c) for c in interventions]
        claim = await self._open_visit.execute(
            PatientId.of(patient),
            service_type,
            codes,
            proof.proof if isinstance(proof, Authorization) else proof,
        )
        return ClaimSession(self._gateways, claim.consent_token, claim)

    def resume(self, consent_token: ConsentToken | str) -> ClaimSession:
        """Re-attach to an existing virtual claim (e.g. from a token persisted by NaCare). No network call."""
        return ClaimSession(self._gateways, ConsentToken.of(consent_token))


class EmergencyResource:
    """Emergency case claims: opened without prior OTP consent, billed by protocol."""

    def __init__(self, gateways: ClaimGateways) -> None:
        self._gateways = gateways

    async def open_case(
        self,
        attending: PractitionerRef,
        reference_number: str,
        brought_by: BroughtBy,
        mode_of_arrival: ModeOfArrival,
        interventions: Sequence[InterventionCode | str],
        *,
        patient: PatientId | str | None = None,
        otp: Otp | None = None,
        notes: str,
    ) -> ClaimSession:
        """`POST /claims/emergency` — `patient=None` for an unidentified casualty.

        `notes` is required by SHA. Interventions must belong to the emergency fund (see
        `InterventionCoverage.is_emergency`); the facility must be accredited for emergency services.
        """
        try:
            case = EmergencyCase(
                attending,
                reference_number,
                brought_by,
                mode_of_arrival,
                tuple(InterventionCode.of(c) for c in interventions),
                PatientId.of(patient) if patient is not None else None,
                otp,
                notes,
            )
        except ValueError as exc:
            raise RequestValidationError([Violation("emergency", str(exc))]) from exc
        claim = await self._gateways.emergency.open_case(case)
        return ClaimSession(self._gateways, claim.consent_token, claim)

    async def protocols(
        self, intervention: InterventionCode | str, *, active: bool = True
    ) -> tuple[EmergencyProtocol, ...]:
        """`GET /claims/emergency/protocols` — billable treatment protocols for an intervention."""
        return await self._gateways.emergency.protocols(InterventionCode.of(intervention), active)


class AsyncSHAClient:
    """Entry point. Use as `async with AsyncSHAClient.from_env() as sha:`.

    Every collaborator is injectable for tests; defaults wire httpx + OAuth2 + retries.
    """

    def __init__(
        self,
        settings: SHASettings,
        *,
        transport: Transport | None = None,
        tokens: TokenProvider | None = None,
        clock: Clock | None = None,
        retry: RetryPolicy = DEFAULT_RETRY,
        http: httpx.AsyncClient | None = None,
        on_event: EventHook | None = None,
    ) -> None:
        self.settings = settings
        self._clock = clock or SystemClock()
        self._owns_http = http is None and transport is None
        self._http = http or httpx.AsyncClient(headers={"User-Agent": "sha-claim/0.1"})
        self._tokens = tokens or OAuth2ClientCredentials(
            token_url=f"{settings.api_root}/tenants/token",
            client_id=settings.client_id,
            client_secret=settings.client_secret,
            http=self._http,
            clock=self._clock,
            expiry_skew_seconds=settings.token_expiry_skew_seconds,
            on_event=on_event,
        )
        self._transport: Transport = transport or HttpxTransport(
            http=self._http,
            api_root=settings.api_root,
            tokens=self._tokens,
            timeouts=settings.timeouts,
            retry=retry,
            on_event=on_event,
            clock=self._clock,
            default_facility=FacilityScope(FacilityCode(settings.facility), settings.facility_id_type)
            if settings.facility
            else None,
        )
        self.auth = AuthResource(self._tokens)
        self.eligibility = EligibilityResource(HttpEligibilityGateway(self._transport))
        self.consent = ConsentResource(HttpConsentGateway(self._transport))
        gateways = ClaimGateways(
            claims=HttpVirtualClaimGateway(self._transport),
            preauths=HttpPreauthGateway(self._transport),
            prescriptions=HttpPrescriptionGateway(self._transport),
            emergency=HttpEmergencyGateway(self._transport),
        )
        self.claims = ClaimsResource(gateways)
        self.emergency = EmergencyResource(gateways)
        self.files = FilesResource(HttpFileGateway(self._transport))

    @classmethod
    def from_env(cls, *, on_event: EventHook | None = None) -> Self:
        return cls(SHASettings.from_env(), on_event=on_event)

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        await self.aclose()
