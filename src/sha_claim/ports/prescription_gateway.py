from __future__ import annotations

from typing import Protocol

from sha_claim.domain.codes import InterventionCode
from sha_claim.domain.identifiers import ConsentToken
from sha_claim.domain.prescription import Dispense, DispenseRequest, Prescription, PrescriptionRequest


class PrescriptionGateway(Protocol):
    async def create(self, token: ConsentToken, request: PrescriptionRequest) -> Prescription: ...

    async def get(self, token: ConsentToken) -> Prescription | None: ...

    async def dispense(self, token: ConsentToken, request: DispenseRequest) -> Dispense: ...

    async def remove_doctor(
        self, token: ConsentToken, intervention: InterventionCode, registration_number: str
    ) -> None: ...
