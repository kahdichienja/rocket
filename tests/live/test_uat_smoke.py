"""Hits the DHA UAT environment. Run with: RUN_LIVE=1 pytest -m live"""

import os
from datetime import date

import pytest

from sha_claim import AsyncSHAClient, BadRequestError, IdentificationType

pytestmark = [pytest.mark.live, pytest.mark.skipif(not os.getenv("RUN_LIVE"), reason="set RUN_LIVE=1")]


@pytest.fixture(autouse=True)
def _load_dotenv() -> None:
    from dotenv import load_dotenv

    load_dotenv()


async def test_eligibility_synthetic_member() -> None:
    async with AsyncSHAClient.from_env() as sha:
        e = await sha.eligibility.check("00000000", IdentificationType.NATIONAL_ID)
    assert e.member_found
    assert e.is_covered_on(date.today())


async def test_server_validation_error_is_typed() -> None:
    """Bypass local validation on purpose: we want the *server's* 400 envelope translated."""
    from sha_claim.adapters.wire.error_translator import raise_for_status
    from sha_claim.adapters.wire.transport import WireRequest

    async with AsyncSHAClient.from_env() as sha:
        response = await sha._transport.send(
            WireRequest(
                "GET",
                "/patients/eligibility",
                params={"identification_number": "1", "identification_type": "garbage"},
            )
        )
        with pytest.raises(BadRequestError) as exc:
            raise_for_status(response)
    assert exc.value.trace_id
    assert "identification type" in str(exc.value)
