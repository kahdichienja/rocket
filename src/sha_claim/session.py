"""ClaimSession: a virtual claim's handle plus every operation on it, so callers never thread the token."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from sha_claim.domain.attachments import Attachment
from sha_claim.domain.claim import (
    ClaimAttachment,
    ClaimDiagnosis,
    ClaimIntervention,
    ClaimLine,
    LineEdit,
    NewClaimLine,
    PayerClaimRecord,
    VirtualClaim,
)
from sha_claim.domain.codes import Icd11Code, InterventionCode, SchemeCode
from sha_claim.domain.enums import CancelReason
from sha_claim.domain.identifiers import AttachmentId, ConsentToken, InvoiceNumber, LineGuid
from sha_claim.domain.money import Money
from sha_claim.errors import RequestValidationError, Violation
from sha_claim.ports.virtual_claim_gateway import VirtualClaimGateway
from sha_claim.use_cases.submit_claim import SubmitClaim


class ClaimSession:
    """Operations on one server-side virtual claim.

    `claim` is the latest snapshot the server returned (refreshed by `preview`, `submit`, `close`);
    it may be `None` for a session resumed from a bare token until `preview()` is called.
    """

    def __init__(
        self, gateway: VirtualClaimGateway, token: ConsentToken, claim: VirtualClaim | None = None
    ) -> None:
        self._gateway = gateway
        self._submit = SubmitClaim(gateway)
        self.consent_token = token
        self.claim = claim

    # ── interventions ──

    async def add_intervention(self, code: InterventionCode | str) -> ClaimIntervention:
        return await self._gateway.add_intervention(self.consent_token, InterventionCode.of(code))

    async def retire_intervention(self, code: InterventionCode | str) -> None:
        await self._gateway.retire_intervention(self.consent_token, InterventionCode.of(code))

    async def restore_intervention(self, code: InterventionCode | str) -> None:
        await self._gateway.restore_intervention(self.consent_token, InterventionCode.of(code))

    # ── diagnoses ──

    async def add_diagnosis(
        self, icd: Icd11Code | str, intervention: InterventionCode | str
    ) -> ClaimDiagnosis:
        return await self._gateway.add_diagnosis(
            self.consent_token, Icd11Code.of(icd), InterventionCode.of(intervention)
        )

    async def remove_diagnosis(self, icd: Icd11Code | str, intervention: InterventionCode | str) -> None:
        await self._gateway.remove_diagnosis(
            self.consent_token, Icd11Code.of(icd), InterventionCode.of(intervention)
        )

    # ── billing lines ──

    async def add_line(
        self,
        intervention: InterventionCode | str,
        unit_price: Money,
        quantity: Decimal | int = 1,
        *,
        scheme_code: SchemeCode | str | None = None,
        charge_date: date | None = None,
        diagnoses: Sequence[Icd11Code | str] = (),
    ) -> ClaimLine:
        try:
            line = NewClaimLine(
                intervention_code=InterventionCode.of(intervention),
                unit_price=unit_price,
                quantity=quantity,
                scheme_code=SchemeCode.of(scheme_code) if scheme_code is not None else None,
                charge_date=charge_date,
                diagnoses=tuple(Icd11Code.of(d) for d in diagnoses),
            )
        except ValueError as exc:
            raise RequestValidationError([Violation("line", str(exc))]) from exc
        return await self._gateway.add_line(self.consent_token, line)

    async def remove_line(self, line: LineGuid | str) -> None:
        await self._gateway.remove_line(self.consent_token, LineGuid.of(line))

    async def edit_line(
        self,
        line: LineGuid | str,
        *,
        quantity: int | None = None,
        unit_price: Money | None = None,
        scheme_code: SchemeCode | str | None = None,
    ) -> ClaimLine:
        try:
            edit = LineEdit(
                LineGuid.of(line),
                quantity,
                unit_price,
                SchemeCode.of(scheme_code) if scheme_code is not None else None,
            )
        except ValueError as exc:
            raise RequestValidationError([Violation("line", str(exc))]) from exc
        return await self._gateway.edit_line(edit)

    # ── attachments ──

    async def attach(self, attachment: Attachment, intervention: InterventionCode | str) -> ClaimAttachment:
        return await self._gateway.add_attachment(
            self.consent_token, attachment, InterventionCode.of(intervention)
        )

    async def remove_attachment(
        self, attachment: AttachmentId | str, intervention: InterventionCode | str
    ) -> None:
        await self._gateway.remove_attachment(
            self.consent_token, AttachmentId.of(attachment), InterventionCode.of(intervention)
        )

    # ── lifecycle ──

    async def preview(self) -> VirtualClaim:
        """`POST /claims/preview` — the claim as the server sees it. Safe to call any time; refreshes `claim`."""
        self.claim = await self._gateway.preview(self.consent_token)
        return self.claim

    async def submit(
        self,
        invoice_number: InvoiceNumber | str | None = None,
        *,
        reason_for_unknown_patient: str | None = None,
    ) -> VirtualClaim:
        """`POST /claims/submit` — final. Attempted once; on ambiguity raises SubmissionOutcomeUnknownError."""
        invoice = InvoiceNumber.of(invoice_number) if invoice_number is not None else None
        self.claim = await self._submit.execute(self.consent_token, invoice, reason_for_unknown_patient)
        return self.claim

    async def close(self, reason: CancelReason, text: str) -> VirtualClaim:
        """`POST /claims/close` — abandon a claim that will not be submitted."""
        if not text.strip():
            raise RequestValidationError([Violation("cancel_reason_text", "cannot be empty")])
        self.claim = await self._gateway.close(self.consent_token, reason, text.strip())
        return self.claim

    async def payer_status(self, provider_claim_no: str) -> tuple[PayerClaimRecord, ...]:
        """`GET /claims/preview/payer` — how the payer sees the submitted claim."""
        if self.claim is None or self.claim.guid is None:
            await self.preview()
        assert self.claim is not None
        if self.claim.guid is None:
            raise RequestValidationError([Violation("claim", "server has not assigned a claim GUID yet")])
        return await self._gateway.payer_status(self.claim.guid, provider_claim_no)
