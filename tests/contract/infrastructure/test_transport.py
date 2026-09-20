import httpx
import pytest
import respx

from sha_claim.adapters.wire.transport import WireRequest
from sha_claim.errors import TransportError
from sha_claim.infrastructure.retry import RetryPolicy
from sha_claim.infrastructure.transport import HttpxTransport
from sha_claim.settings import Timeouts

ROOT = "https://uat.example/uat-middleware/api/v1"


class FakeTokens:
    def __init__(self) -> None:
        self.tokens = ["T1", "T2", "T3"]
        self.invalidated = 0

    async def access_token(self) -> str:
        return self.tokens[min(self.invalidated, len(self.tokens) - 1)]

    async def invalidate(self) -> None:
        self.invalidated += 1


class Sleeps:
    def __init__(self) -> None:
        self.calls: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


def transport(
    http: httpx.AsyncClient, tokens: FakeTokens, sleeps: Sleeps, attempts: int = 3
) -> HttpxTransport:
    return HttpxTransport(
        http=http,
        api_root=ROOT,
        tokens=tokens,
        timeouts=Timeouts(),
        retry=RetryPolicy(max_attempts=attempts),
        sleep=sleeps,
    )


@respx.mock
async def test_injects_bearer_and_query_params() -> None:
    route = respx.get(f"{ROOT}/patients/eligibility").mock(
        return_value=httpx.Response(200, json={"ok": 1}, headers={"x-request-id": "req-1"})
    )
    async with httpx.AsyncClient() as http:
        r = await transport(http, FakeTokens(), Sleeps()).send(
            WireRequest("GET", "/patients/eligibility", params={"a": "b"})
        )
    assert r.status == 200 and r.json() == {"ok": 1} and r.request_id == "req-1"
    assert route.calls[0].request.headers["authorization"] == "Bearer T1"
    assert route.calls[0].request.url.params["a"] == "b"


@respx.mock
async def test_401_refreshes_token_once_and_replays() -> None:
    route = respx.get(f"{ROOT}/x").mock(
        side_effect=[
            httpx.Response(401, json={"error": "Unauthorized", "message": "expired"}),
            httpx.Response(200, json={}),
        ]
    )
    tokens = FakeTokens()
    async with httpx.AsyncClient() as http:
        r = await transport(http, tokens, Sleeps()).send(WireRequest("GET", "/x"))
    assert r.status == 200 and tokens.invalidated == 1
    assert [c.request.headers["authorization"] for c in route.calls] == ["Bearer T1", "Bearer T2"]


@respx.mock
async def test_second_401_is_returned_not_looped() -> None:
    route = respx.get(f"{ROOT}/x").mock(return_value=httpx.Response(401, json={}))
    async with httpx.AsyncClient() as http:
        r = await transport(http, FakeTokens(), Sleeps()).send(WireRequest("GET", "/x"))
    assert r.status == 401 and route.call_count == 2


@respx.mock
async def test_get_retries_transient_status_with_backoff_then_succeeds() -> None:
    route = respx.get(f"{ROOT}/x").mock(
        side_effect=[httpx.Response(503), httpx.Response(502), httpx.Response(200, json={})]
    )
    sleeps = Sleeps()
    async with httpx.AsyncClient() as http:
        r = await transport(http, FakeTokens(), sleeps).send(WireRequest("GET", "/x"))
    assert r.status == 200 and route.call_count == 3 and len(sleeps.calls) == 2
    assert all(0 <= s <= 8 for s in sleeps.calls)


@respx.mock
async def test_get_returns_last_transient_response_when_budget_exhausted() -> None:
    respx.get(f"{ROOT}/x").mock(return_value=httpx.Response(503))
    async with httpx.AsyncClient() as http:
        r = await transport(http, FakeTokens(), Sleeps(), attempts=2).send(WireRequest("GET", "/x"))
    assert r.status == 503


@respx.mock
async def test_post_is_never_retried() -> None:
    route = respx.post(f"{ROOT}/claims/submit").mock(return_value=httpx.Response(503))
    sleeps = Sleeps()
    async with httpx.AsyncClient() as http:
        r = await transport(http, FakeTokens(), sleeps).send(
            WireRequest("POST", "/claims/submit", json={"a": 1})
        )
    assert r.status == 503 and route.call_count == 1 and sleeps.calls == []


@respx.mock
async def test_post_timeout_surfaces_as_transport_error_without_retry() -> None:
    route = respx.post(f"{ROOT}/claims/submit").mock(side_effect=httpx.ReadTimeout("slow"))
    async with httpx.AsyncClient() as http:
        with pytest.raises(TransportError, match="timeout"):
            await transport(http, FakeTokens(), Sleeps()).send(WireRequest("POST", "/claims/submit"))
    assert route.call_count == 1


@respx.mock
async def test_get_network_error_retried_then_raised() -> None:
    route = respx.get(f"{ROOT}/x").mock(side_effect=httpx.ConnectError("down"))
    async with httpx.AsyncClient() as http:
        with pytest.raises(TransportError, match="network"):
            await transport(http, FakeTokens(), Sleeps()).send(WireRequest("GET", "/x"))
    assert route.call_count == 3


@respx.mock
async def test_multipart_and_unauthenticated_requests() -> None:
    route = respx.post(f"{ROOT}/uploads").mock(return_value=httpx.Response(200, json={}))
    async with httpx.AsyncClient() as http:
        await transport(http, FakeTokens(), Sleeps()).send(
            WireRequest(
                "POST",
                "/uploads",
                form={"consent_token": "c"},
                files={"file": ("a.pdf", b"%PDF", "application/pdf")},
                authenticated=False,
            )
        )
    req = route.calls[0].request
    assert "authorization" not in req.headers
    assert req.headers["content-type"].startswith("multipart/form-data")
    assert b'name="consent_token"' in req.content and b"%PDF" in req.content
