"""httpx-backed Transport: bearer injection, one 401 refresh-and-replay, idempotent retries, error mapping."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable

import httpx

from sha_claim.adapters.wire.transport import TimeoutKind, WireRequest, WireResponse
from sha_claim.errors import TransportError
from sha_claim.infrastructure.logging import logger
from sha_claim.infrastructure.retry import DEFAULT_RETRY, RetryPolicy
from sha_claim.ports.token_provider import TokenProvider
from sha_claim.settings import Timeouts

Sleeper = Callable[[float], Awaitable[None]]


class HttpxTransport:
    def __init__(
        self,
        *,
        http: httpx.AsyncClient,
        api_root: str,
        tokens: TokenProvider,
        timeouts: Timeouts,
        retry: RetryPolicy = DEFAULT_RETRY,
        sleep: Sleeper = asyncio.sleep,
        rng: random.Random | None = None,
    ) -> None:
        self._http = http
        self._root = api_root.rstrip("/")
        self._tokens = tokens
        self._timeouts = timeouts
        self._retry = retry
        self._sleep = sleep
        self._rng = rng

    async def send(self, request: WireRequest) -> WireResponse:
        delays = list(self._retry.delays(self._rng)) if request.idempotent else []
        attempt = 0
        while True:
            try:
                response = await self._send_once(request)
            except httpx.TimeoutException as exc:
                if attempt >= len(delays):
                    raise TransportError(f"timeout calling {request.method} {request.path}: {exc}") from exc
            except httpx.HTTPError as exc:
                if attempt >= len(delays):
                    raise TransportError(
                        f"network error calling {request.method} {request.path}: {exc}"
                    ) from exc
            else:
                if not (self._retry.is_transient_status(response.status) and attempt < len(delays)):
                    return response
            await self._sleep(delays[attempt])
            attempt += 1

    async def _send_once(self, request: WireRequest) -> WireResponse:
        response = await self._dispatch(request)
        if response.status == 401 and request.authenticated:
            await self._tokens.invalidate()
            response = await self._dispatch(request)
        return response

    async def _dispatch(self, request: WireRequest) -> WireResponse:
        headers: dict[str, str] = {}
        if request.authenticated:
            headers["Authorization"] = f"Bearer {await self._tokens.access_token()}"
        timeout = self._timeout_for(request.timeout)
        raw = await self._http.request(
            request.method,
            f"{self._root}{request.path}",
            params=dict(request.params) or None,
            json=request.json,
            data=dict(request.form) if request.form else None,
            files=dict(request.files) if request.files else None,
            headers=headers,
            timeout=timeout,
        )
        logger.debug(
            "sha_claim: %s %s -> %s (x-request-id=%s)",
            request.method,
            request.path,
            raw.status_code,
            raw.headers.get("x-request-id"),
        )
        return WireResponse(raw.status_code, dict(raw.headers), raw.content)

    def _timeout_for(self, kind: TimeoutKind) -> httpx.Timeout:
        read = self._timeouts.upload if kind is TimeoutKind.UPLOAD else self._timeouts.read
        return httpx.Timeout(
            connect=self._timeouts.connect, read=read, write=read, pool=self._timeouts.connect
        )
