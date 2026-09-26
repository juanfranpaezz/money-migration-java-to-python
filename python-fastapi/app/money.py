"""money.py -- the Python/FastAPI port of the Java ``Money`` value-object.

This is an IDIOMATIC migration, not a line-by-line port. The mapping:

    Java                          Python
    --------------------------    ------------------------------------------
    BigDecimal                    decimal.Decimal       (NEVER float)
    RoundingMode.HALF_EVEN        decimal.ROUND_HALF_EVEN
    Currency.getInstance(code)    a small CURRENCIES table (code -> minor units)
    immutable final class         frozen dataclass
    IllegalArgumentException      ValueError

The subtle traps the migration has to get right (see the README):

  1. float vs Decimal. ``0.1 + 0.2 == 0.30000000000000004`` in binary float; that error
     accrues into balances. Money MUST keep amounts as Decimal and MUST reject a float
     constructed amount (``Decimal(0.1)`` already carries the float error, so we require a
     str/Decimal/int input, mirroring ``new BigDecimal("0.10")`` not ``new BigDecimal(0.10)``).
  2. Rounding mode. Java's monetary default is HALF_EVEN ("bankers' rounding"); Python's
     Decimal default context is ROUND_HALF_EVEN too, but ``round()`` / float formatting are
     NOT -- so we quantize explicitly with ROUND_HALF_EVEN, never ``round()``.
  3. Currency scale. USD -> 2 minor units, JPY -> 0. The scale is a property of the
     currency, not a hard-coded 2.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Union

# ISO-4217 minor-unit digits for the currencies this demo supports.
# (The Java side reads this from java.util.Currency; we keep a tiny explicit table.)
CURRENCIES: dict[str, int] = {
    "USD": 2,
    "EUR": 2,
    "GBP": 2,
    "JPY": 0,  # the trap currency: no minor unit
}

AmountIn = Union[str, int, Decimal]


def minor_units(currency: str) -> int:
    try:
        return CURRENCIES[currency]
    except KeyError:
        raise ValueError(f"unsupported currency: {currency!r}") from None


def _quantum(currency: str) -> Decimal:
    """The Decimal step for one minor unit, e.g. Decimal('0.01') for USD, Decimal('1') for JPY."""
    digits = minor_units(currency)
    return Decimal(1).scaleb(-digits)  # 10**-digits as an exact Decimal


@dataclass(frozen=True)
class Money:
    """Immutable (amount, currency) pair with safe, currency-checked arithmetic.

    ``amount`` is always a Decimal normalised to the currency's minor-unit scale using
    ROUND_HALF_EVEN. Construct via :meth:`of`, not the dataclass ctor, so the amount is
    validated and quantised.
    """

    amount: Decimal
    currency: str

    @staticmethod
    def of(amount: AmountIn, currency: str) -> "Money":
        """Build a Money from a decimal amount and an ISO-4217 currency code.

        The amount is quantised to the currency's minor units with ROUND_HALF_EVEN.
        A ``float`` amount is REJECTED (it already carries binary rounding error); pass a
        str like ``"0.10"`` or a Decimal, mirroring ``new BigDecimal("0.10")`` in Java.
        """
        if isinstance(amount, float):
            raise TypeError(
                "refusing a float amount (binary rounding error); pass a str or Decimal"
            )
        currency = currency.upper()
        q = _quantum(currency)
        value = Decimal(amount) if not isinstance(amount, Decimal) else amount
        scaled = value.quantize(q, rounding=ROUND_HALF_EVEN)
        return Money(scaled, currency)

    def _require_same_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise ValueError(f"currency mismatch: {self.currency} vs {other.currency}")

    def add(self, other: "Money") -> "Money":
        self._require_same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def subtract(self, other: "Money") -> "Money":
        self._require_same_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def multiply(self, factor: int) -> "Money":
        """Multiply by an integer quantity (unit price x N items). Exact, no rounding."""
        if not isinstance(factor, int) or isinstance(factor, bool):
            raise TypeError("multiply expects an int quantity")
        return Money(self.amount * Decimal(factor), self.currency)

    def percentage(self, rate: AmountIn) -> "Money":
        """Apply a rate (e.g. Decimal('0.21') for 21% tax) and re-quantise HALF_EVEN."""
        if isinstance(rate, float):
            raise TypeError("refusing a float rate; pass a str or Decimal")
        r = Decimal(rate) if not isinstance(rate, Decimal) else rate
        raw = self.amount * r
        scaled = raw.quantize(_quantum(self.currency), rounding=ROUND_HALF_EVEN)
        return Money(scaled, self.currency)

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"
