"""SmartClaimSession: binds an active visit session to claim and benefit operations."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from smart_access.domain.claim import (
    ClaimStatusFeedback,
    ClaimSubmissionResult,
    SmartClaim,
)
from smart_access.domain.identifiers import (
    InvoiceNumber,
    MedicalAidCode,
    MemberNumber,
    PatientNumber,
    PolicyId,
    SessionId,
    VisitNumber,
)
from smart_access.domain.member import SmartMember
from smart_access.domain.preauth import (
    PreauthRequest,
    PreauthResponse,
    PreauthStatusFeedback,
)
from smart_access.domain.rules import (
    RulesCheckItem,
    RulesCheckRequest,
    RuleValidationResult,
)
from smart_access.domain.session import (
    SessionCloseResult,
    SessionLinkResult,
    VisitSession,
)

if TYPE_CHECKING:
    from smart_access.client import AsyncSmartClient


class SmartClaimSession:
    """Convenience coordinator bound to an active or pending biometric card session.

    Enables chaining member inspection, rules validation, pre-auth, and claims posting
    without having to pass session_id on every call.
    """

    def __init__(
        self,
        client: AsyncSmartClient,
        session_id: SessionId | int,
        patient_number: PatientNumber | str,
        session: VisitSession | None = None,
    ) -> None:
        self.client = client
        self.session_id = SessionId.of(session_id)
        self.patient_number = PatientNumber.of(patient_number)
        self.session = session
        self.members: tuple[SmartMember, ...] = ()

    async def link(self, visit_number: VisitNumber | str) -> SessionLinkResult:
        """Link this biometric session to an HMIS visit/encounter number."""
        result = await self.client.sessions.link(self.session_id, visit_number)
        if self.session and result.success:
            # Refresh session object with linked visit number and ACTIVE status
            from smart_access.domain.enums import SessionStatus

            self.session = VisitSession(
                id=self.session.id,
                patient_number=self.session.patient_number,
                status=SessionStatus.ACTIVE,
                sp_id=self.session.sp_id,
                location_code=self.session.location_code,
                payer_code=self.session.payer_code,
                payer_name=self.session.payer_name,
                scheme_code=self.session.scheme_code,
                scheme_name=self.session.scheme_name,
                visit_number=VisitNumber.of(visit_number),
                member_number=self.session.member_number,
            )
        return result

    async def get_members(self) -> tuple[SmartMember, ...]:
        """Fetch member bio, schemes, and benefit pools for this session."""
        self.members = await self.client.members.get_details(self.patient_number, self.session_id)
        return self.members

    async def validate_rules(
        self,
        items: list[tuple[str, Decimal | float | int, int]],  # (item_code, net_amount, pool_nr)
        medical_aid_code: MedicalAidCode | str,
        medical_aid_number: MemberNumber | str,
        medical_aid_plan: str,
        policy_id: PolicyId | int,
    ) -> RuleValidationResult:
        """Validate planned billing items against payer rules."""
        rule_items = tuple(
            RulesCheckItem(
                provider_item_code=code,
                item_net_amount=Decimal(str(net_amt)),
                pool_number=pool_nr,
            )
            for code, net_amt, pool_nr in items
        )
        req = RulesCheckRequest(
            items=rule_items,
            medical_aid_code=MedicalAidCode.of(medical_aid_code),
            medical_aid_number=MemberNumber.of(medical_aid_number),
            medical_aid_plan=medical_aid_plan,
            policy_id=PolicyId.of(policy_id),
        )
        return await self.client.rules.validate(req)

    async def submit_preauth(self, request: PreauthRequest) -> PreauthResponse:
        """Submit a pre-authorization request under this session."""
        return await self.client.preauth.submit(request)

    async def get_preauth_feedback(
        self,
        visit_number: VisitNumber | str,
        invoice_no: InvoiceNumber | str | None = None,
    ) -> tuple[PreauthStatusFeedback, ...]:
        """Check pre-authorization decision for this session's patient and visit."""
        return await self.client.preauth.get_feedback(
            visit_number=visit_number,
            patient_file_no=self.patient_number,
            invoice_no=invoice_no,
        )

    async def post_claim(self, claim: SmartClaim) -> ClaimSubmissionResult:
        """Post the finalized bill to Smart."""
        return await self.client.claims.submit(claim)

    async def check_claim_status(
        self, invoice_number: InvoiceNumber | str, visit_number: VisitNumber | str
    ) -> ClaimStatusFeedback | None:
        """Query swipe authentication status on the cashier reader."""
        return await self.client.claims.check_status(invoice_number, visit_number)

    async def close(self, session_number: str | None = None) -> SessionCloseResult:
        """End the active biometric session."""
        return await self.client.sessions.close(self.session_id, session_number)
