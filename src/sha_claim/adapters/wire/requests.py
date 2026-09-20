"""Domain → WireRequest. The only place that knows field names and payload shapes."""

from __future__ import annotations

import json
from collections.abc import Sequence
from decimal import Decimal

from sha_claim.adapters.wire.transport import TimeoutKind, WireRequest
from sha_claim.domain.attachments import Attachment
from sha_claim.domain.claim import Discharge, LineEdit, NewClaimLine, NextOfKin
from sha_claim.domain.codes import Icd11Code, InterventionCode
from sha_claim.domain.consent import BiometricGuid, ConsentProof, MatchId, Otp
from sha_claim.domain.enums import CancelReason, IdentificationType, ServiceType
from sha_claim.domain.identifiers import (
    AttachmentId,
    ClaimGuid,
    ConsentToken,
    InvoiceNumber,
    LineGuid,
    PatientId,
)
from sha_claim.domain.practitioner import PractitionerRef
from sha_claim.domain.preauth import DoctorConsentRequest, PreauthRequest


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


def get_authorization(token: str, guid: str, beneficiary: PatientId | None) -> WireRequest:
    params = {"token": token, "guid": guid}
    if beneficiary is not None:
        params["beneficiary_code"] = beneficiary.value
    return WireRequest("GET", "/claims/authorizations", params=params)


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
    return WireRequest("POST", "/claims/lines", form=form, multipart=True)


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


def submit(
    token: ConsentToken, invoice: InvoiceNumber | None, reason_for_unknown_patient: str | None
) -> WireRequest:
    body: dict[str, object] = {"consent_token": token.value}
    if invoice is not None:
        body["invoice_number"] = invoice.value
    if reason_for_unknown_patient:
        body["reason_for_unknown_patient"] = reason_for_unknown_patient
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
            "discharge_date": d.discharge_date.isoformat(),
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
