"""Public mechanics constructions against independent rational expressions.

Oracles use Fraction polynomials and the independent binary64-cell reference,
not production geometry, wrench, tangent, LP assembly or derivative helpers.
Transcendental coefficients are the documented libm input model, not a claim
that sin/cos themselves are rational or correctly rounded transcendental maps.
"""
from fractions import Fraction as F
import inspect
import math
import sys

import pytest

from construction_oracle import scalar_exact, sqrt_exact
from eab import construction, dual, limit, limit_multi, lp, rational3


@pytest.mark.parametrize("exponent", [-1074, -600, 0, 600, 1022])
@pytest.mark.parametrize("sign", [-1, 1])
def test_public_wrench_and_power_each_value_matches_rational_reference(exponent, sign):
    s = F(2)**exponent
    force, point, origin = (s, -s, s), (3, 5, 7), (2, 4, 6)
    force = tuple(sign*v for v in force)
    expected = (*force, 2*sign*s, 0, -2*sign*s)
    result = limit.wrench(force, point, origin, 3)
    assert result == [scalar_exact(v) for v in expected], "wrench final components"
    contact = limit.LimitContact(point, (0, 0, 1))
    motion = (1, 2, 3, 2, 3, 4)
    power = sum(F(a)*b for a, b in zip(motion, expected))
    assert limit.mechanism_power(motion, contact, force, origin, 3) == scalar_exact(power), "power final scalar"


@pytest.mark.parametrize("exponent", [-1074, -600, 0, 600, 1022])
def test_public_rational3_polynomials_do_not_use_a_display_as_input(exponent):
    s = F(2)**exponent
    a, b = (s, 2*s, -3*s), (4*s, -5*s, 6*s)
    assert rational3.dot(a, b) == -24*s*s
    assert rational3.cross(a, b) == (-3*s*s, -18*s*s, -13*s*s)


def test_public_vector_constructor_has_independent_extreme_cells_and_distinct_outputs():
    cells = [F(2)**-1074, F(2)**-600, F(1, 3), F(2)**600,
             F(sys.float_info.max)+F(2)**969]
    outputs = []
    for q in cells:
        expected = (scalar_exact(q), scalar_exact(-q), 0.0)
        actual = construction.vector_rational((q, -q, F(0)))
        assert actual == expected, "vector final coordinate reference"
        outputs.append(actual)
    assert len(set(outputs)) == len(cells), "extreme grid must produce distinct coordinate tuples"
    for q in [F(2)**-1076, F(2)**1024]:
        with pytest.raises(ArithmeticError):
            construction.vector_rational((q, -q, F(0)))


@pytest.mark.parametrize("mu", [math.ulp(0.0), 0.5, math.nextafter(1.0, 0.0), 2.0**1022])
def test_public_friction_generators_round_complete_component(mu):
    n = (0.6, 0.8)
    tangent = (-F(n[1]), F(n[0]))
    expected = [tuple(scalar_exact(F(n[i])+sign*F(mu)*tangent[i]) for i in range(2))
                for sign in (1, -1)]
    assert limit.friction_generators(n, mu, 2) == expected, "friction complete component rational rounding"


@pytest.mark.parametrize("k", [5, 8])
@pytest.mark.parametrize("mu", [math.ulp(0.0), 0.5, math.nextafter(1.0, 0.0), 2.0**1022])
def test_public_3d_friction_generators_follow_exact_given_coefficient_model(k, mu):
    # Non-axis normal; supplied y tangent is exactly orthogonal. This avoids
    # copying the production tangent-selection/normalisation algorithm.
    n, t1, t2 = (0.6, 0.0, 0.8), (0, 1, 0), (-F(0.8), 0, F(0.6))
    exact = []
    for j in range(k):
        angle = 2.0*math.pi*j/k  # the documented supplied binary64 angle model
        cosine, sine = F(math.cos(angle)), F(math.sin(angle))
        exact.append(tuple(F(n[i])+F(mu)*(cosine*t1[i]+sine*t2[i]) for i in range(3)))
    try:
        expected = [tuple(scalar_exact(q) for q in row) for row in exact]
    except ArithmeticError:
        with pytest.raises(ArithmeticError):
            limit.friction_generators(n, mu, 3, k, tangent=t1)
    else:
        assert limit.friction_generators(n, mu, 3, k, tangent=t1) == expected, "3D friction complete component rational rounding"


@pytest.mark.parametrize("exponent", [-1074, -600, 0, 600, 1022])
def test_public_dual_angular_and_sqrt_derivatives_are_value_bound(exponent):
    s = math.ldexp(1.0, exponent)
    if exponent == -1074:
        assert F(s)/2 == F(math.ulp(0.0))/2
        with pytest.raises(ArithmeticError):
            dual.atan2(dual.Dual(1.0, (s, -s, 0.0)), dual.Dual(1.0, (0.0, s, 0.0)))
    else:
        angular = dual.atan2(dual.Dual(1.0, (s, -s, 0.0)), dual.Dual(1.0, (0.0, s, 0.0)))
        assert angular.e == (scalar_exact(F(s)/2), -s, 0.0), "angular derivative final values"
    root = dual.sqrt(dual.Dual(0.25, (s, -s, 0.0)))
    assert root.v == 0.5 and root.e == (s, -s, 0.0), "sqrt derivative final values"


@pytest.mark.parametrize("exponent", [-1074, -600, 0, 600, 1022])
@pytest.mark.parametrize("function", ["sin", "cos"])
def test_public_trig_derivative_follows_declared_coefficient_model(exponent, function):
    s = math.ldexp(1.0, exponent)
    value = 0.25 if function == "sin" else 1.5
    coefficient = math.cos(value) if function == "sin" else -math.sin(value)
    q = F(coefficient)*F(s)
    expected = scalar_exact(q)
    result = getattr(dual, function)(dual.Dual(value, (s, -s, 0.0)))
    assert result.e == (expected, -expected, 0.0), "trig model derivative final values"


@pytest.mark.parametrize("exponent", [-1075, -1074, -600, 0, 600, 1023, 1024])
@pytest.mark.parametrize("maximize", [False, True])
def test_public_lp_views_are_bound_to_independent_exact_solution(exponent, maximize):
    q = F(2)**exponent
    # Two nonsymmetric rows, a unique primal and a unique dual solution.
    matrix = [[F(1), F(2)], [F(0), F(3)]]
    rhs, cost = [3*q, 3*q], [F(1), F(-1)]
    result = (lp.maximize if maximize else lp.solve)(matrix, rhs, cost)
    assert result.status == lp.OPTIMAL
    assert result.exact_x == (q, q), "LP independent primal"
    assert result.exact_y == (F(1), F(-1)), "LP independent dual"
    view = math.inf if exponent == 1024 else scalar_exact(q, allow_underflow=True)
    assert result.x == [view, view] and result.y == [1.0, -1.0] and result.obj == 0.0, "LP bound display fields"


@pytest.mark.parametrize("exponent", [-1073, -600, 0, 600, 1021])
def test_public_limit_single_and_multi_match_analytic_sliding_capacity(exponent):
    s = math.ldexp(1.0, exponent)
    contacts = [limit.LimitContact((x, 0), (0, 1), 0.5) for x in (-1, 1)]
    dead, live = [0, -s, 0], [1, 0, 0]
    expected = F(s)/2
    single = limit.limit_load(contacts, dead, live, dim=2)
    multi = limit_multi.limit_load_multi([limit_multi.LimitBody(dead, live)],
             [limit_multi.BodyContact(c, 0) for c in contacts], dim=2)
    for result in (single, multi):
        assert result.status == lp.OPTIMAL
        assert result.alpha == scalar_exact(expected), "analytic capacity final view"
        assert getattr(result.alpha, "exact", F(result.alpha)) == expected, "analytic capacity certificate"


def test_friction_component_gate_rejects_internal_rounded_product(monkeypatch):
    source = inspect.getsource(limit.friction_generators)
    needle = "scalar_rational(Fraction(normal[i]) + Fraction(mu) * Fraction(t[i]))"
    assert source.count(needle) == 1
    scope = dict(vars(limit))
    exec(compile(source.replace(needle, "normal[i] + mu * t[i]"), "<r13-friction-early-product>", "exec"), scope)
    monkeypatch.setattr(limit, "friction_generators", scope["friction_generators"])
    with pytest.raises(AssertionError, match="friction complete component rational rounding"):
        test_public_friction_generators_round_complete_component(math.nextafter(1.0, 0.0))
