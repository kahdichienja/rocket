"""Composition root and public facade."""

from __future__ import annotations

from types import TracebackType
from typing import Self

import httpx

from sha_claim.adapters.wire.http_gateways import HttpEligibilityGateway
from sha_claim.adapters.wire.transport import Transport
from sha_claim.domain.eligibility import Eligibility
from sha_claim.domain.enums import IdentificationType
from sha_claim.infrastructure.auth import OAuth2ClientCredentials
from sha_claim.infrastructure.clock import SystemClock
from sha_claim.infrastructure.retry import DEFAULT_RETRY, RetryPolicy
from sha_claim.infrastructure.transport import HttpxTransport
from sha_claim.ports.clock import Clock
from sha_claim.ports.token_provider import TokenProvider
from sha_claim.settings import SHASettings
from sha_claim.use_cases.verify_eligibility import VerifyEligibility


class EligibilityResource:
    def __init__(self, verify: VerifyEligibility) -> None:
        self._verify = verify

    async def check(self, identification_number: str, identification_type: IdentificationType) -> Eligibility:
        """`GET /patients/eligibility` — who is this person to SHA, and what covers them?"""
        return await self._verify.execute(identification_number, identification_type)


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
        self.eligibility = EligibilityResource(VerifyEligibility(HttpEligibilityGateway(self._transport)))

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
