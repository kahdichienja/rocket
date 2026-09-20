"""Patient consent: how it is captured, and the authorization record the server returns."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class Otp:
    """One-time password delivered to the beneficiary's registered phone."""

    code: str

    def __post_init__(self) -> None:
        code = self.code.strip()
        if not code.isdigit():
            raise ValueError("OTP must be numeric")
        object.__setattr__(self, "code", code)

    def __repr__(self) -> str:
        return "Otp('••••')"


@dataclass(frozen=True, slots=True)
class BiometricGuid:
    """GUID of a completed biometric authorization (from POST /claims/authorize)."""

    guid: str

    def __post_init__(self) -> None:
        if not self.guid.strip():
            raise ValueError("authorization GUID cannot be empty")
        object.__setattr__(self, "guid", self.guid.strip())


ConsentProof = Otp | BiometricGuid


@dataclass(frozen=True, slots=True)
class Authorization:
    """Snapshot of an authorization record. Fields beyond these live in `extra` until modelled."""

    guid: str
    token: str
    status: str
    is_complete: bool
    is_open: bool
    needs_preauth: bool
    expiry: datetime | None = None
    beneficiary_name: str = ""
    payer_name: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def usable(self) -> bool:
        return self.is_complete and self.is_open
