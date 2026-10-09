"""Registering the HIE's push channel, through the facade.

Two things here are worth a real HTTP round trip rather than a unit test: DHA returns these listings as
a **bare JSON array** where the rest of the API uses the `{results: […]}` envelope, and an endpoint
registered without an operation delivers nothing while looking perfectly healthy.
"""

import httpx
import respx

from sha_claim import (
    AsyncSHAClient,
    CallbackEntityType,
    CallbackEnvironment,
    NewCallbackEndpoint,
    NewCallbackOperation,
)
from sha_claim.settings import SHASettings

TENANT = "FID-47-105963-0"

ENDPOINT_JSON = {
    "endpoint_id": "ep-1",
    "name": "NaCare claim status",
    "base_url": "https://serviceapi.example.com/api/v1/sha/callbacks",
    "entity_type": "claim",
    "environment": "production",
    "auth_type": "none",
    "is_active": True,
}
OPERATION_JSON = {
    "operation_id": "op-1",
    "name": "claim status changed",
    "action": "status_changed",
    "method": "POST",
    "path": "/claim-status",
    "is_active": True,
}


def _token(settings: SHASettings) -> None:
    respx.post(f"{settings.api_root}/tenants/token").mock(
        return_value=httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
    )


@respx.mock
async def test_listing_reads_a_bare_array(settings: SHASettings) -> None:
    _token(settings)
    respx.get(f"{settings.api_root}/tenants/{TENANT}/endpoints").mock(
        return_value=httpx.Response(200, json=[ENDPOINT_JSON])
    )
    async with AsyncSHAClient(settings) as sha:
        found = await sha.callbacks.endpoints(TENANT)
    assert len(found) == 1
    assert found[0].endpoint_id == "ep-1"
    assert found[0].entity_type is CallbackEntityType.CLAIM
    assert found[0].environment is CallbackEnvironment.PRODUCTION


@respx.mock
async def test_listing_also_reads_the_results_envelope(settings: SHASettings) -> None:
    """Tolerated because a middleware that changed shape once can change it back."""
    _token(settings)
    respx.get(f"{settings.api_root}/tenants/{TENANT}/endpoints").mock(
        return_value=httpx.Response(200, json={"results": [ENDPOINT_JSON]})
    )
    async with AsyncSHAClient(settings) as sha:
        found = await sha.callbacks.endpoints(TENANT)
    assert [e.endpoint_id for e in found] == ["ep-1"]


@respx.mock
async def test_register_attaches_the_operation_that_makes_delivery_happen(
    settings: SHASettings,
) -> None:
    _token(settings)
    created = respx.post(f"{settings.api_root}/tenants/{TENANT}/endpoints").mock(
        return_value=httpx.Response(201, json=ENDPOINT_JSON)
    )
    attached = respx.post(f"{settings.api_root}/tenants/{TENANT}/endpoints/ep-1/operations").mock(
        return_value=httpx.Response(201, json=OPERATION_JSON)
    )

    async with AsyncSHAClient(settings) as sha:
        endpoint, operation = await sha.callbacks.register(
            TENANT,
            NewCallbackEndpoint(
                name="NaCare claim status",
                base_url="https://serviceapi.example.com/api/v1/sha/callbacks",
                entity_type=CallbackEntityType.CLAIM,
                environment=CallbackEnvironment.PRODUCTION,
            ),
            NewCallbackOperation(name="claim status changed", path="/claim-status"),
        )

    assert created.called and attached.called
    assert endpoint.endpoint_id == "ep-1"
    assert operation is not None and operation.operation_id == "op-1"
    assert operation.action == "status_changed"


@respx.mock
async def test_register_without_an_operation_registers_only_the_endpoint(
    settings: SHASettings,
) -> None:
    """Allowed, but it is the configuration that silently receives nothing — hence the explicit None."""
    _token(settings)
    respx.post(f"{settings.api_root}/tenants/{TENANT}/endpoints").mock(
        return_value=httpx.Response(201, json=ENDPOINT_JSON)
    )
    operations = respx.post(f"{settings.api_root}/tenants/{TENANT}/endpoints/ep-1/operations")

    async with AsyncSHAClient(settings) as sha:
        _, operation = await sha.callbacks.register(
            TENANT,
            NewCallbackEndpoint(
                name="NaCare claim status",
                base_url="https://serviceapi.example.com/api/v1/sha/callbacks",
                entity_type=CallbackEntityType.CLAIM,
                environment=CallbackEnvironment.SANDBOX,
            ),
        )
    assert operation is None
    assert not operations.called


@respx.mock
async def test_pause_is_a_patch_that_keeps_the_registration(settings: SHASettings) -> None:
    _token(settings)
    paused = respx.patch(f"{settings.api_root}/tenants/endpoints/ep-1").mock(
        return_value=httpx.Response(200, json={**ENDPOINT_JSON, "is_active": False})
    )
    async with AsyncSHAClient(settings) as sha:
        endpoint = await sha.callbacks.pause_endpoint("ep-1")
    assert paused.called
    assert endpoint.is_active is False


@respx.mock
async def test_reading_one_operation_sees_a_paused_one(settings: SHASettings) -> None:
    """Listings omit paused operations, so this is the only way to tell paused from absent."""
    _token(settings)
    respx.get(f"{settings.api_root}/tenants/endpoints/operations/op-1").mock(
        return_value=httpx.Response(200, json={**OPERATION_JSON, "is_active": False})
    )
    async with AsyncSHAClient(settings) as sha:
        operation = await sha.callbacks.operation("op-1")
    assert operation.is_active is False
