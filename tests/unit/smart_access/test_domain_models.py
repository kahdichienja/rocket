"""Unit tests for smart_access domain models."""

from decimal import Decimal

import pytest

from smart_access.domain.claim import (
    ClaimStatusFeedback,
)
from smart_access.domain.enums import ClaimStatus, SessionStatus
from smart_access.domain.identifiers import (
    GlobalId,
    InvoiceNumber,
    MedicalAidCode,
    MemberNumber,
    PatientNumber,
    SessionId,
    SpId,
    VisitNumber,
)
from smart_access.domain.member import (
    BenefitPool,
    SmartMember,
)
from smart_access.domain.rules import (
    RuleItemValidation,
    RulesCheckItem,
    RuleValidationResult,
)
from smart_access.domain.session import VisitSession


def test_visit_session_behavior() -> None:
    session = VisitSession(
        id=SessionId(123),
        patient_number=PatientNumber("PT01"),
        status=SessionStatus.PENDING,
        sp_id=SpId(678),
    )
    assert session.is_pending is True
    assert session.is_active is False
    assert session.is_closed is False


def test_benefit_pool_and_member_behavior() -> None:
    pool1 = BenefitPool(
        id=1,
        amount=Decimal("25000.00"),
        claimable=True,
        pool_desc="Outpatient",
        pool_nr="3",
        sp_id=SpId(678),
    )
    pool2 = BenefitPool(
        id=2,
        amount=Decimal("0.00"),
        claimable=False,
        pool_desc="Optical",
        pool_nr="4",
        sp_id=SpId(678),
    )

    assert pool1.has_balance is True
    assert pool1.covers(Decimal("20000.00")) is True
    assert pool1.covers(Decimal("30000.00")) is False
    assert pool2.has_balance is False

    member = SmartMember(
        admit_id="5678",
        global_id=GlobalId("KE001"),
        medicalaid_code=MedicalAidCode("MIC"),
        medicalaid_number=MemberNumber("8306004943-00"),
        medicalaid_scheme_name="Smart Applications",
        patient_surname="Murphy",
        patient_forenames="James",
        patient_dob="1985-05-15",
        benefits=(pool1, pool2),
    )

    assert member.full_name == "James Murphy"
    assert member.find_pool(3) == pool1
    assert member.find_pool("4") == pool2
    assert member.find_pool(99) is None


def test_rules_validation_result_helpers() -> None:
    item1 = RuleItemValidation(
        item_code="OPT01",
        item_name="Frames",
        preauth_required=True,
        preauth_amount=Decimal("2000"),
        preauth_rule_code="RULE1",
        excluded=False,
        price_amount=Decimal("2000"),
    )
    item2 = RuleItemValidation(
        item_code="MED01",
        item_name="Drugs",
        preauth_required=False,
        preauth_amount=Decimal(0),
        preauth_rule_code="",
        excluded=True,
        price_amount=Decimal("500"),
    )

    res = RuleValidationResult(code="200", items=(item1, item2))
    assert res.any_preauth_required is True
    assert res.any_excluded is True
    assert res.preauth_items == (item1,)
    assert res.excluded_items == (item2,)


def test_rules_check_item_validation() -> None:
    with pytest.raises(ValueError, match="provider_item_code cannot be empty"):
        RulesCheckItem(provider_item_code="", item_net_amount=Decimal(10), pool_number=1)

    with pytest.raises(ValueError, match="item_net_amount cannot be negative"):
        RulesCheckItem(provider_item_code="X", item_net_amount=Decimal(-1), pool_number=1)


def test_claim_status_feedback() -> None:
    fb_billed = ClaimStatusFeedback(
        session_id=SessionId(1),
        claim_status=ClaimStatus.BILLED,
        payer_name="Payer",
        patient_number=PatientNumber("PT1"),
        visit_number=VisitNumber("VN1"),
        scheme_name="Scheme",
        amount=Decimal("3000"),
        invoice_number=InvoiceNumber("INV-1"),
    )
    assert fb_billed.is_billed is True
    assert fb_billed.is_pending is False
    assert fb_billed.is_terminal_failure is False

    fb_rejected = ClaimStatusFeedback(
        session_id=SessionId(1),
        claim_status=ClaimStatus.REJECTED,
        payer_name="Payer",
        patient_number=PatientNumber("PT1"),
        visit_number=VisitNumber("VN1"),
        scheme_name="Scheme",
        amount=Decimal("3000"),
        invoice_number=InvoiceNumber("INV-1"),
    )
    assert fb_rejected.is_billed is False
    assert fb_rejected.is_terminal_failure is True
