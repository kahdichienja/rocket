"""Every request the SDK builds must still exist in the published spec with the same required inputs."""

from typing import Any

import pytest

from tests.conftest import load_spec

# (method, path, required query params, required body fields) — extend as gateways are added.
SDK_REQUESTS: list[tuple[str, str, set[str], set[str]]] = [
    ("get", "/api/v1/patients/eligibility", {"identification_number", "identification_type"}, set()),
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
