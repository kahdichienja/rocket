from datetime import date
from decimal import Decimal

import pytest

from sha_claim.domain.claim import ClaimIntervention, LineEdit, NewClaimLine, VirtualClaim
from sha_claim.domain.codes import Icd11Code, InterventionCode
from sha_claim.domain.enums import ClaimWorkflowState, PaymentMechanism
from sha_claim.domain.identifiers import ConsentToken, LineGuid
from sha_claim.domain.money import Money

CODE = InterventionCode("SHA-12-001")


def test_new_line_total_and_invariants() -> None:
    line = NewClaimLine(
        CODE, Money.kes("150.50"), 3, charge_date=date(2026, 9, 20), diagnoses=(Icd11Code("1A00"),)
    )
    assert line.total == Money.kes("451.50")
    with pytest.raises(ValueError, match="quantity"):
        NewClaimLine(CODE, Money.kes(1), 0)
    with pytest.raises(ValueError, match="unit_price"):
        NewClaimLine(CODE, Money.kes(-1), 1)
    assert NewClaimLine(CODE, Money.kes(1), Decimal("0.5")).total == Money.kes("0.50")


def test_line_edit_requires_a_change() -> None:
    with pytest.raises(ValueError, match="at least one"):
        LineEdit(LineGuid("g"))
    with pytest.raises(ValueError, match="quantity"):
        LineEdit(LineGuid("g"), quantity=0)
    assert LineEdit(LineGuid("g"), unit_price=Money.kes(5)).quantity is None


def intervention(code: str, needs: bool, exists: bool) -> ClaimIntervention:
    return ClaimIntervention(
        InterventionCode(code), code, PaymentMechanism.CAPITATION, needs, exists, "ACTIVE"
    )


def test_virtual_claim_derived_views() -> None:
    claim = VirtualClaim(
        ConsentToken("abcdefghijkl"),
        None,
        1,
        ClaimWorkflowState.DRAFT,
        "",
        None,
        "",
        "",
        "",
        "",
        "KES",
        None,
        None,
        interventions=(
            intervention("SHA-1", True, False),
            intervention("SHA-2", True, True),
            intervention("SHA-3", False, False),
        ),
    )
    assert [i.code.value for i in claim.preauth_outstanding] == ["SHA-1"]
    assert claim.diagnoses_for(InterventionCode("SHA-1")) == ()
