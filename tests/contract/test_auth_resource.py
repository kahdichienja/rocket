import base64
import json
from datetime import UTC, datetime

import httpx
import pytest
import respx

from sha_claim import AsyncSHAClient, AuthenticationError
from sha_claim.settings import SHASettings


def jwt(claims: dict) -> str:  # type: ignore[type-arg]
    body = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"eyJhbGciOiJSUzI1NiJ9.{body}.sig"


@respx.mock
async def test_identity_is_read_from_the_token_without_exposing_it(settings: SHASettings) -> None:
    now = int(datetime.now(UTC).timestamp())
    token = jwt(
        {
            "iss": "https://accounts-uat.dha.go.ke/realms/hie",
            "tenant_id": "t1",
            "tenant_name": "Tenant",
            "facility_id": "FID-47-105963-0",
            "facility_id_type": "fr-code",
            "client_id": "cid",
            "iat": now,
            "exp": now + 3600,
        }
    )
    route = respx.post(f"{settings.api_root}/tenants/token").mock(
        return_value=httpx.Response(200, json={"access_token": token, "expires_in": 3600})
    )
    async with AsyncSHAClient(settings) as sha:
        assert await sha.auth.check() is True
        who = await sha.auth.identity()
    assert who.facility is not None and who.facility.value == "FID-47-105963-0"
    assert who.tenant_id == "t1" and who.issuer.endswith("/realms/hie") and who.client_id == "cid"
    assert who.seconds_remaining is not None and 3500 < who.seconds_remaining <= 3600
    assert token not in repr(who)
    assert route.call_count == 1  # identity() reused the cached token


@respx.mock
async def test_identity_tolerates_an_opaque_token(settings: SHASettings) -> None:
    respx.post(f"{settings.api_root}/tenants/token").mock(
        return_value=httpx.Response(200, json={"access_token": "opaque-not-a-jwt", "expires_in": 60})
    )
    async with AsyncSHAClient(settings) as sha:
        who = await sha.auth.identity()
    assert who.facility is None and who.expires_at is None and who.seconds_remaining is None


@respx.mock
async def test_check_raises_on_bad_credentials(settings: SHASettings) -> None:
    respx.post(f"{settings.api_root}/tenants/token").mock(
        return_value=httpx.Response(401, json={"error": "Unauthorized", "message": "invalid client"})
    )
    async with AsyncSHAClient(settings) as sha:
        with pytest.raises(AuthenticationError, match="invalid client"):
            await sha.auth.check()
