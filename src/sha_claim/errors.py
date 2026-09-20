"""Exception vocabulary of the SDK.

Every failure crossing the SDK boundary is one of these. httpx exceptions and raw
server envelopes never escape; adapters translate them here.
"""

from __future__ import annotations

from dataclasses import dataclass


class SHAClaimError(Exception):
    """Base class for every error raised by sha_claim."""


class ConfigurationError(SHAClaimError):
    """Settings are missing or invalid. Raised at construction, never lazily."""


@dataclass(frozen=True, slots=True)
class Violation:
    field: str
    message: str

    def __str__(self) -> str:
        return f"{self.field}: {self.message}"


class RequestValidationError(SHAClaimError, ValueError):
    """The request would certainly be rejected by the server; nothing was sent."""

    def __init__(self, violations: list[Violation] | tuple[Violation, ...]) -> None:
        self.violations = tuple(violations)
        super().__init__("; ".join(str(v) for v in self.violations))


class ServerError(SHAClaimError):
    """Base for errors the server reported via its `{error, message, trace_id}` envelope."""

    def __init__(self, message: str, *, status: int, error: str = "", trace_id: str | None = None) -> None:
        self.status = status
        self.error = error
        self.trace_id = trace_id
        super().__init__(f"{status} {error}: {message}" + (f" [trace_id={trace_id}]" if trace_id else ""))


class AuthenticationError(ServerError):
    """Token could not be obtained, or the server rejected it after one refresh (401)."""


class PermissionDeniedError(ServerError):
    """403 — the tenant is not allowed to perform this operation."""


class BadRequestError(ServerError):
    """400 — server-side validation failed."""


class NotFoundError(ServerError):
    """404 — the resource does not exist."""


class TransportError(SHAClaimError):
    """Network failure, timeout or 5xx after the retry budget was exhausted."""

    def __init__(self, message: str, *, trace_id: str | None = None) -> None:
        self.trace_id = trace_id
        super().__init__(message)


class RateLimitedError(TransportError):
    """429 — carries the server's `Retry-After` when present."""

    def __init__(
        self, message: str, *, retry_after: float | None = None, trace_id: str | None = None
    ) -> None:
        self.retry_after = retry_after
        super().__init__(message, trace_id=trace_id)


class SubmissionOutcomeUnknownError(TransportError):
    """`submit` was sent but the outcome is unknown. Resolve with `preview` before retrying."""


class UnexpectedResponseError(SHAClaimError):
    """The server answered with a shape the SDK does not understand."""
