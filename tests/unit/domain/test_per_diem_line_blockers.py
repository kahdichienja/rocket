"""The per-diem rules from DHA's SHIF IP scenario, read off a claim snapshot.

https://hie-docs.dha.go.ke/docs/scenarios/scenario-1-shif-ip-per-diem — DHA writes the per-diem line
itself, allows one active per-diem intervention, and rolls the whole request back on an over-tariff price.
"""

import asyncio
from decimal import Decimal

import pytest

from sha_claim.domain.claim import ClaimIntervention, ClaimLine, Invoice, VirtualClaim
from sha_claim.domain.codes import InterventionCode
from sha_claim.domain.enums import ClaimWorkflowState, PaymentMechanism, ServiceType
from sha_claim.domain.identifiers import ConsentToken, LineGuid
from sha_claim.domain.money import Money
from sha_claim.errors import RequestValidationError
from sha_claim.session import ClaimSession

ICU = InterventionCode("SHA-03-001")
HDU = InterventionCode("SHA-03-002")
THEATRE = InterventionCode("SHA-19-119")


def bed(
    code: InterventionCode = ICU,
    *,
    tariff: str | None = "9000",
    days: int = 3,
    state: str = "ACTIVE",
) -> ClaimIntervention:
    return ClaimIntervention(
        code,
        "ICU bed",
        PaymentMechanism.PER_DIEM,
        False,
        False,
        state,
        accrued_per_diem_days=days,
        keph_level_tariff=Money.kes(tariff) if tariff is not None else None,
    )


def surgical(code: InterventionCode = THEATRE) -> ClaimIntervention:
    return ClaimIntervention(code, "Laparotomy", PaymentMechanism.FEE_FOR_SERVICE, False, False, "ACTIVE")


def line(code: InterventionCode, amount: str = "9000", *, active: bool = True) -> ClaimLine:
    return ClaimLine(
        LineGuid("L"),
        code,
        "",
        "",
        Decimal(1),
        Money.kes(amount),
        Money.kes(amount),
        Money.kes(amount),
        is_active=active,
    )


def claim(*, lines: tuple[ClaimLine, ...] = (), **kw) -> VirtualClaim:  # type: ignore[no-untyped-def]
    base = dict(
        consent_token=ConsentToken("CR1-TOKEN12345"),
        guid=None,
        claim_id=1,
        workflow_state=ClaimWorkflowState("OPEN"),
        claim_auth_status="",
        service_type=None,
        patient_name="",
        member_number="",
        payer_name="",
        scheme_name="",
        currency="KES",
        total_amount=Money.kes(1000),
        net_amount=Money.kes(1000),
    )
    if lines:
        kw["invoices"] = (Invoice("i", None, "", "", "", Money.kes(1000), Money.kes(1000), lines=lines),)
    return VirtualClaim(**{**base, **kw})


def codes(blockers: tuple[object, ...]) -> list[str]:
    return [b.code for b in blockers]  # type: ignore[attr-defined]


# ── active_per_diem ──


def test_active_per_diem_finds_the_bed() -> None:
    assert claim(interventions=(surgical(), bed())).active_per_diem is not None
    assert claim(interventions=(surgical(), bed())).active_per_diem.code == ICU  # type: ignore[union-attr]


def test_active_per_diem_ignores_a_retired_bed_and_fee_for_service() -> None:
    assert claim(interventions=(bed(state="RETIRED"),)).active_per_diem is None
    assert claim(interventions=(surgical(),)).active_per_diem is None
    assert claim().active_per_diem is None


# ── line_blockers ──


def test_fee_for_service_lines_are_never_blocked() -> None:
    c = claim(interventions=(surgical(),), lines=(line(THEATRE, "90000"),))
    assert c.line_blockers(THEATRE, Money.kes("90000")) == ()


def test_unknown_intervention_is_left_to_the_server() -> None:
    assert claim(interventions=(bed(),)).line_blockers(HDU, Money.kes("1")) == ()


def test_first_line_at_the_tariff_is_allowed() -> None:
    assert claim(interventions=(bed(),)).line_blockers(ICU, Money.kes("9000")) == ()


def test_price_above_the_keph_tariff_is_blocked() -> None:
    blockers = claim(interventions=(bed(),)).line_blockers(ICU, Money.kes("12000"))
    assert codes(blockers) == ["LINE_ABOVE_KEPH_TARIFF"]
    assert blockers[0].intervention == ICU


def test_further_charges_are_allowed_once_dha_holds_the_accrued_line() -> None:
    """DHA writing the per-diem line makes ours unnecessary, not forbidden.

    Read the other way, a real inpatient bill could send nothing at all: every charge defaults to the
    visit's one active intervention, so the whole stay was blocked as a duplicate and fell to the patient.
    """
    c = claim(interventions=(bed(tariff="28000"),), lines=(line(ICU, "28000"),))
    for amount in ("20000", "6000", "3000", "1500", "1000"):
        assert c.line_blockers(ICU, Money.kes(amount)) == ()


def test_the_tariff_ceiling_still_applies_with_a_line_present() -> None:
    c = claim(interventions=(bed(),), lines=(line(ICU),))
    assert codes(c.line_blockers(ICU, Money.kes("12000"))) == ["LINE_ABOVE_KEPH_TARIFF"]


def test_no_published_rate_invents_no_ceiling() -> None:
    """Every UAT facility today: SHA publishes no KEPH rate, so there is nothing to compare against."""
    assert claim(interventions=(bed(tariff="0"),)).line_blockers(ICU, Money.kes("50000")) == ()
    assert claim(interventions=(bed(tariff=None),)).line_blockers(ICU, Money.kes("50000")) == ()


def test_a_missing_unit_price_has_nothing_to_check() -> None:
    c = claim(interventions=(bed(),), lines=(line(ICU),))
    assert c.line_blockers(ICU) == ()
    assert claim(interventions=(bed(),)).line_blockers(ICU) == ()


# ── lines_for ──


def test_lines_for_takes_only_active_lines_of_that_intervention() -> None:
    c = claim(
        interventions=(bed(), surgical()),
        lines=(line(ICU), line(ICU, active=False), line(THEATRE)),
    )
    assert len(c.lines_for(ICU)) == 1
    assert len(c.lines_for(THEATRE)) == 1


# ── submission_blockers ──


def test_two_active_per_diem_interventions_block_submission() -> None:
    c = claim(
        interventions=(bed(ICU), bed(HDU)),
        lines=(line(ICU),),
    )
    assert "MULTIPLE_ACTIVE_PER_DIEM" in codes(c.submission_blockers())


def test_one_per_diem_beside_a_surgical_intervention_is_fine() -> None:
    c = claim(interventions=(bed(ICU), surgical()), lines=(line(ICU),))
    assert "MULTIPLE_ACTIVE_PER_DIEM" not in codes(c.submission_blockers())


def test_a_retired_second_bed_does_not_block() -> None:
    c = claim(interventions=(bed(ICU), bed(HDU, state="RETIRED")), lines=(line(ICU),))
    assert "MULTIPLE_ACTIVE_PER_DIEM" not in codes(c.submission_blockers())


# ── switch_intervention's scheme-family check ──


def test_switch_across_scheme_families_is_refused_before_the_call() -> None:
    """DHA's own refusal names the funds in full; the prefixes decide it, so no call is needed."""
    session = ClaimSession.__new__(ClaimSession)
    session.consent_token = ConsentToken("CR1-TOKEN12345")

    with pytest.raises(RequestValidationError) as caught:
        asyncio.run(session.switch_intervention("SHA-03-001", "PMF-03-002", retain_bill_items=False))
    assert "will not combine" in str(caught.value)


# ── submit refuses the service type DHA refuses ──


def _session_with(service_type: ServiceType | None) -> ClaimSession:
    session = ClaimSession.__new__(ClaimSession)
    session.consent_token = ConsentToken("CR1-TOKEN12345")
    session.claim = claim(service_type=service_type)
    return session


def test_submit_refuses_an_inpatient_claim_before_calling() -> None:
    """DHA: "claim of service type INPATIENT cannot be submitted, use appropriate route for the claim"."""
    with pytest.raises(RequestValidationError) as caught:
        asyncio.run(_session_with(ServiceType.INPATIENT).submit("INV-1"))
    assert "discharge()" in str(caught.value)


def test_submit_leaves_every_other_service_type_to_the_server() -> None:
    """No snapshot, or any other type, is not this check's business — only INPATIENT is refused here."""
    for service_type in (ServiceType.OUTPATIENT, ServiceType.CAPITATION, ServiceType.EMERGENCY, None):
        session = _session_with(service_type)
        with pytest.raises(AttributeError):
            # Falls through the guard and reaches the gateway, which this bare session does not have.
            asyncio.run(session.submit("INV-1"))
