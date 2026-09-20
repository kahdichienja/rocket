"""ClaimSession + SubmitClaim against an in-memory gateway. No HTTP."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

import pytest

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
from sha_claim.domain.codes import DocumentType, Icd11Code, InterventionCode
from sha_claim.domain.consent import ConsentProof
from sha_claim.domain.enums import CancelReason, ServiceType
from sha_claim.domain.identifiers import (
    AttachmentId,
    ClaimGuid,
    ConsentToken,
    InvoiceNumber,
    LineGuid,
    PatientId,
)
from sha_claim.domain.money import Money
from sha_claim.errors import RequestValidationError, SubmissionOutcomeUnknownError, TransportError
from sha_claim.session import ClaimSession
from sha_claim.use_cases.submit_claim import SubmitClaim

TOKEN = ConsentToken("CR1-TOKEN12345")
CODE = InterventionCode("SHA-12-001")


def claim(state: str = "DRAFT", guid: str | None = "G") -> VirtualClaim:
    return VirtualClaim(
        TOKEN,
        ClaimGuid(guid) if guid else None,
        1,
        state,
        "",
        ServiceType.CAPITATION,
        "",
        "",
        "",
        "",
        "KES",
        None,
        None,
    )


class FakeGateway:
    def __init__(self, fail_submit: Exception | None = None) -> None:
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.fail_submit = fail_submit

    def _rec(self, name: str, *args: Any) -> None:
        self.calls.append((name, args))

    async def open_visit(
        self,
        patient: PatientId,
        service_type: ServiceType,
        interventions: Sequence[InterventionCode],
        proof: ConsentProof,
    ) -> VirtualClaim:
        return claim()

    async def add_intervention(self, token: ConsentToken, code: InterventionCode) -> ClaimIntervention:
        self._rec("add_intervention", token, code)
        return ClaimIntervention(code, "", None, False, False, "ACTIVE")

    async def retire_intervention(self, token: ConsentToken, code: InterventionCode) -> None:
        self._rec("retire", token, code)

    async def restore_intervention(self, token: ConsentToken, code: InterventionCode) -> None:
        self._rec("restore", token, code)

    async def add_diagnosis(
        self, token: ConsentToken, icd: Icd11Code, intervention: InterventionCode
    ) -> ClaimDiagnosis:
        self._rec("add_diagnosis", token, icd, intervention)
        return ClaimDiagnosis(icd, "", intervention)

    async def remove_diagnosis(
        self, token: ConsentToken, icd: Icd11Code, intervention: InterventionCode
    ) -> None:
        self._rec("remove_diagnosis", token, icd, intervention)

    async def add_line(self, token: ConsentToken, line: NewClaimLine) -> ClaimLine:
        self._rec("add_line", token, line)
        return ClaimLine(
            LineGuid("L1"),
            line.intervention_code,
            "",
            "",
            Decimal(line.quantity),
            line.unit_price,
            line.total,
            line.total,
        )

    async def remove_line(self, token: ConsentToken, line: LineGuid) -> None:
        self._rec("remove_line", token, line)

    async def edit_line(self, edit: LineEdit) -> ClaimLine:
        self._rec("edit_line", edit)
        return ClaimLine(edit.line, None, "", "", Decimal(1), None, None, None)

    async def add_attachment(
        self, token: ConsentToken, attachment: Attachment, intervention: InterventionCode
    ) -> ClaimAttachment:
        self._rec("attach", token, attachment.filename, intervention)
        return ClaimAttachment(
            AttachmentId("A1"), attachment.filename, attachment.document_type.value, intervention
        )

    async def remove_attachment(
        self, token: ConsentToken, attachment: AttachmentId, intervention: InterventionCode
    ) -> None:
        self._rec("remove_attachment", token, attachment, intervention)

    async def preview(self, token: ConsentToken) -> VirtualClaim:
        self._rec("preview", token)
        return claim("PREVIEWED")

    async def submit(
        self, token: ConsentToken, invoice: InvoiceNumber | None, reason: str | None
    ) -> VirtualClaim:
        self._rec("submit", token, invoice, reason)
        if self.fail_submit:
            raise self.fail_submit
        return claim("SUBMITTED")

    async def close(self, token: ConsentToken, reason: CancelReason, text: str) -> VirtualClaim:
        self._rec("close", token, reason, text)
        return claim("CLOSED")

    async def payer_status(
        self, claim_guid: ClaimGuid, provider_claim_no: str
    ) -> tuple[PayerClaimRecord, ...]:
        self._rec("payer_status", claim_guid, provider_claim_no)
        return (PayerClaimRecord({"status": "RECEIVED"}),)


async def test_session_threads_the_token_and_coerces_strings() -> None:
    gw = FakeGateway()
    s = ClaimSession(gw, TOKEN)
    await s.add_intervention("sha-12-001")
    await s.add_diagnosis("1a00", "SHA-12-001")
    line = await s.add_line("SHA-12-001", Money.kes("100"), 2, diagnoses=["1A00"])
    await s.remove_line("L1")
    await s.edit_line("L1", quantity=3)
    await s.attach(Attachment("x.pdf", b"%PDF", DocumentType.INVOICE), CODE)
    await s.remove_attachment("A1", CODE)
    await s.retire_intervention(CODE)
    await s.restore_intervention(CODE)
    await s.remove_diagnosis("1A00", CODE)

    assert line.total_amount == Money.kes(200)
    names = [c[0] for c in gw.calls]
    assert names == [
        "add_intervention",
        "add_diagnosis",
        "add_line",
        "remove_line",
        "edit_line",
        "attach",
        "remove_attachment",
        "retire",
        "restore",
        "remove_diagnosis",
    ]
    assert all(c[1][0] == TOKEN for c in gw.calls if c[0] not in {"edit_line"})
    assert gw.calls[0][1][1] == CODE  # coerced and upper-cased
    assert gw.calls[1][1][1] == Icd11Code("1A00")


async def test_session_local_validation_short_circuits() -> None:
    gw = FakeGateway()
    s = ClaimSession(gw, TOKEN)
    with pytest.raises(RequestValidationError, match="quantity"):
        await s.add_line(CODE, Money.kes(1), 0)
    with pytest.raises(RequestValidationError, match="at least one"):
        await s.edit_line("L1")
    with pytest.raises(RequestValidationError, match="cancel_reason_text"):
        await s.close(CancelReason.OTHER_REASONS, "  ")
    assert gw.calls == []


async def test_lifecycle_refreshes_snapshot() -> None:
    gw = FakeGateway()
    s = ClaimSession(gw, TOKEN, claim())
    assert (await s.preview()).workflow_state == "PREVIEWED"
    assert (await s.submit("INV-1")).workflow_state == "SUBMITTED"
    assert s.claim is not None and s.claim.workflow_state == "SUBMITTED"
    assert gw.calls[-1] == ("submit", (TOKEN, InvoiceNumber("INV-1"), None))
    assert (await s.close(CancelReason.WRONG_PATIENT, "typo")).workflow_state == "CLOSED"


async def test_payer_status_previews_first_when_no_guid() -> None:
    gw = FakeGateway()
    s = ClaimSession(gw, TOKEN)  # resumed from a bare token
    records = await s.payer_status("INV-1")
    assert [c[0] for c in gw.calls] == ["preview", "payer_status"]
    assert records[0].status == "RECEIVED"


async def test_submit_is_attempted_once_and_ambiguity_is_explicit() -> None:
    gw = FakeGateway(fail_submit=TransportError("timeout", trace_id="t-9"))
    with pytest.raises(SubmissionOutcomeUnknownError) as exc:
        await SubmitClaim(gw).execute(TOKEN, InvoiceNumber("INV-1"))
    assert exc.value.trace_id == "t-9"
    assert "preview()" in str(exc.value)
    assert "CR1-TOKEN12345" not in str(exc.value)  # token redacted in the message
    assert len([c for c in gw.calls if c[0] == "submit"]) == 1
