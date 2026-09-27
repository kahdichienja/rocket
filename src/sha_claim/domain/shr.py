"""The Shared Health Record: the patient's clinical history from *other* facilities.

Distinct from everything else in this SDK, which is about billing a visit. The SHR answers a different
question — what has been done for this person elsewhere — and it is gated by its own consent, separate from
the visit OTP:

    POST /shr/consents              → consent_id + otp_record, and DHA texts the patient
    POST /shr/consents/{id}/verify  → consent_token + visit_id
    GET  /shr/patient-records       → FHIR, with the token in `X-Consent-Token`
    POST /shr/bundles               → push our own encounter back, same header
    POST /shr/visits/{id}/refresh   → a fresh token while the visit is still open
    POST /shr/visits/{id}/close     → after which the token can no longer be refreshed

**Two OTPs, not one.** A member who has already consented to the visit has *not* consented to their records
being read; DHA sends a second code for that. Any screen offering SHR has to account for the patient being
asked twice, and for the common case where they have already left by the time a clinician wants the history.

FHIR itself is deliberately not modelled here. DHA passes the upstream search result through unchanged, and
a partial re-implementation of FHIR in this SDK would be a liability — the bundle is carried as a mapping
and handed to the caller, which already speaks FHIR.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from sha_claim.domain.identifiers import Identifier


class ShrVisitType(StrEnum):
    """`visit_type` on a consent request. DHA's spelling is the two-letter form, not the claim vocabulary."""

    OUTPATIENT = "OP"
    INPATIENT = "IP"


class ShrConsentStatus(StrEnum):
    """Observed on UAT and in the portal examples; matched leniently, so an unknown value is not approved."""

    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    EXPIRED = "Expired"


class ShrConsentTokenValue(Identifier):
    """The per-visit token that authorises reading and writing records.

    A credential in the same sense as the claim's `ConsentToken`: whoever holds it can read a patient's
    history from every facility that has ever treated them. `repr` and `str` redact it; `.value` is
    deliberate, and it belongs server-side, never in a browser.
    """

    def __repr__(self) -> str:
        return f"ShrConsentTokenValue('{self.redacted}')"

    def __str__(self) -> str:
        return self.redacted

    @property
    def redacted(self) -> str:
        v = self.value
        return f"{v[:4]}…{v[-2:]}" if len(v) > 8 else "•" * len(v)


@dataclass(frozen=True, slots=True)
class ShrConsentRequest:
    """Command for `POST /shr/consents`."""

    cr_id: str
    facility_id: str
    """Facility Registry (FR) code of the facility asking — not the SHA facility id."""
    requested_by: str
    """Name or role of the person asking. DHA records it on the consent's audit trail, so it should be a
    real person or desk rather than the application's name."""
    visit_type: ShrVisitType = ShrVisitType.OUTPATIENT

    def as_payload(self) -> dict[str, Any]:
        return {
            "cr_id": self.cr_id,
            "facility_id": self.facility_id,
            "requested_by": self.requested_by,
            "visit_type": self.visit_type.value,
        }


@dataclass(frozen=True, slots=True)
class ShrConsent:
    """What `POST /shr/consents` (and `resend-otp`) answers. The patient now holds an OTP."""

    consent_id: str
    status: str
    otp_record: str
    """Ties the OTP back to the consent it was issued for; `verify` needs it beside the code.

    **A resend issues a new one.** Verifying with the value from the original request after a resend fails,
    which is the mistake DHA's own note calls out.
    """
    visit_type: str = ""
    message: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class ShrVerification:
    """What `verify` answers: the visit is open and the token can be used."""

    consent_token: ShrConsentTokenValue
    visit_id: str
    message: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class ShrConsentState:
    """What `status` answers while the patient works through the OTP."""

    consent_id: str
    status: str
    visit_id: str = ""
    message: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def is_approved(self) -> bool:
        """Approved outright.

        Substring-matched and deliberately strict: anything unrecognised is **not** approved, because the
        cost of reading a pending consent as granted is reading a patient's records without their say-so.
        """
        status = self.status.strip().upper()
        return "APPROV" in status and not any(w in status for w in ("PENDING", "AWAIT", "REQUEST"))

    @property
    def is_pending(self) -> bool:
        return "PEND" in self.status.strip().upper()

    @property
    def is_refused(self) -> bool:
        return any(w in self.status.strip().upper() for w in ("REJECT", "DECLIN", "EXPIR", "CANCEL"))


@dataclass(frozen=True, slots=True)
class ShrVisitClosed:
    """What `close` answers. The token cannot be refreshed after this."""

    visit_id: str
    consent_id: str = ""
    end_date: datetime | None = None
    message: str = ""


@dataclass(frozen=True, slots=True)
class ShrBundleReceipt:
    """What `POST /shr/bundles` answers.

    `mediator_id` is DHA's handle for the submission. The bundle's *contents* are validated upstream and
    asynchronously — a `success` here means DHA accepted the envelope, not that every resource in it was
    stored, so it is not proof the record landed.
    """

    status: str
    message: str = ""
    mediator_id: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def accepted(self) -> bool:
        return self.status.strip().lower() == "success"
