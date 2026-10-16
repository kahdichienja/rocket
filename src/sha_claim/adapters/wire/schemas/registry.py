"""Wire models for the Client Registry (`/patients`, `/patients/contacts`)."""

from __future__ import annotations

from typing import Any

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


class HealthWorkerWire(WireModel):
    """`GET /api/v1/professionals` — one entry of DHA's `message.membership`.

    DHA publishes no shape for this, and the shape it actually sends shares almost no key names with the
    ones guessed here originally. Observed on UAT, 2026-10-16:

        {"message": {"membership": {"id": "PUID-0035218-8", "full_name": "Dr Eight One",
                                    "registration_id": "PUID-035219",
                                    "external_reference_id": "T-80000781",
                                    "licensing_body": "KMPDC", "specialty": "MEDICINE",
                                    "is_active": 1}, ...}}

    Not one of `registry_id`, `registration_number`, `name`, `regulator` or `status` is present. Every
    lookup therefore validated — each field being optional — and produced a practitioner with an empty
    registry id, which reads downstream as "the registry holds nobody with that number". The registry
    had answered, in full, and the answer was thrown away.

    Both spellings are kept: the optimistic ones in case DHA ever flattens it, the observed ones because
    they are what arrives today.
    """

    id: str = ""
    registry_id: str = ""
    registration_number: str = ""
    name: str = ""
    full_name: str = ""
    regulator: str = ""
    status: str = ""
    specialty: str = ""
    #: What DHA actually sends.
    external_reference_id: str = ""
    """The regulator's own number — `T-80000781`, or the bare number for PPB."""
    registration_id: str = ""
    """A second PUID, distinct from `id`. Not the registry id an SHR read wants."""
    licensing_body: str = ""
    """`KMPDC`, or spelled out as `Pharmacy and Poisons Board`. Taken verbatim."""
    is_active: Any = None
    """`1`/`0` as an integer, where the flat shape would have carried a `status` string."""
