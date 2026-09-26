"""VisitGateway port."""

from __future__ import annotations

from typing import Protocol

from smart_access.domain.enums import SessionStatus
from smart_access.domain.identifiers import PatientNumber, SessionId, VisitNumber
from smart_access.domain.session import SessionCloseResult, SessionLinkResult, VisitSession


class VisitGateway(Protocol):
    """Port for interacting with Smart biometric card sessions."""

    async def list_sessions(
        self, patient_number: PatientNumber, status: SessionStatus | str = SessionStatus.PENDING
    ) -> tuple[VisitSession, ...]:
        """Fetch all card sessions for a patient."""
        ...

    async def link_session(self, session_id: SessionId, visit_number: VisitNumber) -> SessionLinkResult:
        """Link an HMIS encounter ID to activate the card session."""
        ...

    async def close_session(
        self, session_id: SessionId, session_number: str | None = None
    ) -> SessionCloseResult:
        """Close an active card session when visit is completed."""
        ...
