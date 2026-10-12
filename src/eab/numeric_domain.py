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


MAX_MU = Fraction(2**20)


def check_mu(value, quantity="friction.mu"):
    """Exact dimensionless friction domain: 0 <= mu <= 2**20.

    The bound limits mu*eps to 2**-32. It is NOT a cone certificate:
    final rays must separately pass the exact circular-cone containment gate.
    Tests: test_r14_domain.py::test_friction_domain_checks_exact_boundaries.
    """
    q = exact_input(value, quantity)
    if not 0 <= q <= MAX_MU:
        raise ConstructionDomainError(quantity, "friction coefficient must be in [0, 2^20]")
    return q


def binary64_argument(value, quantity: str) -> float:
    """Check the exact parameter before conversion to the binary64 libm model.

    A reduced rational is binary64 iff its denominator is a power of two,
    its odd significand has <=53 bits, its lowest bit is >=2**-1074, and
    its highest bit is <=2**1023. This admits all finite binary64 values,
    but not an int with lost parity or a nonzero rational rounded to zero.
    Gate: test_r14_trig_rejects_lossy_exact_parameters.
    """
    q = exact_input(value, quantity)
    if not q:
        return value if isinstance(value, float) else 0.0
    numerator, denominator = abs(q.numerator), q.denominator
    trailing = (numerator & -numerator).bit_length() - 1
    bits = numerator.bit_length() - trailing
    exponent = trailing - (denominator.bit_length() - 1)
    if (denominator & (denominator - 1) or bits > 53
            or exponent < -1074 or exponent + bits - 1 > 1023):
        raise ConstructionDomainError(quantity, "exact parameter must be losslessly representable finite binary64")
    return float(q)
