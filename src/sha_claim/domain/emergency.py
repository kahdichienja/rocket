"""Emergency case claims: opened without prior consent, billed by treatment protocol, and EMT (ambulance) claims."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from sha_claim.domain.attachments import Attachment
from sha_claim.domain.codes import Icd11Code, InterventionCode, ProtocolCode
from sha_claim.domain.consent import Otp
from sha_claim.domain.enums import BroughtBy, ModeOfArrival
from sha_claim.domain.identifiers import PatientId
from sha_claim.domain.money import Money
from sha_claim.domain.practitioner import PractitionerRef


@dataclass(frozen=True, slots=True)
class EmergencyCase:
    """Command for `POST /claims/emergency`. `beneficiary` is None for an unidentified patient.

    `notes` is mandatory: the portal marks it optional, but UAT rejects a missing or blank value
    (`{"notes": ["This field may not be blank."]}`).
    """

    attending: PractitionerRef
    reference_number: str
    brought_by: BroughtBy
    mode_of_arrival: ModeOfArrival
    interventions: tuple[InterventionCode, ...]
    beneficiary: PatientId | None = None
    otp: Otp | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.reference_number.strip():
            raise ValueError("reference_number cannot be empty")
        if not self.interventions:
            raise ValueError("at least one intervention code is required")
        if not self.notes.strip():
            raise ValueError("notes cannot be empty (SHA rejects an emergency case without notes)")
        object.__setattr__(self, "reference_number", self.reference_number.strip())
        object.__setattr__(self, "notes", self.notes.strip())


@dataclass(frozen=True, slots=True)
class EmergencyProtocol:
    code: ProtocolCode
    name: str
    protocol_type: str
    classification: str
    status: str
    tariff: Money | None
    guid: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class ProtocolLine:
    """Command for `POST /claims/emergency/protocols` — bills a treatment protocol on an emergency claim."""

    protocol_code: ProtocolCode
    intervention_code: InterventionCode
    unit_price: Money
    quantity: int = 1
    diagnoses: tuple[Icd11Code, ...] = ()

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.unit_price.is_negative:
            raise ValueError("unit_price cannot be negative")


@dataclass(frozen=True, slots=True)
class EmtClaim:
    """Command for `POST /claims/emt` — the ambulance / EMT provider's claim for an emergency case."""

    protocol_code: ProtocolCode
    case_number: str
    practitioner_registration_number: str
    provider_registration_number: str
    beneficiary: PatientId
    otp: Otp
    diagnoses: tuple[Icd11Code, ...]
    interventions: tuple[InterventionCode, ...]
    attachments: tuple[Attachment, ...] = ()

    def __post_init__(self) -> None:
        for name in ("case_number", "practitioner_registration_number", "provider_registration_number"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} cannot be empty")
        if not self.diagnoses:
            raise ValueError("at least one diagnosis is required")
        if not self.interventions:
            raise ValueError("at least one intervention code is required")
