"""Pre-authorisation: the request a facility files for an intervention that needs payer approval, and the record back."""

from __future__ import annotations

import json
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
from sha_claim.domain.preauth_vocabulary import (
    AnaesthesiaType,
    CarcinomaStaging,
    LensPrescription,
    MetastasisSite,
    NewOrReplacement,
    SessionFrequency,
    TreatmentSetting,
)

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


# ── the specialised forms ───────────────────────────────────────────────────────────────────────────────
#
# `POST /preauths` is one endpoint for every kind of pre-auth. What changes is the clinical detail SHA asks
# for: a surgeon states the anaesthesia and the findings, a renal unit states the session schedule, an
# oncologist states the staging. Modelled as a detail object hung off the request rather than a subclass per
# type, so the common half — items, diagnoses, doctors, attachments — is written and validated once.


@dataclass(frozen=True, slots=True)
class NoDetails:
    """A normal pre-auth: the common fields and nothing else."""

    def as_payload(self) -> dict[str, Any]:
        return {}


@dataclass(frozen=True, slots=True)
class SurgicalDetails:
    """A planned operation. SHA always routes these to the attending doctor for approval."""

    chief_complaint: str
    vital_signs: str
    history_of_present_illness: str
    physical_examination: str
    investigation_report_details: str
    type_of_anaesthesia: AnaesthesiaType
    surgery_date: datetime
    is_condition_related_to_employment: bool | None = None
    is_condition_related_to_auto_or_other_accident: bool | None = None
    is_co_insured: bool | None = None
    co_insurance_details: str = ""

    def as_payload(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "chief_complaint": self.chief_complaint,
            "vital_signs": self.vital_signs,
            "history_of_present_illness": self.history_of_present_illness,
            "physical_examination": self.physical_examination,
            "investigation_report_details": self.investigation_report_details,
            "type_of_anaesthesia": self.type_of_anaesthesia.value,
            "surgery_date": self.surgery_date.isoformat(),
        }
        _put_optional(body, "is_condition_related_to_employment", self.is_condition_related_to_employment)
        _put_optional(
            body,
            "is_condition_related_to_auto_or_other_accident",
            self.is_condition_related_to_auto_or_other_accident,
        )
        _put_optional(body, "is_co_insured", self.is_co_insured)
        if self.co_insurance_details.strip():
            body["co_insurance_details"] = self.co_insurance_details.strip()
        return body


@dataclass(frozen=True, slots=True)
class RenalDetails:
    """Dialysis: a course of sessions, priced per session rather than per visit."""

    number_of_sessions_required: int
    cost_per_session: Money
    frequency_of_sessions: SessionFrequency
    clinical_indications: str
    start_date: datetime
    is_co_insured: bool | None = None

    def __post_init__(self) -> None:
        if self.number_of_sessions_required <= 0:
            raise ValueError("number_of_sessions_required must be positive")
        if self.cost_per_session.is_negative:
            raise ValueError("cost_per_session cannot be negative")

    def as_payload(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "number_of_sessions_required": str(self.number_of_sessions_required),
            "cost_per_session": self.cost_per_session.as_wire(),
            "frequency_of_sessions": self.frequency_of_sessions.value,
            "clinical_indications": self.clinical_indications,
            "start_date": self.start_date.isoformat(),
        }
        _put_optional(body, "is_co_insured", self.is_co_insured)
        return body


@dataclass(frozen=True, slots=True)
class OncologyDetails:
    """A course of cancer treatment: staging, where it has spread, and how the sessions are given."""

    carcinoma_staging: CarcinomaStaging
    comorbidity: str
    metastases: tuple[MetastasisSite, ...]
    treatment_setting: tuple[TreatmentSetting, ...]
    number_of_sessions_required: int
    cost_per_session: Money
    is_co_insured: bool | None = None
    progress_report: str = ""

    def __post_init__(self) -> None:
        if self.number_of_sessions_required <= 0:
            raise ValueError("number_of_sessions_required must be positive")
        if self.cost_per_session.is_negative:
            raise ValueError("cost_per_session cannot be negative")

    def as_payload(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "carcinoma_staging": self.carcinoma_staging.value,
            "comorbidity": self.comorbidity,
            # Lists, JSON-encoded like every other array on this multipart form.
            "metastases": json.dumps([m.value for m in self.metastases]),
            "treatment_setting": json.dumps([t.value for t in self.treatment_setting]),
            "number_of_sessions_required": str(self.number_of_sessions_required),
            "cost_per_session": self.cost_per_session.as_wire(),
        }
        _put_optional(body, "is_co_insured", self.is_co_insured)
        if self.progress_report.strip():
            body["progress_report"] = self.progress_report.strip()
        return body


@dataclass(frozen=True, slots=True)
class OpticalDetails:
    """Spectacles and eye services, priced in three parts SHA wants stated separately."""

    necessity_of_service: str
    lens_prescription: LensPrescription | None = None
    new_or_replacement: NewOrReplacement | None = None
    lens_amount: Money | None = None
    eye_examination_amount: Money | None = None
    frame_amount: Money | None = None
    clinical_indications: str = ""

    def as_payload(self) -> dict[str, Any]:
        body: dict[str, Any] = {"necessity_of_service": self.necessity_of_service}
        if self.lens_prescription is not None:
            body["lens_prescription"] = self.lens_prescription.value
        if self.new_or_replacement is not None:
            body["new_or_replacement"] = self.new_or_replacement.value
        for name, amount in (
            ("lens_amount", self.lens_amount),
            ("eye_examination_amount", self.eye_examination_amount),
            ("frame_amount", self.frame_amount),
        ):
            if amount is not None:
                body[name] = amount.as_wire()
        if self.clinical_indications.strip():
            body["clinical_indications"] = self.clinical_indications.strip()
        return body


@dataclass(frozen=True, slots=True)
class ImagingDetails:
    """A scan. The lightest of the specialised forms: why it is being asked for."""

    clinical_indications: str

    def as_payload(self) -> dict[str, Any]:
        return {"clinical_indications": self.clinical_indications}


PreauthDetails = (
    NoDetails | SurgicalDetails | RenalDetails | OncologyDetails | OpticalDetails | ImagingDetails
)


def _put_optional(body: dict[str, Any], name: str, value: bool | None) -> None:
    """Booleans go on the form as `true`/`false`; an unanswered one is left off entirely.

    Sending `false` where the facility simply did not answer states something they did not say — and on the
    employment and accident questions that is a claim about liability.
    """
    if value is not None:
        body[name] = "true" if value else "false"


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
    details: PreauthDetails = field(default_factory=NoDetails)
    """The specialised half of the form. `NoDetails` is a normal pre-auth."""

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
    """SHA's own clock on this pre-auth. **The unit is not published and has not been seen on UAT.**

    Call it a number, not a number of days. The guides give it as a bare integer with no description, no
    Postman request produces one, and the plain readings — days left, hours left, sessions left — differ by
    orders of magnitude. Rendering it as "expires in 5 days" would be an invention that a desk would plan
    an operating list around. `countdown_label()` is the only thing that should put it in front of anyone.
    """
    is_elective: bool = False
    """Raised ahead of the visit it is for, and carried into that visit when the patient returns.

    Read-only: SHA sets it. There is no elective endpoint and no elective field on the create request —
    the published API has 48 endpoints and none of them is one — so a facility cannot ask for this, only
    recognise it.
    """
    record_id: int | None = None
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    def countdown_label(self) -> str:
        """`countdown` phrased so it cannot be mistaken for a deadline nobody verified.

        SHA sends a bare integer and says nothing about what it counts. Until UAT settles it, this reports
        the number and names it as SHA's, which is true, instead of dressing it as days remaining — a desk
        that schedules an operating list around an invented expiry is worse off than one that asks.
        """
        if self.countdown is None:
            return ""
        return f"SHA countdown: {self.countdown}"

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
