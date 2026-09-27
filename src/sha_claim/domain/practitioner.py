"""Health-worker identification as the API expects it."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from sha_claim.domain.codes import RegulationBody
from sha_claim.domain.enums import IdentificationType


@dataclass(frozen=True, slots=True)
class PractitionerRef:
    """Identifies a doctor by registration number (preferred) or a national identity document."""

    identification_number: str
    identification_type: IdentificationType
    regulation_body: RegulationBody

    def __post_init__(self) -> None:
        if not self.identification_number.strip():
            raise ValueError("identification_number cannot be empty")
        object.__setattr__(self, "identification_number", self.identification_number.strip())

    @classmethod
    def registered(cls, registration_number: str, body: RegulationBody) -> PractitionerRef:
        return cls(registration_number, IdentificationType.REGISTRATION_NUMBER, body)


@dataclass(frozen=True, slots=True)
class HealthWorker:
    """A practitioner as the Health Worker Registry holds them — `GET /api/v1/professionals`.

    The registry's own `id` is **not** the regulator's registration number, and the two are not
    interchangeable: a claim names a doctor by their KMPDC number, the Shared Health Record names them by
    this one. Resolving between them is the only reason this lookup exists.

    Beyond that, it is the cheapest way to check a registration number before it is sent. A typo in the
    pre-auth form is otherwise discovered by SHA, after submission, as a rejection.
    """

    registry_id: str
    """The Health Worker Registry identifier — `practitioner_id` on an SHR read."""
    registration_number: str
    name: str = ""
    regulator: str = ""
    status: str = ""
    specialty: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def is_active(self) -> bool:
        """Anything unrecognised is **not** active: claiming a struck-off practitioner is licensed is worse
        than saying we do not know."""
        return self.status.strip().upper() in {"ACTIVE", "VALID", "LICENSED", "REGISTERED"}
