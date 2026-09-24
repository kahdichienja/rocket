from __future__ import annotations

from typing import Any

from pydantic import Field

from sha_claim.adapters.wire.schemas.common import WireModel

Number = float | int | str | None


class MessageWire(WireModel):
    """`{data, message}` acknowledgement returned by retire/restore/remove operations."""

    message: str = ""
    data: Any = None


class ClaimInterventionWire(WireModel):
    id: str = ""
    intervention_code: str = ""
    intervention_name: str = ""
    intervention_payment_mechanism: str = ""
    intervention_overall_tariff: Number = None
    intervention_fund: str = ""
    sub_benefit_code: str = ""
    needs_preauth: bool = False
    preauth_exist: bool = False
    workflow_state: str = ""
    applicable_document_types: list[str] = Field(default_factory=list)
    required_preauth_document_types: list[str] = Field(default_factory=list)
    bill_from: str = ""
    bill_to: str = ""
    # What a PER DIEM intervention has earned so far. SHA accrues these itself over `bill_from`..`bill_to`;
    # the tariff is per KEPH level, which is why `intervention_overall_tariff` can be 0 while a rate exists.
    accrued_per_diem_amount: Number = None
    accrued_per_diem_days: int | None = None
    keph_level_tarrif: Number = None  # SHA's spelling


class ClaimDiagnosisWire(WireModel):
    claim_diagnosis_id: int | None = None
    diagnosis_code: str = ""
    diagnosis_name: str = ""
    intervention_code: str = ""
    is_flagged_diagnosis: bool = False
    recorded_on: str = ""


class ClaimLineWire(WireModel):
    id: str = ""
    intervention_code: str = ""
    item_code: str = ""
    item_name: str = ""
    quantity: Number = None
    unit_price: Number = None
    line_total_amount: Number = None
    line_net_amount: Number = None
    line_copay: Number = None
    scheme_code: str = ""
    charge_date: str = ""
    is_active: bool = True
    doctor_name: str = ""
    # What SHA worked out for this line. `nhif_rebate_amount` keeps the pre-SHA name on the wire.
    nhif_rebate_amount: Number = None
    sponsor_net_price: Number = None
    patient_net_price: Number = None
    uhc_exceeded: bool = False


class ClaimAttachmentWire(WireModel):
    id: str = ""
    title: str = ""
    attachment_type: str = ""
    intervention_code: str = ""
    description: str = ""


class InvoiceWire(WireModel):
    id: str = ""
    invoice_number: str = ""
    invoice_type: str = ""
    invoice_date: str = ""
    workflow_state: str = ""
    dispatch_status: str = ""
    total_inv_amount: Number = None
    total_inv_net_amount: Number = None
    total_inv_copay: Number = None
    total_inv_discount: Number = None
    lines: list[ClaimLineWire] = Field(default_factory=list)


class PayerClaimWire(WireModel):
    id: int | str | None = None
    guid: str = ""
    provider_claim_no: str = ""
    tracking_number: str = ""
    workflow_state: str = ""
    workflow_display_name: str = ""
    claim_type: str = ""
    is_inpatient: bool = False
    proposed_value: Number = None
    proposed_value_less_copays: Number = None
    total_copay_value: Number = None
    member_name: str = ""
    member_number: str = ""
    scheme_name: str = ""
    created: str = ""


class VirtualClaimWire(WireModel):
    """Response of /claims/visit, /claims/preview, /claims/submit, /claims/close (snake_case on the wire)."""

    id: str = ""
    claim_id: int | None = None
    authorization_code: str = ""
    authorization_guid: str = ""
    workflow_state: str = ""
    claim_auth_status: str = ""
    service_type: str = ""
    patient_name: str = ""
    member_number: str = ""
    payer_name: str = ""
    scheme_name: str = ""
    currency: str = "KES"
    total_claim_amount: Number = None
    total_claim_net_amount: Number = None
    total_claim_copay: Number = None
    total_claim_discount: Number = None
    invoice_number: str = ""
    visit_number: str = ""
    visit_start: str = ""
    visit_end: str = ""
    is_negative: bool = False
    is_zero: bool = False
    interventions: list[ClaimInterventionWire] = Field(default_factory=list)
    claim_diagnoses: list[ClaimDiagnosisWire] = Field(default_factory=list)
    claim_attachments: list[ClaimAttachmentWire] = Field(default_factory=list)
    invoices: list[InvoiceWire] = Field(default_factory=list)


class NextOfKinContactWire(WireModel):
    guid: str = ""
    next_of_kin_full_name: str = ""
    next_of_kin_id_number: str = ""
    contact_value: str = ""
    contact_type: str = ""
    is_verified: bool = False
    is_confirmed: bool = False
    is_main_contact: bool = False
    owner_type: str = ""


class LineResubmissionWire(WireModel):
    line_id: str = ""
    status: str = ""
    message: str = ""
    resubmitted_at: str = ""
