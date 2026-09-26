"""Domain enumerations for Smart Access workflows."""

from __future__ import annotations

from enum import StrEnum
from typing import Self


class LenientStrEnum(StrEnum):
    """String enum that falls back to UNKNOWN for unobserved upstream values."""

    @classmethod
    def _missing_(cls, value: object) -> Self:
        for member in cls:
            if member.name.upper() == "UNKNOWN":
                return member
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")


class SessionStatus(LenientStrEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    BILLED = "BILLED"
    CLOSED = "CLOSED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


class ClaimStatus(LenientStrEnum):
    PENDING = "Pending"
    BILLED = "Billed"
    CANCELLED = "Cancelled"
    REJECTED = "Rejected"
    UNKNOWN = "UNKNOWN"

    @property
    def is_billed(self) -> bool:
        """True if the claim has been confirmed by biometrics/card deduction."""
        return self == ClaimStatus.BILLED

    @property
    def is_terminal_failure(self) -> bool:
        return self in (ClaimStatus.CANCELLED, ClaimStatus.REJECTED)


class PaymentModifierType(LenientStrEnum):
    CASH_EXCESS = "0"
    COPAY_FIXED = "1"
    COPAY_PERCENTAGE = "2"
    TIER_CASH = "3"
    NHIF_SHA = "5"
    DISCOUNT = "6"
    UNKNOWN = "UNKNOWN"


class CopayType(LenientStrEnum):
    FIXED = "FIXED"
    PERCENTAGE = "PERCENTAGE"
    UNKNOWN = "UNKNOWN"


class HospitalizationType(LenientStrEnum):
    PLANNED = "Planned"
    EMERGENCY = "Emergency"
    DAY_CARE = "DayCare"
    UNKNOWN = "UNKNOWN"


class AdmissionType(LenientStrEnum):
    REFERRAL = "REFERRAL"
    INHOUSE = "INHOUSE"
    UNKNOWN = "UNKNOWN"


class DoctorType(LenientStrEnum):
    PRIVATE = "PRIVATE"
    RESIDENT = "RESIDENT"
    UNKNOWN = "UNKNOWN"


class CodingStandard(LenientStrEnum):
    ICD10 = "ICD10"
    ICD11 = "ICD11"
    UNKNOWN = "UNKNOWN"


class PreauthStatus(LenientStrEnum):
    APPROVED = "Approved"
    PENDING = "Pending"
    REJECTED = "Rejected"
    UNKNOWN = "UNKNOWN"


class SmartResponseType(LenientStrEnum):
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"
