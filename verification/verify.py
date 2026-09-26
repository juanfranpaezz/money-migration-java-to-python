"""verify.py -- run OUR verification discipline on the migrated money code.

WHAT THIS DEMONSTRATES (and what it does NOT):
  - It DERIVES a postcondition FROM INTENT -- "the order total must equal the EXACT
    decimal-money total" -- independently re-derivable from the spec. The FLAG on the
    buggy impl does NOT depend on the fixed implementation's body (an independent
    rational-arithmetic re-derivation yields the same expected value).
  - It feeds that postcondition to the applier in `_selfcert.apply_pc` (a
    self-contained module that ships with this repo), which runs the same
    0-false-positive negative-control + degeneracy guard.
  - It proves the check FIRES BOTH WAYS on a deployment-realistic input
    (price=0.07, qty=5, tax=10%, where float money is off by a cent):
        * the buggy float impl     -> FLAG  (self-certifies a wrong cent)
        * the fixed Decimal impl   -> CLEAR (intent-consistent)
  - It is a PROCESS / determinism demo: a reproducible, mechanical trail. It is NOT a
    claim that this catches more bugs than a human code review (see the README's
    honest-framing section).

The postcondition is intent-derived: the "known-correct output" (the negative control) is
computed by an INDEPENDENT exact-decimal oracle here, re-derived from the spec rather than
read off a body. So if the pc were wrong it would reject the oracle's own correct answer
and the harness would mark the verdict untrusted (it does not -- the negative control
passes).

Run:  py verify.py            (human-readable)
      py verify.py --json     (machine-readable; exit 0 iff both-ways proven)
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path

# Import the applier from the LOCAL module that ships with this repo, so the
# verification runs on a fresh `git clone` with nothing else installed.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _selfcert import apply_pc  # noqa: E402

import impl_buggy  # noqa: E402
import impl_fixed  # noqa: E402

_CENT = Decimal("0.01")

# A deployment-realistic input where binary-float money DIVERGES from decimal money:
#   one line, unit price 0.07, quantity 5, 10% tax.
#   exact money: (0.07*5)=0.35 ; *1.10 = 0.385 -> HALF_EVEN 2dp = 0.38
#   naive float: 0.07*5 = 0.35000000000000003 ; *1.1 = 0.3850000... ; round(_,2) = 0.39
INPUTS = (["0.07"], [5], "0.10")


def exact_money_total(line_prices, quantities, tax_rate) -> Decimal:
    """The INTENT oracle: the exact decimal-money grand total, HALF_EVEN to 2dp.

    This is derived from the SPEC ("subtotal + tax, money-exact") and is independently
    re-derivable (a Fraction-based hand re-derivation gives the same value). It produces
    the negative-control correct output and underlies the postcondition. It encodes the
    same rule app/money.py implements; the FLAG on the buggy impl does not depend on the
    fixed body.
    """
    subtotal = Decimal(0)
    for price, qty in zip(line_prices, quantities):
        subtotal += Decimal(str(price)) * Decimal(qty)
    grand = subtotal * (Decimal(1) + Decimal(str(tax_rate)))
    return grand.quantize(_CENT, rounding=ROUND_HALF_EVEN)


def make_postcondition(inputs):
    """Author the intent-derived postcondition `pc(inputs, output) -> bool` from the spec.

    The intent: the returned total must equal the exact decimal-money total for these
    inputs. We normalise the candidate output through Decimal(str(...)) so a float output
    (the buggy shape) and a Decimal output (the fixed shape) are compared on equal terms --
    the pc judges the VALUE, not the type. A wrong cent fails; the exact cent passes.
    """
    expected = exact_money_total(*inputs)

    def pc(_inputs, output) -> bool:
        try:
            got = Decimal(str(output))
        except Exception:
            return False
        return got == expected

    return pc


def run():
    pc = make_postcondition(INPUTS)
    # The negative control / known-correct output is the INTENT oracle's answer,
    # NOT lifted from either body.
    known_correct = exact_money_total(*INPUTS)

    buggy_out = impl_buggy.f(*INPUTS)
    fixed_out = impl_fixed.f(*INPUTS)

    buggy_verdict = apply_pc(pc, INPUTS, buggy_out, known_correct)
    fixed_verdict = apply_pc(pc, INPUTS, fixed_out, known_correct)

    # The both-ways proof: the SAME instrument FLAGs the bug AND CLEARs the fix,
    # and is trusted (passed its negative control + degeneracy guard) in both runs.
    fires_both = (
        buggy_verdict["flag"] is True
        and buggy_verdict["trusted"] is True
        and fixed_verdict["flag"] is False
        and fixed_verdict["trusted"] is True
    )

    return {
        "input": {"line_prices": INPUTS[0], "quantities": INPUTS[1], "tax_rate": INPUTS[2]},
        "intent_oracle_expected": str(known_correct),
        "buggy_impl_output": str(buggy_out),
        "fixed_impl_output": str(fixed_out),
        "buggy_verdict": buggy_verdict,
        "fixed_verdict": fixed_verdict,
        "fires_both_ways": fires_both,
    }


def main(argv):
    result = run()
    if "--json" in argv:
        print(json.dumps(result, indent=2, default=str))
    else:
        r = result
        print("== money-migration verification: float-money bug, both-ways proof ==")
        print(f"input            : {r['input']}")
        print(f"intent oracle    : {r['intent_oracle_expected']}  (exact decimal money)")
        print(f"buggy impl output: {r['buggy_impl_output']}  ->  "
              f"FLAG={r['buggy_verdict']['flag']} trusted={r['buggy_verdict']['trusted']}")
        print(f"  reason: {r['buggy_verdict']['reason']}")
        print(f"fixed impl output: {r['fixed_impl_output']}  ->  "
              f"FLAG={r['fixed_verdict']['flag']} trusted={r['fixed_verdict']['trusted']}")
        print(f"  reason: {r['fixed_verdict']['reason']}")
        print(f"FIRES BOTH WAYS  : {r['fires_both_ways']}  "
              f"(flags the bug, clears the fix, trusted in both)")
    return 0 if result["fires_both_ways"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
