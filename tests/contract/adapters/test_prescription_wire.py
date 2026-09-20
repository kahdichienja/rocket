from datetime import date
from decimal import Decimal

from sha_claim.adapters.wire import mappers, requests
from sha_claim.adapters.wire.schemas.prescription import DispenseWire, PrescriptionWire
from sha_claim.domain.codes import InterventionCode, RegulationBody
from sha_claim.domain.identifiers import ConsentToken
from sha_claim.domain.money import Money
from sha_claim.domain.practitioner import PractitionerRef
from sha_claim.domain.prescription import (
    DispensedProduct,
    DispenseRequest,
    MedicationOrder,
    PrescriptionRequest,
)
from tests.conftest import load_examples

TOKEN = ConsentToken("CR1-ABCDEFGHIJ")
CODE = InterventionCode("SHA-12-004")


def test_create_prescription_body_matches_portal_field_names() -> None:
    order = MedicationOrder(
        "AMOX500",
        Decimal("1.5"),
        "TABLET",
        3,
        "DAY",
        5,
        "DAY",
        date(2026, 9, 20),
        end_date=date(2026, 9, 25),
        patient_instruction="after meals",
        needs_refill=True,
        refill_count=1,
    )
    r = requests.create_prescription(
        TOKEN, PrescriptionRequest(CODE, (order,), PractitionerRef.registered("A1", RegulationBody.KMPDC))
    )
    assert r.method == "POST" and r.path == "/prescriptions" and not r.idempotent
    body = r.json
    assert body["consent_token"] == "CR1-ABCDEFGHIJ" and body["intervention_code"] == "SHA-12-004"
    assert body["identification_type"] == "registration_number" and body["regulation_body"] == "KMPDC"
    item = body["items"][0]
    portal_fields = set(
        load_examples()["eclaims"]["POST /api/v1/prescriptions"]["requestBodyExample"]["items"][0]
    )
    assert set(item) <= portal_fields, set(item) - portal_fields
    assert item["dose_quantity"] == 1.5 and item["frequency"] == 3 and item["start_date"] == "2026-09-20"
    assert item["end_date"] == "2026-09-25" and item["needs_refill"] is True and item["refill_count"] == 1
    assert "additional_instruction" not in item


def test_create_dispense_body_matches_portal_field_names() -> None:
    r = requests.create_dispense(
        TOKEN,
        DispenseRequest(
            CODE,
            (DispensedProduct("AMOX500-GEN", 15, Money.kes("12.50")),),
            (PractitionerRef.registered("A1", RegulationBody.COC),),
        ),
    )
    example = load_examples()["eclaims"]["POST /api/v1/prescriptions/dispenses"]["requestBodyExample"]
    assert set(r.json) == set(example)
    assert set(r.json["actual_products"][0]) == set(example["actual_products"][0])
    assert set(r.json["doctors"][0]) == set(example["doctors"][0])
    assert r.json["actual_products"][0] == {
        "actual_product_code": "AMOX500-GEN",
        "total_quantity": 15,
        "medication_price": 12.5,
    }


def test_get_and_remove_doctor_requests() -> None:
    assert requests.get_prescription(TOKEN).params == {"consent_token": "CR1-ABCDEFGHIJ"}
    r = requests.remove_prescription_doctor(TOKEN, CODE, "A1")
    assert r.method == "DELETE" and r.json["practitioner_registration_number"] == "A1"


def test_prescription_and_dispense_map_from_portal_examples() -> None:
    ex = load_examples()["eclaims"]
    rx = mappers.to_prescription(
        PrescriptionWire.model_validate(ex["GET /api/v1/prescriptions"]["responses"]["200"])
    )
    assert rx.guid == "guid" and rx.intervention_code == InterventionCode("CODE")
    assert len(rx.dosage) == 1 and rx.dosage[0].medication == "medication"
    assert (
        rx.dosage[0].dose_quantity is None
    )  # portal placeholder "doseQuantity" is not a number → None, not a crash
    d = mappers.to_dispense(
        DispenseWire.model_validate(ex["POST /api/v1/prescriptions/dispenses"]["responses"]["200"])
    )
    assert d.status == "status" and len(d.dosages) == 1 and "prescription" in d.extra
