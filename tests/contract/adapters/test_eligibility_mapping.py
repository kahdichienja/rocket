from datetime import date

from sha_claim.adapters.wire.mappers import to_eligibility
from sha_claim.adapters.wire.schemas.eligibility import EligibilityWire
from sha_claim.domain.enums import CoverageStatus, EligibilityStatus
from sha_claim.domain.identifiers import PatientId
from tests.conftest import load_fixture


def test_recorded_uat_response_maps_to_domain() -> None:
    wire = EligibilityWire.model_validate(load_fixture("eligibility_member_found.json"))
    e = to_eligibility(wire)

    assert e.patient_id == PatientId("CR0000000000000-0")
    assert e.status is EligibilityStatus.MEMBER_FOUND
    assert e.member_found
    assert e.whitelisted_for_otp is False  # `whitelistedForOTP` needs an explicit alias
    assert e.date_of_birth is None  # empty string → None, not an error
    assert len(e.schemes) == 1
    uhc = e.schemes[0]
    assert uhc.name == "UHC" and uhc.policy_number == "UHC-BE3MMPW5"
    assert uhc.coverage.status is CoverageStatus.COVERED
    assert uhc.policy_period.start == date(2024, 10, 1)
    assert e.is_covered_on(date(2026, 9, 20))
    assert "facilityContracts" in e.extra  # unmodelled fields are preserved, not dropped


def test_unknown_status_code_does_not_break_mapping() -> None:
    wire = EligibilityWire.model_validate({"statusCode": "42", "statusDesc": "weird", "memberCrNumber": ""})
    e = to_eligibility(wire)
    assert e.status is not None and not e.status.is_known
    assert e.patient_id is None and not e.member_found
