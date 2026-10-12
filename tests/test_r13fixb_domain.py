"""R13FIXb numerical domains and remaining geometry constructions.

Oracle: only Fraction arithmetic, binary64 midpoint inequalities and analytic
3-4-12 boxes. No eab geometry/construction primitive is used to obtain expected
values. Mutants replace executable statements inside the real implementation.
"""
from fractions import Fraction as F
import inspect
import math
import textwrap

import pytest

from eab import construction as C
from eab import numeric_domain as D
from eab.kernel2d import geom as G2
from eab.kernel3d import geom3 as G3


@pytest.mark.parametrize("exponent", [-400, 0, 400])
@pytest.mark.parametrize("sign", [-1, 1])
def test_engineering_input_envelope_is_exact(exponent, sign):
    q = sign * F(2)**exponent
    for value in (q, float(q)):
        assert D.check_input(value, "force.x") == q
        assert D.check_inputs([0, value], "force") is None
    assert D.check_input(0, "force.x") == 0


@pytest.mark.parametrize("value", [F(1, 2**401), F(2)**401, -F(1, 2**401), -F(2)**401,
                                  F(2)**400 + 1, F(1, 2**400) - F(1, 2**900)])
def test_outside_engineering_input_envelope_is_a_named_domain_error(value):
    with pytest.raises(D.ConstructionDomainError, match=r"force\[1\].*2\^-400"):
        D.check_inputs([0, value], "force")


def test_nonfinite_conversion_and_unrepresentable_outputs_are_named_domain_errors():
    for value in (math.inf, -math.inf, math.nan, F(2)**1100, F(1, 2**1100)):
        with pytest.raises(D.ConstructionDomainError, match="distance"):
            C.scalar_rational(value, quantity="distance")
    with pytest.raises(D.ConstructionDomainError, match="sqrt_rational"):
        C.sqrt_rational(F(2)**2200)
    with pytest.raises(D.ConstructionDomainError, match="sqrt_rational"):
        C.sqrt_rational(F(1, 2**2200))
    with pytest.raises(D.ConstructionDomainError, match="vector_rational component"):
        C.vector_rational([0, F(2)**1100])


@pytest.mark.parametrize("exponent", [-1000, -400, 0, 400, 1000])
def test_full_range_exact_constructions_are_not_artificially_narrowed(exponent):
    q = F(2)**exponent
    assert C.scalar_rational(q) == float(q)
    assert C.ratio_rational(3*q, 3) == float(q)
    assert C.sqrt_rational(q*q) == float(q)
    assert C.norm_rational([3*q, 4*q]) == float(5*q)
    assert C.unit_rational([3*q, 4*q]) == (float(F(3, 5)), float(F(4, 5)))


@pytest.mark.parametrize("exponent", [-400, 0, 396])
def test_mixed_raw_vectors_match_complete_independent_polynomials(exponent):
    s = F(2)**exponent
    for module, n in ((G2, 2), (G3, 3)):
        a = (3*s, float(7*s), *([11*s] if n == 3 else []))
        b = (float(5*s), 13*s, *([float(-17*s)] if n == 3 else []))
        qa, qb = tuple(F(x) for x in a), tuple(F(x) for x in b)
        assert module.add(a, b) == tuple(float(x+y) for x, y in zip(qa, qb)), "mixed complete add"
        assert module.sub(a, b) == tuple(float(x-y) for x, y in zip(qa, qb)), "mixed complete sub"
        assert module.dot(a, b) == float(sum(x*y for x, y in zip(qa, qb))), "mixed complete dot"
        if n == 2:
            assert module.cross(a, b) == float(qa[0]*qb[1]-qa[1]*qb[0]), "mixed complete cross"
        else:
            expected = (qa[1]*qb[2]-qa[2]*qb[1], qa[2]*qb[0]-qa[0]*qb[2], qa[0]*qb[1]-qa[1]*qb[0])
            assert module.cross(a, b) == tuple(float(x) for x in expected), "mixed complete cross"
            assert module.mul(a, float(s)) == tuple(float(x*s) for x in qa)


def test_mixed_int_float_cancellation_retains_the_unit_residual():
    a, b = (2**54+1, 2**54+1, 0), (-float(2**54), -float(2**54), 0.)
    assert G3.add(a, b) == (1., 1., 0.), "mixed integer exact residual"
    assert G2.add(a[:2], b[:2]) == (1., 1.), "mixed integer exact residual"
    assert G3.dot((2**54+1, -2**54, 0), (1., 1., 0.)) == 1., "mixed dot residual"
    assert G2.cross((2**54+1, 2**54), (1., 1.)) == 1., "mixed determinant residual"


def test_mixed_raw_vectors_reject_outside_output_range_loudly():
    huge = 2**1024
    for module, n in ((G2, 2), (G3, 3)):
        with pytest.raises(D.ConstructionDomainError, match="scalar"):
            module.add((huge,)*n, (0.,)*n)
        with pytest.raises(D.ConstructionDomainError, match="scalar"):
            module.dot((huge,)*n, (1.,)*n)
    with pytest.raises(D.ConstructionDomainError, match="scalar"):
        G3.mul((F(1, 2**1074), 0, 0), .25)


@pytest.mark.parametrize("exponent", [-400, 0, 396])
def test_remaining_geometry_reports_and_exact_vectors_have_three_scale_references(exponent):
    s = F(2)**exponent
    points2 = [(0, 0), (3*s, 0), (3*s, 4*s), (0, 4*s)]
    assert G2.coord_scale(points2) == 4*s
    assert G2.neg(points2[2]) == (-3*s, -4*s)
    assert G2.reflect(points2) == [tuple(-x for x in p) for p in points2]
    floor = F(2)**-46 * 4*s
    assert G2.round_floor(4*s) == float(floor)
    assert G2.eff_tol(s/2, points2) == s/2
    assert G2.angle_floor(4*s, 3*s) == float(F(2)**-46*F(4, 3))
    assert G2.turn_floor(points2, 0) == float(F(2)**-46*F(4, 3))
    p = G3.box(center=(F(3, 2)*s, 2*s, 6*s), half=(F(3, 2)*s, 2*s, 6*s))
    assert p.metrics() == (12*s, float(13*s), float(3*s)), "independent metric components"
    assert G3.coord_scale(*p.verts) == 12*s
    assert G3.noise_floor(12*s) == float(F(2)**-46*12*s)
    assert G3.neg(p.verts[6]) == tuple(-x for x in p.verts[6])
    assert p.reflected().verts == [tuple(-x for x in v) for v in p.verts]
    assert G3.exact_vector((float(s), 3*s, 0)) == (s, 3*s, 0)
    assert G3.exact_edge_vector(p, (0, 1)) == (3*s, 0, 0)
    assert G3.exact_face_normal(p, 0) == (0, 0, -24*s*s)
    t = G3.tetra((0, 0, 0), (3*s, 0, 0), (0, 4*s, 0), (0, 0, 12*s))
    assert t.verts == [(0, 0, 0), (3*s, 0, 0), (0, 4*s, 0), (0, 0, 12*s)]
    tri = [(0, 0, 0), (3*s, 0, 0), (0, 4*s, 0)]
    assert set(G3.exact_triangle_intersection(tri, tri)) == set(tri)


@pytest.mark.parametrize("exponent", [-400, 0, 396])
def test_interior_point_declared_roundoff_bound_on_analytic_box(exponent):
    s = F(2)**exponent
    p = G3.box(center=(F(3, 2)*s, 2*s, 6*s), half=(F(3, 2)*s, 2*s, 6*s))
    # First bottom triangle has center (s, 8s/3, 0), inward step eps*13s.
    exact = (s, F(8, 3)*s, F(.001)*13*s)
    actual = p.interior_point()
    assert all(abs(F(x)-r) <= F(16, 2**53)*13*s for x, r in zip(actual, exact)), "interior point roundoff bound"
    assert all(0 < F(x) < hi*s for x, hi in zip(actual, (3, 4, 12)))


@pytest.mark.parametrize("exponent", [-1070, -400, 0, 400, 1023, 1100])
def test_face_noise_support_does_not_depend_on_intermediate_edge_range(exponent):
    s = F(2)**exponent
    # Raw rational coordinates have no binary64 range restriction. Long edges
    # are not outputs; the final dimensionless ratio has an ordinary value.
    p = G3.Polyhedron([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [(0, 1, 2, 3)])
    assert p.face_noise(0) == float(F(2)**-46), "face noise final rational ratio"


@pytest.mark.parametrize("exponent", [-400, 0, 390])
def test_face_noise_non_axis_error_bound_is_independently_squared(exponent):
    s = F(2)**exponent
    p = G3.Polyhedron([(0, 0, 0), (s, 0, 0), (0, s, 0)], [(0, 1, 2)])
    value = F(p.face_noise(0))/F(2)**-46
    # Exact target is 2+sqrt(2). No reference square root implementation.
    delta = F(3, 2**53)*4
    assert (value-2-delta)**2 <= 2 <= (value-2+delta)**2, "face noise radical error bound"


def test_predicates_keep_full_finite_int_fraction_domain():
    for s in (F(2)**-2000, F(2)**2000):
        assert G2.orient2d((0, 0), (s, 0), (0, s)) == 1
        assert G3.orient3d((0, 0, 0), (s, 0, 0), (0, s, 0), (0, 0, s)) != 0
        assert G2.point_in_polygon((s/2, s/2), [(0, 0), (s, 0), (s, s), (0, s)]) == 1


def test_domain_check_removal_is_caught_inside_the_real_input_guard(monkeypatch):
    source = inspect.getsource(D.check_input)
    old = "if q and not INPUT_MIN <= abs(q) <= INPUT_MAX:"
    assert old in source
    namespace = dict(vars(D))
    exec(compile(source.replace(old, "if False:"), "<R13FIXb removed guard>", "exec"), namespace)
    monkeypatch.setattr(D, "check_input", namespace["check_input"])
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        test_outside_engineering_input_envelope_is_a_named_domain_error(F(2)**401)


def test_mixed_gate_rejects_real_internal_early_coercion(monkeypatch):
    source = inspect.getsource(G3.add)
    assert "float_algebra((*a, *b))" in source
    namespace = dict(vars(G3))
    exec(compile(source.replace("float_algebra((*a, *b))", "all(type(x) is float for x in (*a, *b))"),
                 "<R13FIXb early coercion>", "exec"), namespace)
    monkeypatch.setattr(G3, "add", namespace["add"])
    with pytest.raises(AssertionError, match="mixed integer exact residual"):
        test_mixed_int_float_cancellation_retains_the_unit_residual()


def test_scalar_output_guard_removal_is_caught(monkeypatch):
    source = inspect.getsource(C.scalar_rational)
    old = "if exact and result == 0 and not allow_underflow:"
    assert old in source
    namespace = dict(vars(C))
    exec(compile(source.replace(old, "if False:"), "<R13FIXb underflow guard removed>", "exec"), namespace)
    monkeypatch.setattr(C, "scalar_rational", namespace["scalar_rational"])
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        test_nonfinite_conversion_and_unrepresentable_outputs_are_named_domain_errors()


def test_face_noise_internal_early_edge_length_is_caught(monkeypatch):
    source = textwrap.dedent(inspect.getsource(G3.Polyhedron.face_noise))
    assert "_extended_edge_length(" in source
    namespace = dict(vars(G3))
    exec(compile(source.replace("_extended_edge_length(", "Fraction(norm(" ).replace(
        "(f[i], f[(i+1)%len(f)])))", "(f[i], f[(i+1)%len(f)]))))"),
        "<R13FIXb early edge length>", "exec"), namespace)
    monkeypatch.setattr(G3.Polyhedron, "face_noise", namespace["face_noise"])
    with pytest.raises(D.ConstructionDomainError):
        test_face_noise_support_does_not_depend_on_intermediate_edge_range(1100)
