"""Mappers converting between wire schemas and domain entities."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from smart_access.adapters.wire.schemas.claim import (
    ClaimStatusResponseWire,
)
from smart_access.adapters.wire.schemas.member import (
    CopaymentRuleWire,
    SmartMemberWire,
)
from smart_access.adapters.wire.schemas.preauth import (
    PreauthResponseWire,
    PreauthStatusFeedbackWire,
)
from smart_access.adapters.wire.schemas.rules import (
    RulesResponseWire,
)
from smart_access.adapters.wire.schemas.visit import (
    SessionActionResponseWire,
    VisitSessionWire,
)
from smart_access.domain.claim import (
    ClaimStatusFeedback,
    ClaimSubmissionResult,
)
from smart_access.domain.enums import (
    ClaimStatus,
    CopayType,
    PreauthStatus,
    SessionStatus,
    SmartResponseType,
)
from smart_access.domain.identifiers import (
    CardSerialNumber,
    GlobalId,
    InvoiceNumber,
    LocationCode,
    MedicalAidCode,
    MemberNumber,
    PatientNumber,
    PolicyId,
    PreauthRequestId,
    SchemeCode,
    SessionId,
    SpId,
    VisitNumber,
)
from smart_access.domain.member import (
    BenefitGroup,
    BenefitPool,
    CopaymentRule,
    SmartMember,
)
from smart_access.domain.preauth import (
    PreauthResponse,
    PreauthStatusFeedback,
    PreauthStatusItem,
)
from smart_access.domain.rules import (
    RuleItemValidation,
    RuleValidationResult,
)
from smart_access.domain.session import (
    SessionCloseResult,
    SessionLinkResult,
    VisitSession,
)


def map_visit_session(raw: dict[str, Any]) -> VisitSession:
    wire = VisitSessionWire.model_validate(raw)
    return VisitSession(
        id=SessionId.of(wire.id),
        patient_number=PatientNumber.of(wire.patient_number),
        status=SessionStatus(wire.sessionStatus),
        sp_id=SpId.of(wire.sp_id),
        location_code=LocationCode.of(wire.location_code) if wire.location_code else None,
        payer_code=MedicalAidCode.of(wire.payer_code) if wire.payer_code else None,
        payer_name=wire.payer_name,
        scheme_code=SchemeCode.of(wire.schemecode) if wire.schemecode else None,
        scheme_name=wire.scheme_name,
        visit_number=VisitNumber.of(wire.visit_number) if wire.visit_number else None,
        member_number=MemberNumber.of(wire.member_number) if wire.member_number else None,
    )


def map_visit_sessions(raw_data: Any) -> tuple[VisitSession, ...]:
    if not raw_data:
        return ()

    sessions_raw: list[Any] = []
    if isinstance(raw_data, list):
        sessions_raw = raw_data
    elif isinstance(raw_data, dict):
        if "content" in raw_data and isinstance(raw_data["content"], list):
            sessions_raw = raw_data["content"]
        elif "id" in raw_data or "session_id" in raw_data:
            sessions_raw = [raw_data]

    results: list[VisitSession] = []
    for s in sessions_raw:
        if isinstance(s, dict) and (s.get("id") or s.get("session_id")):
            try:
                results.append(map_visit_session(s))
            except (ValueError, KeyError, TypeError):
                continue
    return tuple(results)


def map_session_link_result(raw: dict[str, Any]) -> SessionLinkResult:
    wire = SessionActionResponseWire.model_validate(raw)
    is_success = str(wire.code) in ("200", "201") or str(wire.response_type).upper() == "SUCCESS"
    return SessionLinkResult(
        success=is_success,
        code=str(wire.code),
        message=wire.message,
        response_type=SmartResponseType(str(wire.response_type).upper()),
    )


def map_session_close_result(raw: dict[str, Any]) -> SessionCloseResult:
    wire = SessionActionResponseWire.model_validate(raw)
    is_success = str(wire.code) in ("200", "201") or str(wire.response_type).upper() == "SUCCESS"
    return SessionCloseResult(
        success=is_success,
        code=str(wire.code),
        message=wire.message,
        response_type=SmartResponseType(str(wire.response_type).upper()),
    )


def map_smart_members(raw_data: Any) -> tuple[SmartMember, ...]:
    if not raw_data:
        return ()

    list_raw: list[Any] = []
    if isinstance(raw_data, list):
        list_raw = raw_data
    elif isinstance(raw_data, dict):
        if "content" in raw_data and isinstance(raw_data["content"], list):
            list_raw = raw_data["content"]
        elif "global_id" in raw_data or "member_name" in raw_data:
            list_raw = [raw_data]

    members: list[SmartMember] = []
    for item in list_raw:
        if not isinstance(item, dict):
            continue
        try:
            wire = SmartMemberWire.model_validate(item)
            benefits = [
                BenefitPool(
                    id=b.id,
                    amount=Decimal(str(b.amount)),
                    claimable=b.claimable,
                    pool_desc=b.pool_desc,
                    pool_nr=str(b.pool_nr),
                    sp_id=SpId.of(b.sp_id),
                    groups=tuple(BenefitGroup(code=g.code, name=g.name) for g in b.groups),
                )
                for b in wire.benefits
            ]

            members.append(
                SmartMember(
                    admit_id=wire.admit_id,
                    global_id=GlobalId.of(wire.global_id or "UNKNOWN"),
                    medicalaid_code=MedicalAidCode.of(wire.medicalaid_code or "UNKNOWN"),
                    medicalaid_number=MemberNumber.of(wire.medicalaid_number or "UNKNOWN"),
                    medicalaid_scheme_name=wire.medicalaid_scheme_name or "",
                    patient_surname=wire.patient_surname,
                    patient_forenames=wire.patient_forenames,
                    patient_dob=wire.patient_dob,
                    benefits=tuple(benefits),
                    card_serial_number=CardSerialNumber.of(wire.card_serial_number)
                    if wire.card_serial_number
                    else None,
                    has_copay=wire.has_copay,
                    copay_amount=Decimal(str(wire.co_pay_amount)),
                    medicalaid_name=wire.medicalaid_name,
                    medicalaid_scheme_code=SchemeCode.of(wire.medicalaid_scheme_code)
                    if wire.medicalaid_scheme_code
                    else None,
                    medicalaid_plan=wire.medicalaid_plan,
                    patient_gender=wire.patient_gender,
                    policy_id=PolicyId.of(wire.policy_id) if wire.policy_id is not None else None,
                    policy_currency=wire.policy_currency,
                    vip_message=wire.vip_message,
                    session_type=wire.session_type,
                )
            )
        except (ValueError, KeyError, TypeError):
            continue

    return tuple(members)


def map_copayment_rule(raw: dict[str, Any], benefit_id: int) -> CopaymentRule:
    wire = CopaymentRuleWire.model_validate(raw)
    return CopaymentRule(
        benefit_id=benefit_id,
        amount=Decimal(str(wire.amount)),
        is_copay_per_visit=wire.is_copay_per_visit,
        paid_amount=Decimal(str(wire.paid_amount)),
        type=CopayType(wire.type.upper()),
        invoice_number=InvoiceNumber.of(wire.invoice_number) if wire.invoice_number else None,
        receipt_number=wire.receipt_number,
    )


def map_rules_validation_result(raw: dict[str, Any]) -> RuleValidationResult:
    wire = RulesResponseWire.model_validate(raw)
    items: list[RuleItemValidation] = []
    for content in wire.content:
        for it in content.items:
            items.append(
                RuleItemValidation(
                    item_code=it.item_code,
                    item_name=it.item_name,
                    preauth_required=it.preauth_required,
                    preauth_amount=Decimal(str(it.preauth_amount)),
                    preauth_rule_code=it.preauth_rule_code,
                    excluded=it.excluded,
                    price_amount=Decimal(str(it.price_amount)),
                )
            )
    return RuleValidationResult(code=str(wire.code), items=tuple(items))


def map_preauth_response(raw: dict[str, Any]) -> PreauthResponse:
    wire = PreauthResponseWire.model_validate(raw)
    return PreauthResponse(
        preauth_request_id=PreauthRequestId.of(wire.preauth_request_id),
        visit_number=VisitNumber.of(wire.visit_number),
        status=PreauthStatus(wire.status),
    )


def map_preauth_status_feedback(raw_data: Any) -> tuple[PreauthStatusFeedback, ...]:
    if not raw_data:
        return ()

    raw_list: list[Any] = []
    if isinstance(raw_data, list):
        raw_list = raw_data
    elif isinstance(raw_data, dict):
        if "content" in raw_data and isinstance(raw_data["content"], list):
            raw_list = raw_data["content"]
        elif "preauth_request_code" in raw_data or "preauth_request_id" in raw_data:
            raw_list = [raw_data]

    results: list[PreauthStatusFeedback] = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        try:
            wire = PreauthStatusFeedbackWire.model_validate(item)
            items: list[PreauthStatusItem] = []
            for r in wire.rules:
                if isinstance(r, dict) and "items" in r and isinstance(r["items"], list):
                    for sub in r["items"]:
                        if isinstance(sub, dict):
                            items.append(
                                PreauthStatusItem(
                                    item_code=str(sub.get("item_code") or ""),
                                    item_name=str(sub.get("item_name") or ""),
                                    approved_amount=Decimal(str(sub.get("approved_amount") or 0)),
                                    balance_amount=Decimal(str(sub.get("balance_amount") or 0)),
                                    declined_amount=Decimal(str(sub.get("declined_amount") or 0)),
                                    requested_amount=Decimal(str(sub.get("requested_amount") or 0)),
                                    rule_code=str(sub.get("rule_code") or ""),
                                )
                            )

            results.append(
                PreauthStatusFeedback(
                    id=wire.id,
                    preauth_request_code=PreauthRequestId.of(wire.preauth_request_code or "UNKNOWN"),
                    preauth_amount=Decimal(str(wire.preauth_amount)),
                    consumed_amount=Decimal(str(wire.consumed_amount)),
                    preauth_switch_status=wire.preauth_switch_status,
                    invoice_number=InvoiceNumber.of(wire.invoice_number or "UNKNOWN"),
                    patient_number=PatientNumber.of(wire.patient_number or "UNKNOWN"),
                    visit_number=VisitNumber.of(wire.visit_number or "UNKNOWN"),
                    items=tuple(items),
                    diagnosis_code=wire.diagnosis_code,
                    operation_name=wire.operation_name,
                    preauth_notes=wire.preauth_notes,
                )
            )
        except (ValueError, KeyError, TypeError):
            continue

    return tuple(results)


def map_claim_submission_result(raw: dict[str, Any]) -> ClaimSubmissionResult:
    code = str(raw.get("code") or "200")
    resp_type = str(raw.get("response_type") or "SUCCESS").upper()
    is_success = code in ("200", "201") or resp_type == "SUCCESS"
    msg = str(raw.get("message") or "")
    if not msg and isinstance(raw.get("content"), dict):
        msg = str(raw["content"].get("message") or "")
    return ClaimSubmissionResult(
        success=is_success,
        code=code,
        message=msg,
        response_type=SmartResponseType(resp_type),
    )


def map_claim_status_feedback(raw_data: Any) -> tuple[ClaimStatusFeedback, ...]:
    if not raw_data:
        return ()

    raw_list: list[Any] = []
    if isinstance(raw_data, list):
        raw_list = raw_data
    elif isinstance(raw_data, dict):
        if "content" in raw_data and isinstance(raw_data["content"], list):
            raw_list = raw_data["content"]
        elif "claim_status" in raw_data or "session_id" in raw_data:
            raw_list = [raw_data]

    results: list[ClaimStatusFeedback] = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        try:
            wire = ClaimStatusResponseWire.model_validate(item)
            results.append(
                ClaimStatusFeedback(
                    session_id=SessionId.of(wire.session_id),
                    claim_status=ClaimStatus(wire.claim_status),
                    payer_name=wire.payer_name,
                    patient_number=PatientNumber.of(wire.patient_number or "UNKNOWN"),
                    visit_number=VisitNumber.of(wire.visit_number or "UNKNOWN"),
                    scheme_name=wire.scheme_name,
                    amount=Decimal(str(wire.amount)),
                    invoice_number=InvoiceNumber.of(wire.invoice_number or "UNKNOWN"),
                )
            )
        except (ValueError, KeyError, TypeError):
            continue

    return tuple(results)
