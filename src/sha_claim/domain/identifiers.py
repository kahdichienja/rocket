"""Opaque identifiers the API hands out or expects. Each is a distinct type so they cannot be mixed up."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class Identifier:
    """Non-empty, whitespace-trimmed string wrapper. Subclass to name a concept."""

    value: str

    def __post_init__(self) -> None:
        cleaned = self.value.strip()
        if not cleaned:
            raise ValueError(f"{type(self).__name__} cannot be empty")
        object.__setattr__(self, "value", cleaned)

    def __str__(self) -> str:
        return self.value

    @classmethod
    def of(cls, value: str | Self) -> Self:
        return value if isinstance(value, cls) else cls(str(value))


@dataclass(frozen=True, slots=True)
class PatientId(Identifier):
    """Client Registry (CR) number of a beneficiary — `patient_id` throughout the API."""


@dataclass(frozen=True, slots=True)
class FacilityCode(Identifier):
    """Facility Registry ("FR") code, e.g. FID-47-105963-0. Usually implied by the credential."""


@dataclass(frozen=True, slots=True)
class ClaimGuid(Identifier):
    """Server-side GUID of a virtual claim."""


@dataclass(frozen=True, slots=True)
class LineGuid(Identifier):
    """GUID of a billing line inside a virtual claim."""


@dataclass(frozen=True, slots=True)
class AttachmentId(Identifier):
    """Identifier of an attachment on a virtual claim."""


@dataclass(frozen=True, slots=True)
class FileId(Identifier):
    """Identifier returned by the uploads endpoint."""


@dataclass(frozen=True, slots=True)
class InvoiceNumber(Identifier):
    """Provider's own invoice number for a claim."""


@dataclass(frozen=True, slots=True)
class ConsentToken(Identifier):
    """The `authorization_code` returned when a virtual claim is opened.

    It is both the claim's handle and the proof of the patient's consent, so it is treated
    as a secret: `repr` and `str` redact it. Use `.value` deliberately when sending it.
    """

    def __repr__(self) -> str:
        return f"ConsentToken('{self.redacted}')"

    def __str__(self) -> str:
        return self.redacted

    @property
    def redacted(self) -> str:
        v = self.value
        return f"{v[:4]}…{v[-2:]}" if len(v) > 8 else "•" * len(v)
