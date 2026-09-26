"""impl_fixed.py -- the CORRECT order-total impl (the planted bug removed).

Same signature and intent as impl_buggy.f, but money-exact: Decimal throughout and an
explicit ROUND_HALF_EVEN quantize to 2dp. This is what the idiomatic migration in
app/service.py + app/money.py compiles down to for the USD single-rate case.
"""
from decimal import Decimal, ROUND_HALF_EVEN

_CENT = Decimal("0.01")


def f(line_prices, quantities, tax_rate):
    """Total an order in USD: subtotal = sum(price*qty), grand = subtotal*(1+tax_rate).

    Returns the grand total as a Decimal quantised to 2dp with HALF_EVEN. Intent: this
    equals the exact decimal money total (e.g. 3 x 19.99 + 21% tax = 72.56).
    """
    subtotal = Decimal(0)
    for price, qty in zip(line_prices, quantities):
        subtotal += Decimal(str(price)) * Decimal(qty)
    grand = subtotal * (Decimal(1) + Decimal(str(tax_rate)))
    return grand.quantize(_CENT, rounding=ROUND_HALF_EVEN)
