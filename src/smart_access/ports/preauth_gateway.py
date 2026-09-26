"""PreauthGateway port."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from smart_access.domain.identifiers import InvoiceNumber, PatientNumber, PreauthRequestId, VisitNumber
from smart_access.domain.preauth import (
    PreauthAttachment,
    PreauthRequest,
    PreauthResponse,
    PreauthStatusFeedback,
)


class PreauthGateway(Protocol):
    """Port for creating and tracking pre-authorization requests."""

    async def submit_preauth(self, request: PreauthRequest) -> PreauthResponse:
        """Submit a pre-authorization request to `/api/preauth-request`."""
        ...

    async def get_preauth_status(
        self,
        visit_number: VisitNumber,
        patient_file_no: PatientNumber | None = None,
        invoice_no: InvoiceNumber | None = None,
    ) -> tuple[PreauthStatusFeedback, ...]:
        """Fetch pre-authorization decision feedback from `/api/preauth-request`."""
        ...

    async def add_attachment(
        self, preauth_request_id: PreauthRequestId, attachments: Sequence[PreauthAttachment]
    ) -> bool:
        """Upload additional attachments for a preauthorization via `PUT /api/attachment/{id}`."""
        ...
