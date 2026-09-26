"""SmartTransport implementation using httpx."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

import httpx

from smart_access.adapters.wire.error_translator import translate_error
from smart_access.adapters.wire.transport import Transport
from smart_access.errors import SmartTransportError
from smart_access.infrastructure.logging import LOGGER
from smart_access.infrastructure.retry import DEFAULT_RETRY, RetryPolicy
from smart_access.ports.token_provider import TokenProvider
from smart_access.settings import SmartTimeouts


class SmartTransport(Transport):
    """Authenticated HTTP transport executing calls against Smart Provider API."""

    def __init__(
        self,
        base_url: str,
        provider_key: str,
        tokens: TokenProvider,
        http: httpx.AsyncClient,
        timeouts: SmartTimeouts | None = None,
        language: str = "en",
        retry: RetryPolicy = DEFAULT_RETRY,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._provider_key = provider_key
        self._tokens = tokens
        self._http = http
        self._timeouts = timeouts or SmartTimeouts()
        self._language = language
        self._retry = retry

    @property
    def provider_key(self) -> str:
        return self._provider_key

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, str | int] | None = None,
        json_body: Any = None,
    ) -> Any:
        url = f"{self._base_url}{path}"
        timeout = httpx.Timeout(
            connect=self._timeouts.connect,
            read=self._timeouts.read,
            write=self._timeouts.upload,
            pool=self._timeouts.connect,
        )

        attempt = 1
        has_replayed_auth = False

        while True:
            token = await self._tokens.access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "provider-key": self._provider_key,
                "accept-language": self._language,
                "Content-Type": "application/json",
            }

            try:
                LOGGER.info("Smart Request: %s %s params=%s", method, url, params)
                resp = await self._http.request(
                    method,
                    url,
                    headers=headers,
                    params={k: str(v) for k, v in (params or {}).items() if v is not None},
                    json=json_body,
                    timeout=timeout,
                )
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                LOGGER.warning("Transport error calling %s %s (attempt %d): %s", method, url, attempt, exc)
                if self._retry.should_retry(method, None, attempt):
                    backoff = self._retry.backoff_for(attempt)
                    await asyncio.sleep(backoff)
                    attempt += 1
                    continue
                raise SmartTransportError(f"Network error calling Smart API: {exc}") from exc

            # 401 handling: refresh token once and retry
            if resp.status_code == 401 and not has_replayed_auth:
                LOGGER.info("Received 401 from Smart; invalidating token cache and retrying once...")
                has_replayed_auth = True
                inv = getattr(self._tokens, "invalidate", None)
                if callable(inv):
                    await inv()
                attempt += 1
                continue

            # Transient errors retry on safe reads
            if resp.status_code >= 400 and self._retry.should_retry(method, resp.status_code, attempt):
                LOGGER.warning(
                    "Retryable status %d from %s %s (attempt %d)", resp.status_code, method, url, attempt
                )
                backoff = self._retry.backoff_for(attempt)
                await asyncio.sleep(backoff)
                attempt += 1
                continue

            # Decode JSON or body
            data: Any = None
            if resp.content:
                try:
                    data = resp.json()
                except (ValueError, UnicodeDecodeError):
                    data = resp.text

            if resp.status_code not in (200, 201):
                LOGGER.error("Smart HTTP error %d from %s %s: %s", resp.status_code, method, url, data)
                raise translate_error(resp.status_code, data)

            LOGGER.info("Smart Response: %s %s status=%d", method, url, resp.status_code)
            return data
