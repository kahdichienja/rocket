"""Closed vocabularies documented by the API (request side) and lenient ones observed in responses."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Self


class LenientStrEnum(StrEnum):
    """StrEnum for *server* vocabularies that are not fully documented.

    Unknown values become pseudo-members instead of raising, so a new server state degrades
    to `is_known == False` rather than crashing a billing run.
    """

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if not isinstance(value, str):
            return None
        member = str.__new__(cls, value)
        member._name_ = f"UNKNOWN_{value}"
        member._value_ = value
        return member

    @property
    def is_known(self) -> bool:
        return self.name in type(self).__members__

    @classmethod
    def parse(cls, raw: str | None) -> Self | None:
        return None if raw is None or raw == "" else cls(raw)


class ServiceType(StrEnum):
    CAPITATION = "CAPITATION"
    OUTPATIENT = "OUTPATIENT"
    INPATIENT = "INPATIENT"
    EMERGENCY = "EMERGENCY"


class IdentificationType(StrEnum):
    """`identification_type` for patients (eligibility) and practitioners."""

    NATIONAL_ID = "National ID"
    ALIEN_ID = "Alien ID"
    REFUGEE_ID = "Refugee ID"
    REGISTRATION_NUMBER = "registration_number"  # practitioners only


class NextOfKinIdType(StrEnum):
    NATIONAL_ID = "National ID"
    CLIENT_REGISTRY_ID = "ClientRegistry ID"
    BIRTH_NOTIFICATION = "Birth Notification"
    BIRTH_CERTIFICATE = "Birth Certificate"
    ALIEN_ID = "Alien ID"
    REFUGEE_ID = "Refugee ID"
    MANDATE_NUMBER = "Mandate Number"
    TEMPORARY_ID = "Temporary ID"


class CancelReason(StrEnum):
    WRONG_PATIENT = "WRONG_PATIENT"
    NO_SERVICE_GIVEN = "NO_SERVICE_GIVEN"
    WRONG_BENEFIT = "WRONG_BENEFIT"
    EXPIRED_VISIT = "EXPIRED_VISIT"
    EXHAUSTED_BENEFIT = "EXHAUSTED_BENEFIT"
    TIME_BARRED = "TIME_BARRED"
    OTHER_REASONS = "OTHER_REASONS"


class DischargeReason(StrEnum):
    RECOVERED = "RECOVERED"
    REFERRED = "REFERRED"
    DECEASED = "DECEASED"
    ABSCONDED = "ABSCONDED"
    OTHER = "OTHER"


class DoctorConsentRequestType(StrEnum):
    PREAUTH_DOCTOR_APPROVAL = "PREAUTH_DOCTOR_APPROVAL_REQUEST"
    EMERGENCY_CLAIM_DOCTOR_APPROVAL = "EMERGENCY_CLAIM_DOCTOR_APPROVAL_REQUEST"
    PRESCRIPTION = "PRESCRIPTION_REQUEST"


class BroughtBy(StrEnum):
    RELATIVE = "RELATIVE"
    UNKNOWN = "UNKNOWN"
    SAMARITAN = "SAMARITAN"
    PARAMEDICS = "PARAMEDICS"


class ModeOfArrival(StrEnum):
    AMBULANCE = "AMBULANCE"
    WALK_IN = "WALK-IN"
    OTHER = "OTHER"


# ── server vocabularies (lenient; extended as UAT recordings reveal values) ──


class EligibilityStatus(LenientStrEnum):
    MEMBER_FOUND = "10"


class AuthorizationStatus(LenientStrEnum):
    PENDING = "PENDING"


class PaymentMechanism(LenientStrEnum):
    CAPITATION = "CAPITATION"
    CASE_BASED = "CASE BASED"
    FEE_FOR_SERVICE = "FEE FOR SERVICE"


class CoverageStatus(LenientStrEnum):
    COVERED = "1"
