"""Health-worker identification as the API expects it."""

from __future__ import annotations

from dataclasses import dataclass

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
