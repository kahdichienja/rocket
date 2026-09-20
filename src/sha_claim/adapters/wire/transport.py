"""The adapter layer's view of HTTP: a request spec in, a parsed response out. No httpx here."""

from __future__ import annotations

import json as _json
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol


class TimeoutKind(Enum):
    DEFAULT = "default"
    UPLOAD = "upload"


@dataclass(frozen=True, slots=True)
class WireRequest:
    method: str
    path: str  # relative to the API root, e.g. "/patients/eligibility"
    params: Mapping[str, str] = field(default_factory=dict)
    json: Any = None
    form: Mapping[str, str] | None = None
    files: Mapping[str, tuple[str, bytes, str]] | None = None  # name -> (filename, content, content_type)
    multipart: bool = (
        False  # force multipart/form-data even when `files` is empty (the API expects it for /claims/lines)
    )
    timeout: TimeoutKind = TimeoutKind.DEFAULT
    authenticated: bool = True
    retry_safe: bool = False  # opt a POST into retries (e.g. /claims/preview is a read)

    @property
    def idempotent(self) -> bool:
        """Safe to retry blindly. Only reads qualify; POST /claims/preview is opted in by the caller."""
        return self.retry_safe or self.method.upper() in {"GET", "HEAD"}


@dataclass(frozen=True, slots=True)
class WireResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes

    @property
    def request_id(self) -> str | None:
        return self.headers.get("x-request-id")

    def json(self) -> Any:
        if not self.body:
            return None
        return _json.loads(self.body)


class Transport(Protocol):
    async def send(self, request: WireRequest) -> WireResponse:
        """Deliver the request; raise TransportError/AuthenticationError on failure to obtain *any* response."""
        ...
