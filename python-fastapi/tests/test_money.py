"""test_money.py -- parity tests: the Python port must reproduce the Java reference.

Each expected value here was produced by running the Java Demo (java-spring/.../Demo.java)
and is reproduced in the README. The point is number-for-number parity AND the traps.
Run:  py -m pytest -q   (from python-fastapi/), or  py run_demo.py  for the plain demo.
"""
from decimal import Decimal

import pytest

from app.money import Money
from app.service import LineItem, OrderTotalService


def test_no_float_drift_on_addition():
    # The headline trap: 0.10 + 0.20. Float gives 0.30000000000000004; Money gives exactly 0.30.
    total = Money.of("0.10", "USD").add(Money.of("0.20", "USD"))
    assert total.amount == Decimal("0.30")
    assert str(total) == "0.30 USD"
    # And prove the naive float path really is wrong (so the test isn't vacuous):
    assert 0.10 + 0.20 != 0.30


def test_bankers_rounding_half_even():
    # 2.005 at 2dp HALF_EVEN rounds to the EVEN neighbour 2.00, not 2.01.
    assert Money.of("2.005", "USD").amount == Decimal("2.00")
    # 2.015 -> 2.02 (even), 2.025 -> 2.02 (even). Bankers' rounding, both directions.
    assert Money.of("2.015", "USD").amount == Decimal("2.02")
    assert Money.of("2.025", "USD").amount == Decimal("2.02")


def test_currency_scale_jpy_has_no_minor_unit():
    assert Money.of("199.7", "JPY").amount == Decimal("200")
    assert str(Money.of("199.7", "JPY")) == "200 JPY"


def test_currency_mismatch_is_a_hard_error():
    with pytest.raises(ValueError, match="currency mismatch"):
        Money.of("1.00", "USD").add(Money.of("1.00", "EUR"))


def test_reject_float_amount():
    with pytest.raises(TypeError):
        Money.of(0.10, "USD")  # a float carries binary error -> refused


def test_order_total_matches_java():
    svc = OrderTotalService()
    total = svc.total(
        [LineItem(Money.of("19.99", "USD"), 3)],
        Decimal("0.21"),
    )
    # Java Demo printed: 3x19.99 +21% = 72.56 USD
    assert total.amount == Decimal("72.56")
    assert total.currency == "USD"


def test_multiply_is_exact():
    assert Money.of("0.01", "USD").multiply(3).amount == Decimal("0.03")


def test_currency_code_is_case_insensitive_and_consistent_with_java():
    # Both ports normalise the currency code to upper case, so "usd" == "USD".
    # (Java's Currency.getInstance is case-sensitive on its own; Money.of up-cases the
    # code on BOTH sides so lower- and upper-case input behave identically -- see the
    # README "currency scale" trap and Money.java's of(...).)
    lower = Money.of("19.99", "usd")
    upper = Money.of("19.99", "USD")
    assert lower.currency == "USD"
    assert lower == upper
    assert str(lower) == "19.99 USD"
    # JPY (0 minor units) up-cases too, so the scale lookup still hits the table.
    assert Money.of("199.7", "jpy").amount == Decimal("200")
    assert Money.of("199.7", "jpy") == Money.of("199.7", "JPY")


def test_tax_percentage_tie_rounds_half_even_like_java():
    # The tax path (Money.percentage) must re-quantise HALF_EVEN, exactly like Java's
    # Money.percentage. 10.50 USD x 5% = 0.525 -- an exact tie at 2dp -- so HALF_EVEN gives
    # the even neighbour 0.52 (Java prints 0.52 too), while HALF_UP would give 0.53.
    # Without this tie, a HALF_EVEN -> HALF_UP slip in percentage() leaves every other test green.
    assert Decimal("10.50") * Decimal("0.05") == Decimal("0.525")  # really a tie (not vacuous)
    tax = Money.of("10.50", "USD").percentage(Decimal("0.05"))
    assert tax.amount == Decimal("0.52")
    assert str(tax) == "0.52 USD"
