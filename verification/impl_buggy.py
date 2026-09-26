"""impl_buggy.py -- the SUSPECT order-total impl with a PLANTED, realistic money bug.

This is the #1 trap of a Java->Python money migration done carelessly: the developer
reaches for ``float`` (the default Python number) instead of Decimal, and rounds with the
built-in ``round()`` (which is NOT bankers'-rounding-on-a-Decimal). The function looks
right, has a confident docstring, and even ASSERTS its own result is "correct" -- this is
the self-certification pattern: the body certifies a wrong answer.

The exported callable is ``f(line_prices, quantities, tax_rate)`` (parallel lists +
fraction). The intent is identical to app/service.py: subtotal + tax, money-exact,
HALF_EVEN to 2dp for USD.
"""


def f(line_prices, quantities, tax_rate):
    """Total an order in USD: subtotal = sum(price*qty), grand = subtotal*(1+tax_rate).

    Returns the grand total as a float rounded to 2 decimal places. Intent: this must
    equal the exact decimal money total (e.g. 3 x 19.99 + 21% tax = 72.56).
    """
    subtotal = 0.0
    for price, qty in zip(line_prices, quantities):
        subtotal += float(price) * qty          # BUG: float money accumulation
    grand = subtotal * (1.0 + float(tax_rate))
    result = round(grand, 2)                     # BUG: round() on a float, not Decimal HALF_EVEN
    # The body "certifies" itself -- but the assertion is computed the SAME wrong way,
    # so it passes while the answer is wrong. This is exactly self-certification.
    assert abs(result - round(grand, 2)) < 1e-9, "internal check: total is correct"
    return result
