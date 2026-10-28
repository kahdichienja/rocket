from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from sha_claim.domain.codes import InterventionCode
from sha_claim.domain.consent import Authorization, BiometricContext, Otp, OtpWhitelistRequest
from sha_claim.domain.enums import ServiceType
from sha_claim.domain.identifiers import PatientId


class ConsentGateway(Protocol):
    async def authorize(
        self,
        patient: PatientId,
        service_type: ServiceType,
        interventions: Sequence[InterventionCode],
        otp: Otp | None,
        biometrics: BiometricContext | None = None,
    ) -> Authorization: ...

    async def get(self, token: str, guid: str, beneficiary: PatientId | None) -> Authorization | None: ...

    async def reject(self, token: str) -> None: ...

    async def send_otp(self, patient: PatientId, interventions: Sequence[InterventionCode]) -> str: ...

    async def list(self, beneficiary: PatientId) -> tuple[Authorization, ...]: ...

    async def create_otp_whitelist(self, request: OtpWhitelistRequest) -> Mapping[str, Any]: ...

    async def get_otp_whitelist(self, beneficiary: PatientId, facility_fr_code: str) -> Mapping[str, Any]: ...
