"""Root scan: exact radical-minus-offset is also a final construction boundary."""
from fractions import Fraction as F
import math
import sys

import pytest

from eab.kernel3d.frozen import _normalized_difference


@pytest.mark.parametrize("sign", [-1, 1])
def test_compound_constructor_rounds_values_between_max_and_overflow_midpoint(sign):
    maximum = F(sys.float_info.max)
    ulp = F(2)**971
    exact = maximum + ulp/4
    try:
        actual = _normalized_difference(sign*(exact+1), F(1), sign*F(1))
    except OverflowError as error:
        raise AssertionError("compound finite RN-even overflow-edge value was rejected") from error
    assert actual == sign*sys.float_info.max, "compound finite RN-even overflow-edge value"
    # Independent Fraction cell around max (conceptual next finite value 2**1024).
    assert maximum-ulp/2 < abs(sign*exact) < (maximum+F(2)**1024)/2


def test_compound_range_and_cancellation_are_not_decided_by_intermediate_displays():
    big = F(2)**1100
    assert _normalized_difference(big, F(1), big-1) == 1
    assert _normalized_difference(-big, F(1), 1-big) == -1
    maximum = F(sys.float_info.max)
    with pytest.raises(OverflowError):
        _normalized_difference(maximum+F(2)**970+1, F(1), F(1))
    with pytest.raises(ArithmeticError):
        _normalized_difference(F(1)+F(2)**-1076, F(1), F(1))


def test_compound_overflow_edge_gate_rejects_pre_r9_internal_algorithm(monkeypatch):
    import eab.construction as boundary
    original = boundary.normalized_difference_rational
    def strict_max(c, nn, offset, **kwargs):
        if nn == 1 and abs(c-offset) > F(sys.float_info.max):
            raise OverflowError("old strictly-above-max rejection")
        return original(c, nn, offset, **kwargs)
    monkeypatch.setattr(boundary, "normalized_difference_rational", strict_max)
    with pytest.raises(AssertionError, match="compound finite RN-even overflow-edge value was rejected"):
        test_compound_constructor_rounds_values_between_max_and_overflow_midpoint(1)
