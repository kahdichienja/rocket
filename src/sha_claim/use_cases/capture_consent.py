"""Step 1 of every claim: create an authorization, which sends the beneficiary an OTP."""

from __future__ import annotations

from collections.abc import Sequence

from sha_claim.domain.codes import InterventionCode
from sha_claim.domain.consent import Authorization, Otp
from sha_claim.domain.enums import ServiceType
from sha_claim.domain.identifiers import PatientId
from sha_claim.errors import RequestValidationError, Violation
from sha_claim.ports.consent_gateway import ConsentGateway


def require_interventions(interventions: Sequence[InterventionCode]) -> tuple[InterventionCode, ...]:
    unique = tuple(dict.fromkeys(interventions))
    if not unique:
        raise RequestValidationError(
            [Violation("interventions", "at least one intervention code is required")]
        )
    return unique


class CaptureConsent:
    def __init__(self, gateway: ConsentGateway) -> None:
        self._gateway = gateway

    async def execute(
        self,
        patient: PatientId,
        service_type: ServiceType,
        interventions: Sequence[InterventionCode],
        otp: Otp | None = None,
    ) -> Authorization:
        return await self._gateway.authorize(patient, service_type, require_interventions(interventions), otp)
