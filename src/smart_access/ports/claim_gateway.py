"""ClaimGateway port."""

from __future__ import annotations

from typing import Protocol

from smart_access.domain.claim import (
    ClaimStatusFeedback,
    ClaimSubmissionResult,
    SmartClaim,
)
from smart_access.domain.identifiers import InvoiceNumber, VisitNumber


class ClaimGateway(Protocol):
    """Port for submitting claims and polling claim settlement status."""

    async def post_claim(self, claim: SmartClaim) -> ClaimSubmissionResult:
        """Submit a finalized claim to `POST /api/claims`."""
        ...

    async def post_interim_claim(self, claim: SmartClaim) -> ClaimSubmissionResult:
        """Submit an interim claim to `POST /api/interim-claim`."""
        ...

    async def check_claim_status(
        self, invoice_number: InvoiceNumber, visit_number: VisitNumber
    ) -> tuple[ClaimStatusFeedback, ...]:
        """Query biometric swipe / billing status from `GET /api/claim-status`."""
        ...
