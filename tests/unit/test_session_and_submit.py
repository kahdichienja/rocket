"""ClaimSession + SubmitClaim against an in-memory gateway. No HTTP."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from sha_claim.domain.attachments import Attachment
from sha_claim.domain.claim import (
    ClaimAttachment,
    ClaimDiagnosis,
    ClaimIntervention,
    ClaimLine,
    Discharge,
    LineEdit,
    LineResubmission,
    NewClaimLine,
    NextOfKin,
    NextOfKinContact,
    PayerClaimRecord,
    VirtualClaim,
)
from sha_claim.domain.codes import DocumentType, Icd11Code, InterventionCode, RegulationBody
from sha_claim.domain.consent import ConsentProof, Otp
from sha_claim.domain.enums import CancelReason, DischargeReason, NextOfKinIdType, ServiceType
from sha_claim.domain.identifiers import (
    AttachmentId,
    ClaimGuid,
    ConsentToken,
    InvoiceNumber,
    LineGuid,
    PatientId,
)
from sha_claim.domain.money import Money
from sha_claim.domain.practitioner import PractitionerRef
from sha_claim.domain.preauth import DoctorConsentRequest, PreauthItem, Preauthorization, PreauthRequest
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

    async def send_discharge_otp(self, token: ConsentToken, patient: PatientId) -> str:
        self._rec("send_discharge_otp", token, patient)
        return "OTP sent"

    async def discharge(self, token: ConsentToken, discharge: Discharge) -> VirtualClaim:
        self._rec("discharge", token, discharge)
        return claim("DISCHARGED")

    async def add_next_of_kin(self, token: ConsentToken, next_of_kin: NextOfKin) -> NextOfKinContact:
        self._rec("add_next_of_kin", token, next_of_kin)
        return NextOfKinContact(
            "nk",
            next_of_kin.full_name,
            next_of_kin.id_number,
            next_of_kin.contact_value,
            "PHONE",
            False,
            False,
            True,
        )

    async def resubmit_lines(self, token: ConsentToken) -> LineResubmission:
        self._rec("resubmit_lines", token)
        return LineResubmission(LineGuid("L1"), "RESUBMITTED", "ok")

    async def payer_status(
        self, claim_guid: ClaimGuid, provider_claim_no: str
    ) -> tuple[PayerClaimRecord, ...]:
        self._rec("payer_status", claim_guid, provider_claim_no)
        return (
            PayerClaimRecord("g", provider_claim_no, "TRK", "RECEIVED", "", "OP", False, None, None, None),
        )


class FakePreauths:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    async def create(self, token: ConsentToken, request: PreauthRequest) -> Preauthorization:
        self.calls.append(("create", (token, request)))
        return preauth()

    async def list(self, token: ConsentToken) -> tuple[Preauthorization, ...]:
        self.calls.append(("list", (token,)))
        return (preauth(),)

    async def remove_diagnosis(
        self, token: ConsentToken, icd: Icd11Code, intervention: InterventionCode
    ) -> Preauthorization:
        self.calls.append(("remove_diagnosis", (token, icd, intervention)))
        return preauth()

    async def remove_doctor(
        self, token: ConsentToken, intervention: InterventionCode, registration_number: str
    ) -> None:
        self.calls.append(("remove_doctor", (token, intervention, registration_number)))

    async def cancel(self, token: ConsentToken, intervention: InterventionCode) -> Preauthorization:
        self.calls.append(("cancel", (token, intervention)))
        return preauth()

    async def request_doctor_consent(self, token: ConsentToken, request: DoctorConsentRequest) -> str:
        self.calls.append(("doctor_consent", (token, request)))
        return "sent"


def preauth() -> Preauthorization:
    return Preauthorization(
        "pg", "pt", CODE, "PENDING", "", True, False, 1, True, False, Money.kes(100), None, None
    )


async def test_session_threads_the_token_and_coerces_strings() -> None:
    gw = FakeGateway()
    s = ClaimSession(gw, FakePreauths(), TOKEN)
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
    s = ClaimSession(gw, FakePreauths(), TOKEN)
    with pytest.raises(RequestValidationError, match="quantity"):
        await s.add_line(CODE, Money.kes(1), 0)
    with pytest.raises(RequestValidationError, match="at least one"):
        await s.edit_line("L1")
    with pytest.raises(RequestValidationError, match="cancel_reason_text"):
        await s.close(CancelReason.OTHER_REASONS, "  ")
    assert gw.calls == []


async def test_lifecycle_refreshes_snapshot() -> None:
    gw = FakeGateway()
    s = ClaimSession(gw, FakePreauths(), TOKEN, claim())
    assert (await s.preview()).workflow_state == "PREVIEWED"
    assert (await s.submit("INV-1")).workflow_state == "SUBMITTED"
    assert s.claim is not None and s.claim.workflow_state == "SUBMITTED"
    assert gw.calls[-1] == ("submit", (TOKEN, InvoiceNumber("INV-1"), None))
    assert (await s.close(CancelReason.WRONG_PATIENT, "typo")).workflow_state == "CLOSED"


async def test_payer_status_previews_first_when_no_guid() -> None:
    gw = FakeGateway()
    s = ClaimSession(gw, FakePreauths(), TOKEN)  # resumed from a bare token
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


async def test_preauth_flow_through_session() -> None:
    gw, pa = FakeGateway(), FakePreauths()
    s = ClaimSession(gw, pa, TOKEN)
    doctor = PractitionerRef.registered("A1234", RegulationBody.KMPDC)
    start = datetime(2026, 9, 20, 8, tzinfo=UTC)
    created = await s.request_preauth(
        "sha-08-006",
        service_start=start,
        service_end=start.replace(hour=12),
        items=[PreauthItem("CS", "Cesarean section", 1, Money.kes("30000"))],
        diagnoses=["JB0Z"],
        doctors=[doctor],
        notification_email="claims@facility.example",
    )
    assert created.awaiting_doctor and not created.decided
    assert (await s.preauths())[0].guid == "pg"
    await s.remove_preauth_diagnosis("JB0Z", "SHA-08-006")
    await s.remove_preauth_doctor("SHA-08-006", "A1234")
    await s.cancel_preauth("SHA-08-006")
    assert await s.request_doctor_consent("SHA-08-006", doctor) == "sent"

    names = [c[0] for c in pa.calls]
    assert names == ["create", "list", "remove_diagnosis", "remove_doctor", "cancel", "doctor_consent"]
    request = pa.calls[0][1][1]
    assert request.intervention_code == InterventionCode(
        "SHA-08-006"
    ) and request.estimated_total == Money.kes(30000)
    assert pa.calls[5][1][1].request_type.value == "PREAUTH_DOCTOR_APPROVAL_REQUEST"
    assert gw.calls == []


async def test_preauth_local_validation() -> None:
    s = ClaimSession(FakeGateway(), FakePreauths(), TOKEN)
    start = datetime(2026, 9, 20, 8, tzinfo=UTC)
    items = [PreauthItem("CS", "x", 1, Money.kes(1))]
    with pytest.raises(RequestValidationError, match="service_end"):
        await s.request_preauth(
            CODE,
            service_start=start,
            service_end=start.replace(hour=7),
            items=items,
            diagnoses=["JB0Z"],
            doctors=[],
            notification_email="a@b.co",
        )
    with pytest.raises(RequestValidationError, match="email"):
        await s.request_preauth(
            CODE,
            service_start=start,
            service_end=start,
            items=items,
            diagnoses=["JB0Z"],
            doctors=[],
            notification_email="nope",
        )
    with pytest.raises(RequestValidationError, match="diagnosis"):
        await s.request_preauth(
            CODE,
            service_start=start,
            service_end=start,
            items=items,
            diagnoses=[],
            doctors=[],
            notification_email="a@b.co",
        )
    with pytest.raises(RequestValidationError, match="item"):
        await s.request_preauth(
            CODE,
            service_start=start,
            service_end=start,
            items=[],
            diagnoses=["JB0Z"],
            doctors=[],
            notification_email="a@b.co",
        )


async def test_inpatient_discharge_flow() -> None:
    from datetime import date

    gw = FakeGateway()
    s = ClaimSession(gw, FakePreauths(), TOKEN, claim())
    contact = await s.add_next_of_kin(
        full_name="Jane Doe",
        id_number="1",
        id_type=NextOfKinIdType.NATIONAL_ID,
        contact_value="+254700000000",
    )
    assert contact.is_main_contact
    assert await s.send_discharge_otp("CR1") == "OTP sent"
    discharged = await s.discharge(
        discharge_date=date(2026, 9, 21),
        reason=DischargeReason.RECOVERED,
        invoice_number="INV-1",
        otp="123456",
    )
    assert discharged.workflow_state == "DISCHARGED" and s.claim is discharged
    assert (await s.resubmit_lines()).status == "RESUBMITTED"
    names = [c[0] for c in gw.calls]
    assert names == ["add_next_of_kin", "send_discharge_otp", "discharge", "resubmit_lines"]
    command = gw.calls[2][1][1]
    assert command.otp == Otp("123456") and command.invoice_number == InvoiceNumber("INV-1")


async def test_next_of_kin_validation() -> None:
    s = ClaimSession(FakeGateway(), FakePreauths(), TOKEN)
    with pytest.raises(RequestValidationError, match="contact_value"):
        await s.add_next_of_kin(
            full_name="J", id_number="1", id_type=NextOfKinIdType.NATIONAL_ID, contact_value=" "
        )
