from __future__ import annotations

from typing import Protocol

from sha_claim.domain.claim import ClaimLine, VirtualClaim
from sha_claim.domain.codes import InterventionCode
from sha_claim.domain.emergency import EmergencyCase, EmergencyProtocol, EmtClaim, ProtocolLine
from sha_claim.domain.identifiers import ConsentToken
from sha_claim.domain.practitioner import PractitionerRef


class EmergencyGateway(Protocol):
    async def open_case(self, case: EmergencyCase) -> VirtualClaim: ...

    async def protocols(
        self, intervention: InterventionCode, active: bool
    ) -> tuple[EmergencyProtocol, ...]: ...

    async def add_protocol(self, token: ConsentToken, line: ProtocolLine) -> ClaimLine: ...

    async def add_doctor(self, token: ConsentToken, doctor: PractitionerRef) -> str: ...

    async def remove_doctor(self, token: ConsentToken) -> None: ...

    async def open_emt(self, token: ConsentToken, claim: EmtClaim) -> VirtualClaim: ...
