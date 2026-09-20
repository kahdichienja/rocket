import asyncio

import httpx
import pytest
import respx

from sha_claim import AsyncSHAClient, FacilityCode, facility_scope
from sha_claim.settings import SHASettings


@respx.mock
async def test_no_headers_by_default(settings: SHASettings) -> None:
    respx.post(f"{settings.api_root}/tenants/token").mock(
        return_value=httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
    )
    route = respx.get(f"{settings.api_root}/patients/benefits").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    async with AsyncSHAClient(settings) as sha:
        await sha.eligibility.benefits("CR1")
    assert "x-facility-id" not in route.calls[0].request.headers


@respx.mock
async def test_scope_sends_both_headers_and_is_per_task(settings: SHASettings) -> None:
    respx.post(f"{settings.api_root}/tenants/token").mock(
        return_value=httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
    )
    route = respx.get(f"{settings.api_root}/patients/benefits").mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    async def call(facility: str | None) -> None:
        if facility is None:
            await sha.eligibility.benefits("CR1")
        else:
            with facility_scope(facility):
                await asyncio.sleep(0)  # yield so tasks interleave
                await sha.eligibility.benefits("CR1")

    async with AsyncSHAClient(settings) as sha:
        await asyncio.gather(call("FID-47-115307-8"), call(None), call("FID-1-2-3"))

    seen = sorted(
        (c.request.headers.get("x-facility-id", ""), c.request.headers.get("x-facility-id-type", ""))
        for c in route.calls
    )
    assert seen == [("", ""), ("FID-1-2-3", "fr-code"), ("FID-47-115307-8", "fr-code")]


@respx.mock
async def test_static_default_from_settings_and_scope_overrides_it() -> None:
    settings = SHASettings(
        client_id="c", client_secret="s", base_url="https://uat.example/uat-middleware", facility="FID-9-9-9"
    )
    respx.post(f"{settings.api_root}/tenants/token").mock(
        return_value=httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
    )
    route = respx.get(f"{settings.api_root}/patients/benefits").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    async with AsyncSHAClient(settings) as sha:
        await sha.eligibility.benefits("CR1")
        with facility_scope(FacilityCode("FID-1-1-1")):
            await sha.eligibility.benefits("CR1")
    assert [c.request.headers["x-facility-id"] for c in route.calls] == ["FID-9-9-9", "FID-1-1-1"]


def test_settings_from_env_reads_facility() -> None:
    s = SHASettings.from_env({"SHA_CLIENT_ID": "a", "SHA_CLIENT_SECRET": "b", "SHA_FACILITY_ID": "FID-1-2-3"})
    assert s.facility == "FID-1-2-3" and s.facility_id_type == "fr-code"


def test_empty_id_type_rejected() -> None:
    with pytest.raises(ValueError, match="id_type"), facility_scope("FID-1-2-3", id_type=" "):
        pass


def test_activate_and_clear() -> None:
    from sha_claim import activate_facility, clear_facility, current_facility

    assert current_facility() is None
    scope = activate_facility("fid-1-2-3")
    assert current_facility() == scope and scope.facility.value == "fid-1-2-3"
    clear_facility()
    assert current_facility() is None
