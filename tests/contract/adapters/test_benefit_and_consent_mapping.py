from datetime import datetime

from sha_claim.adapters.wire import mappers
from sha_claim.adapters.wire.schemas.authorization import AuthorizationWire
from sha_claim.adapters.wire.schemas.benefits import BenefitPackageWire, InterventionWire, SubBenefitWire
from sha_claim.adapters.wire.schemas.claim import VirtualClaimWire
from sha_claim.adapters.wire.schemas.common import Page
from sha_claim.domain.codes import InterventionCode
from sha_claim.domain.enums import AuthorizationStatus, PaymentMechanism, ServiceType
from sha_claim.domain.identifiers import PatientId
from sha_claim.domain.money import Money
from tests.conftest import load_fixture


def test_benefits_page() -> None:
    page = Page[BenefitPackageWire].model_validate(load_fixture("benefits.json"))
    packages = [mappers.to_benefit_package(b) for b in page.results]
    assert page.count == 2
    assert {p.code for p in packages} == {"SHA-08", "SHA-12"}


def test_sub_benefits_page() -> None:
    page = Page[SubBenefitWire].model_validate(load_fixture("sub_benefits.json"))
    subs = [mappers.to_sub_benefit(s) for s in page.results]
    op = next(s for s in subs if s.code == "SHA-12-SC-01")
    assert op.parent_code == "SHA-12"
    assert op.access_point == "OP"


def test_interventions_page_and_service_type_rule() -> None:
    page = Page[InterventionWire].model_validate(load_fixture("interventions.json"))
    coverage = [mappers.to_intervention_coverage(i) for i in page.results]
    consultation = next(c for c in coverage if c.code == InterventionCode("SHA-12-001"))
    assert consultation.payment_mechanism is PaymentMechanism.CAPITATION
    assert consultation.needs_preauth is False
    assert consultation.overall_tariff == Money.kes(0)
    assert consultation.applicable_schemes == ("UHC",)
    # Observed on UAT: CAPITATION interventions are refused under OUTPATIENT.
    assert consultation.service_type_for_authorization is ServiceType.CAPITATION


def test_pending_authorization_maps() -> None:
    a = mappers.to_authorization(AuthorizationWire.model_validate(load_fixture("authorization_pending.json")))
    assert a.status is AuthorizationStatus.PENDING
    assert a.is_pending and a.is_open
    assert a.label == "UNAUTHORIZED"
    assert a.beneficiary == PatientId("CR0000000000000-0")
    assert a.token == "TESTTOKEN0"
    assert a.guid
    assert a.interventions[0].code == InterventionCode("SHA-12-001")
    assert not a.needs_preauth
    assert isinstance(a.expiry, datetime) and a.expiry.tzinfo is not None
    assert a.as_biometric_proof().value == a.guid


def test_virtual_claim_maps_from_documented_snake_case_shape() -> None:
    wire = VirtualClaimWire.model_validate(
        {
            "id": "guid-1",
            "claim_id": 77,
            "authorization_code": "CR1-ABCDEFGH",
            "workflow_state": "DRAFT",
            "claim_auth_status": "AUTHORIZED",
            "service_type": "CAPITATION",
            "patient_name": "T",
            "currency": "KES",
            "total_claim_amount": 1500.5,
            "total_claim_net_amount": "1400.00",
            "invoice_number": "",
            "visit_start": "2026-09-20T10:00:00+03:00",
            "unknown_future_field": 1,
        }
    )
    claim = mappers.to_virtual_claim(wire)
    assert claim.consent_token.value == "CR1-ABCDEFGH"
    assert claim.guid is not None and claim.guid.value == "guid-1"
    assert claim.workflow_state == "DRAFT"
    assert claim.service_type is ServiceType.CAPITATION
    assert claim.total_amount == Money.kes("1500.50")
    assert claim.net_amount == Money.kes("1400.00")
    assert claim.invoice_number is None
    assert claim.visit_start is not None
    assert "unknown_future_field" in claim.extra
