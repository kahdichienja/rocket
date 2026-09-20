"""Composition root and public facade."""

from __future__ import annotations

from collections.abc import Sequence
from types import TracebackType
from typing import Self

import httpx

from sha_claim.adapters.wire.http_gateways import (
    HttpConsentGateway,
    HttpEligibilityGateway,
    HttpPreauthGateway,
    HttpVirtualClaimGateway,
)
from sha_claim.adapters.wire.transport import Transport
from sha_claim.domain.benefits import BenefitPackage, InterventionCoverage, SubBenefit
from sha_claim.domain.codes import InterventionCode
from sha_claim.domain.consent import Authorization, ConsentProof, Otp
from sha_claim.domain.eligibility import Eligibility
from sha_claim.domain.enums import IdentificationType, ServiceType
from sha_claim.domain.identifiers import ConsentToken, PatientId
from sha_claim.infrastructure.auth import OAuth2ClientCredentials
from sha_claim.infrastructure.clock import SystemClock
from sha_claim.infrastructure.retry import DEFAULT_RETRY, RetryPolicy
from sha_claim.infrastructure.transport import HttpxTransport
from sha_claim.ports.clock import Clock
from sha_claim.ports.consent_gateway import ConsentGateway
from sha_claim.ports.eligibility_gateway import EligibilityGateway
from sha_claim.ports.preauth_gateway import PreauthGateway
from sha_claim.ports.token_provider import TokenProvider
from sha_claim.ports.virtual_claim_gateway import VirtualClaimGateway
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

    def __init__(self, gateway: VirtualClaimGateway, preauths: PreauthGateway) -> None:
        self._gateway = gateway
        self._preauths = preauths
        self._open_visit = OpenVisit(gateway)

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
        return ClaimSession(self._gateway, self._preauths, claim.consent_token, claim)

    def resume(self, consent_token: ConsentToken | str) -> ClaimSession:
        """Re-attach to an existing virtual claim (e.g. from a token persisted by NaCare). No network call."""
        return ClaimSession(self._gateway, self._preauths, ConsentToken.of(consent_token))


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
        self.claims = ClaimsResource(
            HttpVirtualClaimGateway(self._transport), HttpPreauthGateway(self._transport)
        )

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
