"""Every response schema the SDK owns must accept the portal's own example for that endpoint."""

from typing import Any

import pytest
from pydantic import BaseModel

from sha_claim.adapters.wire import mappers
from sha_claim.adapters.wire.schemas.authorization import AuthorizationWire
from sha_claim.adapters.wire.schemas.benefits import BenefitPackageWire, InterventionWire, SubBenefitWire
from sha_claim.adapters.wire.schemas.claim import (
    ClaimAttachmentWire,
    ClaimDiagnosisWire,
    ClaimInterventionWire,
    ClaimLineWire,
    MessageWire,
    PayerClaimWire,
    VirtualClaimWire,
)
from sha_claim.adapters.wire.schemas.common import Page
from sha_claim.adapters.wire.schemas.eligibility import EligibilityWire
from sha_claim.adapters.wire.schemas.preauth import DoctorConsentWire, PreauthorizationWire
from tests.conftest import load_examples

# endpoint → (wire model, mapper or None). Page[...] models are unwrapped via `.results`.
CASES: dict[str, tuple[type[BaseModel], Any]] = {
    "GET /api/v1/patients/eligibility": (EligibilityWire, mappers.to_eligibility),
    "GET /api/v1/patients/benefits": (Page[BenefitPackageWire], mappers.to_benefit_package),
    "GET /api/v1/patients/sub-benefits": (Page[SubBenefitWire], mappers.to_sub_benefit),
    "GET /api/v1/patients/benefits/interventions": (Page[InterventionWire], mappers.to_intervention_coverage),
    "POST /api/v1/claims/authorize": (AuthorizationWire, mappers.to_authorization),
    "GET /api/v1/claims/authorizations": (AuthorizationWire, mappers.to_authorization),
    "POST /api/v1/claims/visit": (VirtualClaimWire, mappers.to_virtual_claim),
    "POST /api/v1/claims/preview": (VirtualClaimWire, mappers.to_virtual_claim),
    "POST /api/v1/claims/submit": (VirtualClaimWire, mappers.to_virtual_claim),
    "POST /api/v1/claims/close": (VirtualClaimWire, mappers.to_virtual_claim),
    "POST /api/v1/claims/interventions": (ClaimInterventionWire, mappers.to_claim_intervention),
    "POST /api/v1/claims/interventions/retire": (MessageWire, None),
    "POST /api/v1/claims/interventions/restore": (MessageWire, None),
    "POST /api/v1/claims/diagnoses": (ClaimDiagnosisWire, mappers.to_claim_diagnosis),
    "PATCH /api/v1/claims/diagnoses": (MessageWire, None),
    "POST /api/v1/claims/lines": (ClaimLineWire, mappers.to_claim_line),
    "PATCH /api/v1/claims/lines": (MessageWire, None),
    "PATCH /api/v1/claims/lines/edit": (ClaimLineWire, mappers.to_claim_line),
    "POST /api/v1/claims/attachments": (ClaimAttachmentWire, mappers.to_claim_attachment),
    "PATCH /api/v1/claims/attachments": (MessageWire, None),
    "GET /api/v1/claims/preview/payer": (Page[PayerClaimWire], mappers.to_payer_record),
    "GET /api/v1/preauths": (PreauthorizationWire, mappers.to_preauthorization),
    "POST /api/v1/preauths/cancel": (PreauthorizationWire, mappers.to_preauthorization),
    "DELETE /api/v1/preauths/diagnoses/{icd_code}": (PreauthorizationWire, mappers.to_preauthorization),
    "POST /api/v1/claims/doctor-consent": (DoctorConsentWire, None),
}


@pytest.mark.parametrize("endpoint", sorted(CASES))
def test_schema_accepts_portal_example_and_maps(endpoint: str) -> None:
    example = load_examples()["eclaims"][endpoint]["responses"].get("200")
    if example is None:
        pytest.skip("portal publishes no 200 example")
    model, mapper = CASES[endpoint]
    parsed = model.model_validate(example)
    if mapper is None:
        return
    items = parsed.results if isinstance(parsed, Page) else [parsed]
    for item in items:
        mapper(item)  # must not raise — placeholder strings and zeros are tolerated


def test_every_implemented_endpoint_is_covered_here() -> None:
    """Keep this table in step with the spec-drift table: same endpoints, response side."""
    from tests.contract.adapters.test_spec_drift import SDK_REQUESTS

    implemented = {f"{m.upper()} {p}" for m, p, _, _ in SDK_REQUESTS}
    uncovered = (
        implemented
        - set(CASES)
        - {
            "POST /api/v1/claims/authorizations/{consent_token}/reject",  # `{message}` only, no schema
            "DELETE /api/v1/preauths/doctors",  # 200 with empty body
            "POST /api/v1/preauths",  # portal example echoes the request, not a Preauthorization
        }
    )
    assert uncovered == set(), f"add response-shape cases for: {sorted(uncovered)}"
