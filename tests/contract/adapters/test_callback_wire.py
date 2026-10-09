"""The status-callbacks management API, wire shape by wire shape.

DHA's page specifies these nine operations precisely and says nothing at all about the payload it
delivers — so this pins the half that is documented, and the three traps in it that each cost a day:
an endpoint registered without an operation, `prod` instead of `production`, and an auth type with no
secret reference.
"""

import pytest

from sha_claim.adapters.wire import requests
from sha_claim.domain.callbacks import (
    STATUS_CHANGED,
    CallbackAuthType,
    CallbackEndpointUpdate,
    CallbackEntityType,
    CallbackEnvironment,
    CallbackOperationUpdate,
    NewCallbackEndpoint,
    NewCallbackOperation,
)

TENANT = "FID-47-105963-0"
ENDPOINT = "ep-123"
OPERATION = "op-456"


def endpoint(**over) -> NewCallbackEndpoint:  # type: ignore[no-untyped-def]
    return NewCallbackEndpoint(
        **{
            "name": "NaCare claim status",
            "base_url": "https://serviceapi.example.com/api/v1/sha/callbacks",
            "entity_type": CallbackEntityType.CLAIM,
            "environment": CallbackEnvironment.PRODUCTION,
            **over,
        }
    )


def operation(**over) -> NewCallbackOperation:  # type: ignore[no-untyped-def]
    return NewCallbackOperation(**{"name": "claim status changed", "path": "/claim-status", **over})


# ── endpoints ──


def test_list_endpoints_filters_by_entity_type_only_when_given() -> None:
    assert requests.list_callback_endpoints(TENANT).params == {}
    r = requests.list_callback_endpoints(TENANT, "claim")
    assert r.method == "GET"
    assert r.path == f"/tenants/{TENANT}/endpoints"
    assert r.params == {"entity_type": "claim"}


def test_register_endpoint_sends_the_five_required_fields() -> None:
    r = requests.register_callback_endpoint(TENANT, endpoint())
    assert r.method == "POST"
    assert r.path == f"/tenants/{TENANT}/endpoints"
    assert r.json == {
        "name": "NaCare claim status",
        "base_url": "https://serviceapi.example.com/api/v1/sha/callbacks",
        "entity_type": "claim",
        "environment": "production",
        "auth_type": "none",
    }


def test_register_endpoint_omits_what_was_not_set() -> None:
    """An empty optional sent as `""` is not the same as absent; DHA has rejected both before."""
    body = requests.register_callback_endpoint(TENANT, endpoint()).json
    for absent in ("secret_ref", "facility_fr_code", "tenant_code", "timeout_ms", "headers"):
        assert absent not in body


def test_update_endpoint_is_a_patch_on_the_id_without_a_tenant() -> None:
    """DHA addresses an endpoint under a tenant to create it and without one afterwards."""
    r = requests.update_callback_endpoint(ENDPOINT, CallbackEndpointUpdate(is_active=False))
    assert r.method == "PATCH"
    assert r.path == f"/tenants/endpoints/{ENDPOINT}"
    assert r.json == {"is_active": False}


def test_delete_endpoint() -> None:
    r = requests.delete_callback_endpoint(ENDPOINT)
    assert r.method == "DELETE" and r.path == f"/tenants/endpoints/{ENDPOINT}"


# ── operations ──


def test_register_operation_defaults_to_status_changed_over_post() -> None:
    r = requests.register_callback_operation(TENANT, ENDPOINT, operation())
    assert r.method == "POST"
    assert r.path == f"/tenants/{TENANT}/endpoints/{ENDPOINT}/operations"
    assert r.json["action"] == STATUS_CHANGED
    assert r.json["method"] == "POST"
    assert r.json["path"] == "/claim-status"
    assert r.json["request_content_type"] == "application/json"


def test_operation_routes_drop_the_tenant_once_an_id_exists() -> None:
    assert requests.read_callback_operation(OPERATION).path == f"/tenants/endpoints/operations/{OPERATION}"
    assert requests.delete_callback_operation(OPERATION).method == "DELETE"
    r = requests.update_callback_operation(OPERATION, CallbackOperationUpdate(method="put"))
    assert r.method == "PATCH"
    assert r.json == {"method": "PUT"}  # normalised


def test_list_operations_can_narrow_to_one_action() -> None:
    assert requests.list_callback_operations(TENANT, ENDPOINT).params == {}
    assert requests.list_callback_operations(TENANT, ENDPOINT, STATUS_CHANGED).params == {
        "action": STATUS_CHANGED
    }


# ── the three traps ──


def test_an_unreachable_base_url_is_refused_before_it_is_registered() -> None:
    """Registering a relative or local URL succeeds and then never delivers."""
    with pytest.raises(ValueError, match="absolute"):
        endpoint(base_url="/api/v1/sha/callbacks")
    with pytest.raises(ValueError, match="absolute"):
        endpoint(base_url="serviceapi.example.com/hook")


def test_an_auth_type_without_a_secret_reference_is_refused() -> None:
    with pytest.raises(ValueError, match="secret_ref"):
        endpoint(auth_type=CallbackAuthType.API_KEY)
    # With one, it is fine — and the reference is what goes on the wire, never a credential.
    body = requests.register_callback_endpoint(
        TENANT, endpoint(auth_type=CallbackAuthType.API_KEY, secret_ref="hie-ref-1")
    ).json
    assert body["auth_type"] == "api_key" and body["secret_ref"] == "hie-ref-1"


def test_delete_is_refused_as_a_delivery_method() -> None:
    """DHA accepts it at registration and then fails every delivery with it."""
    with pytest.raises(ValueError, match="DELETE"):
        operation(method="DELETE")


def test_an_operation_needs_somewhere_to_deliver() -> None:
    with pytest.raises(ValueError, match="path"):
        NewCallbackOperation(name="nowhere")
    # An absolute override is the other way to satisfy it.
    body = requests.register_callback_operation(
        TENANT, ENDPOINT, operation(path="", path_url_override="https://elsewhere.example.com/hook")
    ).json
    assert body["path_url_override"] == "https://elsewhere.example.com/hook"
    assert "path" not in body


def test_prod_is_not_production() -> None:
    """DHA refuses `prod`. `LenientStrEnum` lets it through as unknown, so the value is checked here."""
    assert CallbackEnvironment("production").is_known
    assert not CallbackEnvironment("prod").is_known


# ── empty patches ──


def test_an_empty_patch_has_nothing_to_change() -> None:
    """DHA answers 400 for an empty body; `has_changes` is what lets the caller refuse first."""
    assert not CallbackEndpointUpdate().has_changes
    assert not CallbackOperationUpdate().has_changes
    assert CallbackEndpointUpdate(is_active=False).has_changes
    assert CallbackOperationUpdate(name="x").has_changes
