"""Contract tests for SmartOAuth2TokenProvider and SmartTransport using respx."""

import httpx
import pytest
import respx

from smart_access.errors import (
    SmartAuthenticationError,
    SmartNotFoundError,
    SmartPermissionDeniedError,
)
from smart_access.infrastructure.auth import SmartOAuth2TokenProvider
from smart_access.infrastructure.transport import SmartTransport


@pytest.mark.asyncio
@respx.mock
async def test_oauth_token_acquisition_and_caching() -> None:
    token_route = respx.post("https://data.smartapplicationsgroup.com/providerapi-dev/oauth/token").respond(
        status_code=200,
        json={"access_token": "mocked-smart-token", "token_type": "bearer", "expires_in": 3600},
    )

    async with httpx.AsyncClient() as http:
        provider = SmartOAuth2TokenProvider(
            token_url="https://data.smartapplicationsgroup.com/providerapi-dev/oauth/token",
            provider_key="SKSP_6245",
            username="cashier1",
            password="secretpassword",
            client_id="client1",
            client_secret="clientsecret",
            http=http,
        )

        token1 = await provider.access_token()
        assert token1 == "mocked-smart-token"
        assert token_route.call_count == 1

        # Second call returns cached token without re-hitting network
        token2 = await provider.access_token()
        assert token2 == "mocked-smart-token"
        assert token_route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_oauth_token_failure() -> None:
    respx.post("https://data.smartapplicationsgroup.com/providerapi-dev/oauth/token").respond(
        status_code=401,
        text="Bad credentials",
    )

    async with httpx.AsyncClient() as http:
        provider = SmartOAuth2TokenProvider(
            token_url="https://data.smartapplicationsgroup.com/providerapi-dev/oauth/token",
            provider_key="SKSP_6245",
            username="bad_user",
            password="bad_password",
            http=http,
        )

        with pytest.raises(SmartAuthenticationError, match="Smart OAuth authentication failed"):
            await provider.access_token()


@pytest.mark.asyncio
@respx.mock
async def test_transport_401_refresh_and_replay() -> None:
    respx.post("https://data.smartapplicationsgroup.com/providerapi-dev/oauth/token").respond(
        status_code=200,
        json={"access_token": "token-1", "token_type": "bearer", "expires_in": 3600},
    )

    # First call returns 401, replay with token-2 succeeds
    api_route = respx.get("https://data.smartapplicationsgroup.com/providerapi-dev/api/visit")
    api_route.side_effect = [
        httpx.Response(401, json={"message": "Token expired"}),
        httpx.Response(200, json=[{"id": 1, "patient_number": "P1", "sessionStatus": "PENDING", "sp_id": 1}]),
    ]

    async with httpx.AsyncClient() as http:
        tokens = SmartOAuth2TokenProvider(
            token_url="https://data.smartapplicationsgroup.com/providerapi-dev/oauth/token",
            provider_key="SKSP_6245",
            username="cashier1",
            password="pwd",
            http=http,
        )

        transport = SmartTransport(
            base_url="https://data.smartapplicationsgroup.com/providerapi-dev",
            provider_key="SKSP_6245",
            tokens=tokens,
            http=http,
        )

        data = await transport.request("GET", "/api/visit")
        assert len(data) == 1
        assert data[0]["id"] == 1
        assert api_route.call_count == 2


@pytest.mark.asyncio
@respx.mock
async def test_transport_translates_http_errors() -> None:
    respx.post("https://data.smartapplicationsgroup.com/providerapi-dev/oauth/token").respond(
        status_code=200,
        json={"access_token": "token", "token_type": "bearer", "expires_in": 3600},
    )
    respx.get("https://data.smartapplicationsgroup.com/providerapi-dev/api/notfound").respond(
        status_code=404,
        json={"message": "Resource missing"},
    )
    respx.get("https://data.smartapplicationsgroup.com/providerapi-dev/api/forbidden").respond(
        status_code=403,
        json={"message": "Provider key unauthorized"},
    )

    async with httpx.AsyncClient() as http:
        tokens = SmartOAuth2TokenProvider(
            token_url="https://data.smartapplicationsgroup.com/providerapi-dev/oauth/token",
            provider_key="KEY",
            username="user",
            password="pwd",
            http=http,
        )
        transport = SmartTransport(
            base_url="https://data.smartapplicationsgroup.com/providerapi-dev",
            provider_key="KEY",
            tokens=tokens,
            http=http,
        )

        with pytest.raises(SmartNotFoundError, match="Resource missing"):
            await transport.request("GET", "/api/notfound")

        with pytest.raises(SmartPermissionDeniedError, match="Provider key unauthorized"):
            await transport.request("GET", "/api/forbidden")
