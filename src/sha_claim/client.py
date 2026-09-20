"""Composition root and public facade."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
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
from sha_claim.domain.practitioner import PractitionerRef
from sha_claim.errors import RequestValidationError, Violation
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
    ) -> UtilizationBalance:
        """`GET /patients/benefits/utilization` — remaining limits for one intervention. (Returned 400 upstream on UAT, 2026-09.)"""
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

    async def get(
        self, token: str, guid: str, patient: PatientId | str | None = None
    ) -> Authorization | None:
        """`GET /claims/authorizations` — re-read an authorization; `None` if the server knows nothing."""
        return await self._gateway.get(token, guid, PatientId.of(patient) if patient else None)

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
        proof: ConsentProof,
    ) -> ClaimSession:
        """`POST /claims/visit` — opens the server-side virtual claim and returns a session bound to its consent token."""
        codes = [InterventionCode.of(c) for c in interventions]
        claim = await self._open_visit.execute(PatientId.of(patient), service_type, codes, proof)
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
        notes: str = "",
    ) -> ClaimSession:
        """`POST /claims/emergency` — `patient=None` for an unidentified casualty."""
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
        )
        self._transport: Transport = transport or HttpxTransport(
            http=self._http,
            api_root=settings.api_root,
            tokens=self._tokens,
            timeouts=settings.timeouts,
            retry=retry,
        )
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
    def from_env(cls) -> Self:
        return cls(SHASettings.from_env())

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        await self.aclose()
