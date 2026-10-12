"""Central numerical support policy; see docs/exact_predicates_plan.md (R13FIXb).

Predicates and exact rational constructions are NOT restricted by this module.
Approximate public constructions opt into the engineering input envelope;
checked rational-to-binary64 constructions retain their larger output domain.
Tests: test_r13fixb_domain.py::test_engineering_input_envelope_is_exact.
"""
from fractions import Fraction
import math


INPUT_MIN = Fraction(1, 2**400)
INPUT_MAX = Fraction(2**400)


class ConstructionDomainError(OverflowError):
    """A named constructed quantity lies outside its numerical support domain."""

    def __init__(self, quantity, detail="outside numerical support domain"):
        self.quantity = quantity
        super().__init__(f"{quantity}: {detail}")


def exact_input(value, quantity):
    """Preserve finite int/Fraction/binary64 input, rejecting nonfinite floats."""
    if isinstance(value, float) and not math.isfinite(value):
        raise ConstructionDomainError(quantity, "nonfinite input")
    return Fraction(value)


def check_input(value, quantity):
    """Return the exact input after checking zero or [2**-400, 2**400]."""
    q = exact_input(value, quantity)
    if q and not INPUT_MIN <= abs(q) <= INPUT_MAX:
        raise ConstructionDomainError(quantity, "nonzero input magnitude must be in [2^-400, 2^400]")
    return q


def check_inputs(values, quantity):
    """Check a flat sequence, naming the offending coordinate/channel."""
    for i, value in enumerate(values):
        check_input(value, f"{quantity}[{i}]")


def float_algebra(values):
    """Whether builtin real inputs require a once-rounded binary64 result.

    Exact-only algebra and Dual/custom scalar protocols keep their own type.
    Mixed int/float/Fraction inputs must never use Python's early coercion.
    """
    return (all(type(x) in (int, float, Fraction) for x in values)
            and any(type(x) is float for x in values))
