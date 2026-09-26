"""The pre-auth multipart, pinned to the shape Postman actually sends.

This request was written against a portal reference that does not publish the inner schema of `items`,
`diagnoses`, `doctors` or `attachments`, and four things were guessed wrong. The attachment one lost every
file silently: an entry names its own form part through `file_field_name`, and ours named a part that did
not exist. Attachments are the substance of a pre-auth — SHA approves on them — so they are pinned hardest.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import NamedTuple

import pytest

from sha_claim import (
    AnaesthesiaType,
    Attachment,
    CarcinomaStaging,
    ConsentToken,
    DocumentType,
    Icd11Code,
    IdentificationType,
    ImagingDetails,
    InterventionCode,
    LensPrescription,
    MetastasisSite,
    Money,
    NewOrReplacement,
    OncologyDetails,
    OpticalDetails,
    PractitionerRef,
    PreauthItem,
    PreauthRequest,
    RegulationBody,
    RenalDetails,
    SessionFrequency,
    SurgicalDetails,
    TreatmentSetting,
)
from sha_claim.adapters.wire.requests import create_preauth
from sha_claim.domain.preauth import PreauthDetails

TOKEN = ConsentToken("tok-123")
WHEN = datetime(2026, 3, 5, 15, 30, tzinfo=UTC)


class Built(NamedTuple):
    """The multipart `create_preauth` produced, with both halves known to be present.

    `WireRequest.form` and `.files` are optional in general — most calls are JSON — but every pre-auth is
    multipart. Narrowing once here keeps the assertions about the wire, not about `None`.
    """

    form: Mapping[str, str]
    files: Mapping[str, tuple[str, bytes, str]]


def build(details: PreauthDetails | None = None, attachments: tuple[Attachment, ...] = ()) -> Built:
    request = PreauthRequest(
        intervention_code=InterventionCode.of("SHA-19-074"),
        service_start=WHEN,
        service_end=WHEN,
        items=(PreauthItem("C1", "Consultation", 1, Money.kes("500.00")),),
        diagnoses=(Icd11Code.of("ca07.0"),),
        doctors=(PractitionerRef("12345678", IdentificationType.NATIONAL_ID, RegulationBody.KMPDC),),
        provider_notification_email="provider@example.com",
        attachments=attachments,
        **({"details": details} if details else {}),
    )
    wire = create_preauth(TOKEN, request)
    assert wire.form is not None
    # A pre-auth with no documents carries no file parts at all, so `files` is legitimately absent there.
    return Built(wire.form, wire.files or {})


class TestTheAttachmentContract:
    def test_the_meta_entry_names_a_form_part_that_exists(self) -> None:
        """The bug this file exists for: `file_field_name` pointed at `attachment_0`, which was never sent."""
        wire = build(
            attachments=(Attachment("lab.pdf", b"%PDF", DocumentType.LAB_RESULTS, "application/pdf"),)
        )
        meta = json.loads(wire.form["attachments"])
        assert meta == [
            {
                "document_title": "lab.pdf",
                "document_type": "LAB_RESULTS",
                "file_field_name": "attachments_0_file_blob",
            }
        ]
        assert set(wire.files) == {"attachments_0_file_blob"}
        for entry in meta:
            assert entry["file_field_name"] in wire.files

    def test_every_attachment_gets_its_own_indexed_part(self) -> None:
        wire = build(
            attachments=(
                Attachment("a.pdf", b"%PDF", DocumentType.LAB_RESULTS, "application/pdf"),
                Attachment("b.pdf", b"%PDF", DocumentType.MEDICAL_REPORT, "application/pdf"),
            )
        )
        assert set(wire.files) == {"attachments_0_file_blob", "attachments_1_file_blob"}
        assert [e["file_field_name"] for e in json.loads(wire.form["attachments"])] == list(wire.files)

    def test_no_attachments_sends_no_files(self) -> None:
        wire = build()
        assert json.loads(wire.form["attachments"]) == []
        # No file parts at all. `create_preauth` leaves `files` unset here; `Built` reports that as empty.
        assert wire.files == {}


class TestTheOtherThreeThatWereWrong:
    def test_each_diagnosis_repeats_the_consent_token(self) -> None:
        assert json.loads(build().form["diagnoses"]) == [{"consent_token": "tok-123", "icd_code": "CA07.0"}]

    def test_an_item_carries_only_its_unit_price(self) -> None:
        assert json.loads(build().form["items"]) == [{"unit_price": "500.00"}]

    def test_a_doctor_carries_the_intervention_they_are_attached_to(self) -> None:
        assert json.loads(build().form["doctors"]) == [
            {
                "identification_type": "National ID",
                "identification_number": "12345678",
                "regulation_body": "KMPDC",
                "intervention_code": "SHA-19-074",
            }
        ]


class TestTheSpecialisedForms:
    def test_a_normal_preauth_adds_nothing(self) -> None:
        common = {
            "consent_token",
            "intervention_code",
            "service_start",
            "service_end",
            "items",
            "diagnoses",
            "doctors",
            "attachments",
            "provider_notification_email",
        }
        assert set(build().form) == common

    def test_surgical(self) -> None:
        wire = build(SurgicalDetails("Pain", "110 BP", "None", "Pale", "None", AnaesthesiaType.GENERAL, WHEN))
        assert wire.form["type_of_anaesthesia"] == "GENERAL"
        assert wire.form["surgery_date"] == WHEN.isoformat()
        assert wire.form["chief_complaint"] == "Pain"

    def test_renal(self) -> None:
        wire = build(
            RenalDetails(
                7, Money.kes("5000.00"), SessionFrequency.ONCE_A_MONTH, "Pain", WHEN, is_co_insured=True
            )
        )
        assert wire.form["number_of_sessions_required"] == "7"
        assert wire.form["cost_per_session"] == "5000.00"
        assert wire.form["frequency_of_sessions"] == "ONCE_A_MONTH"
        assert wire.form["is_co_insured"] == "true"

    def test_oncology_sends_its_lists_json_encoded(self) -> None:
        wire = build(
            OncologyDetails(
                CarcinomaStaging.STAGE_1,
                "None",
                (MetastasisSite.LUNG,),
                (TreatmentSetting.DAY_WARD,),
                20,
                Money.kes("2500.00"),
            )
        )
        assert wire.form["carcinoma_staging"] == "STAGE_1"
        assert json.loads(wire.form["metastases"]) == ["LUNG"]
        assert json.loads(wire.form["treatment_setting"]) == ["DAY_WARD"]

    def test_optical_states_the_three_amounts_separately(self) -> None:
        wire = build(
            OpticalDetails(
                "To see clearly",
                LensPrescription.FRAMES_LENSES,
                NewOrReplacement.REPLACEMENT,
                Money.kes("10000.00"),
                Money.kes("2000.00"),
                Money.kes("10000.00"),
            )
        )
        assert wire.form["lens_amount"] == "10000.00"
        assert wire.form["eye_examination_amount"] == "2000.00"
        assert wire.form["frame_amount"] == "10000.00"
        assert wire.form["new_or_replacement"] == "REPLACEMENT"

    def test_imaging(self) -> None:
        assert build(ImagingDetails("Head pains")).form["clinical_indications"] == "Head pains"


class TestAnUnansweredQuestionIsNotAnAnswer:
    def test_optional_booleans_are_omitted_rather_than_sent_false(self) -> None:
        """On the employment and accident questions, a `false` nobody typed is a claim about liability."""
        wire = build(SurgicalDetails("Pain", "110 BP", "None", "Pale", "None", AnaesthesiaType.LOCAL, WHEN))
        for name in (
            "is_condition_related_to_employment",
            "is_condition_related_to_auto_or_other_accident",
            "is_co_insured",
        ):
            assert name not in wire.form

    def test_an_answered_one_is_sent(self) -> None:
        wire = build(
            SurgicalDetails(
                "Pain",
                "110 BP",
                "None",
                "Pale",
                "None",
                AnaesthesiaType.LOCAL,
                WHEN,
                is_condition_related_to_employment=False,
            )
        )
        assert wire.form["is_condition_related_to_employment"] == "false"


class TestImpossibleCourses:
    @pytest.mark.parametrize("sessions", [0, -1])
    def test_a_course_of_no_sessions_is_refused(self, sessions: int) -> None:
        with pytest.raises(ValueError, match="number_of_sessions_required"):
            RenalDetails(sessions, Money.kes("1"), SessionFrequency.ONCE_A_WEEK, "x", WHEN)
