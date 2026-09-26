"""Request builders converting domain commands to HTTP specs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

from smart_access.domain.claim import SmartClaim
from smart_access.domain.clinical import (
    AdmissionDetails,
    ClinicalRecord,
    ClinicalRequests,
    DischargeDetails,
    ItemMapping,
)
from smart_access.domain.enums import SessionStatus
from smart_access.domain.identifiers import (
    InvoiceNumber,
    PatientNumber,
    PreauthRequestId,
    SessionId,
    VisitNumber,
)
from smart_access.domain.preauth import PreauthAttachment, PreauthRequest
from smart_access.domain.rules import RulesCheckRequest


@dataclass(frozen=True)
class RequestSpec:
    method: str
    path: str
    params: Mapping[str, str | int] | None = None
    json_body: Any = None


def build_list_sessions_request(
    patient_number: PatientNumber, status: SessionStatus | str = SessionStatus.PENDING
) -> RequestSpec:
    st = status.value if isinstance(status, SessionStatus) else str(status)
    return RequestSpec(
        method="GET",
        path="/api/visit",
        params={"patientNumber": str(patient_number), "sessionStatus": st},
    )


def build_link_session_request(session_id: SessionId, visit_number: VisitNumber) -> RequestSpec:
    safe_vnum = quote(str(visit_number), safe="")
    return RequestSpec(
        method="PUT",
        path=f"/api/visit/{int(session_id)}/visit-number/{safe_vnum}",
    )


def build_close_session_request(session_id: SessionId, session_number: str | None = None) -> RequestSpec:
    body = {"sessionNumber": session_number} if session_number else None
    return RequestSpec(
        method="PUT",
        path=f"/api/visit/{int(session_id)}/close-session",
        json_body=body,
    )


def build_get_member_request(patient_number: PatientNumber, session_id: SessionId) -> RequestSpec:
    return RequestSpec(
        method="GET",
        path="/api/member",
        params={"patientNumber": str(patient_number), "sessionId": int(session_id)},
    )


def build_get_copayment_request(benefit_id: int, provider_key: str, visit_number: VisitNumber) -> RequestSpec:
    return RequestSpec(
        method="GET",
        path="/api/copayment",
        params={
            "benefitId": benefit_id,
            "providerKey": provider_key,
            "visitNumber": str(visit_number),
        },
    )


def build_rules_request(request: RulesCheckRequest) -> RequestSpec:
    body = {
        "items": [
            {
                "item_net_amount": float(it.item_net_amount),
                "pool_number": it.pool_number,
                "provider_item_code": it.provider_item_code,
            }
            for it in request.items
        ],
        "medical_aid_code": str(request.medical_aid_code),
        "medical_aid_number": str(request.medical_aid_number),
        "medical_aid_plan": request.medical_aid_plan,
        "policy_id": int(request.policy_id),
    }
    return RequestSpec(
        method="POST",
        path="/api/sbb-rules",
        json_body=body,
    )


def build_preauth_request(request: PreauthRequest, provider_key: str) -> RequestSpec:
    body: dict[str, Any] = {
        "admit_id": int(request.admit_id),
        "condition_diganosis_date": request.condition_diagnosis_date,
        "copay_amount": float(request.copay_amount),
        "copay_type": str(request.copay_type),
        "diagnosis_code": request.diagnosis_code,
        "doctor_name": request.doctor_name,
        "global_id": str(request.global_id),
        "invoice_number": str(request.invoice_number),
        "medical_aid_code": str(request.medical_aid_code),
        "medical_aid_number": str(request.medical_aid_number),
        "medical_aid_plan": request.medical_aid_plan,
        "patient_file_no": str(request.patient_file_no),
        "phone_number": request.phone_number,
        "policy_id": int(request.policy_id),
        "pool_number": request.pool_number,
        "location_code": str(request.location_code),
        "preauth_type": request.preauth_type,
        "treatment_cost_estimate": float(request.treatment_cost_estimate),
        "treatment_date": request.treatment_date,
        "visit_number": str(request.visit_number),
        "is_congenital": request.is_congenital,
        "is_integrated": request.is_integrated,
        "is_optical": request.is_optical,
        "provider_key": request.provider_key or provider_key,
        "rules": [
            {
                "rule_code": r.rule_code,
                "request_amount": float(r.request_amount),
                "items": [
                    {
                        "item_code": it.item_code,
                        "item_name": it.item_name,
                        "quantity": float(it.quantity),
                        "unit_amount": float(it.unit_amount),
                        "total_amount": float(it.total_amount),
                        "discount": float(it.discount),
                        "prov_comment": it.prov_comment,
                    }
                    for it in r.items
                ],
            }
            for r in request.rules
        ],
    }

    if request.attachments:
        body["attachments"] = [
            {"attachment": a.attachment, "type": a.type} for a in request.attachments
        ]
    if request.contact_details:
        body["contact_details"] = [
            {
                "contact_person_name": c.contact_person_name,
                "email_address": c.email_address,
                "phone_number": c.phone_number,
            }
            for c in request.contact_details
        ]
    if request.doctor_phone_no:
        body["doctor_phone_no"] = request.doctor_phone_no
    if request.estimated_stay is not None:
        body["estimated_stay"] = request.estimated_stay
    if request.first_diag_date:
        body["first_diag_date"] = request.first_diag_date
    if request.hospitalization_type:
        body["hospitalization_type"] = str(request.hospitalization_type)
    if request.preauth_notes:
        body["preauth_notes"] = request.preauth_notes
    if request.presenting_complaints:
        body["presenting_complaints"] = request.presenting_complaints
    if request.provider_comments:
        body["provider_comments"] = request.provider_comments
    if request.treatment_line:
        body["treatment_line"] = request.treatment_line

    if request.optical_request:
        opt = request.optical_request
        body["preauth_optical_request"] = {
            "frame_brand": opt.frame_brand,
            "frame_color": opt.frame_color,
            "frame_model": opt.frame_model,
            "frame_rim_type": opt.frame_rim_type,
            "frame_size": opt.frame_size,
            "frame_type": opt.frame_type,
            "is_new_frames": opt.is_new_frames,
            "lens_type": opt.lens_type,
            "spectacles_reason": opt.spectacles_reason,
        }

    return RequestSpec(method="POST", path="/api/preauth-request", json_body=body)


def build_preauth_status_request(
    visit_number: VisitNumber,
    patient_file_no: PatientNumber | None = None,
    invoice_no: InvoiceNumber | None = None,
) -> RequestSpec:
    params: dict[str, str | int] = {"visitNo": str(visit_number)}
    if patient_file_no is not None:
        params["patientFileNo"] = str(patient_file_no)
    if invoice_no is not None:
        params["invoiceNo"] = str(invoice_no)

    return RequestSpec(method="GET", path="/api/preauth-request", params=params)


def build_preauth_attachment_request(
    preauth_request_id: PreauthRequestId, attachments: Sequence[PreauthAttachment]
) -> RequestSpec:
    body = [{"attachment": a.attachment, "type": a.type} for a in attachments]
    return RequestSpec(
        method="PUT",
        path=f"/api/attachment/{preauth_request_id!s}",
        json_body=body,
    )


def build_claim_request(claim: SmartClaim) -> RequestSpec:
    body: dict[str, Any] = {
        "claim_code": str(claim.claim_code),
        "payer_code": str(claim.payer_code),
        "payer_name": claim.payer_name,
        "medicalaid_code": str(claim.medicalaid_code),
        "amount": float(claim.amount),
        "gross_amount": float(claim.gross_amount),
        "batch_number": claim.batch_number,
        "dispatch_date": claim.dispatch_date,
        "patient_number": str(claim.patient_number),
        "patient_name": claim.patient_name,
        "location_code": str(claim.location_code),
        "location_name": claim.location_name,
        "scheme_code": str(claim.scheme_code),
        "scheme_name": claim.scheme_name,
        "member_number": str(claim.member_number),
        "visit_number": str(claim.visit_number),
        "session_id": int(claim.session_id),
        "visit_start": claim.visit_start,
        "visit_end": claim.visit_end,
        "currency": claim.currency,
        "doctor_name": claim.doctor_name,
        "sp_id": int(claim.sp_id),
        "diagnosis": [
            {
                "code": d.code,
                "name": d.name,
                "coding_standard": str(d.coding_standard),
                "is_added_with_claim": d.is_added_with_claim,
                "primary": d.primary,
            }
            for d in claim.diagnosis
        ],
        "invoices": [
            {
                "amount": float(inv.amount),
                "gross_amount": float(inv.gross_amount),
                "invoice_date": inv.invoice_date,
                "invoice_number": str(inv.invoice_number),
                "invoice_ref_number": str(inv.invoice_ref_number),
                "lines": [
                    {
                        "item_code": line.item_code,
                        "item_name": line.item_name,
                        "quantity": float(line.quantity),
                        "unit_price": float(line.unit_price),
                        "amount": float(line.amount),
                        "service_group": line.service_group,
                        "charge_date": line.charge_date,
                        "charge_time": line.charge_time,
                        "additional_info": line.additional_info,
                        "pre_authorization_code": line.pre_authorization_code,
                    }
                    for line in inv.lines
                ],
                "etims_number": inv.etims_number,
                "etims_qrcode": inv.etims_qrcode,
            }
            for inv in claim.invoices
        ],
    }

    if claim.pool_number is not None:
        body["pool_number"] = claim.pool_number

    if claim.pre_authorization:
        body["pre_authorization"] = [
            {
                "code": pa.code,
                "amount": float(pa.amount),
                "authorized_by": pa.authorized_by,
                "message": pa.message,
            }
            for pa in claim.pre_authorization
        ]

    if claim.payment_modifiers:
        body["payment_modifiers"] = [
            {
                "type": str(pm.type),
                "amount": float(pm.amount),
                "reference_number": pm.reference_number,
                "nhif_contributor_nr": pm.nhif_contributor_nr,
                "nhif_employer_code": pm.nhif_employer_code,
                "nhif_member_nr": pm.nhif_member_nr,
                "nhif_patient_relation": pm.nhif_patient_relation,
                "nhif_site_nr": pm.nhif_site_nr,
            }
            for pm in claim.payment_modifiers
        ]

    if claim.preauth_overrides:
        body["preauth_overrides"] = [
            {
                "override_reason": ov.override_reason,
                "preauth_overides_types": ov.preauth_overides_types,
                "preauth_request_code": ov.preauth_request_code,
                "preauth_request_rule_code": ov.preauth_request_rule_code,
                "username": ov.username,
            }
            for ov in claim.preauth_overrides
        ]

    if claim.admission:
        body["admission"] = [
            {
                "admission_date": adm.admission_date,
                "admission_number": adm.admission_number,
                "discharge_date": adm.discharge_date,
                "discharge_summary": adm.discharge_summary,
                "additional_info": adm.additional_info,
            }
            for adm in claim.admission
        ]

    params: dict[str, str | int] = {
        "patientNumber": str(claim.patient_number),
        "sessionId": int(claim.session_id),
        "spID": int(claim.sp_id),
    }

    return RequestSpec(method="POST", path="/api/claims", params=params, json_body=body)


def build_interim_claim_request(claim: SmartClaim) -> RequestSpec:
    spec = build_claim_request(claim)
    return RequestSpec(method="POST", path="/api/interim-claim", json_body=spec.json_body)


def build_claim_status_request(invoice_number: InvoiceNumber, visit_number: VisitNumber) -> RequestSpec:
    return RequestSpec(
        method="GET",
        path="/api/claim-status",
        params={"invoiceNumber": str(invoice_number), "visitNumber": str(visit_number)},
    )


def build_clinical_record_request(record: ClinicalRecord) -> RequestSpec:
    body = {
        "invoice_number": str(record.invoice_number),
        "member_number": str(record.member_number),
        "patient_number": str(record.patient_number),
        "session_id": str(record.session_id),
        "visit_number": str(record.visit_number),
        "diagnosis": [
            {
                "code": d.code,
                "name": d.name,
                "coding_standard": str(d.coding_standard),
                "is_added_with_claim": d.is_added_with_claim,
                "is_primary": d.primary,
            }
            for d in record.diagnosis
        ],
    }
    return RequestSpec(method="POST", path="/api/clinic-record", json_body=body)


def build_clinical_requests_request(requests: ClinicalRequests) -> RequestSpec:
    body: dict[str, Any] = {
        "member_number": str(requests.member_number),
        "patient_number": str(requests.patient_number),
        "visit_number": str(requests.visit_number),
    }
    if requests.preauth_request_id:
        body["preauth_request_id"] = str(requests.preauth_request_id)

    if requests.prescription:
        body["prescription"] = [
            {
                "item_code": p.item_code,
                "item_name": p.item_name,
                "dosage": p.dosage,
                "duration": p.duration,
                "frequency": p.frequency,
                "price": float(p.price),
                "quantity": float(p.quantity),
                "amount": float(p.amount),
                "route": p.route,
            }
            for p in requests.prescription
        ]
    if requests.laboratory:
        body["laboratory"] = [
            {
                "item_code": o.item_code,
                "item_name": o.item_name,
                "price": float(o.price),
                "quantity": float(o.quantity),
                "amount": float(o.amount),
            }
            for o in requests.laboratory
        ]
    if requests.radiology:
        body["radiology"] = [
            {
                "item_code": o.item_code,
                "item_name": o.item_name,
                "price": float(o.price),
                "quantity": float(o.quantity),
                "amount": float(o.amount),
            }
            for o in requests.radiology
        ]
    if requests.procedure:
        body["procedure"] = [
            {
                "item_code": o.item_code,
                "item_name": o.item_name,
                "price": float(o.price),
                "quantity": float(o.quantity),
                "amount": float(o.amount),
            }
            for o in requests.procedure
        ]
    if requests.other:
        body["other"] = [
            {
                "request_type": o.request_type,
                "item_code": o.item_code,
                "item_name": o.item_name,
                "price": float(o.price),
                "quantity": float(o.quantity),
                "amount": float(o.amount),
            }
            for o in requests.other
        ]

    return RequestSpec(method="POST", path="/api/requests", json_body=body)


def build_admission_request(admission: AdmissionDetails) -> RequestSpec:
    body: dict[str, Any] = {
        "admission_number": admission.admission_number,
        "visit_number": str(admission.visit_number),
        "patient_number": str(admission.patient_number),
        "admission_type": str(admission.admission_type),
        "admission_date": admission.admission_date,
        "admitting_doctor": admission.admitting_doctor,
        "admitting_doctor_type": str(admission.admitting_doctor_type),
        "ward_name": admission.ward_name,
        "ward_number": admission.ward_number,
        "bed_type": admission.bed_type,
        "bed_number": admission.bed_number,
        "inpatient_number": admission.inpatient_number,
        "admission_notes": admission.admission_notes,
        "additional_info": admission.additional_info,
    }
    if admission.preauth_request_id:
        body["preauth_request_id"] = str(admission.preauth_request_id)
    return RequestSpec(method="POST", path="/api/admission", json_body=body)


def build_discharge_request(discharge: DischargeDetails) -> RequestSpec:
    body = {
        "admission_number": discharge.admission_number,
        "patient_number": str(discharge.patient_number),
        "discharge_date": discharge.discharge_date,
        "discharging_doctor": discharge.discharging_doctor,
        "discharge_summary": discharge.discharge_summary,
    }
    return RequestSpec(method="POST", path="/api/discharge", json_body=body)


def build_item_mapping_request(mapping: ItemMapping) -> RequestSpec:
    params = {
        "group_code": mapping.group_code,
        "group_name": mapping.group_name,
        "item_code": mapping.item_code,
        "item_name": mapping.item_name,
    }
    body = {
        "items": [
            {
                "group_code": mapping.group_code,
                "item_code": mapping.item_code,
                "item_name": mapping.item_name,
            }
        ],
        "provider_key": mapping.provider_key,
    }
    return RequestSpec(method="POST", path="/api/new-mapping", params=params, json_body=body)
