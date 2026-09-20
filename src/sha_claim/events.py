"""Emit-only observability. The SDK stores nothing; your callback decides what to persist, count or alert on."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SDKEvent:
    """One HTTP attempt made by the SDK.

    `consent_token` is already redacted (`CR76…G6`) — safe to log. `status` is None when no response
    arrived (timeout, connection error); `error` then names the exception type.
    """

    occurred_at: datetime
    method: str
    path: str
    status: int | None
    duration_ms: float
    attempt: int
    trace_id: str | None = None
    consent_token: str | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.status is not None and self.status < 400

    @property
    def operation(self) -> str:
        return f"{self.method} {self.path}"


EventHook = Callable[[SDKEvent], None]
