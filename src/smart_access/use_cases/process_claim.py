"""Use cases for claims submission and status polling."""

from __future__ import annotations

from smart_access.domain.claim import (
    ClaimStatusFeedback,
    ClaimSubmissionResult,
    SmartClaim,
)
from smart_access.domain.identifiers import InvoiceNumber, VisitNumber
from smart_access.ports.claim_gateway import ClaimGateway


class SubmitClaim:
    """Posts finalized claim invoice, line items, and modifiers to Smart."""

    def __init__(self, gateway: ClaimGateway) -> None:
        self._gateway = gateway

    async def execute(self, claim: SmartClaim) -> ClaimSubmissionResult:
        return await self._gateway.post_claim(claim)


class SubmitInterimClaim:
    """Posts interim claim bill during prolonged admission."""

    def __init__(self, gateway: ClaimGateway) -> None:
        self._gateway = gateway

    async def execute(self, claim: SmartClaim) -> ClaimSubmissionResult:
        return await self._gateway.post_interim_claim(claim)


class CheckClaimStatus:
    """Queries biometric swipe authentication status and selects effective claim state."""

    def __init__(self, gateway: ClaimGateway) -> None:
        self._gateway = gateway

    async def execute(
        self, invoice_number: InvoiceNumber | str, visit_number: VisitNumber | str
    ) -> ClaimStatusFeedback | None:
        inum = InvoiceNumber.of(invoice_number)
        vnum = VisitNumber.of(visit_number)
        feedbacks = await self._gateway.check_claim_status(inum, vnum)
        if not feedbacks:
            return None

        # Effective status resolution:
        # If any attempt reached BILLED, that is our effective answer.
        for fb in feedbacks:
            if fb.is_billed:
                return fb
        # Otherwise return the last recorded status
        return feedbacks[-1]
