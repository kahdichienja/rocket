"""httpx-backed Transport: bearer injection, one 401 refresh-and-replay, idempotent retries, error mapping."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from sha_claim.adapters.wire.transport import TimeoutKind, WireRequest, WireResponse
from sha_claim.errors import TransportError
from sha_claim.events import EventHook, SDKEvent
from sha_claim.facility import FacilityScope, current_facility
from sha_claim.infrastructure.clock import SystemClock
from sha_claim.infrastructure.logging import logger, redact
from sha_claim.infrastructure.retry import DEFAULT_RETRY, RetryPolicy
from sha_claim.ports.clock import Clock
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
        on_event: EventHook | None = None,
        clock: Clock | None = None,
        default_facility: FacilityScope | None = None,
    ) -> None:
        self._http = http
        self._root = api_root.rstrip("/")
        self._tokens = tokens
        self._timeouts = timeouts
        self._retry = retry
        self._sleep = sleep
        self._rng = rng
        self._on_event = on_event
        self._default_facility = default_facility
        self._clock: Clock = clock or SystemClock()

    async def send(self, request: WireRequest) -> WireResponse:
        delays = list(self._retry.delays(self._rng)) if request.idempotent else []
        attempt = 0
        while True:
            started = self._clock.monotonic()
            try:
                response = await self._send_once(request)
            except httpx.TimeoutException as exc:
                self._emit(request, None, started, attempt, error=exc)
                if attempt >= len(delays):
                    raise TransportError(f"timeout calling {request.method} {request.path}: {exc}") from exc
            except httpx.HTTPError as exc:
                self._emit(request, None, started, attempt, error=exc)
                if attempt >= len(delays):
                    raise TransportError(
                        f"network error calling {request.method} {request.path}: {exc}"
                    ) from exc
            else:
                self._emit(request, response, started, attempt)
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
        scope = current_facility() or self._default_facility
        if scope is not None:
            headers.update(scope.headers())  # both headers or neither — DHA ignores a lone one
        timeout = self._timeout_for(request.timeout)
        data, files = _encode_body(request)
        raw = await self._http.request(
            request.method,
            f"{self._root}{request.path}",
            params=dict(request.params) or None,
            json=request.json,
            data=data,
            files=files,
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

    def _emit(
        self,
        request: WireRequest,
        response: WireResponse | None,
        started: float,
        attempt: int,
        error: Exception | None = None,
    ) -> None:
        if self._on_event is None:
            return
        event = SDKEvent(
            occurred_at=self._clock.now(),
            method=request.method.upper(),
            path=request.path,
            status=response.status if response else None,
            duration_ms=round((self._clock.monotonic() - started) * 1000, 1),
            attempt=attempt + 1,
            trace_id=_trace_id(response),
            consent_token=_redacted_token(request),
            error=type(error).__name__ if error else None,
        )
        try:
            self._on_event(event)
        except Exception:  # noqa: BLE001 — a broken observer must never break a claim call
            logger.exception("sha_claim: on_event hook raised; ignoring")


def _encode_body(request: WireRequest) -> tuple[dict[str, str] | None, dict[str, Any] | None]:
    """Plain form → urlencoded; multipart → every field as a part (filename-less parts for scalars)."""
    form = dict(request.form or {})
    files: dict[str, Any] = dict(request.files or {})
    if not (request.multipart or files):
        return (form or None), None
    parts: dict[str, Any] = {k: (None, v) for k, v in form.items()}
    parts.update(files)
    return None, parts


def _trace_id(response: WireResponse | None) -> str | None:
    if response is None:
        return None
    if response.status >= 400:
        try:
            payload = response.json()
            if isinstance(payload, dict) and payload.get("trace_id"):
                return str(payload["trace_id"])
        except ValueError:
            pass
    return response.request_id


def _redacted_token(request: WireRequest) -> str | None:
    for source in (request.json if isinstance(request.json, dict) else None, request.form, request.params):
        if source and (raw := source.get("consent_token")):
            value = str(raw)
            return f"{value[:4]}…{value[-2:]}" if len(value) > 8 else "•" * len(value)
    return redact(request.path) if "/authorizations/" in request.path else None
