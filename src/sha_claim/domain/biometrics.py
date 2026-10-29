"""Fingerprint consent for a minor: enrolment, verification, and the match that proves consent.

**Why this exists separately from `BiometricContext` and the eKYC path.** Adult consent runs through SHA's
eKYC: it resolves the member from the CR number, reads the *national ID* its own Client Registry holds, and
forwards that to its identity provider as `subject_id_number`. A minor has no national ID, so there is
nothing to forward and the capture is refused before it starts — see `biometric_eligibility` on the NaCare
side for the controlled test that established the nine-character limit. The fingerprint flow is not an
alternative for children, it is the only one.

**Three calls, and a different shape of answer from anything else in this SDK.** Enrolment, verification and
match are all asynchronous: each returns `202` with a job or match id and `next_action: await_callback`.
There is no verdict in the response, and DHA says plainly that there is nothing to poll — the outcome is
delivered to the facility's registered callback endpoint. One endpoint, `GET /biometrics/matches/{id}`, is a
*reconciliation read* for a caller that missed its callback, and DHA says it should not be called in a loop.

Only `GET /biometrics/enrollment-status` answers immediately, and it touches no hardware at all. It is
therefore the call a screen is built around: it says which of three situations a child is in — no prints,
prints awaiting confirmation, or a confirmed finger ready to consent — before anybody is sent to a scanner.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from sha_claim.domain.consent import MatchId
from sha_claim.domain.enums import LenientStrEnum
from sha_claim.domain.identifiers import Identifier, PatientId

#: Finger positions, as DHA numbers them. Enrolment and verification name one; a match may leave it at
#: `ANY_FINGER`.
FIRST_FINGER = 1
LAST_FINGER = 10

#: `position` on a match request. DHA: "Defaults to 0, which for a minor means any enrolled finger."
ANY_FINGER = 0


@dataclass(frozen=True, slots=True)
class JobId(Identifier):
    """Identifies an enrolment or verification capture. Its outcome arrives only by callback."""


@dataclass(frozen=True, slots=True)
class MatchRequestId(Identifier):
    """Identifies a match attempt.

    Distinct from `MatchId` in `domain.consent`, deliberately. This one names the *attempt*; `MatchId` is
    the proof presented to `/claims/visit`, and it only exists once an attempt has come back `matched`.
    Giving them one type would let an unresolved attempt be passed as consent, which is the single worst
    mistake available in this flow.
    """


class MatchStatus(LenientStrEnum):
    """State of a match attempt. Documented: `pending`, `matched`, `no_match`, `failed`."""

    PENDING = "pending"
    MATCHED = "matched"
    NO_MATCH = "no_match"
    FAILED = "failed"


def finger_position(position: int, *, allow_any: bool = False) -> int:
    """Validate a finger position before it leaves, rather than reading DHA's `400` back.

    `allow_any` admits `0` — meaningful only on a match, where it means "any enrolled finger". Enrolment and
    verification are per finger and must name one, so `0` there is a caller error, not a wildcard.
    """
    if allow_any and position == ANY_FINGER:
        return ANY_FINGER
    if not FIRST_FINGER <= position <= LAST_FINGER:
        allowed = f"{FIRST_FINGER} to {LAST_FINGER}" + (f" (or {ANY_FINGER} for any)" if allow_any else "")
        raise ValueError(f"finger position must be {allowed}, got {position}")
    return position


@dataclass(frozen=True, slots=True)
class CaptureStation:
    """The workstation, reader and operator a capture is performed at.

    **Not `BiometricContext`, and the field names are why.** eKYC spells it `work_station_id`; the minors
    endpoints spell it `workstation_id`. Reusing one payload builder for both would mean one of the two
    flows silently sending a field the server ignores, and then a `400` naming a field the caller believes
    it sent. They are assembled separately and each spells it the way its own endpoint does.

    `device_id` has no adult equivalent: eKYC runs in a browser, while this drives a physical reader
    attached to this desk.
    """

    workstation_id: str
    device_id: str
    agent_id: str

    def __post_init__(self) -> None:
        for name in ("workstation_id", "device_id", "agent_id"):
            if not str(getattr(self, name)).strip():
                # DHA rejects a missing one with a 400 naming the field "rather than being dispatched and
                # failing at the workstation with an opaque device error". Same intent, one round trip earlier.
                raise ValueError(f"a minors fingerprint capture needs {name}")
        for name in ("workstation_id", "device_id", "agent_id"):
            object.__setattr__(self, name, str(getattr(self, name)).strip())

    def as_payload(self) -> dict[str, Any]:
        return {
            "workstation_id": self.workstation_id,
            "device_id": self.device_id,
            "agent_id": self.agent_id,
        }


@dataclass(frozen=True, slots=True)
class CaptureJob:
    """`202` from an enrolment or verification capture. Carries no outcome — by design."""

    job_id: JobId | None
    next_action: str = ""
    message: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def awaits_callback(self) -> bool:
        """DHA sets `next_action: await_callback`. Absent, we still assume a callback — the endpoints are
        documented as asynchronous, and treating a missing hint as "answered already" would read a
        dispatched capture as a finished one."""
        return self.next_action.strip().lower() in ("", "await_callback")


@dataclass(frozen=True, slots=True)
class MatchAttempt:
    """`202` from `POST /biometrics/matches` — a dispatched attempt, not a verdict."""

    match_id: MatchRequestId | None
    next_action: str = ""
    message: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def awaits_callback(self) -> bool:
        return self.next_action.strip().lower() in ("", "await_callback")


@dataclass(frozen=True, slots=True)
class MatchResult:
    """The state of a match attempt, from the reconciliation read.

    `is_matched` is the only question worth asking of it, and it is deliberately narrow.
    """

    match_id: MatchRequestId | None
    status: MatchStatus | None
    error_code: str = ""
    message: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def is_matched(self) -> bool:
        """**Only** `matched` authorizes. Anything unrecognised is not consent.

        The inverse of the bug fixed in 0.1.49, and the reason it is written as an equality rather than a
        "not pending" test. There, an unrecognised authorization status silently meant *keep waiting*, and
        a discharge hung. Here the silent meaning of an unrecognised status must be *this is not consent* —
        a hung capture is an inconvenience, a capture wrongly read as proof is a child treated and billed on
        consent nobody gave.
        """
        return self.status == MatchStatus.MATCHED

    @property
    def is_terminal(self) -> bool:
        """`no_match` and `failed` are terminal and need a fresh capture — a retry of the *read* will never
        change them. `pending` is not terminal; an unknown status is treated as not terminal, so the caller
        keeps the attempt open rather than discarding one DHA may still resolve."""
        return self.status in (MatchStatus.NO_MATCH, MatchStatus.FAILED)

    @property
    def deadline_exceeded(self) -> bool:
        """The capture window closed with no result. DHA names this one explicitly, and it is the failure a
        desk can actually act on: the child was never at the reader in time."""
        return self.error_code.strip().lower() == "deadline_exceeded"

    def proof(self) -> MatchId:
        """This attempt as consent proof for `open_visit`.

        Raises unless the attempt matched, so a pending or failed attempt cannot be handed to
        `/claims/visit` by a caller that forgot to check.
        """
        if not self.is_matched or self.match_id is None:
            state = self.status.value if self.status else "unknown"
            raise ValueError(f"match is {state}, not matched — it cannot prove consent")
        return MatchId(self.match_id.value)


@dataclass(frozen=True, slots=True)
class EnrollmentStatus:
    """Which of a beneficiary's fingers are stored, and which are usable for consent.

    The distinction is the whole value of this type. A stored print is **not** usable until a second capture
    has confirmed it — "the print is stored but not yet usable for consent" — so a child can be enrolled and
    still unable to consent, which is a state a screen has to be able to name.
    """

    beneficiary: PatientId | None
    verified: tuple[int, ...] = ()
    non_verified: tuple[int, ...] = ()
    total: int = 0
    state: str = ""
    """DHA's own word: `fully_enrolled`, `partially_enrolled`, or empty when nothing is stored."""
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def can_consent(self) -> bool:
        """A match can be requested. Any verified finger will satisfy one."""
        return bool(self.verified)

    @property
    def needs_enrollment(self) -> bool:
        """Nothing stored at all — the child has never been to a reader."""
        return self.total == 0 and not self.verified and not self.non_verified

    @property
    def needs_verification(self) -> bool:
        """Prints are stored but none is confirmed: the second capture was never done, or never succeeded.

        Narrower than "has non-verified fingers" on purpose. A child with one confirmed finger and one
        half-done finger can consent today, and sending that desk to finish an enrolment instead of scanning
        would hold up a visit for housekeeping.
        """
        return not self.verified and bool(self.non_verified)

    @property
    def resumable_positions(self) -> tuple[int, ...]:
        """Where an interrupted enrolment left off — verify these rather than enrolling a fresh finger."""
        return self.non_verified
