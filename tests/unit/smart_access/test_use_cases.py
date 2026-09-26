"""Unit tests for smart_access use cases with in-memory fake gateways."""

from decimal import Decimal

import pytest

from smart_access.domain.claim import (
    ClaimStatusFeedback,
    ClaimSubmissionResult,
    SmartClaim,
)
from smart_access.domain.enums import ClaimStatus, SessionStatus, SmartResponseType
from smart_access.domain.identifiers import (
    InvoiceNumber,
    PatientNumber,
    SessionId,
    SpId,
    VisitNumber,
)
from smart_access.domain.session import SessionCloseResult, SessionLinkResult, VisitSession
from smart_access.use_cases.manage_session import (
    CloseSession,
    FetchPendingSession,
    LinkSession,
    ListSessions,
)
from smart_access.use_cases.process_claim import CheckClaimStatus


class FakeVisitGateway:
    def __init__(self, sessions: list[VisitSession]) -> None:
        self.sessions = sessions
        self.linked: list[tuple[SessionId, VisitNumber]] = []
        self.closed: list[tuple[SessionId, str | None]] = []

    async def list_sessions(
        self, patient_number: PatientNumber, status: SessionStatus | str = SessionStatus.PENDING
    ) -> tuple[VisitSession, ...]:
        return tuple(s for s in self.sessions if s.patient_number == patient_number)

    async def link_session(self, session_id: SessionId, visit_number: VisitNumber) -> SessionLinkResult:
        self.linked.append((session_id, visit_number))
        return SessionLinkResult(success=True, code="200", message="Linked", response_type=SmartResponseType.SUCCESS)

    async def close_session(
        self, session_id: SessionId, session_number: str | None = None
    ) -> SessionCloseResult:
        self.closed.append((session_id, session_number))
        return SessionCloseResult(success=True, code="200", message="Closed", response_type=SmartResponseType.SUCCESS)


class FakeClaimGateway:
    def __init__(self, feedbacks: list[ClaimStatusFeedback] | None = None) -> None:
        self.feedbacks = feedbacks or []
        self.submitted_claims: list[SmartClaim] = []

    async def post_claim(self, claim: SmartClaim) -> ClaimSubmissionResult:
        self.submitted_claims.append(claim)
        return ClaimSubmissionResult(success=True, code="200", message="Posted", response_type=SmartResponseType.SUCCESS)

    async def post_interim_claim(self, claim: SmartClaim) -> ClaimSubmissionResult:
        return await self.post_claim(claim)

    async def check_claim_status(
        self, invoice_number: InvoiceNumber, visit_number: VisitNumber
    ) -> tuple[ClaimStatusFeedback, ...]:
        return tuple(self.feedbacks)


@pytest.mark.asyncio
async def test_manage_session_use_cases() -> None:
    s1 = VisitSession(id=SessionId(1), patient_number=PatientNumber("PT1"), status=SessionStatus.ACTIVE, sp_id=SpId(10))
    s2 = VisitSession(id=SessionId(2), patient_number=PatientNumber("PT1"), status=SessionStatus.PENDING, sp_id=SpId(10))
    gateway = FakeVisitGateway([s1, s2])

    list_uc = ListSessions(gateway)
    sessions = await list_uc.execute("PT1")
    assert len(sessions) == 2

    pending_uc = FetchPendingSession(gateway)
    pending = await pending_uc.execute("PT1")
    assert pending is not None
    assert pending.id == 2
    assert pending.is_pending is True

    link_uc = LinkSession(gateway)
    link_res = await link_uc.execute(2, "AC000001")
    assert link_res.success is True
    assert gateway.linked == [(SessionId(2), VisitNumber("AC000001"))]

    close_uc = CloseSession(gateway)
    close_res = await close_uc.execute(2)
    assert close_res.success is True
    assert gateway.closed == [(SessionId(2), None)]


@pytest.mark.asyncio
async def test_claim_status_effective_resolution() -> None:
    # If insurer had Pending first and then Billed on resubmission, Billed is returned
    fb1 = ClaimStatusFeedback(
        session_id=SessionId(1),
        claim_status=ClaimStatus.PENDING,
        payer_name="Payer",
        patient_number=PatientNumber("PT1"),
        visit_number=VisitNumber("VN1"),
        scheme_name="Scheme",
        amount=Decimal("3000"),
        invoice_number=InvoiceNumber("INV-1"),
    )
    fb2 = ClaimStatusFeedback(
        session_id=SessionId(1),
        claim_status=ClaimStatus.BILLED,
        payer_name="Payer",
        patient_number=PatientNumber("PT1"),
        visit_number=VisitNumber("VN1"),
        scheme_name="Scheme",
        amount=Decimal("3000"),
        invoice_number=InvoiceNumber("INV-1"),
    )
    gateway = FakeClaimGateway([fb1, fb2])
    status_uc = CheckClaimStatus(gateway)

    eff = await status_uc.execute("INV-1", "VN1")
    assert eff is not None
    assert eff.is_billed is True
    assert eff.claim_status == ClaimStatus.BILLED
