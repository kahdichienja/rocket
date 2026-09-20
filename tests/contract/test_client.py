import httpx
import respx

from sha_claim import AsyncSHAClient, IdentificationType
from sha_claim.settings import SHASettings
from tests.conftest import load_fixture


@respx.mock
async def test_end_to_end_eligibility_through_facade(settings: SHASettings) -> None:
    respx.post(f"{settings.api_root}/tenants/token").mock(
        return_value=httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
    )
    respx.get(f"{settings.api_root}/patients/eligibility").mock(
        return_value=httpx.Response(200, json=load_fixture("eligibility_member_found.json"))
    )

    async with AsyncSHAClient(settings) as sha:
        e = await sha.eligibility.check("00000000", IdentificationType.NATIONAL_ID)
    assert e.member_found and e.schemes[0].name == "UHC"
