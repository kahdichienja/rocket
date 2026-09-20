"""OAuth2 client-credentials against POST {base}/api/v1/tenants/token (form-urlencoded)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx

from sha_claim.errors import AuthenticationError, TransportError
from sha_claim.infrastructure.logging import logger
from sha_claim.ports.clock import Clock


@dataclass(frozen=True, slots=True)
class _CachedToken:
    value: str
    expires_at_monotonic: float


class OAuth2ClientCredentials:
    def __init__(
        self,
        *,
        token_url: str,
        client_id: str,
        client_secret: str,
        http: httpx.AsyncClient,
        clock: Clock,
        expiry_skew_seconds: int = 60,
    ) -> None:
        self._token_url = token_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._http = http
        self._clock = clock
        self._skew = expiry_skew_seconds
        self._cached: _CachedToken | None = None
        self._lock = asyncio.Lock()

    async def access_token(self) -> str:
        cached = self._cached
        if cached and cached.expires_at_monotonic > self._clock.monotonic():
            return cached.value
        async with self._lock:  # single-flight: concurrent callers share one refresh
            cached = self._cached
            if cached and cached.expires_at_monotonic > self._clock.monotonic():
                return cached.value
            self._cached = await self._fetch()
            return self._cached.value

    async def invalidate(self) -> None:
        self._cached = None

    async def _fetch(self) -> _CachedToken:
        try:
            response = await self._http.post(
                self._token_url,
                data={"client_id": self._client_id, "client_secret": self._client_secret},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.HTTPError as exc:
            raise TransportError(f"token endpoint unreachable: {exc}") from exc
        if response.status_code != 200:
            detail = _safe_message(response)
            raise AuthenticationError(detail, status=response.status_code, error=response.reason_phrase)
        payload = response.json()
        token = payload.get("access_token")
        expires_in = int(payload.get("expires_in", 0))
        if not token or expires_in <= 0:
            raise AuthenticationError("token response missing access_token/expires_in", status=200)
        logger.info("sha_claim: obtained access token (expires_in=%ss)", expires_in)
        return _CachedToken(token, self._clock.monotonic() + max(expires_in - self._skew, 1))


def _safe_message(response: httpx.Response) -> str:
    try:
        body = response.json()
        return str(body.get("message") or body.get("error") or response.text[:200])
    except ValueError:
        return response.text[:200]
