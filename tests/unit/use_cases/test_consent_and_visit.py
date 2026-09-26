from collections.abc import Sequence

import pytest

from sha_claim.domain.claim import VirtualClaim
from sha_claim.domain.codes import InterventionCode
from sha_claim.domain.consent import Authorization, BiometricContext, ConsentProof, Otp
from sha_claim.domain.enums import ClaimWorkflowState, ServiceType
from sha_claim.domain.identifiers import ConsentToken, PatientId
from sha_claim.errors import RequestValidationError
from sha_claim.use_cases.capture_consent import CaptureConsent
from sha_claim.use_cases.open_visit import OpenVisit

P = PatientId("CR1111111111111-1")


def authorization() -> Authorization:
    return Authorization("g", "t", "a", None, "", True, "CAPITATION", P, "", "", ())


class FakeConsent:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []

    async def authorize(
        self,
        patient: PatientId,
        service_type: ServiceType,
        interventions: Sequence[InterventionCode],
        otp: Otp | None,
        biometrics: BiometricContext | None = None,
    ) -> Authorization:
        self.calls.append((patient, service_type, tuple(interventions), otp, biometrics))
        return authorization()

    async def get(self, token: str, guid: str, beneficiary: PatientId | None) -> Authorization | None:
        return None

    async def reject(self, token: str) -> None:
        pass

    async def send_otp(self, patient: PatientId, interventions: Sequence[InterventionCode]) -> str:
        return "sent"

    async def list(self, beneficiary: PatientId) -> tuple[Authorization, ...]:
        return ()


class FakeClaims:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []

    async def open_visit(
        self,
        patient: PatientId,
        service_type: ServiceType,
        interventions: Sequence[InterventionCode],
        proof: ConsentProof,
    ) -> VirtualClaim:
        self.calls.append((patient, service_type, tuple(interventions), proof))
        return VirtualClaim(
            ConsentToken("abcdefghij"),
            None,
            1,
            ClaimWorkflowState("OPEN"),
            "",
            service_type,
            "",
            "",
            "",
            "",
            "KES",
            None,
            None,
        )


async def test_capture_consent_dedupes_codes_and_forwards() -> None:
    gw = FakeConsent()
    codes = [InterventionCode("SHA-12-001"), InterventionCode("sha-12-001"), InterventionCode("SHA-12-002")]
    await CaptureConsent(gw).execute(P, ServiceType.CAPITATION, codes)
    assert gw.calls == [
        (
            P,
            ServiceType.CAPITATION,
            (InterventionCode("SHA-12-001"), InterventionCode("SHA-12-002")),
            None,
            None,
        )
    ]


async def test_capture_consent_forwards_the_biometric_context() -> None:
    """The eKYC path is the same call with the workstation and agent attached."""
    gw = FakeConsent()
    bio = BiometricContext(agent_id="12345678", work_station_id="3c5e4cece90bc45c")
    await CaptureConsent(gw).execute(P, ServiceType.OUTPATIENT, [InterventionCode("SHA-12-001")], None, bio)
    assert gw.calls[0][4] is bio


async def test_capture_consent_requires_interventions() -> None:
    gw = FakeConsent()
    with pytest.raises(RequestValidationError, match="intervention"):
        await CaptureConsent(gw).execute(P, ServiceType.CAPITATION, [])
    assert gw.calls == []


async def test_open_visit_forwards_proof() -> None:
    gw = FakeClaims()
    claim = await OpenVisit(gw).execute(
        P, ServiceType.CAPITATION, [InterventionCode("SHA-12-001")], Otp("123456")
    )
    assert claim.consent_token.value == "abcdefghij"
    assert gw.calls[0][3] == Otp("123456")


async def test_open_visit_requires_interventions() -> None:
    with pytest.raises(RequestValidationError):
        await OpenVisit(FakeClaims()).execute(P, ServiceType.CAPITATION, [], Otp("1"))
