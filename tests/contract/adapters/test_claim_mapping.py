from datetime import date
from decimal import Decimal

from sha_claim.adapters.wire import mappers
from sha_claim.adapters.wire.schemas.claim import (
    ClaimDiagnosisWire,
    ClaimInterventionWire,
    ClaimLineWire,
    VirtualClaimWire,
)
from sha_claim.domain.codes import Icd11Code, InterventionCode
from sha_claim.domain.enums import PaymentMechanism
from sha_claim.domain.money import Money


def test_claim_intervention_from_documented_shape() -> None:
    w = ClaimInterventionWire.model_validate(
        {
            "id": "i1",
            "intervention_code": "SHA-12-001",
            "intervention_name": "Consultation",
            "intervention_payment_mechanism": "CAPITATION",
            "intervention_overall_tariff": 0,
            "needs_preauth": True,
            "preauth_exist": False,
            "workflow_state": "ACTIVE",
            "applicable_document_types": ["INVOICE"],
            "bill_from": "2026-09-20T08:00:00Z",
        }
    )
    i = mappers.to_claim_intervention(w)
    assert i.code == InterventionCode("SHA-12-001") and i.payment_mechanism is PaymentMechanism.CAPITATION
    assert i.preauth_outstanding and i.applicable_document_types == ("INVOICE",)
    assert i.bill_from is not None and i.overall_tariff == Money.kes(0)


def test_claim_line_numbers_are_decimal_and_bad_icd_is_tolerated() -> None:
    line = mappers.to_claim_line(
        ClaimLineWire.model_validate(
            {
                "id": "L1",
                "intervention_code": "SHA-12-001",
                "quantity": 2,
                "unit_price": "150.5",
                "line_total_amount": 301.0,
                "charge_date": "2026-09-20",
                "is_active": True,
            }
        )
    )
    assert (
        line.quantity == Decimal(2)
        and line.unit_price == Money.kes("150.50")
        and line.total_amount == Money.kes("301.00")
    )
    assert line.charge_date == date(2026, 9, 20)
    d = mappers.to_claim_diagnosis(
        ClaimDiagnosisWire.model_validate(
            {"diagnosis_code": "not a code", "diagnosis_name": "X", "intervention_code": ""}
        )
    )
    assert d.code is None and d.intervention_code is None and d.name == "X"


def test_virtual_claim_with_nested_collections() -> None:
    w = VirtualClaimWire.model_validate(
        {
            "id": "g",
            "authorization_code": "CR1-TOKEN12345",
            "workflow_state": "DRAFT",
            "total_claim_copay": "10",
            "is_zero": True,
            "interventions": [{"intervention_code": "SHA-12-001", "needs_preauth": False}],
            "claim_diagnoses": [
                {"diagnosis_code": "1A00", "intervention_code": "SHA-12-001", "claim_diagnosis_id": 5}
            ],
            "claim_attachments": [{"id": "a1", "title": "t", "attachment_type": "INVOICE"}],
            "invoices": [{"anything": 1}],
        }
    )
    c = mappers.to_virtual_claim(w)
    assert c.is_zero and c.total_copay == Money.kes(10)
    assert c.interventions[0].code == InterventionCode("SHA-12-001")
    assert c.diagnoses_for(InterventionCode("SHA-12-001"))[0].code == Icd11Code("1A00")
    assert c.attachments[0].attachment_id is not None and c.attachments[0].attachment_id.value == "a1"
    assert c.invoices[0].extra == {"anything": 1}


def test_payer_record_from_portal_example() -> None:
    from sha_claim.adapters.wire.schemas.claim import PayerClaimWire
    from tests.conftest import load_examples

    sample = load_examples()["eclaims"]["GET /api/v1/claims/preview/payer"]["responses"]["200"]["results"][0]
    record = mappers.to_payer_record(PayerClaimWire.model_validate(sample))
    assert record.guid == "guid" and record.provider_claim_no == "providerClaimNo"
    assert record.status == "workflowDisplayName"
    assert record.proposed_value == Money.kes(0)
    assert "claimLines" in record.extra and "authorization" in record.extra


def test_invoices_and_lines_from_portal_example() -> None:
    from tests.conftest import load_examples

    sample = load_examples()["eclaims"]["POST /api/v1/claims/visit"]["responses"]["200"]
    claim = mappers.to_virtual_claim(VirtualClaimWire.model_validate(sample))
    assert claim.consent_token.value == "authorization_code"
    assert len(claim.invoices) == 1 and claim.invoices[0].invoice_type == "invoice_type"
    assert claim.invoices[0].dispatch_status == "dispatch_status"
    # portal sample has `lines: [{}]`: an empty line object maps to defaults rather than failing
    assert len(claim.lines) == 1 and claim.lines[0].guid is None
    assert (
        len(claim.interventions) == 1 and claim.interventions[0].preauth_outstanding is False
    )  # preauth_exist: true in sample


def test_real_uat_visit_response_maps() -> None:
    """Recorded from UAT 2026-09-20: nulls where the docs promise lists/strings, server-assigned invoice number."""
    from tests.conftest import load_fixture

    claim = mappers.to_virtual_claim(
        VirtualClaimWire.model_validate(load_fixture("virtual_claim_opened.json"))
    )
    assert claim.workflow_state == "DRAFT" and claim.claim_auth_status == "AUTHORIZED"
    assert claim.consent_token.value == "TESTTOKEN0"
    assert (
        claim.interventions[0].workflow_state == "ACTIVE"
        and claim.interventions[0].required_preauth_document_types == ()
    )
    assert claim.invoices[0].workflow_state == "VALID" and claim.invoice_number is not None
    assert claim.is_zero and claim.submission_blockers()[0].code == "NO_BILLING_LINES"


def test_per_diem_intervention_carries_sha_accrual() -> None:
    """ICU/HDU care is paid by the day; SHA accrues the days itself and says what they have earned."""
    i = mappers.to_claim_intervention(
        ClaimInterventionWire.model_validate(
            {
                "intervention_code": "SHA-03-001",
                "intervention_name": "ICU CARE",
                "intervention_payment_mechanism": "PER DIEM",
                "workflow_state": "ACTIVE",
                "accrued_per_diem_days": 4,
                "accrued_per_diem_amount": "18000",
                "keph_level_tarrif": "4500",
                "bill_from": "2026-09-20T08:00:00Z",
            }
        )
    )
    assert i.is_per_diem and i.accrued_per_diem_days == 4
    assert i.per_diem_allowance == Money.kes(Decimal("18000"))


def test_per_diem_allowance_falls_back_to_the_keph_rate_when_sha_publishes_no_accrual() -> None:
    """Every UAT facility today: the rate is per KEPH level and none is set, so the accrual reads 0."""
    i = mappers.to_claim_intervention(
        ClaimInterventionWire.model_validate(
            {
                "intervention_code": "SHA-03-002",
                "intervention_payment_mechanism": "PER DIEM",
                "accrued_per_diem_days": 3,
                "accrued_per_diem_amount": 0,
                "keph_level_tarrif": "2500",
            }
        )
    )
    assert i.per_diem_allowance == Money.kes(Decimal("7500"))


def test_per_diem_allowance_is_silent_rather_than_zero_when_sha_knows_nothing() -> None:
    """A zero allowance would read as 'SHA pays nothing' and push a covered stay onto the patient."""
    i = mappers.to_claim_intervention(
        ClaimInterventionWire.model_validate(
            {
                "intervention_code": "SHA-03-003",
                "intervention_payment_mechanism": "PER DIEM",
                "accrued_per_diem_days": 2,
                "accrued_per_diem_amount": 0,
                "keph_level_tarrif": 0,
            }
        )
    )
    assert i.per_diem_allowance is None


def test_fee_for_service_intervention_is_not_per_diem() -> None:
    i = mappers.to_claim_intervention(
        ClaimInterventionWire.model_validate(
            {"intervention_code": "SHA-19-119", "intervention_payment_mechanism": "FEE FOR SERVICE"}
        )
    )
    assert not i.is_per_diem and i.per_diem_allowance is None


def test_claim_line_carries_what_sha_settled_and_what_it_left_the_patient() -> None:
    line = mappers.to_claim_line(
        ClaimLineWire.model_validate(
            {
                "id": "L9",
                "intervention_code": "SHA-03-001",
                "line_total_amount": "5000",
                "nhif_rebate_amount": "4500",
                "sponsor_net_price": "4500",
                "patient_net_price": "500",
                "uhc_exceeded": True,
            }
        )
    )
    assert line.rebate_amount == Money.kes(Decimal("4500"))
    assert line.sponsor_net == Money.kes(Decimal("4500"))
    assert line.patient_net == Money.kes(Decimal("500"))
    assert line.benefit_exceeded
