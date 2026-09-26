"""Exception hierarchy for the Smart Access integration SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Violation:
    """A field-level validation failure detected locally."""

    field: str
    message: str


class SmartAccessError(Exception):
    """Base exception for all smart_access errors."""

    def __init__(self, message: str, *, status_code: int | None = None, response_body: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body


class SmartConfigurationError(SmartAccessError):
    """Raised when environment or provided settings are missing or invalid."""


class SmartValidationError(SmartAccessError):
    """Raised when request invariants are violated before hitting the network."""

    def __init__(self, violations: list[Violation]) -> None:
        self.violations = violations
        lines = [f" - {v.field}: {v.message}" for v in violations]
        super().__init__(f"Validation failed with {len(violations)} violation(s):\n" + "\n".join(lines))


class SmartAuthenticationError(SmartAccessError):
    """Raised when OAuth token negotiation fails or credentials are rejected."""


class SmartPermissionDeniedError(SmartAccessError):
    """HTTP 403: provider key or credentials lack permission."""


class SmartNotFoundError(SmartAccessError):
    """HTTP 404: requested visit session, member, or claim was not found."""


class SmartBadRequestError(SmartAccessError):
    """HTTP 400: Smart API rejected request parameters or payload."""


class SmartTransportError(SmartAccessError):
    """Network connection, timeout, or unexpected communication failure."""


class SmartRateLimitedError(SmartTransportError):
    """HTTP 429: Too Many Requests."""


class SmartClaimSubmissionError(SmartAccessError):
    """Raised when posting a claim fails or the claim is in an invalid state."""
