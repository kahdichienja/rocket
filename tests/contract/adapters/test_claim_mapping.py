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
