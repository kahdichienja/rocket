"""Elective pre-authorisations, as the API actually offers them.

There is no elective *endpoint* and no elective field on the create request — but there is an elective
*flow*, and this file used to deny it. The claim was that `POST /preauths` needs a `consent_token` which
only `POST /claims/visit` issues. `POST /claims/authorize` issues one as well, and DHA's elective scenario
files the pre-auth against it in a pre-visit phase, with no virtual claim in existence: created
`PENDING_DOCTOR_APPROVAL`, signed by the doctor into `ACTIVE`, finalised by the payer into `FINALISED`,
and only then is the visit opened on the day. `ClaimsResource.before_visit` is that path.

What stays true is the recognition half: `isElective` is read-only, and the approval comes back on the
*later* authorization rather than anywhere it can be looked up. These tests cover both — the flow, and
the two ways of misreading it: treating an unapproved elective pre-auth as usable, and dressing
`countdown` as an expiry nobody has verified.
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


class TestTheStatusesTheScenarioEndsOn:
    """`PENDING_DOCTOR_APPROVAL` → `ACTIVE` → `FINALISED`, and what each one allows."""

    def test_finalised_is_an_approval(self) -> None:
        """The state DHA's elective scenario finishes on: "payer approved; valid for claim creation".

        It contains no "APPROV", so it read as pending — and a desk holding a real approval was told to
        keep waiting, with the operation already booked.
        """
        for spelling in ("FINALISED", "FINALIZED", "Finalised"):
            auth = to_authorization(
                AuthorizationWire.model_validate({"guid": "a", "electivePreauth": {"status": spelling}})
            )
            assert auth.elective_preauth is not None
            assert auth.elective_preauth.is_approved is True, spelling

    def test_active_is_not_an_approval(self) -> None:
        """The doctor has signed; the payer has not. A claim billed here is billed against nothing."""
        auth = to_authorization(
            AuthorizationWire.model_validate({"guid": "a", "electivePreauth": {"status": "ACTIVE"}})
        )
        assert auth.elective_preauth is not None
        assert auth.elective_preauth.is_approved is False


class TestWhenAClaimMayBeCreated:
    """`AUTHORIZED_PENDING_VISIT` → `AUTHORIZED` happens when the pre-auth is finalised, not before."""

    def _auth(self, **over: object):  # type: ignore[no-untyped-def]
        return to_authorization(AuthorizationWire.model_validate({"guid": "a", **over}))

    def test_an_elective_authorization_waits_for_its_preauth(self) -> None:
        auth = self._auth(isElective=True, electivePreauth={"status": "PENDING_DOCTOR_APPROVAL"})
        assert auth.awaiting_elective_preauth is True

    def test_and_stops_waiting_once_it_is_finalised(self) -> None:
        auth = self._auth(isElective=True, electivePreauth={"status": "FINALISED"})
        assert auth.awaiting_elective_preauth is False

    def test_an_elective_authorization_with_no_summary_falls_back_to_the_flag(self) -> None:
        assert self._auth(isElective=True, overallPreauthFinalised=False).awaiting_elective_preauth is True
        assert self._auth(isElective=True, overallPreauthFinalised=True).awaiting_elective_preauth is False

    def test_an_ordinary_visit_is_never_held_up_by_this(self) -> None:
        """`overallPreauthFinalised` is false on ordinary authorizations too.

        Blocking an everyday visit on a flag about a pre-auth nobody raised is a worse failure than the
        one this property exists to prevent, so it fires only where SHA itself said elective.
        """
        assert self._auth(overallPreauthFinalised=False).awaiting_elective_preauth is False
        assert self._auth(needsPreauth=True, overallPreauthFinalised=False).awaiting_elective_preauth is False


class TestReachingOneInterventionsCoverage:
    """`required_preauth_document_types` is published on the coverage lookup and nowhere else.

    A caller holding only an intervention code — off a claim, where the sub-benefit is not carried —
    could not read it, so a chemotherapy pre-auth was filed blind and refused: *"missing the following
    required documents histopathology results, prescription, treatment plan"* (UAT, 2026-10-10,
    SHA-06-022). Both filters on this endpoint are optional; `code` is the one that was never sent.
    """

    def test_code_alone_is_a_valid_query(self) -> None:
        from sha_claim.adapters.wire import requests
        from sha_claim.domain.identifiers import PatientId

        r = requests.interventions(PatientId("CR-2026-000502"), code="SHA-06-022")
        assert r.params == {"patient_id": "CR-2026-000502", "code": "SHA-06-022"}

    def test_an_empty_filter_is_omitted_rather_than_sent_blank(self) -> None:
        """A blank `sub_benefit_code` is read as "match nothing", which returns an empty list."""
        from sha_claim.adapters.wire import requests
        from sha_claim.domain.identifiers import PatientId

        assert requests.interventions(PatientId("CR-2026-000502")).params == {"patient_id": "CR-2026-000502"}

    def test_optional_documents_are_kept_apart_from_required_ones(self) -> None:
        """Five documents of which two are optional is not the same as five required ones."""
        from sha_claim.adapters.wire.mappers import to_intervention_coverage
        from sha_claim.adapters.wire.schemas.benefits import InterventionWire

        coverage = to_intervention_coverage(
            InterventionWire.model_validate(
                {
                    "code": "SHA-06-022",
                    "name": "Chemotherapy medicines",
                    "requiredPreauthDocumentTypes": [
                        "HISTOPATHOLOGY_RESULTS",
                        "MEDICAL_REPORT",
                        "PREAUTH_FORM",
                        "PRESCRIPTION",
                        "TREATMENT_PLAN",
                    ],
                    "optionalPreauthDocumentTypes": ["IMAGING_RESULT", "LAB_RESULTS"],
                }
            )
        )
        assert coverage.required_preauth_document_types == (
            "HISTOPATHOLOGY_RESULTS",
            "MEDICAL_REPORT",
            "PREAUTH_FORM",
            "PRESCRIPTION",
            "TREATMENT_PLAN",
        )
        assert coverage.optional_preauth_document_types == ("IMAGING_RESULT", "LAB_RESULTS")
