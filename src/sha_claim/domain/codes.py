"""Clinical and administrative code systems used by SHA."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from sha_claim.domain.identifiers import Identifier

# ICD-11 stem codes ("1A00", "BA00.1", "XN5Y") and ICD-10 ("J18.9") share this shape.
_ICD_PATTERN = re.compile(r"^[0-9A-Z][0-9A-Z]{1,3}(\.[0-9A-Z]{1,4})?$")


@dataclass(frozen=True, slots=True)
class Icd11Code(Identifier):
    """Diagnosis code as sent in `icd_code`. Normalised to upper case."""

    def __post_init__(self) -> None:
        Identifier.__post_init__(
            self
        )  # explicit: zero-arg super() breaks in slots=True dataclasses before Python 3.14
        code = self.value.upper()
        if not _ICD_PATTERN.match(code):
            raise ValueError(f"{code!r} is not a valid ICD code")
        object.__setattr__(self, "value", code)


@dataclass(frozen=True, slots=True)
class InterventionCode(Identifier):
    """SHA benefit-package intervention code (the unit of authorisation, billing and preauth)."""

    def __post_init__(self) -> None:
        Identifier.__post_init__(
            self
        )  # explicit: zero-arg super() breaks in slots=True dataclasses before Python 3.14
        object.__setattr__(self, "value", self.value.upper())


@dataclass(frozen=True, slots=True)
class SchemeCode(Identifier):
    """Payer scheme code (optional on billing lines)."""


@dataclass(frozen=True, slots=True)
class ProtocolCode(Identifier):
    """Emergency treatment protocol code."""


class RegulationBody(StrEnum):
    """Professional regulator that issued a practitioner's registration."""

    KMPDC = "KMPDC"
    COC = "COC"
    NCK = "NCK"


class DocumentType(StrEnum):
    """Allowed `document_type` values for claim attachments."""

    BIO_DETAILS = "BIO_DETAILS"
    BIRTH_NOTIFICATION = "BIRTH_NOTIFICATION"
    CARE_PLAN = "CARE_PLAN"
    CASE_NOTE = "CASE_NOTE"
    CASE_SUMMARY = "CASE_SUMMARY"
    CERTIFIED_BURIAL_PERMIT = "CERTIFIED_BURIAL_PERMIT"
    CERTIFIED_COPY_OF_DECEASED_ID = "CERTIFIED_COPY_OF_DECEASED_ID"
    CLAIM_FORM = "CLAIM_FORM"
    COVER_LETTER_FROM_EMPLOYER = "COVER_LETTER_FROM_EMPLOYER"
    CRITICAL_CARE_UNIT_CASE = "CRITICAL_CARE_UNIT_CASE"
    CT_SCAN = "CT_SCAN"
    DEATH_NOTICE = "DEATH_NOTICE"
    DIALYSIS_CHART = "DIALYSIS_CHART"
    DISCHARGE_SUMMARY = "DISCHARGE_SUMMARY"
    ENTRY_EXIT_VISA_STAMP = "ENTRY_EXIT_VISA_STAMP"
    FINAL_BILL = "FINAL_BILL"
    IMAGING_ORDER = "IMAGING_ORDER"
    IMAGING_REPORT = "IMAGING_REPORT"
    INVOICE = "INVOICE"
    LAB_ORDER = "LAB_ORDER"
    LAB_RESULTS = "LAB_RESULTS"
    MAGNETIC_RESONANCE_IMAGING = "MAGNETIC_RESONANCE_IMAGING"
    MEDICAL_REPORT = "MEDICAL_REPORT"
    OTHER = "OTHER"
    POST_SERVICE_IMAGING_REPORT = "POST_SERVICE_IMAGING_REPORT"
    PRE_SERVICE_IMAGING_REPORT = "PRE_SERVICE_IMAGING_REPORT"
    PREAUTH_FORM = "PREAUTH_FORM"
    PRESCRIPTION = "PRESCRIPTION"
    REQUEST_FORM_BY_RELEVANT_CONSULTANT = "REQUEST_FORM_BY_RELEVANT_CONSULTANT"
    RHESUS_FACTOR = "RHESUS_FACTOR"
    THEATRE_NOTES = "THEATRE_NOTES"
