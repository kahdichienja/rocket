"""What the minors fingerprint types promise, with the dangerous answers pinned.

A fingerprint match is a **consent decision about a child**, and the asymmetry of the two ways to get it
wrong runs through every assertion here: a capture wrongly read as proof means a child treated and billed
on consent nobody gave, while a capture wrongly read as unfinished costs a retry. So every unknown, every
absent field and every unrecognised status must fall on the side of *not consent*.
"""

from __future__ import annotations

import pytest

from sha_claim.domain.biometrics import (
    ANY_FINGER,
    CaptureStation,
    EnrollmentStatus,
    MatchRequestId,
    MatchResult,
    MatchStatus,
    finger_position,
)
from sha_claim.domain.consent import MatchId
from sha_claim.domain.identifiers import PatientId

CHILD = PatientId("CR7678914660684-5")
MATCH = MatchRequestId("4b0f2f8e-7a6c-4d1b-9f3a-0c2d6e8a1b47")


def _result(status: str | None, **over: object) -> MatchResult:
    return MatchResult(match_id=MATCH, status=MatchStatus.parse(status), **over)  # type: ignore[arg-type]


class TestOnlyMatchedIsConsent:
    def test_matched_authorizes(self) -> None:
        assert _result("matched").is_matched

    @pytest.mark.parametrize("status", ["pending", "no_match", "failed"])
    def test_nothing_else_authorizes(self, status: str) -> None:
        assert not _result(status).is_matched

    def test_an_unrecognised_status_is_not_consent(self) -> None:
        """The inverse of the 0.1.49 bug, and the direction matters.

        There, an unknown authorization status silently meant "keep waiting" and a discharge hung. Here an
        unknown status must silently mean "this is not consent". `LenientStrEnum` keeps the value rather
        than raising, so the test is that keeping it does not make it true.
        """
        surprise = _result("AUTHORIZED_PENDING_SOMETHING")

        assert not surprise.is_matched
        assert surprise.status is not None, "the unknown value is kept, not discarded"
        assert not surprise.status.is_known

    def test_a_missing_status_is_not_consent(self) -> None:
        assert not _result(None).is_matched
        assert not _result("").is_matched


class TestProofRefusesWhatIsNotProven:
    def test_a_matched_attempt_becomes_consent_proof(self) -> None:
        proof = _result("matched").proof()

        assert isinstance(proof, MatchId)
        assert proof.value == MATCH.value

    @pytest.mark.parametrize("status", ["pending", "no_match", "failed", "weird", None])
    def test_anything_else_raises_rather_than_handing_over_consent(self, status: str | None) -> None:
        """A caller that forgot to check must not be able to pass this to `open_visit`."""
        with pytest.raises(ValueError, match="cannot prove consent"):
            _result(status).proof()

    def test_a_match_with_no_id_cannot_prove_consent_either(self) -> None:
        with pytest.raises(ValueError, match="cannot prove consent"):
            MatchResult(match_id=None, status=MatchStatus.MATCHED).proof()


class TestTerminalAndDeadline:
    @pytest.mark.parametrize("status", ["no_match", "failed"])
    def test_terminal_states_need_a_fresh_capture(self, status: str) -> None:
        assert _result(status).is_terminal

    def test_pending_is_not_terminal(self) -> None:
        assert not _result("pending").is_terminal

    def test_an_unknown_status_is_not_terminal(self) -> None:
        """Kept open rather than discarded: DHA may still resolve an attempt whose state we cannot read,
        and throwing it away would lose a capture the child already gave."""
        assert not _result("something_new").is_terminal

    def test_deadline_exceeded_is_named(self) -> None:
        assert _result("failed", error_code="deadline_exceeded").deadline_exceeded
        assert _result("failed", error_code="DEADLINE_EXCEEDED").deadline_exceeded
        assert not _result("failed", error_code="device_offline").deadline_exceeded
        assert not _result("failed").deadline_exceeded


class TestEnrollmentStatusAnswersTheScreensQuestion:
    def test_a_verified_finger_can_consent(self) -> None:
        status = EnrollmentStatus(beneficiary=CHILD, verified=(2,), total=1, state="fully_enrolled")

        assert status.can_consent
        assert not status.needs_enrollment
        assert not status.needs_verification

    def test_nothing_stored_needs_enrolling(self) -> None:
        status = EnrollmentStatus(beneficiary=CHILD, total=0, state="")

        assert status.needs_enrollment
        assert not status.can_consent

    def test_a_stored_but_unconfirmed_print_cannot_consent_yet(self) -> None:
        """DHA: "the print is stored but not yet usable for consent". A child can be enrolled and still
        unable to prove anything, which is the state a desk has to be able to name."""
        status = EnrollmentStatus(beneficiary=CHILD, non_verified=(3,), total=1, state="partially_enrolled")

        assert not status.can_consent
        assert status.needs_verification
        assert status.resumable_positions == (3,)

    def test_one_confirmed_finger_is_not_sent_to_finish_the_other(self) -> None:
        """Narrower than "has unverified fingers" on purpose: this child can consent *now*, and routing the
        desk into housekeeping would hold up a visit for nothing."""
        status = EnrollmentStatus(beneficiary=CHILD, verified=(2,), non_verified=(3,), total=2)

        assert status.can_consent
        assert not status.needs_verification

    def test_an_empty_status_is_not_mistaken_for_enrolled(self) -> None:
        assert not EnrollmentStatus(beneficiary=None).can_consent


class TestFingerPosition:
    @pytest.mark.parametrize("position", [1, 5, 10])
    def test_real_positions_pass(self, position: int) -> None:
        assert finger_position(position) == position

    @pytest.mark.parametrize("position", [0, -1, 11, 99])
    def test_enrolment_refuses_anything_else(self, position: int) -> None:
        """Including 0: enrolment and verification are per finger and must name one. DHA answers a bad
        position with a 400 naming the field; refusing here is the same answer, one round trip earlier."""
        with pytest.raises(ValueError, match="finger position"):
            finger_position(position)

    def test_a_match_may_mean_any_enrolled_finger(self) -> None:
        assert finger_position(ANY_FINGER, allow_any=True) == ANY_FINGER
        assert finger_position(4, allow_any=True) == 4

    def test_a_match_still_refuses_an_impossible_finger(self) -> None:
        with pytest.raises(ValueError, match="finger position"):
            finger_position(11, allow_any=True)


class TestCaptureStation:
    def test_it_spells_workstation_the_way_the_minors_endpoints_do(self) -> None:
        """eKYC sends `work_station_id`; these endpoints want `workstation_id`. One payload builder for
        both would mean one flow silently sending a field the server ignores, and then a 400 naming a field
        the caller believes it sent."""
        payload = CaptureStation(workstation_id="WS-1", device_id="DEV-9", agent_id="12345678").as_payload()

        assert payload == {"workstation_id": "WS-1", "device_id": "DEV-9", "agent_id": "12345678"}
        assert "work_station_id" not in payload

    @pytest.mark.parametrize("missing", ["workstation_id", "device_id", "agent_id"])
    def test_every_required_identifier_is_refused_when_blank(self, missing: str) -> None:
        fields = {"workstation_id": "WS-1", "device_id": "DEV-9", "agent_id": "12345678", missing: "  "}

        with pytest.raises(ValueError, match=missing):
            CaptureStation(**fields)

    def test_identifiers_are_trimmed(self) -> None:
        station = CaptureStation(workstation_id=" WS-1 ", device_id=" DEV-9 ", agent_id=" 123 ")

        assert station.as_payload() == {"workstation_id": "WS-1", "device_id": "DEV-9", "agent_id": "123"}
