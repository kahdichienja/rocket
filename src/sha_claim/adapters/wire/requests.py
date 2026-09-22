"""Domain → WireRequest. The only place that knows field names and payload shapes."""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from sha_claim.adapters.wire.transport import TimeoutKind, WireRequest
from sha_claim.domain.attachments import Attachment
from sha_claim.domain.claim import CoverageSelection, Discharge, LineEdit, NewClaimLine, NextOfKin, Submission
from sha_claim.domain.codes import Icd11Code, InterventionCode
from sha_claim.domain.consent import BiometricGuid, ConsentProof, MatchId, Otp
from sha_claim.domain.emergency import EmergencyCase, EmtClaim, ProtocolLine
from sha_claim.domain.enums import CancelReason, IdentificationType, ServiceType
from sha_claim.domain.identifiers import (
    AttachmentId,
    ClaimGuid,
    ConsentToken,
    FacilityCode,
    FileId,
    LineGuid,
    PatientId,
)
from sha_claim.domain.practitioner import PractitionerRef
from sha_claim.domain.preauth import DoctorConsentRequest, PreauthRequest
from sha_claim.domain.prescription import DispenseRequest, MedicationOrder, PrescriptionRequest
from sha_claim.errors import RequestValidationError, Violation


def eligibility_check(identification_number: str, identification_type: IdentificationType) -> WireRequest:
    return WireRequest(
        "GET",
        "/patients/eligibility",
        params={
            "identification_number": identification_number,
            "identification_type": identification_type.value,
        },
    )


def benefits(patient: PatientId) -> WireRequest:
    return WireRequest("GET", "/patients/benefits", params={"patient_id": patient.value})


def sub_benefits(patient: PatientId) -> WireRequest:
    return WireRequest("GET", "/patients/sub-benefits", params={"patient_id": patient.value})


def interventions(patient: PatientId, sub_benefit_code: str) -> WireRequest:
    return WireRequest(
        "GET",
        "/patients/benefits/interventions",
        params={"patient_id": patient.value, "sub_benefit_code": sub_benefit_code},
    )


def authorize(
    patient: PatientId, service_type: ServiceType, codes: Sequence[InterventionCode], otp: Otp | None
) -> WireRequest:
    body: dict[str, object] = {
        "patient_id": patient.value,
        "service_type": service_type.value,
        "interventions": [c.value for c in codes],
    }
    if otp is not None:
        body["otp"] = otp.code
    return WireRequest("POST", "/claims/authorize", json=body)


def send_visit_otp(patient: PatientId, codes: Sequence[InterventionCode]) -> WireRequest:
    """`POST /claims/otp` — not on the eclaims portal pages, but live on UAT and used by NaCare's earlier adapter."""
    return WireRequest(
        "POST",
        "/claims/otp",
        json={"patient_id": patient.value, "intervention_codes": [c.value for c in codes]},
    )


def get_authorization(token: str, guid: str, beneficiary: PatientId | None) -> WireRequest:
    params = {"token": token, "guid": guid}
    if beneficiary is not None:
        params["beneficiary_code"] = beneficiary.value
    return WireRequest("GET", "/claims/authorizations", params=params)


def list_authorizations(beneficiary: PatientId) -> WireRequest:
    """Undocumented but live on UAT: `token`/`guid` may be omitted; the whole history for a beneficiary comes back."""
    return WireRequest("GET", "/claims/authorizations", params={"beneficiary_code": beneficiary.value})


def reject_authorization(token: str) -> WireRequest:
    return WireRequest("POST", f"/claims/authorizations/{token}/reject")


def open_visit(
    patient: PatientId, service_type: ServiceType, codes: Sequence[InterventionCode], proof: ConsentProof
) -> WireRequest:
    body: dict[str, object] = {
        "patient_id": patient.value,
        "service_type": service_type.value,
        "intervention_codes": [c.value for c in codes],
    }
    match proof:
        case Otp(code=code):
            body["otp"] = code
        case BiometricGuid(value=guid):
            body["auth_guid"] = guid
        case MatchId(value=match_id):
            body["match_id"] = match_id
        case _:  # the server says so verbatim: "one of otp, auth_guid or match_id is required"
            raise RequestValidationError(
                [Violation("proof", f"expected Otp, BiometricGuid or MatchId, got {type(proof).__name__}")]
            )
    return WireRequest("POST", "/claims/visit", json=body)


# ── virtual claim mutations (all keyed by consent_token) ──


def add_intervention(token: ConsentToken, code: InterventionCode) -> WireRequest:
    return WireRequest(
        "POST", "/claims/interventions", json={"consent_token": token.value, "intervention_code": code.value}
    )


def retire_intervention(token: ConsentToken, code: InterventionCode) -> WireRequest:
    return WireRequest(
        "POST",
        "/claims/interventions/retire",
        json={"consent_token": token.value, "intervention_code": code.value},
    )


def restore_intervention(token: ConsentToken, code: InterventionCode) -> WireRequest:
    return WireRequest(
        "POST",
        "/claims/interventions/restore",
        json={"consent_token": token.value, "intervention_code": code.value},
    )


def switch_intervention(
    token: ConsentToken,
    existing: InterventionCode,
    new: InterventionCode,
    retain_bill_items: bool,
    bill_from: datetime | None,
    bill_to: datetime | None,
) -> WireRequest:
    body: dict[str, object] = {
        "consent_token": token.value,
        "existing_intervention_code": existing.value,
        "new_intervention_code": new.value,
        "retain_bill_items": retain_bill_items,
    }
    if bill_from is not None:
        body["bill_from"] = bill_from.isoformat()
    if bill_to is not None:
        body["bill_to"] = bill_to.isoformat()
    return WireRequest("POST", "/claims/interventions/switch", json=body)


def add_diagnosis(token: ConsentToken, icd: Icd11Code, intervention: InterventionCode) -> WireRequest:
    return WireRequest("POST", "/claims/diagnoses", json=_diagnosis_body(token, icd, intervention))


def remove_diagnosis(token: ConsentToken, icd: Icd11Code, intervention: InterventionCode) -> WireRequest:
    return WireRequest("PATCH", "/claims/diagnoses", json=_diagnosis_body(token, icd, intervention))


def add_line(token: ConsentToken, line: NewClaimLine) -> WireRequest:
    form: dict[str, str] = {
        "consent_token": token.value,
        "intervention_code": line.intervention_code.value,
        "unit_price": line.unit_price.as_wire(),
        "quantity": str(Decimal(line.quantity)),
    }
    if line.scheme_code is not None:
        form["scheme_code"] = line.scheme_code.value
    if line.charge_date is not None:
        form["charge_date"] = line.charge_date.isoformat()
    if line.diagnoses:
        form["diagnoses"] = json.dumps(
            [d.value for d in line.diagnoses]
        )  # spec: "JSON array of ICD diagnosis codes"
    if line.service_name:
        form["service_name"] = line.service_name
    if line.service_identifier:
        form["service_identifier"] = line.service_identifier
    if line.practitioner is not None:
        form["practitioner_identification_type"] = line.practitioner.identification_type.value
        form["practitioner_identification_number"] = line.practitioner.identification_number
        form["practitioner_regulation_body"] = line.practitioner.regulation_body.value
    files: dict[str, tuple[str, bytes, str]] = {}
    if line.attachments:
        # "Add Combined Billing Details": metadata objects name the binary part that carries each file.
        meta = []
        for n, item in enumerate(line.attachments):
            field_name = f"attachment_{n}"
            meta.append(
                {
                    "document_title": item.document_title,
                    "document_type": item.attachment.document_type.value,
                    "file_field_name": field_name,
                }
            )
            files[field_name] = (
                item.attachment.filename,
                item.attachment.content,
                item.attachment.content_type,
            )
        form["attachments"] = json.dumps(meta)
    return WireRequest(
        "POST",
        "/claims/lines",
        form=form,
        files=files or None,
        multipart=True,
        timeout=TimeoutKind.UPLOAD if files else TimeoutKind.DEFAULT,
    )


def set_coverage(token: ConsentToken, selection: CoverageSelection) -> WireRequest:
    """`POST /authorizations/covers` — on the DHA process pages only, not the eclaims portal."""
    return WireRequest(
        "POST",
        "/authorizations/covers",
        json={
            "principal_cr_id": selection.principal.value,
            "consent_token": token.value,
            "policy_number": selection.policy_number,
        },
    )


def remove_line(token: ConsentToken, line: LineGuid) -> WireRequest:
    return WireRequest("PATCH", "/claims/lines", json={"consent_token": token.value, "line_guid": line.value})


def edit_line(edit: LineEdit) -> WireRequest:
    body: dict[str, object] = {"line_id": edit.line.value}
    if edit.quantity is not None:
        body["quantity"] = edit.quantity
    if edit.unit_price is not None:
        body["unit_price"] = edit.unit_price.as_wire()
    if edit.scheme_code is not None:
        body["scheme_code"] = edit.scheme_code.value
    return WireRequest("PATCH", "/claims/lines/edit", json=body)


def add_attachment(
    token: ConsentToken, attachment: Attachment, intervention: InterventionCode
) -> WireRequest:
    return WireRequest(
        "POST",
        "/claims/attachments",
        form={
            "consent_token": token.value,
            "document_type": attachment.document_type.value,
            "intervention_code": intervention.value,
        },
        files={"file_blob": (attachment.filename, attachment.content, attachment.content_type)},
        multipart=True,
        timeout=TimeoutKind.UPLOAD,
    )


def remove_attachment(
    token: ConsentToken, attachment: AttachmentId, intervention: InterventionCode
) -> WireRequest:
    return WireRequest(
        "PATCH",
        "/claims/attachments",
        json={
            "consent_token": token.value,
            "attachment_id": attachment.value,
            "intervention_code": intervention.value,
        },
    )


def preview(token: ConsentToken) -> WireRequest:
    # A read despite the verb: safe to retry.
    return WireRequest("POST", "/claims/preview", json={"consent_token": token.value}, retry_safe=True)


def submit(token: ConsentToken, submission: Submission) -> WireRequest:
    body: dict[str, object] = {"consent_token": token.value}
    if submission.invoice_number is not None:
        body["invoice_number"] = submission.invoice_number.value
    if submission.discharge_reason is not None:
        body["discharge_reason"] = submission.discharge_reason.value  # undocumented; required on UAT
    if submission.otp is not None:
        body["otp"] = submission.otp.code  # undocumented; the discharge OTP, required on UAT
    if submission.reason_for_unknown_patient:
        body["reason_for_unknown_patient"] = submission.reason_for_unknown_patient
    return WireRequest("POST", "/claims/submit", json=body)


def close(token: ConsentToken, reason: CancelReason, text: str) -> WireRequest:
    return WireRequest(
        "POST",
        "/claims/close",
        json={"consent_token": token.value, "cancel_reason_type": reason.value, "cancel_reason_text": text},
    )


def payer_status(claim: ClaimGuid, provider_claim_no: str) -> WireRequest:
    return WireRequest(
        "GET", "/claims/preview/payer", params={"guid": claim.value, "provider_claim_no": provider_claim_no}
    )


def _diagnosis_body(token: ConsentToken, icd: Icd11Code, intervention: InterventionCode) -> dict[str, str]:
    return {"consent_token": token.value, "icd_code": icd.value, "intervention_code": intervention.value}


# ── pre-authorisation ──


def create_preauth(token: ConsentToken, request: PreauthRequest) -> WireRequest:
    """Multipart with JSON-encoded arrays, mirroring `/claims/lines`.

    UNVERIFIED (WORKFLOWS Q3): the portal does not publish the inner schema of `items`, `diagnoses`,
    `doctors`, `attachments`. Field names below reuse the vocabulary the rest of the API uses; the
    attachment convention ("entries reference uploaded form file fields") is documented on `/claims/emt`.
    Fix here, and only here, once UAT confirms.
    """
    files: dict[str, tuple[str, bytes, str]] = {}
    attachment_meta: list[dict[str, str]] = []
    for index, attachment in enumerate(request.attachments):
        part = f"attachment_{index}"
        files[part] = (attachment.filename, attachment.content, attachment.content_type)
        attachment_meta.append(
            {"field": part, "document_type": attachment.document_type.value, "title": attachment.filename}
        )
    form = {
        "consent_token": token.value,
        "intervention_code": request.intervention_code.value,
        "service_start": request.service_start.isoformat(),
        "service_end": request.service_end.isoformat(),
        "items": json.dumps(
            [
                {
                    "item_code": i.code,
                    "item_name": i.description,
                    "quantity": str(Decimal(i.quantity)),
                    "unit_price": i.unit_price.as_wire(),
                }
                for i in request.items
            ]
        ),
        "diagnoses": json.dumps([{"icd_code": d.value} for d in request.diagnoses]),
        "doctors": json.dumps([_practitioner_fields(d) for d in request.doctors]),
        "attachments": json.dumps(attachment_meta),
        "provider_notification_email": request.provider_notification_email,
    }
    return WireRequest(
        "POST", "/preauths", form=form, files=files or None, multipart=True, timeout=TimeoutKind.UPLOAD
    )


def list_preauths(token: ConsentToken) -> WireRequest:
    return WireRequest("GET", "/preauths", params={"consent_token": token.value})


def remove_preauth_diagnosis(
    token: ConsentToken, icd: Icd11Code, intervention: InterventionCode
) -> WireRequest:
    return WireRequest(
        "DELETE", f"/preauths/diagnoses/{icd.value}", json=_diagnosis_body(token, icd, intervention)
    )


def remove_preauth_doctor(
    token: ConsentToken, intervention: InterventionCode, registration_number: str
) -> WireRequest:
    return WireRequest(
        "DELETE",
        "/preauths/doctors",
        json={
            "consent_token": token.value,
            "intervention_code": intervention.value,
            "practitioner_registration_number": registration_number,
        },
    )


def cancel_preauth(token: ConsentToken, intervention: InterventionCode) -> WireRequest:
    return WireRequest(
        "POST",
        "/preauths/cancel",
        json={"consent_token": token.value, "intervention_code": intervention.value},
    )


def doctor_consent(token: ConsentToken, request: DoctorConsentRequest) -> WireRequest:
    body: dict[str, object] = {
        "consent_token": token.value,
        "intervention_code": request.intervention_code.value,
        "request_type": request.request_type.value,
        **_practitioner_fields(request.practitioner),
    }
    if request.service_type is not None:
        body["service_type"] = request.service_type.value
    if request.emergency_claim_id:
        body["emergency_claim_id"] = request.emergency_claim_id
    return WireRequest("POST", "/claims/doctor-consent", json=body)


def _practitioner_fields(p: PractitionerRef) -> dict[str, str]:
    fields = {
        "identification_type": p.identification_type.value,
        "identification_number": p.identification_number,
        "regulation_body": p.regulation_body.value,
    }
    if p.identification_type is IdentificationType.REGISTRATION_NUMBER:
        fields["practitioner_registration_number"] = p.identification_number
    return fields


# ── inpatient discharge, next of kin, resubmission ──


def send_discharge_otp(token: ConsentToken, patient: PatientId) -> WireRequest:
    return WireRequest(
        "POST", "/claims/otp/discharge", json={"consent_token": token.value, "patient_id": patient.value}
    )


def discharge(token: ConsentToken, d: Discharge) -> WireRequest:
    return WireRequest(
        "POST",
        "/claims/discharge",
        json={
            "consent_token": token.value,
            "discharge_date": d.discharged_at.isoformat(timespec="seconds"),
            "discharge_reason": d.reason.value,
            "invoice_number": d.invoice_number.value,
            "otp": d.otp.code,
        },
    )


def add_next_of_kin(token: ConsentToken, n: NextOfKin) -> WireRequest:
    return WireRequest(
        "POST",
        "/patients/next-of-kin/contacts",
        json={
            "consent_token": token.value,
            "next_of_kin_full_name": n.full_name,
            "next_of_kin_id_number": n.id_number,
            "next_of_kin_id_number_type": n.id_type.value,
            "contact_value": n.contact_value,
        },
    )


def resubmit_lines(token: ConsentToken) -> WireRequest:
    return WireRequest("POST", "/claims/lines/resubmit", json={"consent_token": token.value})


# ── ePrescriptions ──


def create_prescription(token: ConsentToken, request: PrescriptionRequest) -> WireRequest:
    body: dict[str, object] = {
        "consent_token": token.value,
        "intervention_code": request.intervention_code.value,
        "items": [_medication_order(item) for item in request.items],
    }
    if request.prescriber is not None:
        body.update(
            identification_number=request.prescriber.identification_number,
            identification_type=request.prescriber.identification_type.value,
            regulation_body=request.prescriber.regulation_body.value,
        )
    return WireRequest("POST", "/prescriptions", json=body)


def get_prescription(token: ConsentToken) -> WireRequest:
    return WireRequest("GET", "/prescriptions", params={"consent_token": token.value})


def create_dispense(token: ConsentToken, request: DispenseRequest) -> WireRequest:
    return WireRequest(
        "POST",
        "/prescriptions/dispenses",
        json={
            "consent_token": token.value,
            "intervention_code": request.intervention_code.value,
            "actual_products": [
                {
                    "actual_product_code": p.product_code,
                    "total_quantity": _number(p.quantity),
                    "medication_price": _number(p.price.amount),
                }
                for p in request.products
            ],
            "doctors": [
                {
                    "identification_number": d.identification_number,
                    "identification_type": d.identification_type.value,
                }
                for d in request.dispensers
            ],
        },
    )


def remove_prescription_doctor(
    token: ConsentToken, intervention: InterventionCode, registration_number: str
) -> WireRequest:
    return WireRequest(
        "DELETE",
        "/prescriptions/doctors",
        json={
            "consent_token": token.value,
            "intervention_code": intervention.value,
            "practitioner_registration_number": registration_number,
        },
    )


def _medication_order(item: MedicationOrder) -> dict[str, object]:
    body: dict[str, object] = {
        "generic_concept_code": item.generic_concept_code,
        "dose_quantity": _number(item.dose_quantity),
        "dose_unit": item.dose_unit,
        "frequency": item.frequency,
        "period_unit": item.period_unit,
        "duration": item.duration,
        "duration_unit": item.duration_unit,
        "start_date": item.start_date.isoformat(),
        "needs_refill": item.needs_refill,
        "refill_count": item.refill_count,
    }
    if item.end_date is not None:
        body["end_date"] = item.end_date.isoformat()
    if item.patient_instruction:
        body["patient_instruction"] = item.patient_instruction
    if item.additional_instruction:
        body["additional_instruction"] = item.additional_instruction
    return body


def _number(value: Decimal | int) -> int | float:
    """JSON number for `number`-typed fields: ints stay ints, decimals become floats (exact for 2dp money)."""
    d = Decimal(value)
    return int(d) if d == d.to_integral_value() else float(d)


# ── emergency ──


def open_emergency_case(case: EmergencyCase) -> WireRequest:
    body: dict[str, object] = {
        "identification_number": case.attending.identification_number,
        "identification_type": case.attending.identification_type.value,
        "regulation_body": case.attending.regulation_body.value,
        "reference_number": case.reference_number,
        "brought_by": case.brought_by.value,
        "mode_of_arrival": case.mode_of_arrival.value,
        "interventions": [c.value for c in case.interventions],
    }
    if case.beneficiary is not None:
        body["beneficiary_cr_id"] = case.beneficiary.value
    if case.otp is not None:
        body["otp"] = case.otp.code
    body["notes"] = case.notes  # mandatory on UAT despite the portal marking it optional
    return WireRequest("POST", "/claims/emergency", json=body)


def emergency_protocols(intervention: InterventionCode, active: bool) -> WireRequest:
    return WireRequest(
        "GET",
        "/claims/emergency/protocols",
        params={"intervention_code": intervention.value, "active": "true" if active else "false"},
    )


def add_emergency_protocol(token: ConsentToken, line: ProtocolLine) -> WireRequest:
    form = {
        "consent_token": token.value,
        "protocol_code": line.protocol_code.value,
        "intervention_code": line.intervention_code.value,
        "unit_price": line.unit_price.as_wire(),
        "quantity": str(line.quantity),
    }
    if line.diagnoses:
        form["diagnoses"] = ",".join(
            d.value for d in line.diagnoses
        )  # spec: comma-separated here, JSON on /claims/lines
    return WireRequest("POST", "/claims/emergency/protocols", form=form, multipart=True)


def add_emergency_doctor(token: ConsentToken, doctor: PractitionerRef) -> WireRequest:
    return WireRequest(
        "POST",
        "/claims/doctors",
        json={
            "consent_token": token.value,
            "identification_number": doctor.identification_number,
            "identification_type": doctor.identification_type.value,
            "regulation_body": doctor.regulation_body.value,
        },
    )


def remove_emergency_doctor(token: ConsentToken) -> WireRequest:
    return WireRequest("DELETE", "/claims/doctors", json={"consent_token": token.value})


def open_emt_claim(token: ConsentToken, claim: EmtClaim) -> WireRequest:
    files: dict[str, tuple[str, bytes, str]] = {}
    meta: list[dict[str, str]] = []
    for index, attachment in enumerate(claim.attachments):
        part = f"attachment_{index}"
        files[part] = (attachment.filename, attachment.content, attachment.content_type)
        meta.append(
            {"field": part, "document_type": attachment.document_type.value, "title": attachment.filename}
        )
    form = {
        "consent_token": token.value,
        "protocol_code": claim.protocol_code.value,
        "case_number": claim.case_number,
        "practitioner_reg_number": claim.practitioner_registration_number,
        "provider_registration_number": claim.provider_registration_number,
        "beneficiary_cr_id": claim.beneficiary.value,
        "otp": claim.otp.code,
        "diagnoses": json.dumps([d.value for d in claim.diagnoses]),
        "interventions": json.dumps([c.value for c in claim.interventions]),
    }
    if meta:
        form["attachments"] = json.dumps(meta)
    return WireRequest(
        "POST", "/claims/emt", form=form, files=files or None, multipart=True, timeout=TimeoutKind.UPLOAD
    )


# ── balances, occupancy, files ──


def utilization(patient: PatientId, intervention: InterventionCode) -> WireRequest:
    return WireRequest(
        "GET",
        "/patients/benefits/utilization",
        params={"patient_id": patient.value, "intervention_code": intervention.value},
    )


def pomsf_balances(patient: PatientId, policy_year: str, principal_member_number: str | None) -> WireRequest:
    params = {"patient_id": patient.value, "policy_year": policy_year}
    if principal_member_number:
        params["principal_member_number"] = principal_member_number
    return WireRequest("GET", "/patients/pomsf-balances", params=params)


def bed_occupancy(facility: FacilityCode) -> WireRequest:
    # Spec says public; UAT requires a bearer token. Authenticated is the safe default.
    return WireRequest("GET", f"/facilities/{facility.value}/beds/occupancy")


def upload(filename: str, content: bytes, content_type: str) -> WireRequest:
    return WireRequest(
        "POST",
        "/uploads",
        files={"file": (filename, content, content_type)},
        multipart=True,
        timeout=TimeoutKind.UPLOAD,
    )


def download_link(file_id: FileId) -> WireRequest:
    return WireRequest("GET", f"/uploads/{file_id.value}")
