"""Pre-authorisation: the request a facility files for an intervention that needs payer approval, and the record back."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from sha_claim.domain.attachments import Attachment
from sha_claim.domain.codes import Icd11Code, InterventionCode
from sha_claim.domain.enums import DoctorConsentRequestType, ServiceType
from sha_claim.domain.money import Money
from sha_claim.domain.practitioner import PractitionerRef

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True, slots=True)
class PreauthItem:
    """A billed item on the pre-auth request."""

    code: str
    description: str
    quantity: Decimal | int
    unit_price: Money

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("item code cannot be empty")
        if Decimal(self.quantity) <= 0:
            raise ValueError("item quantity must be positive")
        if self.unit_price.is_negative:
            raise ValueError("item unit_price cannot be negative")

    @property
    def total(self) -> Money:
        return self.unit_price * Decimal(self.quantity)


@dataclass(frozen=True, slots=True)
class PreauthRequest:
    """Command for `POST /preauths`. Validates what the server would certainly reject."""

    intervention_code: InterventionCode
    service_start: datetime
    service_end: datetime
    items: tuple[PreauthItem, ...]
    diagnoses: tuple[Icd11Code, ...]
    doctors: tuple[PractitionerRef, ...]
    provider_notification_email: str
    attachments: tuple[Attachment, ...] = ()

    def __post_init__(self) -> None:
        if self.service_end < self.service_start:
            raise ValueError("service_end must not be before service_start")
        if not _EMAIL.match(self.provider_notification_email.strip()):
            raise ValueError("provider_notification_email is not a valid email address")
        if not self.items:
            raise ValueError("at least one item is required")
        if not self.diagnoses:
            raise ValueError("at least one diagnosis is required")
        object.__setattr__(self, "provider_notification_email", self.provider_notification_email.strip())

    @property
    def estimated_total(self) -> Money:
        total = Money.zero(self.items[0].unit_price.currency)
        for item in self.items:
            total = total + item.total
        return total


@dataclass(frozen=True, slots=True)
class Preauthorization:
    """Snapshot of a pre-authorisation record (camelCase on the wire)."""

    guid: str
    token: str
    intervention_code: InterventionCode | None
    status: str
    """Raw server vocabulary; promoted to a LenientStrEnum once observed on UAT."""
    doctor_review_status: str
    needs_doctor_approval: bool
    doctor_approved: bool
    doctors_required: int
    is_request_phase: bool
    is_response_phase: bool
    total_estimated: Money | None
    interim_approved: Money | None
    final_approved: Money | None
    service_start: datetime | None = None
    service_end: datetime | None = None
    provider_notification_email: str = ""
    member_name: str = ""
    description: str = ""
    countdown: int | None = None
    record_id: int | None = None
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def awaiting_doctor(self) -> bool:
        return self.needs_doctor_approval and not self.doctor_approved

    @property
    def decided(self) -> bool:
        return self.is_response_phase and not self.is_request_phase


@dataclass(frozen=True, slots=True)
class DoctorConsentRequest:
    """Command for `POST /claims/doctor-consent`."""

    intervention_code: InterventionCode
    request_type: DoctorConsentRequestType
    practitioner: PractitionerRef
    service_type: ServiceType | None = None
    emergency_claim_id: str | None = None
