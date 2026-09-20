from sha_claim.adapters.wire import requests
from sha_claim.domain.codes import InterventionCode
from sha_claim.domain.consent import BiometricGuid, MatchId, Otp
from sha_claim.domain.enums import ServiceType
from sha_claim.domain.identifiers import PatientId

P = PatientId("CR1")
CODES = [InterventionCode("sha-12-001")]


def test_authorize_omits_otp_when_absent() -> None:
    r = requests.authorize(P, ServiceType.CAPITATION, CODES, None)
    assert r.method == "POST" and r.path == "/claims/authorize"
    assert r.json == {"patient_id": "CR1", "service_type": "CAPITATION", "interventions": ["SHA-12-001"]}
    assert not r.idempotent


def test_authorize_includes_otp_when_given() -> None:
    assert requests.authorize(P, ServiceType.OUTPATIENT, CODES, Otp("123456")).json["otp"] == "123456"


def test_open_visit_encodes_each_proof_kind() -> None:
    assert requests.open_visit(P, ServiceType.CAPITATION, CODES, Otp("1")).json["otp"] == "1"
    assert requests.open_visit(P, ServiceType.CAPITATION, CODES, BiometricGuid("g")).json["auth_guid"] == "g"
    assert requests.open_visit(P, ServiceType.CAPITATION, CODES, MatchId("m")).json["match_id"] == "m"
    body = requests.open_visit(P, ServiceType.CAPITATION, CODES, Otp("1")).json
    assert body["intervention_codes"] == ["SHA-12-001"]
    assert "interventions" not in body  # visit uses intervention_codes, authorize uses interventions


def test_get_and_reject_authorization() -> None:
    g = requests.get_authorization("tok", "guid", P)
    assert g.params == {"token": "tok", "guid": "guid", "beneficiary_code": "CR1"} and g.idempotent
    assert "beneficiary_code" not in requests.get_authorization("tok", "guid", None).params
    assert requests.reject_authorization("tok").path == "/claims/authorizations/tok/reject"
