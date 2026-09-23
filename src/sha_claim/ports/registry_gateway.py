"""Port: the Client Registry — identity in, CR number and contactability out."""

from __future__ import annotations

from typing import Protocol

from sha_claim.domain.enums import IdentificationType
from sha_claim.domain.identifiers import PatientId
from sha_claim.domain.registry import PatientContact, PatientRecord


class RegistryGateway(Protocol):
    async def find_patient(
        self, identification_number: str, identification_type: IdentificationType
    ) -> PatientRecord | None: ...

    async def contacts(self, patient: PatientId) -> tuple[PatientContact, ...]: ...
