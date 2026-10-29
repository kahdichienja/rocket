"""A rejected biometric authorization, and the one rejection that comes with a remedy.

DHA: when eCitizen holds fingerprints for a patient that it cannot *use* for matching, no capture can ever
succeed. The HIE rejects the authorization and allows an OTP for roughly 24-48 hours, even at a facility on
enforced biometrics. The signal is `REJECTED` carrying
`authorizationReason = "BIOMETRICS_NOT_FOUND_OTP_ALLOWED"`.

Until 2026-10-29 `REJECTED` was not in `AuthorizationStatus`, so it arrived as an unknown pseudo-member.
`is_verified` was correctly False — but a caller could not tell "not finished yet" from "never will be",
and so polled for ever while the beneficiary's own screen reported the capture had succeeded. That is the
hang these tests exist to prevent.

Two failure directions, and they are not symmetric:

  * reading a bare rejection as an OTP allowance sends a desk down a path SHA refuses with "restricted to
    biometric visits";
  * failing to read a real allowance leaves a patient with no route at all.

So the match is exact on both halves, and nothing is inferred from free text.
"""

from __future__ import annotations

from datetime import date

import pytest

from sha_claim.adapters.wire import mappers
from sha_claim.adapters.wire.schemas.authorization import AuthorizationWire
from sha_claim.domain.consent import Authorization
from sha_claim.domain.enums import AuthorizationReason, AuthorizationStatus

NOTES = "biometrics_not_found: member allowed OTP until 2026-09-29; retry the authorization with OTP."
REASON = "BIOMETRICS_NOT_FOUND_OTP_ALLOWED"


def _authorization(**payload: object) -> Authorization:
    base = {"guid": "g-1", "token": "TOKEN0", "status": "REJECTED"}
    return mappers.to_authorization(AuthorizationWire.model_validate({**base, **payload}))


class TestRejectedIsNowAKnownState:
    def test_rejected_is_a_real_member(self) -> None:
        """Not a pseudo-member. The whole hang rested on this."""
        assert AuthorizationStatus("REJECTED") is AuthorizationStatus.REJECTED
        assert AuthorizationStatus.REJECTED.is_known

    def test_a_rejection_is_terminal(self) -> None:
        assert _authorization().is_rejected

    def test_a_rejection_is_never_consent(self) -> None:
        """Whatever remedy follows it. `is_verified` must not widen."""
        assert not _authorization(authorizationReason=REASON, notes=NOTES).is_verified

    @pytest.mark.parametrize("status", ["PENDING", "AUTHORIZED", "AUTHORIZED_PENDING_VISIT", "CLOSED"])
    def test_nothing_else_reads_as_rejected(self, status: str) -> None:
        assert not _authorization(status=status).is_rejected


class TestTheOtpAllowance:
    def test_a_rejection_with_the_reason_allows_an_otp(self) -> None:
        assert _authorization(authorizationReason=REASON, notes=NOTES).otp_allowed_after_biometrics_not_found

    def test_a_rejection_with_no_reason_allows_nothing(self) -> None:
        """An ordinary biometric failure — a finger that did not match, a lapsed capture, a minor. DHA
        rejects those *without* the reason, and treating them as an allowance sends the desk to an OTP
        that SHA refuses."""
        assert not _authorization().otp_allowed_after_biometrics_not_found

    def test_an_unfamiliar_reason_allows_nothing(self) -> None:
        """DHA publishes one reason and plainly has others. An unknown one survives as itself and grants
        nothing — the same direction every unknown is given in this SDK."""
        rejection = _authorization(authorizationReason="SOME_FUTURE_REASON")

        assert not rejection.otp_allowed_after_biometrics_not_found
        assert rejection.reason is not None and not rejection.reason.is_known

    def test_the_reason_alone_is_not_enough(self) -> None:
        """Both halves, as DHA's own check has them. A reason on a non-rejected authorization is not an
        allowance — it is a record of something else."""
        assert not _authorization(
            status="PENDING", authorizationReason=REASON
        ).otp_allowed_after_biometrics_not_found

    def test_both_spellings_of_the_field_are_read(self) -> None:
        """DHA sends `authorization_reason` on the callback and `authorizationReason` on the GET. One
        field declaration covers both, through `WireModel`'s alias rules — pinned because losing it would
        silently disable the remedy on whichever path changed."""
        assert _authorization(authorizationReason=REASON).otp_allowed_after_biometrics_not_found
        assert _authorization(authorization_reason=REASON).otp_allowed_after_biometrics_not_found


class TestTheAllowanceDate:
    def test_the_date_is_read_out_of_the_notes(self) -> None:
        assert _authorization(authorizationReason=REASON, notes=NOTES).otp_allowed_until == date(2026, 9, 29)

    def test_a_missing_or_reworded_note_costs_the_date_and_nothing_else(self) -> None:
        """DHA says the wording of `notes` may change, so nothing is allowed to depend on parsing it. The
        remedy must survive a sentence we cannot read."""
        reworded = _authorization(authorizationReason=REASON, notes="member may use a one-time password")

        assert reworded.otp_allowed_until is None
        assert reworded.otp_allowed_after_biometrics_not_found, "the remedy does not depend on the date"

    def test_an_impossible_date_is_refused_rather_than_shown(self) -> None:
        assert _authorization(notes="allowed OTP until 2026-13-45").otp_allowed_until is None

    def test_no_notes_at_all(self) -> None:
        assert _authorization().otp_allowed_until is None


class TestTheReasonVocabulary:
    def test_the_published_value_is_named(self) -> None:
        assert AuthorizationReason.BIOMETRICS_NOT_FOUND_OTP_ALLOWED.value == REASON
        assert AuthorizationReason(REASON).is_known

    def test_an_absent_reason_parses_to_none(self) -> None:
        assert AuthorizationReason.parse("") is None
        assert AuthorizationReason.parse(None) is None
