import pytest

from sha_claim.adapters.wire import requests
from sha_claim.domain.codes import InterventionCode
from sha_claim.domain.consent import BiometricGuid, MatchId, Otp
from sha_claim.domain.enums import ServiceType
from sha_claim.domain.identifiers import PatientId

P = PatientId("CR1111111111111-1")
CODES = [InterventionCode("sha-12-001")]


def test_authorize_omits_otp_when_absent() -> None:
    r = requests.authorize(P, ServiceType.CAPITATION, CODES, None)
    assert r.method == "POST" and r.path == "/claims/authorize"
    assert r.json == {
        "patient_id": "CR1111111111111-1",
        "service_type": "CAPITATION",
        "interventions": ["SHA-12-001"],
    }
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
    assert (
        g.params == {"token": "tok", "guid": "guid", "beneficiary_code": "CR1111111111111-1"} and g.idempotent
    )
    assert "beneficiary_code" not in requests.get_authorization("tok", "guid", None).params
    assert requests.reject_authorization("tok").path == "/claims/authorizations/tok/reject"


def test_send_visit_otp_request() -> None:
    r = requests.send_visit_otp(P, CODES)
    assert r.method == "POST" and r.path == "/claims/otp" and not r.idempotent
    assert r.json == {"patient_id": "CR1111111111111-1", "intervention_codes": ["SHA-12-001"]}


def test_open_visit_accepts_each_proof_and_refuses_anything_else() -> None:
    """UAT says it verbatim: "one of otp, auth_guid or match_id is required when starting a visit"."""
    from sha_claim.errors import RequestValidationError

    args = (PatientId("CR1111111111111-1"), ServiceType.OUTPATIENT, [InterventionCode("SHA-18-003")])
    assert requests.open_visit(*args, Otp("123456")).json["otp"] == "123456"
    assert requests.open_visit(*args, BiometricGuid("G-1")).json["auth_guid"] == "G-1"
    assert requests.open_visit(*args, MatchId("M-1")).json["match_id"] == "M-1"
    with pytest.raises(RequestValidationError, match="proof"):
        requests.open_visit(*args, object())  # type: ignore[arg-type]
