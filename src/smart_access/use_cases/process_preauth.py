"""Use cases for pre-authorization requests and decision retrieval."""

from __future__ import annotations

from collections.abc import Sequence

from smart_access.domain.identifiers import InvoiceNumber, PatientNumber, PreauthRequestId, VisitNumber
from smart_access.domain.preauth import (
    PreauthAttachment,
    PreauthRequest,
    PreauthResponse,
    PreauthStatusFeedback,
)
from smart_access.ports.preauth_gateway import PreauthGateway


class SubmitPreauth:
    """Submits preauthorization request with items, diagnoses, and attachments."""

    def __init__(self, gateway: PreauthGateway) -> None:
        self._gateway = gateway

    async def execute(self, request: PreauthRequest) -> PreauthResponse:
        return await self._gateway.submit_preauth(request)


class GetPreauthFeedback:
    """Fetches pre-authorization decision feedback from the payer."""

    def __init__(self, gateway: PreauthGateway) -> None:
        self._gateway = gateway

    async def execute(
        self,
        visit_number: VisitNumber | str,
        patient_file_no: PatientNumber | str | None = None,
        invoice_no: InvoiceNumber | str | None = None,
    ) -> tuple[PreauthStatusFeedback, ...]:
        vnum = VisitNumber.of(visit_number)
        pnum = PatientNumber.of(patient_file_no) if patient_file_no is not None else None
        inum = InvoiceNumber.of(invoice_no) if invoice_no is not None else None
        return await self._gateway.get_preauth_status(vnum, pnum, inum)


class AddPreauthAttachment:
    """Appends supporting documents to an existing pre-authorization."""

    def __init__(self, gateway: PreauthGateway) -> None:
        self._gateway = gateway

    async def execute(
        self, preauth_request_id: PreauthRequestId | str, attachments: Sequence[PreauthAttachment]
    ) -> bool:
        pid = PreauthRequestId.of(preauth_request_id)
        return await self._gateway.add_attachment(pid, attachments)
