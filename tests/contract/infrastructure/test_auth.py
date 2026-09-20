import asyncio

import httpx
import pytest
import respx

from sha_claim.errors import AuthenticationError, TransportError
from sha_claim.infrastructure.auth import OAuth2ClientCredentials

TOKEN_URL = "https://uat.example/uat-middleware/api/v1/tenants/token"


class FakeClock:
    def __init__(self) -> None:
        self.t = 1000.0

    def monotonic(self) -> float:
        return self.t

    def now(self):  # type: ignore[no-untyped-def]
        raise NotImplementedError


def provider(http: httpx.AsyncClient, clock: FakeClock, skew: int = 60) -> OAuth2ClientCredentials:
    return OAuth2ClientCredentials(
        token_url=TOKEN_URL,
        client_id="cid",
        client_secret="sec",
        http=http,
        clock=clock,
        expiry_skew_seconds=skew,
    )


@respx.mock
async def test_fetches_form_encoded_and_caches_until_expiry_minus_skew() -> None:
    route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(
            200, json={"access_token": "T1", "expires_in": 3600, "token_type": "Bearer"}
        )
    )
    clock = FakeClock()
    async with httpx.AsyncClient() as http:
        p = provider(http, clock)
        assert await p.access_token() == "T1"
        assert await p.access_token() == "T1"
        assert route.call_count == 1
        sent = route.calls[0].request
        assert sent.headers["content-type"] == "application/x-www-form-urlencoded"
        assert b"client_id=cid" in sent.content and b"client_secret=sec" in sent.content

        clock.t += 3600 - 60 - 1
        assert await p.access_token() == "T1" and route.call_count == 1
        clock.t += 2
        route.mock(return_value=httpx.Response(200, json={"access_token": "T2", "expires_in": 3600}))
        assert await p.access_token() == "T2" and route.call_count == 2


@respx.mock
async def test_concurrent_callers_share_one_refresh() -> None:
    route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json={"access_token": "T", "expires_in": 60})
    )
    async with httpx.AsyncClient() as http:
        p = provider(http, FakeClock())
        tokens = await asyncio.gather(*(p.access_token() for _ in range(20)))
    assert set(tokens) == {"T"} and route.call_count == 1


@respx.mock
async def test_invalidate_forces_refetch() -> None:
    route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json={"access_token": "T", "expires_in": 60})
    )
    async with httpx.AsyncClient() as http:
        p = provider(http, FakeClock())
        await p.access_token()
        await p.invalidate()
        await p.access_token()
    assert route.call_count == 2


@respx.mock
async def test_bad_credentials_raise_authentication_error_with_server_message() -> None:
    respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(401, json={"error": "Unauthorized", "message": "invalid client"})
    )
    async with httpx.AsyncClient() as http:
        with pytest.raises(AuthenticationError, match="invalid client"):
            await provider(http, FakeClock()).access_token()


@respx.mock
async def test_malformed_token_payload_is_an_auth_error() -> None:
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json={"token_type": "Bearer"}))
    async with httpx.AsyncClient() as http:
        with pytest.raises(AuthenticationError, match="missing"):
            await provider(http, FakeClock()).access_token()


@respx.mock
async def test_network_failure_is_transport_error() -> None:
    respx.post(TOKEN_URL).mock(side_effect=httpx.ConnectError("down"))
    async with httpx.AsyncClient() as http:
        with pytest.raises(TransportError):
            await provider(http, FakeClock()).access_token()
