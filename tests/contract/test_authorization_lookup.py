"""`consent.get` must answer about the authorization it was asked about.

`GET /claims/authorizations` returns a **list**, and its server-side filters cannot be trusted: the
neighbouring `list()` is documented from UAT as receiving the whole facility's authorizations whatever
`beneficiary_code` says, and `test_consent_client_filters_out_other_beneficiaries` pins that on this very
endpoint. This lookup nevertheless read `records[0]`, on the strength of the `token`/`guid` filter it sent.

Where that filter is as loose as its neighbour, a beneficiary holding more than one authorization gets a
different row back — and an older `PENDING` one cannot be told apart from a capture the server is still
working on. A biometric discharge then waits for ever on a capture that has already succeeded, for some
patients and not others, depending only on how many authorization records the member happens to have.

Suspected in production 2026-10-29: the eKYC page showed "Biometrics are successfully captured" while the
claim panel stayed on PENDING, for some patients, on the same desk and the same day.
"""

from typing import Any

import httpx
import respx

from sha_claim import AsyncSHAClient
from sha_claim.settings import SHASettings
from tests.conftest import load_fixture

MINE = "2fee723d-419f-4a1c-882a-247db5ff2f5e"  # the guid in authorization_pending.json
THEIRS = "9d7c1a53-22be-4f80-ae16-7f5b3c90d412"


def _token(settings: SHASettings) -> None:
    respx.post(f"{settings.api_root}/tenants/token").mock(
        return_value=httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
    )


def _other(mine: dict[str, Any], **over: object) -> dict[str, Any]:
    """Another authorization for the same facility — the row DHA adds that we did not ask for."""
    return {**mine, "id": 99, "guid": THEIRS, "token": "OTHERTOKEN", "status": "PENDING", **over}


@respx.mock
async def test_the_requested_guid_is_picked_out_of_several(settings: SHASettings) -> None:
    """The regression. Ours is AUTHORIZED and listed second; theirs is PENDING and listed first."""
    _token(settings)
    mine = {**load_fixture("authorization_pending.json"), "status": "AUTHORIZED"}
    respx.get(f"{settings.api_root}/claims/authorizations").mock(
        return_value=httpx.Response(200, json=[_other(mine), mine])
    )

    async with AsyncSHAClient(settings) as sha:
        found = await sha.consent.get("TESTTOKEN0", MINE, "CR0000000000000-0")

    assert found is not None
    assert found.guid == MINE, "the lookup must answer about the authorization it asked for"
    assert found.is_verified, "reading the other row reports a verified capture as still pending"


@respx.mock
async def test_the_token_identifies_the_record_when_no_guid_is_held(settings: SHASettings) -> None:
    """`StartVisit.open` passes `consent_token or ""`, and the by-token route defaults `guid` to empty —
    so each half is sometimes the only one available."""
    _token(settings)
    mine = load_fixture("authorization_pending.json")
    respx.get(f"{settings.api_root}/claims/authorizations").mock(
        return_value=httpx.Response(200, json=[_other(mine), mine])
    )

    async with AsyncSHAClient(settings) as sha:
        found = await sha.consent.get("TESTTOKEN0", "", "CR0000000000000-0")

    assert found is not None and found.guid == MINE


@respx.mock
async def test_a_single_record_answer_is_unchanged(settings: SHASettings) -> None:
    """The ordinary case, and the one that works in production today. It must not move."""
    _token(settings)
    mine = load_fixture("authorization_pending.json")
    respx.get(f"{settings.api_root}/claims/authorizations").mock(
        return_value=httpx.Response(200, json=[mine])
    )

    async with AsyncSHAClient(settings) as sha:
        found = await sha.consent.get("TESTTOKEN0", MINE, "CR0000000000000-0")

    assert found is not None and found.guid == MINE


@respx.mock
async def test_a_bare_object_is_still_tolerated(settings: SHASettings) -> None:
    """The portal documents one object; UAT answers with a list. Both still work."""
    _token(settings)
    respx.get(f"{settings.api_root}/claims/authorizations").mock(
        return_value=httpx.Response(200, json=load_fixture("authorization_pending.json"))
    )

    async with AsyncSHAClient(settings) as sha:
        found = await sha.consent.get("TESTTOKEN0", MINE, "CR0000000000000-0")

    assert found is not None and found.guid == MINE


@respx.mock
async def test_nothing_matching_falls_back_to_the_first_record(settings: SHASettings) -> None:
    """Deliberate, and the reason this change cannot break the check-in path.

    Returning nothing here would assert that `guid` is always present and always spelled the same way on
    every row SHA returns. This function sits under the check-in consent flow, which works today, so a
    wrong guess would break a working path to fix a suspected one. The caller gets exactly what it got
    before, and NaCare reports when the fallback fires.
    """
    _token(settings)
    mine = load_fixture("authorization_pending.json")
    respx.get(f"{settings.api_root}/claims/authorizations").mock(
        return_value=httpx.Response(200, json=[_other(mine, guid="", token="")])
    )

    async with AsyncSHAClient(settings) as sha:
        found = await sha.consent.get("TESTTOKEN0", MINE, "CR0000000000000-0")

    assert found is not None, "an unidentifiable record is still an answer, as it was before"


@respx.mock
async def test_an_empty_answer_is_still_none(settings: SHASettings) -> None:
    _token(settings)
    respx.get(f"{settings.api_root}/claims/authorizations").mock(return_value=httpx.Response(200, json=[]))

    async with AsyncSHAClient(settings) as sha:
        assert await sha.consent.get("TESTTOKEN0", MINE, "CR0000000000000-0") is None


@respx.mock
async def test_a_guid_in_different_case_is_the_same_authorization(settings: SHASettings) -> None:
    """A UUID differing only in case is the same identifier; treating it as a stranger would be the bug
    this change is meant to prevent, inverted."""
    _token(settings)
    mine = load_fixture("authorization_pending.json")
    respx.get(f"{settings.api_root}/claims/authorizations").mock(
        return_value=httpx.Response(200, json=[_other(mine), {**mine, "guid": MINE.upper()}])
    )

    async with AsyncSHAClient(settings) as sha:
        found = await sha.consent.get("TESTTOKEN0", MINE, "CR0000000000000-0")

    assert found is not None and found.guid.casefold() == MINE
