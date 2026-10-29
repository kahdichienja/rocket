from __future__ import annotations

from typing import Protocol

from sha_claim.domain.biometrics import (
    CaptureJob,
    CaptureStation,
    EnrollmentStatus,
    MatchAttempt,
    MatchRequestId,
    MatchResult,
)
from sha_claim.domain.identifiers import PatientId


class BiometricsGateway(Protocol):
    """Minors fingerprint consent.

    Three of these dispatch a capture to a physical reader and answer `202` with an id; their outcomes
    arrive by callback. Only `enrollment_status` answers with a fact.
    """

    async def enrol(
        self, beneficiary: PatientId, position: int, station: CaptureStation, deadline_seconds: int | None
    ) -> CaptureJob: ...

    async def verify(
        self, beneficiary: PatientId, position: int, station: CaptureStation, deadline_seconds: int | None
    ) -> CaptureJob: ...

    async def enrollment_status(self, beneficiary: PatientId) -> EnrollmentStatus: ...

    async def match(
        self, beneficiary: PatientId, station: CaptureStation, position: int, deadline_seconds: int | None
    ) -> MatchAttempt: ...

    async def match_status(self, match_id: MatchRequestId) -> MatchResult: ...
