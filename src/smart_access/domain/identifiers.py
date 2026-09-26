"""Strongly-typed domain identifiers for Smart Access entities."""

from __future__ import annotations

from typing import Any, Self


class _StrId(str):
    """Base for string-backed value identifiers."""

    @classmethod
    def of(cls, value: Self | str | Any) -> Self:
        if isinstance(value, cls):
            return value
        s = str(value).strip()
        if not s:
            raise ValueError(f"{cls.__name__} cannot be empty")
        return cls(s)


class _IntId(int):
    """Base for integer-backed value identifiers."""

    @classmethod
    def of(cls, value: Self | int | str | Any) -> Self:
        if isinstance(value, cls):
            return value
        try:
            val = int(value)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"{cls.__name__} must be an integer, got {value!r}") from exc
        return cls(val)


class SessionId(_IntId):
    """Unique ID of an active or pending biometric card session on SmartLink."""


class SpId(_IntId):
    """Smart Provider ID (service provider identifier) under which the claim/pool is billed."""


class PolicyId(_IntId):
    """Scheme policy identifier."""


class PatientNumber(_StrId):
    """Patient identifier / Medical Record Number (MRN) in the provider HMIS."""


class VisitNumber(_StrId):
    """Encounter / visit identifier in the provider HMIS (e.g. AC000001)."""


class MemberNumber(_StrId):
    """Insurance membership identifier (e.g. 8306004943-00)."""


class MedicalAidCode(_StrId):
    """Insurance payer code (e.g. MIC)."""


class SchemeCode(_StrId):
    """Scheme / Corporate code (e.g. SAI, S002)."""


class LocationCode(_StrId):
    """Smart terminal/billing location code for the provider facility (e.g. 100, 126)."""


class GlobalId(_StrId):
    """Unique card global identifier (e.g. KE0002714501)."""


class CardSerialNumber(_StrId):
    """Smart card physical serial number (e.g. CK0000014590001)."""


class InvoiceNumber(_StrId):
    """Human-readable invoice identifier (e.g. INV-00000001)."""


class ClaimCode(_StrId):
    """Provider claim code tracking this billing submission."""


class PreauthRequestId(_StrId):
    """Pre-authorization reference code (e.g. PR-998811)."""
