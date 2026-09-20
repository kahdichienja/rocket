import json

from sha_claim.adapters.wire import mappers, requests
from sha_claim.adapters.wire.schemas.common import Page
from sha_claim.adapters.wire.schemas.emergency import EmergencyProtocolWire
from sha_claim.adapters.wire.transport import TimeoutKind
from sha_claim.domain.attachments import Attachment
from sha_claim.domain.codes import DocumentType, Icd11Code, InterventionCode, ProtocolCode, RegulationBody
from sha_claim.domain.consent import Otp
from sha_claim.domain.emergency import EmergencyCase, EmtClaim, ProtocolLine
from sha_claim.domain.enums import BroughtBy, ModeOfArrival
from sha_claim.domain.identifiers import ConsentToken, PatientId
from sha_claim.domain.money import Money
from sha_claim.domain.practitioner import PractitionerRef
from tests.conftest import load_examples

TOKEN = ConsentToken("CR1-ABCDEFGHIJ")
DOCTOR = PractitionerRef.registered("A1234", RegulationBody.KMPDC)
CODE = InterventionCode("SHA-19-001")


def test_open_emergency_case_identified_and_unidentified() -> None:
    identified = requests.open_emergency_case(
        EmergencyCase(
            DOCTOR,
            "REF-1",
            BroughtBy.PARAMEDICS,
            ModeOfArrival.AMBULANCE,
            (CODE,),
            PatientId("CR1"),
            Otp("123456"),
            "unconscious",
        )
    )
    example = load_examples()["eclaims"]["POST /api/v1/claims/emergency"]["requestBodyExample"]
    assert set(identified.json) == set(example)
    assert (
        identified.json["identification_type"] == "registration_number"
        and identified.json["regulation_body"] == "KMPDC"
    )
    assert identified.json["mode_of_arrival"] == "AMBULANCE" and identified.json["interventions"] == [
        "SHA-19-001"
    ]
    unidentified = requests.open_emergency_case(
        EmergencyCase(DOCTOR, "REF-2", BroughtBy.UNKNOWN, ModeOfArrival.WALK_IN, (CODE,))
    )
    assert (
        "beneficiary_cr_id" not in unidentified.json
        and "otp" not in unidentified.json
        and "notes" not in unidentified.json
    )


def test_protocol_line_is_multipart_with_comma_separated_diagnoses() -> None:
    r = requests.add_emergency_protocol(
        TOKEN,
        ProtocolLine(
            ProtocolCode("EP-1"), CODE, Money.kes("5000"), 2, (Icd11Code("NF0A"), Icd11Code("NF0B"))
        ),
    )
    assert r.multipart and r.form is not None
    assert r.form["diagnoses"] == "NF0A,NF0B"  # comma-separated here, JSON on /claims/lines
    assert r.form["unit_price"] == "5000.00" and r.form["quantity"] == "2"


def test_protocols_query_and_doctor_requests() -> None:
    q = requests.emergency_protocols(CODE, active=True)
    assert q.idempotent and q.params == {"intervention_code": "SHA-19-001", "active": "true"}
    d = requests.add_emergency_doctor(TOKEN, DOCTOR)
    assert d.json == {
        "consent_token": "CR1-ABCDEFGHIJ",
        "identification_number": "A1234",
        "identification_type": "registration_number",
        "regulation_body": "KMPDC",
    }
    assert requests.remove_emergency_doctor(TOKEN).method == "DELETE"


def test_emt_claim_multipart_matches_portal_fields() -> None:
    emt = EmtClaim(
        ProtocolCode("EP-1"),
        "CASE-1",
        "A1234",
        "AMB-9",
        PatientId("CR1"),
        Otp("123456"),
        (Icd11Code("NF0A"),),
        (CODE,),
        (Attachment("run.pdf", b"%PDF", DocumentType.CASE_NOTE, "application/pdf"),),
    )
    r = requests.open_emt_claim(TOKEN, emt)
    example = load_examples()["eclaims"]["POST /api/v1/claims/emt"]["requestBodyExample"]
    assert r.form is not None and set(r.form) == set(example)
    assert json.loads(r.form["diagnoses"]) == ["NF0A"] and json.loads(r.form["interventions"]) == [
        "SHA-19-001"
    ]
    assert r.files == {"attachment_0": ("run.pdf", b"%PDF", "application/pdf")}
    assert json.loads(r.form["attachments"])[0]["field"] == "attachment_0"
    assert r.timeout is TimeoutKind.UPLOAD


def test_protocols_map_from_portal_example() -> None:
    page = Page[EmergencyProtocolWire].model_validate(
        load_examples()["eclaims"]["GET /api/v1/claims/emergency/protocols"]["responses"]["200"]
    )
    protocol = mappers.to_emergency_protocol(page.results[0])
    assert protocol.code == ProtocolCode("protocolCode") and protocol.name == "name"
    assert protocol.tariff is None  # placeholder string is not a number
