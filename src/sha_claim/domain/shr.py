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


class ShrReferralStatus(StrEnum):
    """FHIR `ServiceRequest.status`, which is what a referral's state actually is.

    The vocabulary is FHIR's, not DHA's, and it is a *required* binding — so unlike the consent statuses
    above there is no lenient matching here: an unknown value is a resource that does not conform, and
    passing it through as though it were understood would be worse than showing it raw.
    """

    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on-hold"
    REVOKED = "revoked"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ShrReferralQuery:
    """Query for `GET /shr/ServiceRequest`.

    **This search is not scoped by a consent token**, and that is the whole reason a referral inbox is
    possible. Every other read in this module answers *"what is in this person's record"* and needs the
    patient's say-so; this one answers *"which referrals are addressed to this organisation"*, which is a
    question about the facility's own workload. A receiving desk can therefore see that a patient is coming
    before the patient — and their OTP — has arrived.

    Direction is which field you filter on, and the two are easy to confuse:

        performer:Organization=<us>   → referrals sent **to** us      (our inbox)
        requester:Organization=<us>   → referrals we **raised**       (our outbox)

    The `:Organization` suffix is a FHIR reference-type modifier and part of the parameter name. It lives
    here so that no caller has to remember the colon.
    """

    performer_fr_code: str = ""
    """FR code of the facility the referral is addressed to."""
    requester_fr_code: str = ""
    """FR code of the facility that raised it."""
    status: str = ""
    count: int = 0
    page_token: str = ""

    def __post_init__(self) -> None:
        if not self.performer_fr_code and not self.requester_fr_code:
            # Without a direction this is a search across every referral DHA holds. No caller wants that,
            # and DHA would be within its rights to answer with the lot.
            raise ValueError(
                "a referral query needs performer_fr_code (our inbox) or requester_fr_code (our outbox)"
            )
        if self.count < 0:
            raise ValueError(f"count cannot be negative (got {self.count})")

    def as_params(self) -> dict[str, str]:
        params: dict[str, str] = {}
        if self.performer_fr_code:
            params["performer:Organization"] = self.performer_fr_code
        if self.requester_fr_code:
            params["requester:Organization"] = self.requester_fr_code
        if self.status:
            params["status"] = self.status
        if self.count:
            params["count"] = str(self.count)
        if self.page_token:
            params["page_token"] = self.page_token
        return params


class ShrLabelKind(StrEnum):
    """Which of the two label vocabularies a code belongs to.

    They answer different questions and must not be conflated: confidentiality is *how guarded* a resource
    is, sensitivity is *what kind of thing* it is about. A resource can be `N` (normal) and still carry
    `HIV`.
    """

    CONFIDENTIALITY = "CONFIDENTIALITY"
    SENSITIVITY = "SENSITIVITY"
    UNKNOWN = "UNKNOWN"


CONFIDENTIALITY_SYSTEM = "http://terminology.hl7.org/CodeSystem/v3-Confidentiality"
ACT_CODE_SYSTEM = "http://terminology.hl7.org/CodeSystem/v3-ActCode"


@dataclass(frozen=True, slots=True)
class ShrSecurityLabel:
    """One entry in the catalogue `GET /shr/security-labels` returns.

    These are what `meta.security` on an SHR resource refers to, and the reason to fetch the catalogue at
    all is that the codes are not self-explanatory: `SUD`, `GDIS` and `CRITINN` mean nothing to a desk, and
    a referral screen that prints the bare code has told the clinician nothing while *looking* as though it
    has. `PSY` and `HIV` are the cases that matter — a label a receiving clerk cannot read is a label they
    cannot honour.
    """

    code: str
    display: str = ""
    system: str = ""
    kind: ShrLabelKind = ShrLabelKind.UNKNOWN
    description: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def label(self) -> str:
        """What to show a human. The code itself when DHA gave no display — never a guess at its meaning."""
        return self.display or self.code

    @property
    def is_restricted(self) -> bool:
        """`R` on the HL7 confidentiality scale: this resource is not for general viewing."""
        return self.kind is ShrLabelKind.CONFIDENTIALITY and self.code.strip().upper() == "R"


def label_kind_for(system: str, code: str) -> ShrLabelKind:
    """Which vocabulary a label came from, by system first and code second.

    The system URI is authoritative. The code list is the fallback for a catalogue entry that omits the
    system, and it is deliberately not exhaustive — an unrecognised code is reported as `UNKNOWN` rather
    than filed under a guess, because mistaking a sensitivity code for a confidentiality one would
    misreport how guarded a record is.
    """
    system = system.strip()
    if system == CONFIDENTIALITY_SYSTEM:
        return ShrLabelKind.CONFIDENTIALITY
    if system == ACT_CODE_SYSTEM:
        return ShrLabelKind.SENSITIVITY
    code = code.strip().upper()
    if code in {"N", "R", "U", "L", "M", "V"}:
        return ShrLabelKind.CONFIDENTIALITY
    if code in {"HIV", "PSY", "SUD", "STD", "SEX", "PRG", "GDIS", "CRITINN", "FININF", "ETH", "DEMO"}:
        return ShrLabelKind.SENSITIVITY
    return ShrLabelKind.UNKNOWN
