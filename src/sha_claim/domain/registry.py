"""Client Registry records: who the member is, and how SHA can reach them.

The registry is how an HMIS turns an identity document into a Client Registry (CR) number, and how it finds
out — before trying — whether SHA holds a phone contact the OTP can go to. A member with no contact cannot
consent by OTP at all, whatever their cover says.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from sha_claim.domain.identifiers import PatientId


@dataclass(frozen=True, slots=True)
class OtherIdentification:
    identification_type: str  # "Household Number", "SHA Number" …
    identification_number: str


@dataclass(frozen=True, slots=True)
class PatientRecord:
    """`GET /patients` — the member as the Client Registry holds them."""

    patient_id: PatientId | None
    first_name: str
    middle_name: str
    last_name: str
    gender: str
    date_of_birth: date | None
    identification_type: str
    identification_number: str
    phone: str = ""
    citizenship: str = ""
    county: str = ""
    sub_county: str = ""
    ward: str = ""
    other_identifications: tuple[OtherIdentification, ...] = ()
    dependant_ids: tuple[PatientId, ...] = ()
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def full_name(self) -> str:
        return " ".join(p for p in (self.first_name, self.middle_name, self.last_name) if p.strip())

    def identification(self, kind: str) -> str:
        """Another identifier the registry holds, e.g. `identification("SHA Number")`."""
        wanted = kind.strip().casefold()
        return next(
            (
                o.identification_number
                for o in self.other_identifications
                if o.identification_type.strip().casefold() == wanted
            ),
            "",
        )


@dataclass(frozen=True, slots=True)
class PatientContact:
    """`GET /patients/contacts` — a phone SHA can send an OTP to. `value` arrives masked (`+254710***256`)."""

    contact_id: int | None
    value: str
    contact_type: str  # PHO …
    is_confirmed: bool
    is_active: bool
    is_main: bool
    next_of_kin_full_name: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def can_receive_otp(self) -> bool:
        """SHA sends the visit OTP only to a confirmed, active phone contact."""
        return self.is_confirmed and self.is_active and self.contact_type.strip().upper().startswith("PHO")
