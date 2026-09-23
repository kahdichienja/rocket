"""Opaque identifiers the API hands out or expects. Each is a distinct type so they cannot be mixed up."""

from __future__ import annotations

import re
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


#: Two Client Registry formats are live on UAT at once: `CR7678914660684-5` (13 digits + check digit) and
#: `CR-2026-000256` (CR-YYYY-serial). Both are accepted; the guard exists to catch an HMIS patient number or a
#: policy number being passed as a CR, which DHA itself will not refuse.
_CR_NUMBER = re.compile(r"^(CR\d{13}-\d|CR-\d{4}-\d{4,})$")


@dataclass(frozen=True, slots=True)
class PatientId(Identifier):
    """Client Registry (CR) number of a beneficiary — `patient_id` throughout the API.

    Two formats are in use on DHA: `CR` + 13 digits + `-` + check digit (`CR7678914660684-5`) and
    `CR-YYYY-serial` (`CR-2026-000256`). DHA accepts *any* string here and will happily create
    authorizations against an HMIS's internal patient number, so the shape is checked before a request leaves.
    """

    def __post_init__(self) -> None:
        Identifier.__post_init__(self)
        value = self.value.upper()
        if not _CR_NUMBER.match(value):
            raise ValueError(
                f"{self.value!r} is not a Client Registry number (expected CR7678914660684-5 or CR-2026-000256)"
            )
        object.__setattr__(self, "value", value)


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
