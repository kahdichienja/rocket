"""ClaimSession: a virtual claim's handle plus every operation on it, so callers never thread the token."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime
from decimal import Decimal

from sha_claim.domain.attachments import Attachment
from sha_claim.domain.claim import (
    ClaimAttachment,
    ClaimDiagnosis,
    ClaimIntervention,
    ClaimLine,
    CoverageSelection,
    Discharge,
    LineAttachment,
    LineEdit,
    LineResubmission,
    NewClaimLine,
    NextOfKin,
    NextOfKinContact,
    PayerClaimRecord,
    Submission,
    VirtualClaim,
)
from sha_claim.domain.codes import Icd11Code, InterventionCode, ProtocolCode, SchemeCode
from sha_claim.domain.consent import Otp
from sha_claim.domain.emergency import EmtClaim, ProtocolLine
from sha_claim.domain.enums import (
    CancelReason,
    DischargeReason,
    DoctorConsentRequestType,
    NextOfKinIdType,
    ServiceType,
)
from sha_claim.domain.identifiers import AttachmentId, ConsentToken, InvoiceNumber, LineGuid, PatientId
from sha_claim.domain.money import Money
from sha_claim.domain.practitioner import PractitionerRef
from sha_claim.domain.preauth import (
    DoctorConsentRequest,
    PreauthDetails,
    PreauthItem,
    Preauthorization,
    PreauthRequest,
)
from sha_claim.domain.prescription import (
    Dispense,
    DispensedProduct,
    DispenseRequest,
    MedicationOrder,
    Prescription,
    PrescriptionRequest,
)
from sha_claim.domain.schemes import scheme_family
from sha_claim.errors import RequestValidationError, Violation
from sha_claim.ports.claim_gateways import ClaimGateways
from sha_claim.use_cases.submit_claim import SubmitClaim


class ClaimSession:
    """Operations on one server-side virtual claim.

    `claim` is the latest snapshot the server returned (refreshed by `preview`, `submit`, `close`);
    it may be `None` for a session resumed from a bare token until `preview()` is called.
    """

    def __init__(
        self, gateways: ClaimGateways, token: ConsentToken, claim: VirtualClaim | None = None
    ) -> None:
        self._gateway = gateways.claims
        self._preauths = gateways.preauths
        self._prescriptions = gateways.prescriptions
        self._emergency = gateways.emergency
        self._submit = SubmitClaim(gateways.claims)
        self.consent_token = token
        self.claim = claim

    # ── interventions ──

    async def add_intervention(self, code: InterventionCode | str) -> ClaimIntervention:
        """`POST /claims/interventions` — add a service to the open visit.

        DHA rules: the visit must be active; the code must be a recognised intervention; it must not
        break combination rules with what is already on the visit (e.g. no mixing IP and OP interventions).

        **One active per-diem at a time.** A claim may carry only one, so moving a patient between wards
        (General → ICU) is `switch_intervention`, not a second `add_intervention` beside the first. Whether
        a *new* code is per-diem is not on the claim snapshot — it comes from the coverage catalogue — so
        this cannot check it before calling; `claim.active_per_diem` says what the visit is already on, and
        `submission_blockers` reports `MULTIPLE_ACTIVE_PER_DIEM` if two ever end up active.
        """
        return await self._gateway.add_intervention(self.consent_token, InterventionCode.of(code))

    async def retire_intervention(self, code: InterventionCode | str) -> None:
        """`POST /claims/interventions/retire` — logically remove an ACTIVE intervention.

        DHA refuses when the intervention has bill items, has a diagnosis linked to it, or is a per-diem
        intervention. Remove lines/diagnoses first, or use `switch_intervention` to carry them over.
        """
        await self._gateway.retire_intervention(self.consent_token, InterventionCode.of(code))

    async def restore_intervention(self, code: InterventionCode | str) -> None:
        """`POST /claims/interventions/restore` — reinstate a retired intervention (only retired ones)."""
        await self._gateway.restore_intervention(self.consent_token, InterventionCode.of(code))

    async def switch_intervention(
        self,
        existing: InterventionCode | str,
        new: InterventionCode | str,
        *,
        retain_bill_items: bool = True,
        bill_from: datetime | None = None,
        bill_to: datetime | None = None,
    ) -> None:
        """`POST /claims/interventions/switch` — replace an ACTIVE intervention with another.

        DHA rules: the new code must share the existing one's access point and must not require elective
        pre-authorization; when `retain_bill_items` is true, `bill_from` and `bill_to` (the previous
        intervention's billing period) are required — checked here before anything is sent. Retention is
        not possible from per-diem to surgical interventions.

        The two codes must also come from the same scheme family — `PMF-*` is the Public Officers fund and
        `SHA-*` is general cover. DHA refuses to combine them ("Intervention Combination: HDU CARE (Public
        Officers Medical Scheme Fund) (PMF-03-002) cannot be combined with ICU CARE (SHA-03-001)"), which
        is an obscure way to say the right ward was picked from the wrong fund. Checked here, since the
        prefixes decide it and no call is needed to find out.
        """
        existing_code = InterventionCode.of(existing)
        new_code = InterventionCode.of(new)
        families = (scheme_family(existing_code.value), scheme_family(new_code.value))
        if all(families) and families[0] != families[1]:
            raise RequestValidationError(
                [
                    Violation(
                        "new",
                        f"{new_code.value} is {families[1]} cover and {existing_code.value} is "
                        f"{families[0]}; DHA will not combine the two on one claim",
                    )
                ]
            )
        if retain_bill_items and (bill_from is None or bill_to is None):
            raise RequestValidationError(
                [Violation("bill_from/bill_to", "required when retain_bill_items is true")]
            )
        await self._gateway.switch_intervention(
            self.consent_token,
            existing_code,
            new_code,
            retain_bill_items,
            bill_from,
            bill_to,
        )

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
        service_name: str = "",
        service_identifier: str = "",
        practitioner: PractitionerRef | None = None,
        attachments: Sequence[LineAttachment] = (),
    ) -> ClaimLine:
        """`POST /claims/lines` — bill an item on the visit.

        With `diagnoses`/`attachments` this is DHA's "Add Combined Billing Details": one multipart call.
        `service_name`/`service_identifier` label the line and tie it to your own charge record; the
        amount must be within the tariff or the member's PMF balance.

        **A per-diem intervention does not need a manual line**, because DHA builds one from the accrued
        days and the facility's Hospital Level Tariff — but it still accepts the stay's charges, so this
        does not refuse them. What it does refuse is a `unit_price` above that tariff: DHA then "rolls
        back the entire request" and the diagnoses and attachments go with it, in a 400 that names none of
        it. See `VirtualClaim.line_blockers`. A session with no snapshot yet (resumed from a bare token,
        before `preview()`) has nothing to check against and is left to the server.
        """
        code = InterventionCode.of(intervention)
        blockers = self.claim.line_blockers(code, unit_price) if self.claim is not None else ()
        if blockers:
            raise RequestValidationError([Violation("line", str(b)) for b in blockers])
        try:
            line = NewClaimLine(
                intervention_code=code,
                unit_price=unit_price,
                quantity=quantity,
                scheme_code=SchemeCode.of(scheme_code) if scheme_code is not None else None,
                charge_date=charge_date,
                diagnoses=tuple(Icd11Code.of(d) for d in diagnoses),
                service_name=service_name,
                service_identifier=service_identifier,
                practitioner=practitioner,
                attachments=tuple(attachments),
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
        discharge_reason: DischargeReason | None = None,
        otp: Otp | str | None = None,
        reason_for_unknown_patient: str | None = None,
    ) -> VirtualClaim:
        """`POST /claims/submit` — final. Attempted once; on ambiguity raises SubmissionOutcomeUnknownError.

        Observed on UAT for every service type: the server also requires `discharge_reason`, the OTP from
        `send_discharge_otp()`, and a doctor on the claim (`add_doctor`). Pass them here.
        """
        submission = Submission(
            invoice_number=InvoiceNumber.of(invoice_number) if invoice_number is not None else None,
            discharge_reason=discharge_reason,
            otp=(otp if isinstance(otp, Otp) else Otp(otp)) if otp is not None else None,
            reason_for_unknown_patient=reason_for_unknown_patient,
        )
        self.claim = await self._submit.execute(self.consent_token, submission)
        return self.claim

    async def add_doctor(self, doctor: PractitionerRef) -> str:
        """`POST /claims/doctors` — attach the attending practitioner (HWR-registered). Required before `submit`."""
        return await self._gateway.add_doctor(self.consent_token, doctor)

    async def remove_doctor(self) -> None:
        """`DELETE /claims/doctors` — detach the attending practitioner (one doctor per claim, so no argument)."""
        await self._emergency.remove_doctor(self.consent_token)

    async def close(self, reason: CancelReason, text: str) -> VirtualClaim:
        """`POST /claims/close` — abandon a claim that will not be submitted."""
        if not text.strip():
            raise RequestValidationError([Violation("cancel_reason_text", "cannot be empty")])
        self.claim = await self._gateway.close(self.consent_token, reason, text.strip())
        return self.claim

    async def payer_status(self, provider_claim_no: str) -> tuple[PayerClaimRecord, ...]:
        """`GET /claims/preview/payer` — how the payer sees the submitted claim.

        Keyed on `provider_claim_no` alone. It used to `preview()` first so it could also send the claim
        guid, which was wrong twice over: the payer filters on its *own* guid, so ours matched nothing and
        the endpoint answered `200 {"results": []}` — a silent empty, indistinguishable from "not
        adjudicated yet" — and the preview call made a pure read depend on a consent token that has long
        expired by the time anyone asks how a claim is going.
        """
        if not provider_claim_no.strip():
            raise RequestValidationError([Violation("provider_claim_no", "cannot be empty")])
        return await self._gateway.payer_status(None, provider_claim_no)

    # ── inpatient discharge & consent fallbacks ──

    async def send_discharge_otp(self, patient: PatientId | str) -> str:
        """`POST /claims/otp/discharge` — OTP to the beneficiary or their next of kin for discharge consent."""
        return await self._gateway.send_discharge_otp(self.consent_token, PatientId.of(patient))

    async def discharge(
        self,
        *,
        reason: DischargeReason,
        invoice_number: InvoiceNumber | str,
        otp: Otp | str,
        discharged_at: datetime | None = None,
    ) -> VirtualClaim:
        """`POST /claims/discharge` — ends the visit. **Required before `submit` for every service type** (observed on UAT).

        **For inpatient this is also the submit.** DHA's published per-diem scenario states that discharge
        "both discharges the patient and simultaneously submits the claim to SHA. There is no separate
        submit step for inpatient claims", and its call sequence ends here — no `/claims/submit` appears in
        it. That contradicts what UAT was observed to require (discharge, then `submit`, for every service
        type, which is why `submit` still exists and is still called). Until the two agree, treat a
        `submit` after an inpatient `discharge` as possibly redundant rather than load-bearing: if it comes
        back refused with the claim already submitted, `preview()` is what settles which of the two filed it.

        Run `preview()` first either way — it is the only check that the claim is complete, and after this
        call nothing can be changed.

        `discharged_at` defaults to now (UTC); if given it must be timezone-aware.
        """
        try:
            command = Discharge(
                discharged_at or datetime.now(UTC),
                reason,
                InvoiceNumber.of(invoice_number),
                otp if isinstance(otp, Otp) else Otp(otp),
            )
        except ValueError as exc:
            raise RequestValidationError([Violation("discharge", str(exc))]) from exc
        self.claim = await self._gateway.discharge(self.consent_token, command)
        return self.claim

    async def add_next_of_kin(
        self, *, full_name: str, id_number: str, id_type: NextOfKinIdType, contact_value: str
    ) -> NextOfKinContact:
        """`POST /patients/next-of-kin/contacts` — registers who receives OTPs when the beneficiary cannot."""
        try:
            command = NextOfKin(full_name, id_number, id_type, contact_value)
        except ValueError as exc:
            raise RequestValidationError([Violation("next_of_kin", str(exc))]) from exc
        return await self._gateway.add_next_of_kin(self.consent_token, command)

    async def set_coverage(self, principal: PatientId | str, policy_number: str) -> None:
        """`POST /authorizations/covers` — choose which member's policy pays (POMSF schemes only).

        Call before adding lines or pre-auths. `policy_number` comes from eligibility
        (`Scheme.policy_number`); `principal` is the member whose cover pays, not necessarily the patient.
        """
        try:
            selection = CoverageSelection(PatientId.of(principal), policy_number)
        except ValueError as exc:
            raise RequestValidationError([Violation("coverage", str(exc))]) from exc
        await self._gateway.set_coverage(self.consent_token, selection)

    async def resubmit_lines(self) -> LineResubmission:
        """`POST /claims/lines/resubmit` — after `edit_line` following payer review."""
        return await self._gateway.resubmit_lines(self.consent_token)

    # ── pre-authorisation ──

    async def request_preauth(
        self,
        intervention: InterventionCode | str,
        *,
        service_start: datetime,
        service_end: datetime,
        items: Sequence[PreauthItem],
        diagnoses: Sequence[Icd11Code | str],
        doctors: Sequence[PractitionerRef],
        notification_email: str,
        attachments: Sequence[Attachment] = (),
        details: PreauthDetails | None = None,
    ) -> Preauthorization:
        """`POST /preauths` — file a pre-authorisation for an intervention flagged `needs_preauth`.

        `details` carries the specialised half of the form — `SurgicalDetails`, `RenalDetails`,
        `OncologyDetails`, `OpticalDetails` or `ImagingDetails`. Omitted, this files a normal pre-auth.
        """
        try:
            request = PreauthRequest(
                intervention_code=InterventionCode.of(intervention),
                service_start=service_start,
                service_end=service_end,
                items=tuple(items),
                diagnoses=tuple(Icd11Code.of(d) for d in diagnoses),
                doctors=tuple(doctors),
                provider_notification_email=notification_email,
                attachments=tuple(attachments),
                **({"details": details} if details is not None else {}),
            )
        except ValueError as exc:
            raise RequestValidationError([Violation("preauth", str(exc))]) from exc
        return await self._preauths.create(self.consent_token, request)

    async def preauths(self) -> tuple[Preauthorization, ...]:
        """`GET /preauths` — pre-authorisations linked to this claim."""
        return await self._preauths.list(self.consent_token)

    async def remove_preauth_diagnosis(
        self, icd: Icd11Code | str, intervention: InterventionCode | str
    ) -> Preauthorization:
        return await self._preauths.remove_diagnosis(
            self.consent_token, Icd11Code.of(icd), InterventionCode.of(intervention)
        )

    async def remove_preauth_doctor(
        self, intervention: InterventionCode | str, registration_number: str
    ) -> None:
        """Only possible before the pre-authorisation is submitted."""
        await self._preauths.remove_doctor(
            self.consent_token, InterventionCode.of(intervention), registration_number
        )

    async def cancel_preauth(self, intervention: InterventionCode | str) -> Preauthorization:
        return await self._preauths.cancel(self.consent_token, InterventionCode.of(intervention))

    async def request_doctor_consent(
        self,
        intervention: InterventionCode | str,
        practitioner: PractitionerRef,
        *,
        request_type: DoctorConsentRequestType = DoctorConsentRequestType.PREAUTH_DOCTOR_APPROVAL,
        service_type: ServiceType | None = None,
        emergency_claim_id: str | None = None,
    ) -> str:
        """`POST /claims/doctor-consent` — ask a doctor to approve a pre-auth / emergency claim / prescription."""
        request = DoctorConsentRequest(
            InterventionCode.of(intervention), request_type, practitioner, service_type, emergency_claim_id
        )
        return await self._preauths.request_doctor_consent(self.consent_token, request)

    # ── ePrescriptions ──

    async def prescribe(
        self,
        intervention: InterventionCode | str,
        items: Sequence[MedicationOrder],
        *,
        prescriber: PractitionerRef | None = None,
    ) -> Prescription:
        """`POST /prescriptions` — record what the doctor ordered under this claim."""
        try:
            request = PrescriptionRequest(InterventionCode.of(intervention), tuple(items), prescriber)
        except ValueError as exc:
            raise RequestValidationError([Violation("prescription", str(exc))]) from exc
        return await self._prescriptions.create(self.consent_token, request)

    async def prescription(self) -> Prescription | None:
        """`GET /prescriptions` — the prescription linked to this claim, if any."""
        return await self._prescriptions.get(self.consent_token)

    async def dispense(
        self,
        intervention: InterventionCode | str,
        products: Sequence[DispensedProduct],
        dispensers: Sequence[PractitionerRef],
    ) -> Dispense:
        """`POST /prescriptions/dispenses` — what the pharmacy actually handed over."""
        try:
            request = DispenseRequest(InterventionCode.of(intervention), tuple(products), tuple(dispensers))
        except ValueError as exc:
            raise RequestValidationError([Violation("dispense", str(exc))]) from exc
        return await self._prescriptions.dispense(self.consent_token, request)

    async def remove_prescription_doctor(
        self, intervention: InterventionCode | str, registration_number: str
    ) -> None:
        await self._prescriptions.remove_doctor(
            self.consent_token, InterventionCode.of(intervention), registration_number
        )

    # ── emergency ──

    async def add_protocol(
        self,
        protocol: ProtocolCode | str,
        intervention: InterventionCode | str,
        unit_price: Money,
        quantity: int = 1,
        *,
        diagnoses: Sequence[Icd11Code | str] = (),
    ) -> ClaimLine:
        """`POST /claims/emergency/protocols` — bill a treatment protocol on an emergency claim."""
        try:
            line = ProtocolLine(
                ProtocolCode.of(protocol),
                InterventionCode.of(intervention),
                unit_price,
                quantity,
                tuple(Icd11Code.of(d) for d in diagnoses),
            )
        except ValueError as exc:
            raise RequestValidationError([Violation("protocol", str(exc))]) from exc
        return await self._emergency.add_protocol(self.consent_token, line)

    async def add_emergency_doctor(self, doctor: PractitionerRef) -> str:
        """`POST /claims/doctors` — attach the attending doctor to an emergency claim."""
        return await self._emergency.add_doctor(self.consent_token, doctor)

    async def remove_emergency_doctor(self) -> None:
        """Same endpoint as `remove_doctor`; kept for symmetry with `add_emergency_doctor`."""
        await self.remove_doctor()

    async def open_emt_claim(self, claim: EmtClaim) -> VirtualClaim:
        """`POST /claims/emt` — the ambulance provider's claim linked to this emergency case."""
        return await self._emergency.open_emt(self.consent_token, claim)
