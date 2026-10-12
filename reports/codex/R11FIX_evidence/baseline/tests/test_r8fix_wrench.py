"""G6H-04: raw Fraction determinants, no production construction oracle."""
from construction_oracle import scalar_exact
from fractions import Fraction as F
import math

import pytest

import eab.limit as limit


def _oracle(force, point, origin, dim):
    # Independent alternating determinant, not _exact_wrench/_exact_shift.
    r = [F(p) - F(o) for p, o in zip(point, origin)]
    f = list(map(F, force))
    pairs = [(0, 1)] if dim == 2 else [(1, 2), (2, 0), (0, 1)]
    return f + [r[i]*f[j] - r[j]*f[i] for i, j in pairs]


@pytest.mark.parametrize("dim", [2, 3])
@pytest.mark.parametrize("scale", [1e160, 1e200, 2.0**530])
@pytest.mark.parametrize("reference", [0, 1])
def test_wrench_cancels_overflowing_products_before_final_rounding(dim, scale, reference):
    force = (scale,)*dim
    point = (scale,)*dim
    origin = (0.0,)*dim if not reference else (-scale,)*dim
    expected = list(map(scalar_exact, _oracle(force, point, origin, dim)))
    actual = limit.wrench(force, point, origin, dim)
    assert all(map(math.isfinite, actual)), "finite exact wrench must not contain NaN/inf"
    assert actual == expected, "exact zero moments were lost in intermediate products"


@pytest.mark.parametrize("dim", [2, 3])
def test_wrench_preserves_representable_nonzero_cancellation_residual(dim):
    a = 2.0**530
    force = (a, math.nextafter(a, math.inf)) + ((a,) if dim == 3 else ())
    point = (a,)*dim
    origin = (0.0,)*dim
    expected = list(map(scalar_exact, _oracle(force, point, origin, dim)))
    actual = limit.wrench(force, point, origin, dim)
    assert actual == expected, "representable residual of overflowing products must survive"
    assert expected[-1] == 2.0**1008


def test_wrench_subtracts_unrepresentable_lever_before_rounding_final_moment():
    point, origin = (1e308, 0.0), (-1e308, 0.0)
    force = (0.0, 1e-308)
    assert limit.wrench(force, point, origin, 2) == list(map(scalar_exact, _oracle(force, point, origin, 2)))


def test_wrench_retains_final_subnormal_when_each_product_underflows():
    a = 2.0**-538
    force, point, origin = (a, -a), (2*a, 2*a), (0.0, 0.0)
    expected = list(map(scalar_exact, _oracle(force, point, origin, 2)))
    assert expected[-1] == -math.ulp(0.0)
    assert limit.wrench(force, point, origin, 2) == expected


@pytest.mark.parametrize("scale", [1e200, 1e-200])
def test_wrench_unrepresentable_nonzero_moment_fails_loud(scale):
    with pytest.raises((OverflowError, ArithmeticError)):
        limit.wrench((0.0, scale), (scale, 0.0), (0.0, 0.0), 2)


@pytest.mark.parametrize("dim", [2, 3])
def test_shift_wrench_uses_same_final_rounding_contract(dim):
    a = 1e200
    moments = [3.0] if dim == 2 else [3.0, -5.0, 7.0]
    w = [a]*dim + moments
    assert limit._shift_wrench(w, (a,)*dim, dim) == w


@pytest.mark.parametrize("name", ["_twist_back", "_twist_forward"])
def test_twist_transform_cancels_overflow_before_constructing_velocity(name):
    a = 1e200
    y = [3.0, -5.0, 7.0, a, a, a]
    assert getattr(limit, name)(y, (a,)*3, 3) == y
    exact_y, exact_d = list(map(F, y)), (F(a),)*3
    exact = getattr(limit, name)(exact_y, exact_d, 3)
    assert exact == exact_y
    assert all(isinstance(v, F) for v in exact), "LP exact twist must remain rational"


def test_wrench_gate_rejects_internal_premature_float_products(monkeypatch):
    # Reintroduce the original implementation at the real public construction
    # entry point, not by corrupting its returned answer.
    def premature(force, point, origin, dim):
        r = tuple(point[i] - origin[i] for i in range(dim))
        pairs = [(0, 1)] if dim == 2 else [(1, 2), (2, 0), (0, 1)]
        return list(force) + [r[i]*force[j] - r[j]*force[i] for i, j in pairs]
    monkeypatch.setattr(limit, "wrench", premature)
    with pytest.raises(AssertionError, match="finite exact wrench"):
        test_wrench_cancels_overflowing_products_before_final_rounding(3, 1e200, 1)


@pytest.mark.parametrize("dim", [2, 3])
def test_wrench_asymmetric_reference_keeps_exact_cancellation(dim):
    a = 2.0**530
    origin = (2*a, 4*a, 6*a)[:dim]
    point = (3*a, 5*a, 7*a)[:dim]
    force = (a,)*dim
    assert limit.wrench(force, point, origin, dim) == [a]*dim + [0.0]*(1 if dim == 2 else 3)


def test_mechanism_power_cancels_products_before_rounding():
    a = 1e200
    contact = limit.LimitContact((0.0, 1.0), (0.0, 1.0))
    # Power = a*a - a*a + 1*(-a), exactly -a.
    result = limit.mechanism_power([a, -a, 1.0], contact, (a, a), (0.0, 0.0), 2)
    assert result == -a, "finite exact power must survive intermediate overflow"


def test_contact_midpoint_cancels_range_before_rounding():
    from types import SimpleNamespace
    cover = SimpleNamespace(normal=(0.0, 1.0), point_a=(1e308, 1e308),
                            point_b=(1e308, 1e308), label=lambda: ("VF",))
    contact = limit.contacts_from_covers([cover], mu=0.5, side="mid")[0]
    assert contact.point == cover.point_a, "finite contact midpoint must not overflow"


@pytest.mark.parametrize("name,sign", [("_twist_back", 1), ("_twist_forward", -1)])
def test_twist_2d_cancels_overflowing_product_with_finite_velocity(name, sign):
    import sys
    a = 2.0**512
    y, d = [-sign*sys.float_info.max, 0.0, a], (0.0, a)
    result = getattr(limit, name)(y, d, 2)
    assert result == [sign*2.0**971, 0.0, a], "final 2D twist residual must be finite"


def test_mechanism_power_does_not_round_unneeded_out_of_range_moment():
    a = 1e200
    contact = limit.LimitContact((a, 0.0), (0.0, 1.0))
    # Moment a*a is out of range, but zero angular velocity removes it exactly.
    assert limit.mechanism_power([1.0, 1.0, 0.0], contact, (0.0, a), (0.0, 0.0), 2) == a
