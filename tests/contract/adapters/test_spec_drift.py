"""Every request the SDK builds must still exist in the published spec with the same required inputs."""

from typing import Any

import pytest

from tests.conftest import load_spec

# (method, path, required query params, required body fields) — extend as gateways are added.
SDK_REQUESTS: list[tuple[str, str, set[str], set[str]]] = [
    ("get", "/api/v1/patients/eligibility", {"identification_number", "identification_type"}, set()),
    ("get", "/api/v1/patients/benefits", {"patient_id"}, set()),
    ("get", "/api/v1/patients/sub-benefits", {"patient_id"}, set()),
    ("get", "/api/v1/patients/benefits/interventions", {"patient_id", "sub_benefit_code"}, set()),
    # `otp` is documented as required but UAT accepts its absence (creates a PENDING authorization) — WORKFLOWS §9.
    ("post", "/api/v1/claims/authorize", set(), {"patient_id", "service_type", "interventions", "otp"}),
    ("get", "/api/v1/claims/authorizations", {"token", "guid"}, set()),
    ("post", "/api/v1/claims/authorizations/{consent_token}/reject", set(), set()),
    ("post", "/api/v1/claims/visit", set(), {"patient_id", "service_type", "intervention_codes", "otp"}),
    ("post", "/api/v1/claims/interventions", set(), {"consent_token", "intervention_code"}),
    ("post", "/api/v1/claims/interventions/retire", set(), {"consent_token", "intervention_code"}),
    ("post", "/api/v1/claims/interventions/restore", set(), {"consent_token", "intervention_code"}),
    ("post", "/api/v1/claims/diagnoses", set(), {"consent_token", "icd_code", "intervention_code"}),
    ("patch", "/api/v1/claims/diagnoses", set(), {"consent_token", "icd_code", "intervention_code"}),
    ("post", "/api/v1/claims/lines", set(), {"consent_token", "intervention_code", "unit_price", "quantity"}),
    ("patch", "/api/v1/claims/lines", set(), {"consent_token", "line_guid"}),
    ("patch", "/api/v1/claims/lines/edit", set(), {"line_id"}),
    (
        "post",
        "/api/v1/claims/attachments",
        set(),
        {"consent_token", "file_blob", "document_type", "intervention_code"},
    ),
    ("patch", "/api/v1/claims/attachments", set(), {"consent_token", "attachment_id", "intervention_code"}),
    ("post", "/api/v1/claims/preview", set(), {"consent_token"}),
    ("post", "/api/v1/claims/submit", set(), {"consent_token"}),
    ("post", "/api/v1/claims/close", set(), {"consent_token", "cancel_reason_type", "cancel_reason_text"}),
    ("get", "/api/v1/claims/preview/payer", {"guid", "provider_claim_no"}, set()),
    ("get", "/api/v1/preauths", {"consent_token"}, set()),
    (
        "post",
        "/api/v1/preauths",
        set(),
        {
            "consent_token",
            "intervention_code",
            "service_start",
            "service_end",
            "items",
            "diagnoses",
            "doctors",
            "attachments",
            "provider_notification_email",
        },
    ),
    (
        "delete",
        "/api/v1/preauths/diagnoses/{icd_code}",
        set(),
        {"consent_token", "icd_code", "intervention_code"},
    ),
    (
        "delete",
        "/api/v1/preauths/doctors",
        set(),
        {"consent_token", "intervention_code", "practitioner_registration_number"},
    ),
    ("post", "/api/v1/preauths/cancel", set(), {"consent_token", "intervention_code"}),
    ("post", "/api/v1/claims/doctor-consent", set(), {"intervention_code", "request_type"}),
]


def _endpoints(api: str) -> dict[tuple[str, str], Any]:
    return {(e["method"], e["path"]): e for tg in load_spec(api)["tagGroups"] for e in tg["endpoints"]}


@pytest.mark.parametrize(("method", "path", "query", "body"), SDK_REQUESTS)
def test_request_matches_published_spec(method: str, path: str, query: set[str], body: set[str]) -> None:
    endpoint = _endpoints("eclaims").get((method, path))
    assert endpoint is not None, f"{method.upper()} {path} no longer in spec"
    required_query = {p["name"] for p in endpoint["parameters"] if p.get("in") == "query" and p["required"]}
    assert required_query <= query, f"spec now requires {required_query - query}"
    rb = endpoint.get("requestBody") or {}
    required_body = {p["name"] for p in rb.get("properties") or [] if p["required"]}
    assert required_body <= body, f"spec now requires body fields {required_body - body}"


def test_auth_token_endpoint_unchanged() -> None:
    token = _endpoints("auth")[("post", "/tenants/token")]
    assert token["requestBody"]["contentType"] == "application/x-www-form-urlencoded"
    assert {p["name"] for p in token["requestBody"]["properties"]} == {"client_id", "client_secret"}
