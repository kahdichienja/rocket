from __future__ import annotations

from typing import Protocol

from sha_claim.domain.codes import Icd11Code, InterventionCode
from sha_claim.domain.identifiers import ConsentToken
from sha_claim.domain.preauth import DoctorConsentRequest, Preauthorization, PreauthRequest


class PreauthGateway(Protocol):
    async def create(self, token: ConsentToken, request: PreauthRequest) -> Preauthorization: ...

    async def list(self, token: ConsentToken) -> tuple[Preauthorization, ...]: ...

    async def remove_diagnosis(
        self, token: ConsentToken, icd: Icd11Code, intervention: InterventionCode
    ) -> Preauthorization: ...

    async def remove_doctor(
        self, token: ConsentToken, intervention: InterventionCode, registration_number: str
    ) -> None: ...

    async def cancel(self, token: ConsentToken, intervention: InterventionCode) -> Preauthorization: ...

    async def request_doctor_consent(self, token: ConsentToken, request: DoctorConsentRequest) -> str: ...
