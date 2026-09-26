"""Contract tests for Smart wire mappers using official doc payloads."""

from decimal import Decimal

from smart_access.adapters.wire.mappers import (
    map_claim_status_feedback,
    map_preauth_response,
    map_rules_validation_result,
    map_smart_members,
    map_visit_sessions,
)
from smart_access.domain.enums import ClaimStatus, SessionStatus


def test_map_visit_sessions_from_json() -> None:
    sample_json = [
        {
            "id": 12345,
            "patient_number": "PT000001",
            "sessionStatus": "PENDING",
            "sp_id": 678,
            "location_code": "100",
            "payer_code": "MIC",
            "payer_name": "Madson Insurance",
            "schemecode": "SAI",
            "scheme_name": "Smart Applications",
            "visit_number": "AC000001",
            "member_number": "8306004943-00",
        }
    ]
    sessions = map_visit_sessions(sample_json)
    assert len(sessions) == 1
    s = sessions[0]
    assert s.id == 12345
    assert s.patient_number == "PT000001"
    assert s.status == SessionStatus.PENDING
    assert s.sp_id == 678
    assert s.location_code == "100"
    assert s.payer_code == "MIC"
    assert s.member_number == "8306004943-00"


def test_map_member_details_from_json() -> None:
    sample_json = {
        "admit_id": "5678",
        "benefits": [
            {
                "id": 154663,
                "amount": 25000,
                "claimable": True,
                "pool_desc": "Outpatient Benefit",
                "pool_nr": "3",
                "sp_id": 678,
                "groups": [{"code": "GRP1", "name": "General OP"}],
            }
        ],
        "card_serial_number": "CK0000014590001",
        "global_id": "KE0002714501",
        "has_copay": True,
        "co_pay_amount": 500,
        "medicalaid_code": "MIC",
        "medicalaid_name": "Madson Insurance",
        "medicalaid_number": "8306004943-00",
        "medicalaid_scheme_code": "SAI",
        "medicalaid_scheme_name": "Smart Applications",
        "medicalaid_plan": "MIC.SAI",
        "patient_surname": "Murphy",
        "patient_forenames": "James",
        "patient_dob": "1985-05-15",
    }

    members = map_smart_members(sample_json)
    assert len(members) == 1
    m = members[0]
    assert m.admit_id == "5678"
    assert m.full_name == "James Murphy"
    assert m.global_id == "KE0002714501"
    assert m.has_copay is True
    assert m.copay_amount == Decimal("500")
    assert len(m.benefits) == 1
    b = m.benefits[0]
    assert b.id == 154663
    assert b.amount == Decimal("25000")
    assert b.pool_nr == "3"
    assert b.groups[0].code == "GRP1"


def test_map_rules_response() -> None:
    sample_json = {
        "code": "200",
        "content": [
            {
                "items": [
                    {
                        "item_code": "OPT00001",
                        "item_name": "optical frames",
                        "preauth_required": True,
                        "preauth_amount": 2000,
                        "preauth_rule_code": "PREAUTH:900|BENEFIT1641|SAMPLEX2",
                        "excluded": "false",
                        "price_amount": 2000,
                    }
                ]
            }
        ],
    }

    result = map_rules_validation_result(sample_json)
    assert result.code == "200"
    assert len(result.items) == 1
    item = result.items[0]
    assert item.item_code == "OPT00001"
    assert item.preauth_required is True
    assert item.excluded is False
    assert item.price_amount == Decimal("2000")


def test_map_preauth_response() -> None:
    sample_json = {
        "preauth_request_id": "PR-998811",
        "visit_number": "AC000001",
        "status": "Approved",
    }
    resp = map_preauth_response(sample_json)
    assert resp.preauth_request_id == "PR-998811"
    assert resp.visit_number == "AC000001"
    assert resp.is_approved is True


def test_map_claim_status_response() -> None:
    sample_json = [
        {
            "session_id": 4235677,
            "claim_status": "Billed",
            "payer_name": "Madson Insurance",
            "patient_number": "PT000001",
            "visit_number": "AC000001",
            "scheme_name": "Smart Applications",
            "amount": 3000,
            "invoice_number": "INV-00000001",
        }
    ]
    fb = map_claim_status_feedback(sample_json)
    assert len(fb) == 1
    assert fb[0].session_id == 4235677
    assert fb[0].claim_status == ClaimStatus.BILLED
    assert fb[0].amount == Decimal("3000")
    assert fb[0].invoice_number == "INV-00000001"
