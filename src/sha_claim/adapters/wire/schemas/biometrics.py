"""Payloads from the minors fingerprint endpoints.

`WireModel` accepts camelCase or snake_case and tolerates unknown fields, so these stay narrow: only what
the domain reads is modelled, and `unmodelled()` keeps the rest for a caller that needs to see what DHA
actually sent. That matters more than usual here — the callback payloads are undocumented, and the first
thing anyone debugging one will want is the part we did not name.
"""

from __future__ import annotations

from pydantic import Field

from sha_claim.adapters.wire.schemas.common import WireModel


class CaptureJobWire(WireModel):
    """`202` from an enrolment or verification capture."""

    job_id: str = ""
    next_action: str = ""
    message: str = ""


class MatchAttemptWire(WireModel):
    """`202` from `POST /biometrics/matches`."""

    match_id: str = ""
    next_action: str = ""
    message: str = ""


class MatchResultWire(WireModel):
    """`GET /biometrics/matches/{match_id}` — the reconciliation read."""

    match_id: str = ""
    status: str = ""
    error_code: str = ""
    message: str = ""


class EnrollmentStatusWire(WireModel):
    """`GET /biometrics/enrollment-status`.

    `enrollment_status` is DHA's name for the *overall* state (`fully_enrolled`, `partially_enrolled`, or
    empty). It is not a list, despite sitting beside two of them — the domain renames it `state` so a reader
    cannot mistake it for the positions.
    """

    beneficiary_code: str = ""
    enrollment_status: str = ""
    verified: list[int] = Field(default_factory=list)
    non_verified: list[int] = Field(default_factory=list)
    total: int = 0
