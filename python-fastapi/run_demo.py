"""run_demo.py -- the Python mirror of Java's Demo.main, runnable with a plain interpreter.

    py run_demo.py

Prints the same five lines as the Java Demo so the two sides can be diffed by eye.
Needs NO third-party package (only the stdlib + app/).
"""
from decimal import Decimal

from app.money import Money
from app.service import LineItem, OrderTotalService


def main() -> None:
    a, b = Money.of("0.10", "USD"), Money.of("0.20", "USD")
    print(f"0.10 + 0.20 = {a.add(b)}")                 # -> 0.30 USD (exact)

    print(f"round(2.005) = {Money.of('2.005', 'USD')}")  # -> 2.00 USD (bankers')

    print(f"199.7 JPY    = {Money.of('199.7', 'JPY')}")  # -> 200 JPY

    svc = OrderTotalService()
    total = svc.total([LineItem(Money.of("19.99", "USD"), 3)], Decimal("0.21"))
    print(f"3x19.99 +21% = {total}")                    # -> 72.56 USD

    try:
        Money.of("1.00", "USD").add(Money.of("1.00", "EUR"))
    except ValueError as ex:
        print(f"mismatch     = {ex}")


if __name__ == "__main__":
    main()
