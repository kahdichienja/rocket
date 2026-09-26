"""Unit tests for smart_access domain identifiers and enums."""

import pytest

from smart_access.domain.enums import (
    ClaimStatus,
    CodingStandard,
    CopayType,
    DoctorType,
    HospitalizationType,
    PaymentModifierType,
    PreauthStatus,
    SessionStatus,
    SmartResponseType,
)
from smart_access.domain.identifiers import (
    ClaimCode,
    GlobalId,
    InvoiceNumber,
    LocationCode,
    MedicalAidCode,
    MemberNumber,
    PatientNumber,
    PolicyId,
    PreauthRequestId,
    SchemeCode,
    SessionId,
    SpId,
    VisitNumber,
)


def test_int_identifiers() -> None:
    sid = SessionId.of(12345)
    assert sid == 12345
    assert SessionId.of("67890") == 67890
    assert SpId.of(678) == 678
    assert PolicyId.of("1001065") == 1001065

    with pytest.raises(ValueError, match="SessionId must be an integer"):
        SessionId.of("invalid")


def test_str_identifiers() -> None:
    pnum = PatientNumber.of("PT000001")
    assert pnum == "PT000001"
    assert VisitNumber.of("AC000001") == "AC000001"
    assert MemberNumber.of("8306004943-00") == "8306004943-00"
    assert MedicalAidCode.of("MIC") == "MIC"
    assert SchemeCode.of("SAI") == "SAI"
    assert LocationCode.of("100") == "100"
    assert GlobalId.of("KE0002714501") == "KE0002714501"
    assert InvoiceNumber.of("INV-001") == "INV-001"
    assert ClaimCode.of("CLM-001") == "CLM-001"
    assert PreauthRequestId.of("PR-998811") == "PR-998811"

    with pytest.raises(ValueError, match="PatientNumber cannot be empty"):
        PatientNumber.of("   ")


def test_lenient_enums_fallback() -> None:
    assert SessionStatus("PENDING") == SessionStatus.PENDING
    assert SessionStatus("NONEXISTENT_STATUS") == SessionStatus.UNKNOWN

    assert ClaimStatus("Billed") == ClaimStatus.BILLED
    assert ClaimStatus("SOMETHING_NEW") == ClaimStatus.UNKNOWN
    assert ClaimStatus.BILLED.is_billed is True
    assert ClaimStatus.PENDING.is_billed is False
    assert ClaimStatus.CANCELLED.is_terminal_failure is True
    assert ClaimStatus.REJECTED.is_terminal_failure is True

    assert PaymentModifierType("1") == PaymentModifierType.COPAY_FIXED
    assert PaymentModifierType("5") == PaymentModifierType.NHIF_SHA
    assert PaymentModifierType("99") == PaymentModifierType.UNKNOWN

    assert CopayType("PERCENTAGE") == CopayType.PERCENTAGE
    assert CopayType("WEIRD") == CopayType.UNKNOWN

    assert HospitalizationType("Planned") == HospitalizationType.PLANNED
    assert DoctorType("PRIVATE") == DoctorType.PRIVATE
    assert CodingStandard("ICD10") == CodingStandard.ICD10
    assert PreauthStatus("Approved") == PreauthStatus.APPROVED
    assert SmartResponseType("SUCCESS") == SmartResponseType.SUCCESS
