"""Elective pre-authorisations, as the API actually offers them.

There is **no elective endpoint**. Across all 48 endpoints DHA publishes there is no way to raise a
pre-auth before a visit: `POST /preauths` takes a `consent_token`, which only `POST /claims/visit` issues,
which only an authorised consent produces. `isElective` is read-only on the response, and the approval is
carried back to the facility on the *later* authorization rather than looked up.

So everything here is recognition. These tests exist to stop the two ways of getting that wrong: treating
an unapproved elective pre-auth as usable, and dressing `countdown` as an expiry nobody has verified.
"""

from __future__ import annotations

from sha_claim.adapters.wire.mappers import to_authorization, to_preauthorization
from sha_claim.adapters.wire.schemas.authorization import AuthorizationWire
from sha_claim.adapters.wire.schemas.preauth import PreauthorizationWire


def _preauth(**over: object) -> PreauthorizationWire:
    return PreauthorizationWire.model_validate({"guid": "pre-1", "interventionCode": "SHA-19-118", **over})


class TestTheElectiveMark:
    def test_read_off_the_preauth(self) -> None:
        assert to_preauthorization(_preauth(isElective=True)).is_elective is True

    def test_absent_means_not_elective(self) -> None:
        """An ordinary pre-auth has no flag at all, and must not read as elective."""
        assert to_preauthorization(_preauth()).is_elective is False

    def test_null_means_not_elective(self) -> None:
        """UAT sends `null` where the guides promise a boolean."""
        assert to_preauthorization(_preauth(isElective=None)).is_elective is False


class TestTheCountdown:
    def test_the_number_survives(self) -> None:
        assert to_preauthorization(_preauth(countdown=5)).countdown == 5

    def test_it_is_never_labelled_as_days(self) -> None:
        """SHA sends a bare integer and documents no unit.

        Reading it as days is the tempting mistake — it is what the planning notes assumed — and it is the
        one a surgical list would be built on. Until UAT settles it, the label states the number and whose
        it is, and claims nothing else.
        """
        label = to_preauthorization(_preauth(countdown=5)).countdown_label()
        assert "5" in label
        for unit in ("day", "hour", "week", "session", "expire"):
            assert unit not in label.lower(), f"countdown must not be presented in {unit}s"

    def test_silent_when_sha_does_not_send_one(self) -> None:
        assert to_preauthorization(_preauth()).countdown_label() == ""


class TestCarriedOntoTheNextVisit:
    """How a Monday approval is found again on Friday: SHA puts it on the new authorization."""

    def test_the_earlier_approval_arrives_with_the_new_authorization(self) -> None:
        auth = to_authorization(
            AuthorizationWire.model_validate(
                {
                    "guid": "auth-2",
                    "isElective": True,
                    "needsPreauth": True,
                    "electivePreauth": {
                        "isElective": True,
                        "status": "APPROVED",
                        "preauthType": "SURGICAL",
                        "memberName": "ROSE D CHEBET",
                        "serviceStart": "2026-10-02T08:00:00",
                        "serviceEnd": "2026-10-02T12:00:00",
                    },
                }
            )
        )
        assert auth.is_elective is True
        assert auth.server_needs_preauth is True
        assert auth.needs_preauth is True  # the derived property honours SHA's own flag
        assert auth.elective_preauth is not None
        assert auth.elective_preauth.is_approved is True
        assert auth.elective_preauth.preauth_type == "SURGICAL"
        assert auth.elective_preauth.service_start is not None
        assert auth.elective_preauth.service_start.year == 2026

    def test_an_ordinary_authorization_carries_none_of_it(self) -> None:
        auth = to_authorization(AuthorizationWire.model_validate({"guid": "auth-1"}))
        assert auth.is_elective is False
        assert auth.elective_preauth is None

    def test_a_pending_elective_preauth_is_not_approved(self) -> None:
        """The failure this guards is concrete: a theatre list built on an approval SHA has not given."""
        for status in ("PENDING", "PENDING_APPROVAL", "AWAITING_DOCTOR", "PENDING_DOCTOR_APPROVAL", ""):
            auth = to_authorization(
                AuthorizationWire.model_validate(
                    {
                        "guid": "a",
                        "electivePreauth": {"status": status},
                    }
                )
            )
            assert auth.elective_preauth is not None
            assert auth.elective_preauth.is_approved is False, status

    def test_an_unrecognised_status_is_not_approved(self) -> None:
        auth = to_authorization(
            AuthorizationWire.model_validate(
                {
                    "guid": "a",
                    "electivePreauth": {"status": "SOMETHING_NEW"},
                }
            )
        )
        assert auth.elective_preauth is not None
        assert auth.elective_preauth.is_approved is False

    def test_a_rejected_one_is_not_approved(self) -> None:
        auth = to_authorization(
            AuthorizationWire.model_validate(
                {
                    "guid": "a",
                    "electivePreauth": {"status": "REJECTED"},
                }
            )
        )
        assert auth.elective_preauth is not None
        assert auth.elective_preauth.is_approved is False
