"""Use cases for managing Smart visit sessions."""

from __future__ import annotations

from smart_access.domain.enums import SessionStatus
from smart_access.domain.identifiers import PatientNumber, SessionId, VisitNumber
from smart_access.domain.session import SessionCloseResult, SessionLinkResult, VisitSession
from smart_access.ports.visit_gateway import VisitGateway


class ListSessions:
    """List all open/pending card sessions for a patient."""

    def __init__(self, gateway: VisitGateway) -> None:
        self._gateway = gateway

    async def execute(
        self, patient_number: PatientNumber | str, status: SessionStatus | str = SessionStatus.PENDING
    ) -> tuple[VisitSession, ...]:
        patient = PatientNumber.of(patient_number)
        return await self._gateway.list_sessions(patient, status)


class FetchPendingSession:
    """Fetch the latest pending biometric swipe session for a patient."""

    def __init__(self, gateway: VisitGateway) -> None:
        self._gateway = gateway

    async def execute(self, patient_number: PatientNumber | str) -> VisitSession | None:
        patient = PatientNumber.of(patient_number)
        sessions = await self._gateway.list_sessions(patient, SessionStatus.PENDING)
        if not sessions:
            return None
        # Return first PENDING session or first available
        for s in sessions:
            if s.is_pending:
                return s
        return sessions[0]


class LinkSession:
    """Activate/link a biometric session to an HMIS visit/encounter ID."""

    def __init__(self, gateway: VisitGateway) -> None:
        self._gateway = gateway

    async def execute(
        self, session_id: SessionId | int, visit_number: VisitNumber | str
    ) -> SessionLinkResult:
        sid = SessionId.of(session_id)
        vnum = VisitNumber.of(visit_number)
        return await self._gateway.link_session(sid, vnum)


class CloseSession:
    """End an active visit session after encounter completion."""

    def __init__(self, gateway: VisitGateway) -> None:
        self._gateway = gateway

    async def execute(
        self, session_id: SessionId | int, session_number: str | None = None
    ) -> SessionCloseResult:
        sid = SessionId.of(session_id)
        return await self._gateway.close_session(sid, session_number)
