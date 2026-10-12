"""Exact-first boundaries for numeric text transported by readers (R14 N03).

Continuous fields accept zero or an exact rational whose RN-even binary64
value is finite and nonzero: 2**-1075 < abs(q) < 2**1024 - 2**970.
Rounding within that range is deliberate; this is not the narrower D400
engineering construction envelope. Integer identities remain exact, without
a magnitude bound. Strings retained as source evidence are not constructed.
Gate: tests/test_r14_readers.py; no nonstandard JSON NaN/Infinity sentinel.
"""
from fractions import Fraction
import json

from ..construction import scalar_rational
from ..numeric_domain import ConstructionDomainError, exact_input


def _decimal(token):
    q = Fraction(token)
    # Check before any conversion can erase nonzero/finite source information.
    scalar_rational(q, quantity="JSON numeric literal")
    # JSON real negative-zero tokens carry an existing binary64 sign bit;
    # integer -0 keeps json's original integer-zero semantics (parse_int).
    if not q and token.startswith("-"):
        return -0.0
    return q  # Keep exact until the field decides integer versus continuous.


def scalar(value, *, quantity):
    """Checked continuous field, preserving an already supplied signed zero."""
    result = scalar_rational(value, quantity=quantity)
    return value if isinstance(value, float) and value == 0.0 else result


def _nonfinite(token):
    raise ConstructionDomainError("JSON numeric literal", f"nonfinite token {token}")


def loads(text):
    """Preserve exact decimal tokens and arbitrary-size integer identities."""
    return json.loads(text, parse_float=_decimal, parse_constant=_nonfinite)


def integer(value, quantity):
    """Integer identities/counts may not be obtained by truncating real input."""
    q = exact_input(value, quantity)
    if q.denominator != 1:
        raise ConstructionDomainError(quantity, "integer field requires an exact integer")
    return q.numerator


def decode_tree(value, quantity):
    """Check numeric evidence while retaining strings, integers and structure."""
    if isinstance(value, dict):
        return {k: decode_tree(v, f"{quantity}.{k}") for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(decode_tree(v, f"{quantity}[{i}]") for i, v in enumerate(value))
    if isinstance(value, (float, Fraction)):
        return scalar(value, quantity=quantity)
    return value
