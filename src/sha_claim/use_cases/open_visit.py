"""Step 2: turn a consented authorization into a virtual claim. Consumes the OTP."""

from __future__ import annotations

from collections.abc import Sequence

from sha_claim.domain.claim import VirtualClaim
from sha_claim.domain.codes import InterventionCode
from sha_claim.domain.consent import ConsentProof
from sha_claim.domain.enums import ServiceType
from sha_claim.domain.identifiers import PatientId
from sha_claim.ports.virtual_claim_gateway import VisitOpener
from sha_claim.use_cases.capture_consent import require_interventions


class OpenVisit:
    def __init__(self, gateway: VisitOpener) -> None:
        self._gateway = gateway

    async def execute(
        self,
        patient: PatientId,
        service_type: ServiceType,
        interventions: Sequence[InterventionCode],
        proof: ConsentProof,
    ) -> VirtualClaim:
        return await self._gateway.open_visit(
            patient, service_type, require_interventions(interventions), proof
        )
