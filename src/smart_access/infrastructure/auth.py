"""Smart Applications OAuth2 password-grant token provider."""

from __future__ import annotations

import asyncio
import base64
from datetime import datetime

import httpx

from smart_access.adapters.wire.schemas.token import TokenResponseWire
from smart_access.errors import SmartAuthenticationError, SmartTransportError
from smart_access.infrastructure.clock import SystemClock
from smart_access.infrastructure.logging import LOGGER
from smart_access.ports.clock import Clock
from smart_access.ports.token_provider import TokenProvider


class SmartOAuth2TokenProvider(TokenProvider):
    """Acquires and caches Smart OAuth2 bearer tokens via password grant with single-flight refresh."""

    def __init__(
        self,
        token_url: str,
        provider_key: str,
        username: str,
        password: str,
        client_id: str = "",
        client_secret: str = "",
        language: str = "en",
        http: httpx.AsyncClient | None = None,
        clock: Clock | None = None,
        expiry_skew_seconds: int = 60,
    ) -> None:
        self._token_url = token_url
        self._provider_key = provider_key
        self._username = username
        self._password = password
        self._client_id = client_id
        self._client_secret = client_secret
        self._language = language
        self._http = http
        self._owns_http = http is None
        self._clock = clock or SystemClock()
        self._skew_seconds = expiry_skew_seconds

        self._lock = asyncio.Lock()
        self._cached_token: str | None = None
        self._expires_at: datetime | None = None

    async def access_token(self) -> str:
        async with self._lock:
            if self._cached_token and self._expires_at and self._clock.now() < self._expires_at:
                return self._cached_token

            token, expires_in = await self._fetch_new_token()
            self._cached_token = token
            # skew buffer
            effective_lifetime = max(5, expires_in - self._skew_seconds)
            from datetime import timedelta

            self._expires_at = self._clock.now() + timedelta(seconds=effective_lifetime)
            return self._cached_token

    async def invalidate(self) -> None:
        async with self._lock:
            self._cached_token = None
            self._expires_at = None

    async def _fetch_new_token(self) -> tuple[str, int]:
        client = self._http or httpx.AsyncClient()
        headers: dict[str, str] = {
            "Content-Type": "application/x-www-form-urlencoded",
            "provider-key": self._provider_key,
            "accept-language": self._language,
        }

        if self._client_id and self._client_secret:
            credentials = f"{self._client_id}:{self._client_secret}".encode()
            b64_creds = base64.b64encode(credentials).decode("ascii")
            headers["Authorization"] = f"Basic {b64_creds}"

        data = {
            "grant_type": "password",
            "username": self._username or self._client_id,
            "password": self._password or self._client_secret,
        }

        try:
            resp = await client.post(self._token_url, headers=headers, data=data)
        except httpx.TransportError as exc:
            LOGGER.error("Failed to connect to Smart token endpoint: %s", exc)
            raise SmartTransportError(f"Smart token request failed: {exc}") from exc
        finally:
            if self._owns_http and not self._http:
                await client.aclose()

        if resp.status_code != 200:
            LOGGER.error("Smart token negotiation failed with status %d: %s", resp.status_code, resp.text)
            raise SmartAuthenticationError(
                f"Smart OAuth authentication failed: {resp.status_code} {resp.text}",
                status_code=resp.status_code,
                response_body=resp.text,
            )

        try:
            payload = resp.json()
            wire = TokenResponseWire.model_validate(payload)
            return wire.access_token, wire.expires_in
        except Exception as exc:
            LOGGER.error("Failed to parse Smart token response: %s", exc)
            raise SmartAuthenticationError(f"Invalid Smart token response: {exc}") from exc
