"""Port implementations over the wire Transport. One class per port role."""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from sha_claim.adapters.wire import mappers
from sha_claim.adapters.wire.error_translator import raise_for_status
from sha_claim.adapters.wire.schemas.eligibility import EligibilityWire
from sha_claim.adapters.wire.transport import Transport, WireRequest, WireResponse
from sha_claim.domain.eligibility import Eligibility
from sha_claim.domain.enums import IdentificationType
from sha_claim.errors import UnexpectedResponseError

M = TypeVar("M", bound=BaseModel)


def parse_as(model: type[M], response: WireResponse) -> M:
    raise_for_status(response)
    try:
        payload: Any = response.json()
        return model.model_validate(payload)
    except (ValueError, ValidationError) as exc:
        raise UnexpectedResponseError(f"{model.__name__}: {exc}") from exc


class HttpEligibilityGateway:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def check(self, identification_number: str, identification_type: IdentificationType) -> Eligibility:
        response = await self._transport.send(
            WireRequest(
                "GET",
                "/patients/eligibility",
                params={
                    "identification_number": identification_number,
                    "identification_type": identification_type.value,
                },
            )
        )
        return mappers.to_eligibility(parse_as(EligibilityWire, response))
