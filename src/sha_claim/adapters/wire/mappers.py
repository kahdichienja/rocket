"""Wire models → domain read models. The only place that knows both vocabularies."""

from __future__ import annotations

from sha_claim.adapters.wire.parsing import parse_date
from sha_claim.adapters.wire.schemas.eligibility import CoverageWire, EligibilityWire, SchemeWire
from sha_claim.domain.eligibility import Coverage, DateRange, Eligibility, Scheme
from sha_claim.domain.enums import CoverageStatus, EligibilityStatus
from sha_claim.domain.identifiers import PatientId


def to_eligibility(w: EligibilityWire) -> Eligibility:
    return Eligibility(
        patient_id=PatientId(w.member_cr_number) if w.member_cr_number.strip() else None,
        full_name=w.full_name,
        status=EligibilityStatus.parse(w.status_code),
        status_description=w.status_desc,
        schemes=tuple(_to_scheme(s) for s in w.schemes),
        date_of_birth=parse_date(w.date_of_birth),
        gender=w.gender,
        age=w.age,
        is_alive=w.is_alive,
        whitelisted_for_otp=w.whitelisted_for_otp,
        facility_biometrics_enforced=w.facility_biometrics_enforced,
        extra=w.unmodelled(),
    )


def _to_scheme(s: SchemeWire) -> Scheme:
    return Scheme(
        name=s.scheme_name,
        scheme_id=s.scheme_id,
        member_type=s.member_type,
        policy_number=s.policy.number,
        policy_period=DateRange(parse_date(s.policy.start_date), parse_date(s.policy.end_date)),
        coverage=_to_coverage(s.coverage),
    )


def _to_coverage(c: CoverageWire) -> Coverage:
    return Coverage(
        status=CoverageStatus.parse(c.status),
        message=c.message,
        reason=c.reason,
        period=DateRange(parse_date(c.start_date), parse_date(c.end_date)),
    )
