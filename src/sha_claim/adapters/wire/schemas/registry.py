"""Wire models for the Client Registry (`/patients`, `/patients/contacts`)."""

from __future__ import annotations

from pydantic import Field

from sha_claim.adapters.wire.schemas.common import WireModel


class OtherIdentificationWire(WireModel):
    identification_type: str = ""
    identification_number: str = ""


class DependantGroupWire(WireModel):
    relationship: str = ""
    total: int = 0
    result: list[dict] = Field(default_factory=list)  # type: ignore[type-arg]


class PatientRecordWire(WireModel):
    """Flat snake_case, despite the `resourceType: Patient` label — not a FHIR resource."""

    id: str = ""
    first_name: str = ""
    middle_name: str = ""
    last_name: str = ""
    gender: str = ""
    date_of_birth: str = ""
    citizenship: str = ""
    identification_type: str = ""
    identification_number: str = ""
    phone: str = ""
    county: str = ""
    sub_county: str = ""
    ward: str = ""
    other_identifications: list[OtherIdentificationWire] = Field(default_factory=list)
    dependants: list[DependantGroupWire] = Field(default_factory=list)


class PatientContactWire(WireModel):
    id: int | None = None
    contact_value: str = ""
    contact_type: str = ""
    is_confirmed: bool = False
    active: bool = False
    is_main_contact: bool = False
    next_of_kin_full_name: str = ""
