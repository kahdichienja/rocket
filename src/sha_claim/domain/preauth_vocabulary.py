"""The closed choices a specialised pre-authorisation is written against.

**DHA publishes these twice and the two copies disagree.** The prose guides give human-readable values
("General Anaesthesia", "Stage 1", "Once a month", "Framed"); the Postman collection — which is a runnable
artifact people fire at UAT — sends machine values (`GENERAL`, `STAGE_1`, `ONCE_A_MONTH`, `FRAMES_LENSES`).
They also disagree on a field name: the oncology guide says `number_of_sessions`, Postman sends
`number_of_sessions_required`.

This module takes **Postman's spelling**, on the grounds that a collection someone has actually run beats
prose nobody executes — but it is a judgement, not a fact, and the alternatives are recorded beside each set
so the correction is a one-line edit here rather than a hunt through six forms.

That is the same shape as `prescriptionVocabulary.ts` on the NaCare side, where `patient_instruction` cost
several rejected calls before the accepted values were known. The lesson taken from it: put the guess in one
file, say it is a guess, and keep the rejected alternative next to it.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = [
    "DOCS_SPELLINGS",
    "AnaesthesiaType",
    "CarcinomaStaging",
    "LensPrescription",
    "MetastasisSite",
    "NewOrReplacement",
    "SessionFrequency",
    "TreatmentSetting",
]


class AnaesthesiaType(StrEnum):
    """`type_of_anaesthesia` on a surgical pre-auth."""

    GENERAL = "GENERAL"
    LOCAL = "LOCAL"
    SPINAL = "SPINAL"
    SEDATION = "SEDATION"


class SessionFrequency(StrEnum):
    """`frequency_of_sessions` on a renal pre-auth — how often dialysis runs."""

    TWICE_A_WEEK = "TWICE_A_WEEK"
    ONCE_A_WEEK = "ONCE_A_WEEK"
    ONCE_EVERY_2_WEEKS = "ONCE_EVERY_2_WEEKS"
    ONCE_EVERY_3_WEEKS = "ONCE_EVERY_3_WEEKS"
    ONCE_A_MONTH = "ONCE_A_MONTH"


class CarcinomaStaging(StrEnum):
    """`carcinoma_staging` on an oncology pre-auth."""

    STAGE_1 = "STAGE_1"
    STAGE_2 = "STAGE_2"
    STAGE_3 = "STAGE_3"
    STAGE_4 = "STAGE_4"


class MetastasisSite(StrEnum):
    """`metastases` on an oncology pre-auth. A list: a carcinoma can have spread to more than one site."""

    LUNG = "LUNG"
    BRAIN = "BRAIN"
    LIVER = "LIVER"
    OTHER = "OTHER"


class TreatmentSetting(StrEnum):
    """`treatment_setting` on an oncology pre-auth — where the infusion is given. Also a list."""

    DAY_WARD = "DAY_WARD"
    RECLINING_CHAIR = "RECLINING_CHAIR"
    SIDE_ROOM = "SIDE_ROOM"


class LensPrescription(StrEnum):
    """`lens_prescription` on an optical pre-auth.

    The guide names two options ("Framed", "Contact") and Postman sends a third spelling entirely
    (`FRAMES_LENSES`). Both readings are kept: the guide's pair describes what is dispensed, and Postman's
    value is the one a request has actually carried.
    """

    FRAMES_LENSES = "FRAMES_LENSES"
    FRAMED = "FRAMED"
    CONTACT = "CONTACT"


class NewOrReplacement(StrEnum):
    """`new_or_replacement` on an optical pre-auth."""

    NEW = "NEW"
    REPLACEMENT = "REPLACEMENT"


#: What the prose guides print where this module sends something else.
#:
#: Not used in a payload — it exists so the disagreement is written down in the codebase rather than living
#: in somebody's memory of a web page. When UAT answers, the losing side of each pair is deleted.
DOCS_SPELLINGS: dict[str, dict[str, str]] = {
    "type_of_anaesthesia": {
        "GENERAL": "General Anaesthesia",
        "LOCAL": "Local Anaesthesia",
        "SPINAL": "Spinal Anaesthesia",
        "SEDATION": "Sedation",
    },
    "carcinoma_staging": {
        "STAGE_1": "Stage 1",
        "STAGE_2": "Stage 2",
        "STAGE_3": "Stage 3",
        "STAGE_4": "Stage 4",
    },
    "metastases": {"LUNG": "Lung", "BRAIN": "Brain", "LIVER": "Liver", "OTHER": "Other"},
    "treatment_setting": {
        "DAY_WARD": "Day ward",
        "RECLINING_CHAIR": "Reclining chair",
        "SIDE_ROOM": "Side room",
    },
    "frequency_of_sessions": {
        "TWICE_A_WEEK": "Twice a week",
        "ONCE_A_WEEK": "Once a week",
        "ONCE_EVERY_2_WEEKS": "One time every 2 weeks",
        "ONCE_EVERY_3_WEEKS": "One time every 3 weeks",
        "ONCE_A_MONTH": "One a month",
    },
    "lens_prescription": {"FRAMED": "Framed", "CONTACT": "Contact"},
    "new_or_replacement": {"NEW": "New", "REPLACEMENT": "Replacement"},
}
