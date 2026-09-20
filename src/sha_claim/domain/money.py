"""Exact monetary amounts. Floats are rejected on purpose."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Self

_CENTS = Decimal("0.01")


def _is_float(value: object) -> bool:
    return isinstance(value, float)


@dataclass(frozen=True, slots=True, order=False)
class Money:
    amount: Decimal
    currency: str = "KES"

    def __post_init__(self) -> None:
        if _is_float(self.amount):
            raise TypeError("Money does not accept float; pass str, int or Decimal")
        try:
            quantised = Decimal(self.amount).quantize(_CENTS, rounding=ROUND_HALF_UP)
        except InvalidOperation as exc:
            raise ValueError(f"invalid amount {self.amount!r}") from exc
        object.__setattr__(self, "amount", quantised)
        object.__setattr__(self, "currency", self.currency.upper())

    @classmethod
    def kes(cls, amount: str | int | Decimal) -> Self:
        return cls(Decimal(amount) if not isinstance(amount, Decimal) else amount, "KES")

    @classmethod
    def zero(cls, currency: str = "KES") -> Self:
        return cls(Decimal(0), currency)

    @property
    def is_negative(self) -> bool:
        return self.amount < 0

    def __add__(self, other: Money) -> Money:
        self._same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._same_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, quantity: int | Decimal) -> Money:
        if isinstance(quantity, float):
            raise TypeError("multiply Money by int or Decimal, not float")
        return Money(self.amount * Decimal(quantity), self.currency)

    __rmul__ = __mul__

    def __lt__(self, other: Money) -> bool:
        self._same_currency(other)
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        self._same_currency(other)
        return self.amount <= other.amount

    def __gt__(self, other: Money) -> bool:
        return other < self

    def __ge__(self, other: Money) -> bool:
        return other <= self

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:,.2f}"

    def as_wire(self) -> str:
        """Decimal string with two places, the safest representation for `number` fields."""
        return f"{self.amount:.2f}"

    def _same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValueError(f"currency mismatch: {self.currency} vs {other.currency}")
