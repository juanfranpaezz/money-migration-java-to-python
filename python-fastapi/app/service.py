"""service.py -- the Python port of Spring's OrderTotalService bean.

In Spring this is a ``@Service`` injected into a controller. In FastAPI the idiomatic
equivalent is a plain class provided through ``Depends(...)`` (see api.py). The business
logic -- subtotal of the lines + tax -- is identical to the Java service and goes through
:class:`Money` so the rounding/currency rules live in one place.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .money import Money


@dataclass(frozen=True)
class LineItem:
    """One order line: a unit price (Money) and an integer quantity."""

    unit_price: Money
    quantity: int


class OrderTotalService:
    """Totals an order: subtotal = sum(unit_price * quantity), then + tax."""

    def total(self, lines: list[LineItem], tax_rate: Decimal) -> Money:
        """Total an order.

        subtotal = sum over lines of (unit_price * quantity); tax = subtotal * tax_rate
        (rounded HALF_EVEN to the currency scale); grand total = subtotal + tax. All
        lines must share one currency (Money.add enforces it). ``tax_rate`` is a fraction
        like Decimal('0.21') for 21%.
        """
        if not lines:
            raise ValueError("an order needs at least one line")
        subtotal: Money | None = None
        for line in lines:
            line_total = line.unit_price.multiply(line.quantity)
            subtotal = line_total if subtotal is None else subtotal.add(line_total)
        assert subtotal is not None  # guaranteed by the empty-check above
        tax = subtotal.percentage(tax_rate)
        return subtotal.add(tax)
