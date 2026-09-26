"""Domain models for Smart Visit Sessions."""

from __future__ import annotations

from dataclasses import dataclass

from smart_access.domain.enums import SessionStatus, SmartResponseType
from smart_access.domain.identifiers import (
    LocationCode,
    MedicalAidCode,
    MemberNumber,
    PatientNumber,
    SchemeCode,
    SessionId,
    SpId,
    VisitNumber,
)


@dataclass(frozen=True)
class VisitSession:
    """Represents a patient's biometric smart-card swipe session on SmartLink."""

    id: SessionId
    patient_number: PatientNumber
    status: SessionStatus
    sp_id: SpId
    location_code: LocationCode | None = None
    payer_code: MedicalAidCode | None = None
    payer_name: str | None = None
    scheme_code: SchemeCode | None = None
    scheme_name: str | None = None
    visit_number: VisitNumber | None = None
    member_number: MemberNumber | None = None

    @property
    def is_pending(self) -> bool:
        return self.status == SessionStatus.PENDING

    @property
    def is_active(self) -> bool:
        return self.status == SessionStatus.ACTIVE

    @property
    def is_closed(self) -> bool:
        return self.status in (SessionStatus.CLOSED, SessionStatus.BILLED, SessionStatus.EXPIRED)


@dataclass(frozen=True)
class SessionLinkResult:
    """Outcome of activating/linking a session to an HMIS visit/encounter."""

    success: bool
    code: str
    message: str
    response_type: SmartResponseType


@dataclass(frozen=True)
class SessionCloseResult:
    """Outcome of terminating/closing an active session."""

    success: bool
    code: str
    message: str
    response_type: SmartResponseType
