"""Facility scoping, per DHA: https://hie-docs.dha.go.ke/docs/authentication/process/facility-identification

Most claims/preauth/patient endpoints are scoped to one facility. A facility-specific credential already
carries `facility_id` in its token; a multi-facility integration (an HMIS) sends `X-Facility-Id` and
`X-Facility-Id-Type` on every request, and the headers override the token claim. Both headers or neither.

Two ways to set it, both stateless:
  * `SHASettings(facility=..., facility_id_type=...)` — a static default for the whole client.
  * `with facility_scope(code):` / `async with` — per call chain (e.g. one HTTP request in an HMIS). The
    scope is a contextvar, so concurrent requests on one shared client never see each other's facility.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass

from sha_claim.domain.identifiers import FacilityCode

FR_CODE = "fr-code"  # the only identifier type DHA currently supports


@dataclass(frozen=True, slots=True)
class FacilityScope:
    facility: FacilityCode
    id_type: str = FR_CODE

    def __post_init__(self) -> None:
        if not self.id_type.strip():
            raise ValueError("facility id_type cannot be empty")

    def headers(self) -> dict[str, str]:
        return {"X-Facility-Id": self.facility.value, "X-Facility-Id-Type": self.id_type}


_current: ContextVar[FacilityScope | None] = ContextVar("sha_claim_facility_scope", default=None)


def current_facility() -> FacilityScope | None:
    return _current.get()


@contextmanager
def facility_scope(facility: FacilityCode | str, id_type: str = FR_CODE) -> Iterator[FacilityScope]:
    """Scope every SDK call inside the block to `facility`. Nests; the innermost wins."""
    scope = FacilityScope(FacilityCode.of(facility), id_type)
    token = _current.set(scope)
    try:
        yield scope
    finally:
        _current.reset(token)


def activate_facility(facility: FacilityCode | str, id_type: str = FR_CODE) -> FacilityScope:
    """Set the scope for the current context without a `with` block (web-framework dependencies).

    Pair with `clear_facility()` in the request's teardown. Unlike `facility_scope()` this does not
    restore a previous value — it is for one-scope-per-request situations.
    """
    scope = FacilityScope(FacilityCode.of(facility), id_type)
    _current.set(scope)
    return scope


def clear_facility() -> None:
    _current.set(None)
