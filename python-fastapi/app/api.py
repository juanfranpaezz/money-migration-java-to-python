"""api.py -- the FastAPI surface: Pydantic request/response models + DI.

This is the idiomatic FastAPI shape that replaces the Spring @RestController:
  - request/response bodies are Pydantic models (validation at the edge),
  - money fields are ``condecimal`` (Decimal, not float) so the JSON number is parsed
    into a Decimal and never touches binary float,
  - the OrderTotalService is supplied via ``Depends`` (FastAPI's DI), the direct
    analogue of Spring constructor-injecting the @Service bean.

Run:   py -m uvicorn app.api:app --reload      (needs fastapi + uvicorn installed)
The arithmetic itself (app/money.py, app/service.py) needs NO third-party package and is
what the verification step checks; this module is the thin HTTP adapter.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

try:
    from fastapi import Depends, FastAPI
    from pydantic import BaseModel, condecimal, field_validator
    _HAVE_FASTAPI = True
except ImportError:  # keep the module importable for the verification harness w/o fastapi
    _HAVE_FASTAPI = False

from .money import CURRENCIES, Money
from .service import LineItem, OrderTotalService


if _HAVE_FASTAPI:

    # A Decimal field constrained to be >= 0; FastAPI parses the JSON number as a Decimal.
    NonNegMoney = Annotated[condecimal(ge=Decimal("0")), "money amount as a Decimal"]

    class LineItemIn(BaseModel):
        unit_price: NonNegMoney
        currency: str
        quantity: int

        @field_validator("currency")
        @classmethod
        def known_currency(cls, v: str) -> str:
            v = v.upper()
            if v not in CURRENCIES:
                raise ValueError(f"unsupported currency: {v}")
            return v

        @field_validator("quantity")
        @classmethod
        def positive_qty(cls, v: int) -> int:
            if v <= 0:
                raise ValueError("quantity must be positive")
            return v

    class OrderIn(BaseModel):
        lines: list[LineItemIn]
        tax_rate: condecimal(ge=Decimal("0"))

    class MoneyOut(BaseModel):
        amount: Decimal
        currency: str

    def get_order_service() -> OrderTotalService:
        """DI provider -- the FastAPI analogue of Spring injecting the @Service bean."""
        return OrderTotalService()

    app = FastAPI(title="Money migration case study: order total")

    @app.post("/orders/total", response_model=MoneyOut)
    def order_total(
        order: OrderIn,
        service: Annotated[OrderTotalService, Depends(get_order_service)],
    ) -> MoneyOut:
        lines = [
            LineItem(Money.of(li.unit_price, li.currency), li.quantity)
            for li in order.lines
        ]
        total = service.total(lines, Decimal(order.tax_rate))
        return MoneyOut(amount=total.amount, currency=total.currency)
