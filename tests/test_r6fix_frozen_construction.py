"""Closed-form axis/3-4-5 jet oracles; no production geometry primitives."""
from construction_oracle import scalar_exact
from fractions import Fraction as F
import math

import pytest

from eab.dual import Dual
from eab.kernel3d.geom3 import Polyhedron
from eab.kernel3d.frozen import frozen_gap, frozen_normal


@pytest.mark.parametrize("scale", [1.0, 2.0 ** -600, 2.0 ** 600])
def test_frozen_vv_normal_keeps_value_and_zero_primal_derivative_channels_at_extreme_scale(scale):
    A = Polyhedron([(scale, Dual(2 * scale, (scale,)), 2 * scale)], [])
    B = Polyhedron([(0.0, 0.0, 0.0)], [])
    n = frozen_normal(A, B, ("VV3", ("V", 0), ("V", 0)))
    assert [t.v for t in n] == pytest.approx([1 / 3, 2 / 3, 2 / 3], rel=2e-15, abs=0.0)
    assert [t.e[0] for t in n] == pytest.approx([-2 / 27, 5 / 27, -4 / 27], rel=2e-15, abs=0.0)


@pytest.mark.parametrize("scale", [1.0, 2.0 ** -600, 2.0 ** 600])
@pytest.mark.parametrize("swap", [False, True])
def test_frozen_line_normal_keeps_zero_primal_nonzero_derivative_without_square_range_loss(scale, swap):
    point = Polyhedron([(scale, scale, Dual(0.0, (scale,)))], [])
    edge = Polyhedron([(0.0, 0.0, 0.0), (scale, 0.0, 0.0)], [])
    A, B = (edge, point) if swap else (point, edge)
    label = ("EV3", ("E", 0, 1), ("V", 0)) if swap else ("VE3", ("V", 0), ("E", 0, 1))
    sign = -1.0 if swap else 1.0
    n = frozen_normal(A, B, label)
    assert [t.v for t in n] == [0.0, sign, 0.0]
    assert [t.e[0] for t in n] == [0.0, 0.0, sign]


@pytest.mark.parametrize("with_dual", [False, True])
def test_frozen_affine_gap_preserves_fraction_microfeature_at_large_coordinates(with_dual):
    T, s = F(10 ** 8), F(1, 10 ** 9)
    A = Polyhedron([(T + s, T, T)], [])
    B = Polyhedron([(T, T, T)], [])
    x = (Dual(0.0, (1.0,)), 0.0, 0.0) if with_dual else (0.0, 0.0, 0.0)
    label = ("VV3", ("V", 0), ("V", 0))
    n = frozen_normal(A, B, label, x=x)
    g = frozen_gap(A, B, label, x, n)
    if with_dual:
        assert [q.v for q in n] == [1.0, 0.0, 0.0]
        assert g.v == scalar_exact(s) and g.e == (1.0,)
    else:
        assert n == (1.0, 0.0, 0.0)
        assert g == scalar_exact(s)


def test_frozen_gap_does_not_overflow_cancelling_dot_products():
    u = 1e308
    A = Polyhedron([(u, u, 1.0)], [])
    B = Polyhedron([(-u, -u, 0.0)], [])
    n = (0.6, -0.6, math.sqrt(0.28))
    assert frozen_gap(A, B, ("VV3", ("V", 0), ("V", 0)), (0.0, 0.0, 0.0), n) == n[2]


def test_frozen_unit_jet_divides_before_rounding_an_overflowing_tangent_component():
    seed = 1.7e308
    A = Polyhedron([(Dual(1.0, (seed,)), Dual(1.0, (-seed,)), Dual(1.0, (-seed,)))], [])
    B = Polyhedron([(0.0, 0.0, 0.0)], [])
    n = frozen_normal(A, B, ("VV3", ("V", 0), ("V", 0)))
    # dn = (I - nn^T) dp / sqrt(3), n=(1,1,1)/sqrt(3).
    # The former reference divided by an already rounded sqrt(3), retaining
    # the very double rounding fixed in R7. Exact midpoint inequalities below
    # uniquely require the correctly rounded analytic derivative (no tolerance).
    for c, k in zip(n, (4, -2, -2)):
        value = c.e[0]
        assert (value > 0) == (k > 0)
        magnitude = abs(value)
        lo = (F(math.nextafter(magnitude, 0.0)) + F(magnitude)) / 2
        hi = (F(magnitude) + F(math.nextafter(magnitude, math.inf))) / 2
        exact_square = F(seed)**2 * k*k / 27
        assert lo*lo < exact_square < hi*hi
