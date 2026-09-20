"""Wire models → domain read models. The only place that knows both vocabularies."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from sha_claim.adapters.wire.parsing import parse_date, parse_datetime
from sha_claim.adapters.wire.schemas.authorization import AuthorizationWire, AuthorizedInterventionWire
from sha_claim.adapters.wire.schemas.benefits import BenefitPackageWire, InterventionWire, SubBenefitWire
from sha_claim.adapters.wire.schemas.claim import (
    ClaimAttachmentWire,
    ClaimDiagnosisWire,
    ClaimInterventionWire,
    ClaimLineWire,
    InvoiceWire,
    LineResubmissionWire,
    NextOfKinContactWire,
    PayerClaimWire,
    VirtualClaimWire,
)
from sha_claim.adapters.wire.schemas.eligibility import CoverageWire, EligibilityWire, SchemeWire
from sha_claim.adapters.wire.schemas.preauth import PreauthorizationWire
from sha_claim.domain.benefits import BenefitPackage, InterventionCoverage, SubBenefit
from sha_claim.domain.claim import (
    ClaimAttachment,
    ClaimDiagnosis,
    ClaimIntervention,
    ClaimLine,
    Invoice,
    LineResubmission,
    NextOfKinContact,
    PayerClaimRecord,
    VirtualClaim,
)
from sha_claim.domain.codes import Icd11Code, InterventionCode
from sha_claim.domain.consent import Authorization, AuthorizedIntervention
from sha_claim.domain.eligibility import Coverage, DateRange, Eligibility, Scheme
from sha_claim.domain.enums import (
    AuthorizationStatus,
    CoverageStatus,
    EligibilityStatus,
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
from sha_claim.domain.preauth import Preauthorization


def to_eligibility(w: EligibilityWire) -> Eligibility:
    return Eligibility(
        patient_id=_patient(w.member_cr_number),
        full_name=w.full_name,
        status=EligibilityStatus.parse(w.status_code),
        status_description=w.status_desc,
        schemes=tuple(_to_scheme(s) for s in w.schemes),
        date_of_birth=parse_date(w.date_of_birth),
        gender=w.gender,
        age=w.age,
        is_alive=w.is_alive,
        whitelisted_for_otp=w.whitelisted_for_otp,
        facility_biometrics_enforced=w.facility_biometrics_enforced,
        extra=w.unmodelled(),
    )


def to_benefit_package(w: BenefitPackageWire) -> BenefitPackage:
    return BenefitPackage(code=w.parent_benefit_code, name=w.parent_benefit)


def to_sub_benefit(w: SubBenefitWire) -> SubBenefit:
    return SubBenefit(
        code=w.code, name=w.name, parent_code=w.parent_benefit_code, access_point=w.access_point
    )


def to_intervention_coverage(w: InterventionWire) -> InterventionCoverage:
    return InterventionCoverage(
        code=InterventionCode(w.code),
        name=w.name,
        payment_mechanism=PaymentMechanism.parse(w.payment_mechanism),
        needs_preauth=w.needs_preauth or w.needs_manual_preauth_approval,
        needs_doctor_authorization=w.needs_doctor_authorization,
        access_point=w.access_point,
        overall_tariff=_money(w.overall_tariff),
        applicable_schemes=tuple(w.applicable_schemes),
        fund=w.fund,
        sub_benefit_code=w.sub_benefit_code,
        extra=w.unmodelled(),
    )


def to_authorization(w: AuthorizationWire) -> Authorization:
    return Authorization(
        guid=w.guid,
        token=w.token,
        auth_code=w.auth_code,
        status=AuthorizationStatus.parse(w.status),
        label=w.label,
        is_open=w.is_open,
        benefit_type=w.benefit_type,
        beneficiary=_patient(w.beneficiary_code),
        beneficiary_name=w.beneficiary_name,
        provider_fid=w.provider_fid,
        interventions=tuple(_to_authorized_intervention(i) for i in w.interventions),
        expiry=parse_datetime(w.expiry),
        overall_preauth_finalised=w.overall_preauth_finalised,
        record_id=w.id,
        extra=w.unmodelled(),
    )


def to_virtual_claim(w: VirtualClaimWire) -> VirtualClaim:
    return VirtualClaim(
        consent_token=ConsentToken(w.authorization_code),
        guid=ClaimGuid(w.id) if w.id.strip() else None,
        claim_id=w.claim_id,
        workflow_state=w.workflow_state,
        claim_auth_status=w.claim_auth_status,
        service_type=_service_type(w.service_type),
        patient_name=w.patient_name,
        member_number=w.member_number,
        payer_name=w.payer_name,
        scheme_name=w.scheme_name,
        currency=w.currency or "KES",
        total_amount=_money(w.total_claim_amount, w.currency),
        net_amount=_money(w.total_claim_net_amount, w.currency),
        total_copay=_money(w.total_claim_copay, w.currency),
        total_discount=_money(w.total_claim_discount, w.currency),
        invoice_number=InvoiceNumber(w.invoice_number) if w.invoice_number.strip() else None,
        visit_number=w.visit_number,
        visit_start=parse_datetime(w.visit_start),
        visit_end=parse_datetime(w.visit_end),
        interventions=tuple(to_claim_intervention(i) for i in w.interventions),
        diagnoses=tuple(to_claim_diagnosis(d) for d in w.claim_diagnoses),
        attachments=tuple(to_claim_attachment(a) for a in w.claim_attachments),
        invoices=tuple(to_invoice(i, w.currency) for i in w.invoices),
        is_negative=w.is_negative,
        is_zero=w.is_zero,
        extra=w.unmodelled(),
    )


def to_claim_intervention(w: ClaimInterventionWire) -> ClaimIntervention:
    return ClaimIntervention(
        code=InterventionCode(w.intervention_code),
        name=w.intervention_name,
        payment_mechanism=PaymentMechanism.parse(w.intervention_payment_mechanism),
        needs_preauth=w.needs_preauth,
        preauth_exists=w.preauth_exist,
        workflow_state=w.workflow_state,
        sub_benefit_code=w.sub_benefit_code,
        fund=w.intervention_fund,
        overall_tariff=_money(w.intervention_overall_tariff),
        applicable_document_types=tuple(w.applicable_document_types),
        required_preauth_document_types=tuple(w.required_preauth_document_types),
        bill_from=parse_datetime(w.bill_from),
        bill_to=parse_datetime(w.bill_to),
        extra=w.unmodelled(),
    )


def to_claim_diagnosis(w: ClaimDiagnosisWire) -> ClaimDiagnosis:
    return ClaimDiagnosis(
        code=_icd(w.diagnosis_code),
        name=w.diagnosis_name,
        intervention_code=_intervention(w.intervention_code),
        record_id=w.claim_diagnosis_id,
        is_flagged=w.is_flagged_diagnosis,
        recorded_on=parse_datetime(w.recorded_on),
        extra=w.unmodelled(),
    )


def to_claim_line(w: ClaimLineWire) -> ClaimLine:
    return ClaimLine(
        guid=LineGuid(w.id) if w.id.strip() else None,
        intervention_code=_intervention(w.intervention_code),
        item_code=w.item_code,
        item_name=w.item_name,
        quantity=_decimal(w.quantity),
        unit_price=_money(w.unit_price),
        total_amount=_money(w.line_total_amount),
        net_amount=_money(w.line_net_amount),
        copay=_money(w.line_copay),
        scheme_code=w.scheme_code,
        charge_date=parse_date(w.charge_date),
        is_active=w.is_active,
        doctor_name=w.doctor_name,
        extra=w.unmodelled(),
    )


def to_claim_attachment(w: ClaimAttachmentWire) -> ClaimAttachment:
    return ClaimAttachment(
        attachment_id=AttachmentId(w.id) if w.id.strip() else None,
        title=w.title,
        attachment_type=w.attachment_type,
        intervention_code=_intervention(w.intervention_code),
        description=w.description,
        extra=w.unmodelled(),
    )


def to_preauthorization(w: PreauthorizationWire) -> Preauthorization:
    currency = w.provider_currency or "KES"
    return Preauthorization(
        guid=w.guid,
        token=w.token,
        intervention_code=_intervention(w.intervention_code),
        status=w.status,
        doctor_review_status=w.doctor_review_status,
        needs_doctor_approval=w.needs_doctor_approval,
        doctor_approved=w.doctor_approved,
        doctors_required=w.number_of_preauth_doctors_required,
        is_request_phase=w.is_request_phase,
        is_response_phase=w.is_response_phase,
        total_estimated=_money(w.total_estimated_amount_for_preauth, currency),
        interim_approved=_money(w.total_interim_approved_amount_for_preauth, currency),
        final_approved=_money(w.final_approved_amount, currency),
        service_start=parse_datetime(w.service_start),
        service_end=parse_datetime(w.service_end),
        provider_notification_email=w.provider_notification_email,
        member_name=w.member_name,
        description=w.description,
        countdown=w.countdown,
        record_id=w.id,
        extra=w.unmodelled(),
    )


def to_invoice(w: InvoiceWire, currency: str) -> Invoice:
    return Invoice(
        invoice_id=w.id,
        invoice_number=InvoiceNumber(w.invoice_number) if w.invoice_number.strip() else None,
        invoice_type=w.invoice_type,
        workflow_state=w.workflow_state,
        dispatch_status=w.dispatch_status,
        total_amount=_money(w.total_inv_amount, currency),
        net_amount=_money(w.total_inv_net_amount, currency),
        copay=_money(w.total_inv_copay, currency),
        discount=_money(w.total_inv_discount, currency),
        lines=tuple(to_claim_line(line) for line in w.lines),
        invoice_date=parse_date(w.invoice_date),
        extra=w.unmodelled(),
    )


def to_next_of_kin_contact(w: NextOfKinContactWire) -> NextOfKinContact:
    return NextOfKinContact(
        guid=w.guid,
        full_name=w.next_of_kin_full_name,
        id_number=w.next_of_kin_id_number,
        contact_value=w.contact_value,
        contact_type=w.contact_type,
        is_verified=w.is_verified,
        is_confirmed=w.is_confirmed,
        is_main_contact=w.is_main_contact,
        owner_type=w.owner_type,
        extra=w.unmodelled(),
    )


def to_line_resubmission(w: LineResubmissionWire) -> LineResubmission:
    return LineResubmission(
        line=LineGuid(w.line_id) if w.line_id.strip() else None,
        status=w.status,
        message=w.message,
        resubmitted_at=parse_datetime(w.resubmitted_at),
    )


def to_payer_record(w: PayerClaimWire) -> PayerClaimRecord:
    return PayerClaimRecord(
        guid=w.guid,
        provider_claim_no=w.provider_claim_no,
        tracking_number=w.tracking_number,
        workflow_state=w.workflow_state,
        workflow_display_name=w.workflow_display_name,
        claim_type=w.claim_type,
        is_inpatient=w.is_inpatient,
        proposed_value=_money(w.proposed_value),
        proposed_value_less_copays=_money(w.proposed_value_less_copays),
        total_copay=_money(w.total_copay_value),
        member_name=w.member_name,
        member_number=w.member_number,
        scheme_name=w.scheme_name,
        created=parse_datetime(w.created),
        extra=w.unmodelled(),
    )


# ── helpers ──


def _to_scheme(s: SchemeWire) -> Scheme:
    return Scheme(
        name=s.scheme_name,
        scheme_id=s.scheme_id,
        member_type=s.member_type,
        policy_number=s.policy.number,
        policy_period=DateRange(parse_date(s.policy.start_date), parse_date(s.policy.end_date)),
        coverage=_to_coverage(s.coverage),
    )


def _to_coverage(c: CoverageWire) -> Coverage:
    return Coverage(
        status=CoverageStatus.parse(c.status),
        message=c.message,
        reason=c.reason,
        period=DateRange(parse_date(c.start_date), parse_date(c.end_date)),
    )


def _to_authorized_intervention(i: AuthorizedInterventionWire) -> AuthorizedIntervention:
    return AuthorizedIntervention(
        code=InterventionCode(i.code),
        name=i.name,
        needs_preauth=i.needs_preauth,
        payment_mechanism=PaymentMechanism.parse(i.payment_mechanism),
        sub_benefit_code=i.sub_benefit_code,
    )


def _patient(cr_number: str) -> PatientId | None:
    return PatientId(cr_number) if cr_number.strip() else None


def _money(raw: str | float | int | None, currency: str = "KES") -> Money | None:
    if raw is None or raw == "":
        return None
    try:
        return Money(Decimal(str(raw)), currency or "KES")
    except (InvalidOperation, ValueError):
        return None


def _service_type(raw: str) -> ServiceType | None:
    try:
        return ServiceType(raw) if raw else None
    except ValueError:
        return None


def _decimal(raw: str | float | int | None) -> Decimal:
    try:
        return Decimal(str(raw)) if raw not in (None, "") else Decimal(0)
    except InvalidOperation:
        return Decimal(0)


def _icd(raw: str) -> Icd11Code | None:
    try:
        return Icd11Code(raw) if raw.strip() else None
    except ValueError:
        return None


def _intervention(raw: str) -> InterventionCode | None:
    return InterventionCode(raw) if raw.strip() else None
