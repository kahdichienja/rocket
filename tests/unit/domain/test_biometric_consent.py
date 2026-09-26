"""The biometric consent path: which route a member takes, and what goes on the wire."""

from __future__ import annotations

import pytest

from sha_claim.adapters.wire.mappers import to_authorization
from sha_claim.adapters.wire.requests import authorize
from sha_claim.adapters.wire.schemas.authorization import AuthorizationWire
from sha_claim.domain.codes import InterventionCode
from sha_claim.domain.consent import BiometricContext
from sha_claim.domain.eligibility import ConsentRoute, Eligibility
from sha_claim.domain.enums import ServiceType
from sha_claim.domain.identifiers import PatientId

P = PatientId("CR2300980707791-1")
CODES = [InterventionCode("SHA-12-001")]


def eligibility(*, whitelisted: bool, enforced: bool) -> Eligibility:
    return Eligibility(
        patient_id=P,
        full_name="ERIC MULATYA LAZARUS",
        status=None,
        status_description="",
        schemes=(),
        whitelisted_for_otp=whitelisted,
        facility_biometrics_enforced=enforced,
    )


class TestWhichRouteTheMemberTakes:
    def test_an_enforced_facility_uses_biometrics_even_for_a_member_with_a_phone(self) -> None:
        """Enforcement is the payer's decision and outranks the phone: an enforced facility may not OTP."""
        assert eligibility(whitelisted=True, enforced=True).consent_route() is ConsentRoute.BIOMETRIC

    def test_a_whitelisted_member_at_an_ordinary_facility_uses_the_otp(self) -> None:
        assert eligibility(whitelisted=True, enforced=False).consent_route() is ConsentRoute.OTP

    def test_a_member_sha_holds_no_phone_for_uses_biometrics(self) -> None:
        """`send_otp` would fail whatever else is true, so biometrics is the only path left."""
        assert eligibility(whitelisted=False, enforced=False).consent_route() is ConsentRoute.BIOMETRIC
        assert eligibility(whitelisted=False, enforced=True).consent_route() is ConsentRoute.BIOMETRIC

    def test_the_route_never_leaves_the_desk_without_one(self) -> None:
        for whitelisted in (True, False):
            for enforced in (True, False):
                assert eligibility(whitelisted=whitelisted, enforced=enforced).consent_route() in ConsentRoute


class TestTheAuthorizeBody:
    def test_the_otp_path_is_unchanged(self) -> None:
        """Byte-for-byte what it has always sent: the biometric work must not disturb the working path."""
        assert authorize(P, ServiceType.CAPITATION, CODES, None).json == {
            "patient_id": P.value,
            "service_type": "CAPITATION",
            "interventions": ["SHA-12-001"],
        }

    def test_the_biometric_path_sends_what_dha_documents(self) -> None:
        bio = BiometricContext(
            agent_id="12345678", work_station_id="3c5e4cece90bc45c", ekyc_provider_id="Nairobi West"
        )
        body = authorize(P, ServiceType.CAPITATION, CODES, None, bio).json
        assert body == {
            "patient_id": P.value,
            "service_type": "CAPITATION",
            "interventions": ["SHA-12-001"],
            "agent_id": "12345678",
            "work_station_id": "3c5e4cece90bc45c",
            "authorizing_device_os": "windows",
            "factors": ["SHA"],
            "is_integration": True,
            "is_emergency": False,
            "is_biometrics_discharge_authorization": False,
            "ekyc_provider_id": "Nairobi West",
        }

    def test_optional_identifiers_are_omitted_rather_than_sent_blank(self) -> None:
        body = authorize(P, ServiceType.OUTPATIENT, CODES, None, BiometricContext("1", "w")).json
        assert "ekyc_provider_id" not in body and "provider" not in body

    @pytest.mark.parametrize(("agent", "station"), [("", "w"), ("  ", "w"), ("1", ""), ("1", "  ")])
    def test_a_capture_without_an_agent_or_a_workstation_is_refused_here(
        self, agent: str, station: str
    ) -> None:
        """SHA rejects a capture it cannot place, with a message that names neither field. Fail early."""
        with pytest.raises(ValueError):
            BiometricContext(agent_id=agent, work_station_id=station)


class TestTheAuthorizationComingBack:
    def test_the_capture_url_survives_the_mapping(self) -> None:
        """Without `request_url` there is nowhere to send the beneficiary and the authorization sits PENDING."""
        a = to_authorization(
            AuthorizationWire.model_validate(
                {
                    "guid": "9df3774d",
                    "status": "PENDING",
                    "ekycToken": "efe1ad96",
                    "shaVerificationRequest": {
                        "embedExpiry": 120,
                        "embededToken": "efe1ad96",
                        "requestId": "67115bfa",
                        "requestUrl": "https://test.ekyc.pesaflow.com/self-service/embeded/v3/request",
                    },
                }
            )
        )
        assert a.capture_url == "https://test.ekyc.pesaflow.com/self-service/embeded/v3/request"
        assert a.verification is not None and a.verification.embed_expiry == 120
        assert a.ekyc_token == "efe1ad96"
        assert a.is_pending and not a.is_verified

    def test_an_otp_authorization_simply_has_no_capture(self) -> None:
        a = to_authorization(AuthorizationWire.model_validate({"guid": "g", "status": "AUTHORIZED"}))
        assert a.verification is None
        assert a.capture_url == ""

    def test_a_matched_beneficiary_awaiting_the_visit_counts_as_verified(self) -> None:
        """AUTHORIZED_PENDING_VISIT means SHA matched them and is waiting on us — not an unfinished capture."""
        a = to_authorization(
            AuthorizationWire.model_validate({"guid": "g", "status": "AUTHORIZED_PENDING_VISIT"})
        )
        assert a.is_verified
        assert a.proof.value == "g"
