from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from sha_claim.domain.money import Money

amounts = st.decimals(min_value=-(10**9), max_value=10**9, places=2, allow_nan=False, allow_infinity=False)


@given(amounts, amounts)
def test_addition_is_exact_and_commutative(a: Decimal, b: Decimal) -> None:
    assert Money(a) + Money(b) == Money(b) + Money(a) == Money(a + b)


@given(amounts, st.integers(min_value=0, max_value=1000))
def test_multiplication_by_quantity(a: Decimal, q: int) -> None:
    assert (Money(a) * q).amount == (a * q).quantize(Decimal("0.01"))


def test_rejects_float() -> None:
    with pytest.raises(TypeError):
        Money(1.5)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        Money.kes("1") * 1.5  # type: ignore[operator]


def test_quantises_half_up() -> None:
    assert Money.kes("1.005").amount == Decimal("1.01")


def test_currency_mismatch() -> None:
    with pytest.raises(ValueError, match="currency"):
        Money.kes(1) + Money(Decimal(1), "USD")


def test_wire_and_display_formats() -> None:
    m = Money.kes("1500")
    assert m.as_wire() == "1500.00"
    assert str(m) == "KES 1,500.00"
    assert Money.kes("-1").is_negative
    assert Money.kes(2) > Money.kes(1) >= Money.zero()
