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
    Submission,
    VirtualClaim,
)
from sha_claim.domain.codes import DocumentType, Icd11Code, InterventionCode, ProtocolCode, RegulationBody
from sha_claim.domain.consent import ConsentProof, Otp
from sha_claim.domain.emergency import EmergencyCase, EmergencyProtocol, EmtClaim, ProtocolLine
from sha_claim.domain.enums import (
    BroughtBy,
    CancelReason,
    ClaimWorkflowState,
    DischargeReason,
    ModeOfArrival,
    NextOfKinIdType,
    PaymentMechanism,
    ServiceType,
)
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
from sha_claim.domain.prescription import (
    Dispense,
    DispensedProduct,
    DispenseRequest,
    MedicationOrder,
    Prescription,
    PrescriptionRequest,
)
from sha_claim.errors import RequestValidationError, SubmissionOutcomeUnknownError, TransportError
from sha_claim.ports.claim_gateways import ClaimGateways
from sha_claim.session import ClaimSession
from sha_claim.use_cases.submit_claim import SubmitClaim

TOKEN = ConsentToken("CR1-TOKEN12345")
CODE = InterventionCode("SHA-12-001")


def claim(state: str = "DRAFT", guid: str | None = "G") -> VirtualClaim:
    return VirtualClaim(
        TOKEN,
        ClaimGuid(guid) if guid else None,
        1,
        ClaimWorkflowState(state),
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

    async def switch_intervention(
        self,
        token: ConsentToken,
        existing: InterventionCode,
        new: InterventionCode,
        retain_bill_items: bool,
        bill_from: datetime | None,
        bill_to: datetime | None,
    ) -> None:
        self._rec("switch", token, existing, new, retain_bill_items)

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

    async def add_doctor(self, token: ConsentToken, doctor: PractitionerRef) -> str:
        self._rec("add_doctor", token, doctor)
        return "added"

    async def preview(self, token: ConsentToken) -> VirtualClaim:
        self._rec("preview", token)
        return claim("PREVIEWED")

    async def submit(self, token: ConsentToken, submission: Submission) -> VirtualClaim:
        self._rec("submit", token, submission.invoice_number, submission.reason_for_unknown_patient)
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

    async def set_coverage(self, token: ConsentToken, selection: Any) -> None:
        self._rec("set_coverage", token, selection)

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


class FakePrescriptions:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    async def create(self, token: ConsentToken, request: PrescriptionRequest) -> Prescription:
        self.calls.append(("create", (token, request)))
        return Prescription("rx", "RX-1", "ACTIVE", "", request.intervention_code, ())

    async def get(self, token: ConsentToken) -> Prescription | None:
        self.calls.append(("get", (token,)))
        return None

    async def dispense(self, token: ConsentToken, request: DispenseRequest) -> Dispense:
        self.calls.append(("dispense", (token, request)))
        return Dispense(1, "DISPENSED", ())

    async def remove_doctor(
        self, token: ConsentToken, intervention: InterventionCode, registration_number: str
    ) -> None:
        self.calls.append(("remove_doctor", (token, intervention, registration_number)))


class FakeEmergency:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    async def open_case(self, case: EmergencyCase) -> VirtualClaim:
        self.calls.append(("open_case", (case,)))
        return claim("EMERGENCY")

    async def protocols(self, intervention: InterventionCode, active: bool) -> tuple[EmergencyProtocol, ...]:
        self.calls.append(("protocols", (intervention, active)))
        return (EmergencyProtocol(ProtocolCode("EP-1"), "Resus", "TREATMENT", "", "ACTIVE", Money.kes(5000)),)

    async def add_protocol(self, token: ConsentToken, line: ProtocolLine) -> ClaimLine:
        self.calls.append(("add_protocol", (token, line)))
        return ClaimLine(
            LineGuid("L9"),
            line.intervention_code,
            line.protocol_code.value,
            "",
            Decimal(line.quantity),
            line.unit_price,
            None,
            None,
        )

    async def add_doctor(self, token: ConsentToken, doctor: PractitionerRef) -> str:
        self.calls.append(("add_doctor", (token, doctor)))
        return "added"

    async def remove_doctor(self, token: ConsentToken) -> None:
        self.calls.append(("remove_doctor", (token,)))

    async def open_emt(self, token: ConsentToken, emt: EmtClaim) -> VirtualClaim:
        self.calls.append(("open_emt", (token, emt)))
        return claim("EMT")


def gateways(
    claims: FakeGateway | None = None,
    preauths: FakePreauths | None = None,
    prescriptions: FakePrescriptions | None = None,
    emergency: FakeEmergency | None = None,
) -> ClaimGateways:
    return ClaimGateways(
        claims or FakeGateway(),
        preauths or FakePreauths(),
        prescriptions or FakePrescriptions(),
        emergency or FakeEmergency(),
    )


def preauth() -> Preauthorization:
    return Preauthorization(
        "pg", "pt", CODE, "PENDING", "", True, False, 1, True, False, Money.kes(100), None, None
    )


async def test_session_threads_the_token_and_coerces_strings() -> None:
    gw = FakeGateway()
    s = ClaimSession(gateways(claims=gw), TOKEN)
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
    s = ClaimSession(gateways(claims=gw), TOKEN)
    with pytest.raises(RequestValidationError, match="quantity"):
        await s.add_line(CODE, Money.kes(1), 0)
    with pytest.raises(RequestValidationError, match="at least one"):
        await s.edit_line("L1")
    with pytest.raises(RequestValidationError, match="cancel_reason_text"):
        await s.close(CancelReason.OTHER_REASONS, "  ")
    assert gw.calls == []


async def test_lifecycle_refreshes_snapshot() -> None:
    gw = FakeGateway()
    s = ClaimSession(gateways(claims=gw), TOKEN, claim())
    assert (await s.preview()).workflow_state == "PREVIEWED"
    assert (await s.submit("INV-1")).workflow_state == "SUBMITTED"
    assert s.claim is not None and s.claim.workflow_state == "SUBMITTED"
    assert gw.calls[-1] == ("submit", (TOKEN, InvoiceNumber("INV-1"), None))
    assert (await s.close(CancelReason.WRONG_PATIENT, "typo")).workflow_state == "CLOSED"


async def test_payer_status_previews_first_when_no_guid() -> None:
    gw = FakeGateway()
    s = ClaimSession(gateways(claims=gw), TOKEN)  # resumed from a bare token
    records = await s.payer_status("INV-1")
    assert [c[0] for c in gw.calls] == ["preview", "payer_status"]
    assert records[0].status == "RECEIVED"


async def test_submit_is_attempted_once_and_ambiguity_is_explicit() -> None:
    gw = FakeGateway(fail_submit=TransportError("timeout", trace_id="t-9"))
    with pytest.raises(SubmissionOutcomeUnknownError) as exc:
        await SubmitClaim(gw).execute(TOKEN, Submission(InvoiceNumber("INV-1")))
    assert exc.value.trace_id == "t-9"
    assert "preview()" in str(exc.value)
    assert "CR1-TOKEN12345" not in str(exc.value)  # token redacted in the message
    assert len([c for c in gw.calls if c[0] == "submit"]) == 1


async def test_preauth_flow_through_session() -> None:
    gw, pa = FakeGateway(), FakePreauths()
    s = ClaimSession(gateways(claims=gw, preauths=pa), TOKEN)
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
    s = ClaimSession(gateways(), TOKEN)
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

    gw = FakeGateway()
    s = ClaimSession(gateways(claims=gw), TOKEN, claim())
    contact = await s.add_next_of_kin(
        full_name="Jane Doe",
        id_number="1",
        id_type=NextOfKinIdType.NATIONAL_ID,
        contact_value="+254700000000",
    )
    assert contact.is_main_contact
    assert await s.send_discharge_otp("CR1111111111111-1") == "OTP sent"
    discharged = await s.discharge(
        reason=DischargeReason.RECOVERED,
        invoice_number="INV-1",
        otp="123456",
        discharged_at=datetime(2026, 9, 21, 10, tzinfo=UTC),
    )
    assert discharged.workflow_state == "DISCHARGED" and s.claim is discharged
    assert (await s.resubmit_lines()).status == "RESUBMITTED"
    names = [c[0] for c in gw.calls]
    assert names == ["add_next_of_kin", "send_discharge_otp", "discharge", "resubmit_lines"]
    command = gw.calls[2][1][1]
    assert command.otp == Otp("123456") and command.invoice_number == InvoiceNumber("INV-1")


async def test_next_of_kin_validation() -> None:
    s = ClaimSession(gateways(), TOKEN)
    with pytest.raises(RequestValidationError, match="contact_value"):
        await s.add_next_of_kin(
            full_name="J", id_number="1", id_type=NextOfKinIdType.NATIONAL_ID, contact_value=" "
        )


async def test_prescription_flow_through_session() -> None:
    from datetime import date

    rx = FakePrescriptions()
    s = ClaimSession(gateways(prescriptions=rx), TOKEN)
    order = MedicationOrder("AMOX500", 1, "TABLET", 3, "DAY", 5, "DAY", date(2026, 9, 20))
    doctor = PractitionerRef.registered("A1", RegulationBody.KMPDC)
    created = await s.prescribe("sha-12-004", [order], prescriber=doctor)
    assert created.code == "RX-1" and created.intervention_code == InterventionCode("SHA-12-004")
    assert await s.prescription() is None
    dispensed = await s.dispense(
        "SHA-12-004", [DispensedProduct("AMOX500-GEN", 15, Money.kes("12.50"))], [doctor]
    )
    assert dispensed.status == "DISPENSED"
    await s.remove_prescription_doctor("SHA-12-004", "A1")
    assert [c[0] for c in rx.calls] == ["create", "get", "dispense", "remove_doctor"]
    assert all(c[1][0] == TOKEN for c in rx.calls)


async def test_prescription_local_validation() -> None:
    from datetime import date

    s = ClaimSession(gateways(), TOKEN)
    with pytest.raises(RequestValidationError, match="medication"):
        await s.prescribe(CODE, [])
    with pytest.raises(RequestValidationError, match="dispensing practitioner"):
        await s.dispense(CODE, [DispensedProduct("P", 1, Money.kes(1))], [])
    with pytest.raises(ValueError, match="dose_quantity"):
        MedicationOrder("X", 0, "TAB", 1, "DAY", 1, "DAY", date(2026, 1, 1))
    with pytest.raises(ValueError, match="refill"):
        MedicationOrder("X", 1, "TAB", 1, "DAY", 1, "DAY", date(2026, 1, 1), needs_refill=True)
    with pytest.raises(ValueError, match="end_date"):
        MedicationOrder("X", 1, "TAB", 1, "DAY", 1, "DAY", date(2026, 1, 2), end_date=date(2026, 1, 1))


async def test_emergency_flow_through_session() -> None:
    em = FakeEmergency()
    s = ClaimSession(gateways(emergency=em), TOKEN)
    doctor = PractitionerRef.registered("A1", RegulationBody.KMPDC)
    line = await s.add_protocol("EP-1", "SHA-19-001", Money.kes(5000), 2, diagnoses=["NF0A"])
    assert line.item_code == "EP-1" and line.quantity == 2
    assert await s.add_emergency_doctor(doctor) == "added"
    await s.remove_emergency_doctor()
    emt = EmtClaim(
        ProtocolCode("EP-1"),
        "CASE-1",
        "A1",
        "AMB-9",
        PatientId("CR1111111111111-1"),
        Otp("123456"),
        (Icd11Code("NF0A"),),
        (InterventionCode("SHA-19-001"),),
    )
    assert (await s.open_emt_claim(emt)).workflow_state == "EMT"
    assert [c[0] for c in em.calls] == ["add_protocol", "add_doctor", "remove_doctor", "open_emt"]
    with pytest.raises(RequestValidationError, match="quantity"):
        await s.add_protocol("EP-1", "SHA-19-001", Money.kes(1), 0)


def test_emergency_command_invariants() -> None:
    doctor = PractitionerRef.registered("A1", RegulationBody.KMPDC)
    with pytest.raises(ValueError, match="reference_number"):
        EmergencyCase(doctor, " ", BroughtBy.RELATIVE, ModeOfArrival.WALK_IN, (CODE,), notes="x")
    with pytest.raises(ValueError, match="intervention"):
        EmergencyCase(doctor, "REF", BroughtBy.RELATIVE, ModeOfArrival.WALK_IN, (), notes="x")
    with pytest.raises(ValueError, match="notes"):
        EmergencyCase(doctor, "REF", BroughtBy.RELATIVE, ModeOfArrival.WALK_IN, (CODE,), notes=" ")
    with pytest.raises(ValueError, match="case_number"):
        EmtClaim(
            ProtocolCode("P"),
            "",
            "A1",
            "AMB",
            PatientId("CR1111111111111-1"),
            Otp("1"),
            (Icd11Code("NF0A"),),
            (CODE,),
        )
    with pytest.raises(ValueError, match="diagnosis"):
        EmtClaim(ProtocolCode("P"), "C", "A1", "AMB", PatientId("CR1111111111111-1"), Otp("1"), (), (CODE,))


async def test_switch_intervention() -> None:
    gw = FakeGateway()
    await ClaimSession(gateways(claims=gw), TOKEN).switch_intervention(
        "SHA-12-001", "sha-12-002", retain_bill_items=False
    )
    assert gw.calls == [
        ("switch", (TOKEN, InterventionCode("SHA-12-001"), InterventionCode("SHA-12-002"), False))
    ]


async def test_submit_forwards_discharge_fields_and_add_doctor() -> None:
    from sha_claim.domain.enums import DischargeReason

    gw = FakeGateway()
    s = ClaimSession(gateways(claims=gw), TOKEN, claim())
    await s.add_doctor(PractitionerRef.registered("A1", RegulationBody.KMPDC))
    await s.submit("INV-1", discharge_reason=DischargeReason.RECOVERED, otp="123456")
    assert gw.calls[0][0] == "add_doctor"
    assert gw.calls[1] == ("submit", (TOKEN, InvoiceNumber("INV-1"), None))


async def test_switch_with_retained_bill_items_needs_both_dates() -> None:
    s = ClaimSession(gateways(claims=FakeGateway()), TOKEN)
    with pytest.raises(RequestValidationError, match="bill_from/bill_to"):
        await s.switch_intervention("SHA-12-001", "SHA-12-002", retain_bill_items=True)
    with pytest.raises(RequestValidationError):
        await s.switch_intervention(
            "SHA-12-001", "SHA-12-002", retain_bill_items=True, bill_from=datetime(2026, 9, 1, tzinfo=UTC)
        )
    await s.switch_intervention("SHA-12-001", "SHA-12-002", retain_bill_items=False)  # no dates needed
    assert ClaimIntervention(
        InterventionCode("SHA-1"), "x", PaymentMechanism.CAPITATION, False, False, " active "
    ).is_active
    assert not ClaimIntervention(
        InterventionCode("SHA-1"), "x", PaymentMechanism.CAPITATION, False, False, "RETIRED"
    ).is_active


async def test_set_coverage_validates_then_forwards() -> None:
    gw = FakeGateway()
    s = ClaimSession(gateways(claims=gw), TOKEN)
    with pytest.raises(RequestValidationError, match="coverage"):
        await s.set_coverage("CR1111111111111-1", " ")
    await s.set_coverage("CR1111111111111-1", "POMSF-1")
    assert gw.calls[-1][0] == "set_coverage"


async def test_remove_doctor_and_its_emergency_alias_hit_one_endpoint() -> None:
    gw = FakeEmergency()
    s = ClaimSession(gateways(emergency=gw), TOKEN)
    await s.remove_doctor()
    await s.remove_emergency_doctor()
    assert [c[0] for c in gw.calls] == ["remove_doctor", "remove_doctor"]
