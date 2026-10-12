"""R6 construction gates. Oracles are interval products and exact arithmetic;
they share no hull, cover, projection, normal or distance primitive with eab.
"""
from fractions import Fraction as F
from pathlib import Path
import math
import inspect

import pytest

from eab.kernel2d.entrance import shortest_exit, first_entrance
from eab.kernel2d.covers import ve_cover, ev_cover, facet_gap
from eab.kernel3d.geom3 import box
import eab.margin as M


def _square(s):
    return [(0, 0), (s, 0), (s, s), (0, s)]


@pytest.mark.parametrize("exponent", [-600, 0, 600])
def test_g6f06_exit_gap_preserves_representable_nonzero_magnitude(exponent):
    s = 2.**exponent
    r = shortest_exit(_square(s), _square(s), (s/2, 0))
    assert r.kind == "exit"
    assert r.label == ("VE", 0, 1)
    assert r.normal == (1., 0.)
    assert r.gap == -s/2, ("representable signed gap", r.gap, -s/2)


@pytest.mark.parametrize("exponent", [-600, 600])
def test_convex_ray_contact_construction_does_not_square_float_edges(exponent):
    s = 2.**exponent
    r = first_entrance(_square(s), _square(s), (2*s, s/2), (-s, 0))
    assert r.kind == "entrance" and r.t_exact == 1
    assert r.point_a == r.point_b == (s, s/2)
    assert r.gap == 0


@pytest.mark.parametrize("translation", [F(0), F(1000), F(10**8)])
@pytest.mark.parametrize("s", [F(1, 10**9), F(1, 2**600), F(2**600)])
def test_g6f08_distance_and_normal_use_exact_relative_projection(translation, s):
    E = box(center=(translation+2*s, 0, 0), half=(s, s, s))
    x = (translation, 0, 0)
    assert M.distance_to_convex_entrance(E, x) == float(s), "exact relative distance"
    assert M.inflated_normal(E, x) == (-1., 0., 0.), "nonzero exact relative normal"
    assert M.nearest_point_on_convex_entrance(E, x) == (float(translation+s), 0., 0.)


def _assert_current_margin_description(doc):
    line = next(line for line in doc.splitlines() if line.startswith("| **1** 定义"))
    assert "仍先浮点构造" not in line, "stale pre-rounded margin difference claim"
    assert "test_entrance_block_forms_differences_before_any_float_rounding" in line


def test_g6f10_canon_definition_matches_exact_difference_contract():
    _assert_current_margin_description((Path(__file__).parents[1]/"docs/canon_map.md").read_text(encoding="utf-8"))


def test_margin_internal_cached_views_are_isolated():
    E = box()
    vertices, faces = tuple(E.verts), tuple(E.faces)
    view, _ = M._surface_view(vertices, faces)
    view.verts = [(x+100, y, z) for x, y, z in view.verts]
    fresh, _ = M._surface_view(vertices, faces)
    assert tuple(fresh.verts) == vertices, "surface payload alias"


def test_margin_internal_cached_records_are_isolated():
    A, B = box(center=(0, 0, 3)), box()
    resolved = M._resolved(A, B, 0., None, None)
    first = resolved[2][0][0]
    original = first.gap
    first.gap = 12345.
    again = M._resolved(A, B, 0., None, None)
    assert again[2][0][0].gap == original, "record payload alias"


def test_rational_sqrt_rounds_only_the_final_root():
    from eab.construction import sqrt_rational
    for s in (F(1, 2**1074), F(1, 2**600), F(3, 7), F(2**600), F(float.fromhex('0x1.fffffffffffffp1023'))):
        assert sqrt_rational(s*s) == float(s)
    midpoint = F(1)+F(1, 2**53)
    assert sqrt_rational(midpoint**2-F(1, 2**300)) == 1.
    assert sqrt_rational(midpoint**2) == 1.
    assert sqrt_rational(midpoint**2+F(1, 2**300)) == math.nextafter(1., math.inf)
    with pytest.raises(ArithmeticError, match="below binary64"):
        sqrt_rational(F(1, 2**2200))
    with pytest.raises(OverflowError):
        sqrt_rational(F(2**2200))


def test_g6f06_gap_magnitude_gate_has_teeth(monkeypatch):
    import eab.kernel2d.entrance as E
    monkeypatch.setattr(E, "sqrt_rational", lambda value, **kwargs: math.sqrt(float(value)))
    with pytest.raises(AssertionError, match="representable signed gap") as caught:
        test_g6f06_exit_gap_preserves_representable_nonzero_magnitude(-600)
    print("G6F-06 mutant:", caught.value)


def test_g6f08_relative_projection_gate_has_teeth(monkeypatch):
    source = inspect.getsource(M.nearest_point_on_convex_entrance)
    step = "return point if exact else tuple(map(float, point))"
    assert step in source
    scope = dict(vars(M))
    exec(source.replace(step, "return tuple(map(float, point))"), scope)
    monkeypatch.setattr(M, "nearest_point_on_convex_entrance", scope["nearest_point_on_convex_entrance"])
    with pytest.raises(AssertionError, match="exact relative distance") as caught:
        test_g6f08_distance_and_normal_use_exact_relative_projection(F(10**8), F(1, 10**9))
    print("G6F-08 mutant:", caught.value)


def test_g6f10_canon_contract_gate_has_teeth():
    doc = (Path(__file__).parents[1]/"docs/canon_map.md").read_text(encoding="utf-8")
    old = "先有理化输入再作 b−a"
    assert old in doc
    with pytest.raises(AssertionError, match="stale pre-rounded") as caught:
        _assert_current_margin_description(doc.replace(old, "仍先浮点构造 b−a"))
    print("G6F-10 mutant:", caught.value)


def test_mixed_scalar_cover_gap_differences_are_formed_before_rounding():
    T, s = F(10**8), F(1, 10**9)
    A = [(T+s, 0), (T+s+1, 0), (T+s+1, 1), (T+s, 1)]
    B = [(float(T-1), 0.), (float(T), 0.), (float(T), 1.), (float(T-1), 1.)]
    c = ve_cover(A, 0, B, 1)
    d = ev_cover(B, 1, A, 0)
    assert c.gap == d.gap == float(s), "mixed scalar cover gap"
    assert facet_gap(A, B, ("VE", 0, 1), (0, 0)) == float(s)


def test_projection_exposes_exact_witness_beyond_global_float_resolution():
    T, s = F(10**8), F(1, 10**9)
    E = box(center=(T+2*s, 0, 0), half=(s, s, s))
    assert M.nearest_point_on_convex_entrance(E, (T, 0, 0), exact=True) == (T+s, 0, 0)
    assert M.nearest_point_on_convex_entrance(E, (T, 0, 0))[0] == float(T)


def test_exact_relative_projection_covariance_on_nonaxis_corner():
    # Rational 3-4-5 rotation. A corner projection with unequal offsets ensures
    # a missing component or a face-only shortcut cannot satisfy the oracle.
    R = ((F(3, 5), F(-4, 5), 0), (F(4, 5), F(3, 5), 0), (0, 0, 1))
    def rotate(p):
        return tuple(sum(F(a)*b for a, b in zip(row, p)) for row in R)
    from eab.kernel3d.geom3 import Polyhedron
    for scale in (F(1, 2**600), F(1), F(2**600)):
        for t in (0, 10**3, 10**5, 10**6):
            translation = (F(t), F(-3*t), F(2*t))
            E = box(center=(2*scale, 3*scale, 0), half=(scale, scale, scale))
            P = Polyhedron([tuple(c+o for c, o in zip(rotate(p), translation)) for p in E.verts], E.faces)
            assert M.distance_to_convex_entrance(P, translation) == pytest.approx(float(scale)*math.sqrt(5), rel=2e-16, abs=0)
            target = tuple(float(c)/math.sqrt(5) for c in rotate((-1, -2, 0)))
            assert M.inflated_normal(P, translation) == pytest.approx(target, rel=2e-16, abs=0)


def test_unrepresentable_geometric_norm_fails_loudly():
    from eab.kernel3d.geom3 import norm
    with pytest.raises(OverflowError):
        norm((float.fromhex('0x1.fffffffffffffp1023'),)*3)


def test_unit_vector_is_constructed_even_when_unscaled_norm_overflows():
    from eab.kernel3d.geom3 import unit
    largest = float.fromhex('0x1.fffffffffffffp1023')
    assert unit((largest, largest, largest)) == pytest.approx((1/math.sqrt(3),)*3, rel=2e-16)


@pytest.mark.parametrize("exponent", [-1100, -1075, -600, 0])
def test_cover_construction_exposes_exact_nonzero_gap_and_area(exponent):
    from eab.kernel3d import covers3 as C
    from eab.kernel3d.geom3 import Polyhedron
    s = F(2)**exponent
    base = box()
    A = Polyhedron([tuple((F(x)+3)*s for x in p) for p in base.verts], list(base.faces))
    B = Polyhedron([tuple(F(x)*s for x in p) for p in base.verts], list(base.faces))
    full = C.enumerate_covers3(A, B, window=math.inf)
    assert len(full) == 1 and full[0].kind == "VV3"
    c = full[0]
    assert c.exact_gap_squared == 3*s*s and c.exact_gap_sign == 1, "exact gap certificate"
    if exponent == -1075:
        assert c.gap == float.fromhex('0x0.0000000000001p-1022'), "round final norm, not its components"
    elif exponent == -1100:
        assert c.gap == 0 and c.exact_gap_squared > 0
    else:
        assert c.gap == pytest.approx(float(s)*math.sqrt(3), rel=2e-16, abs=0)
    raw = C.enumerate_covers3(A, B, window=math.inf, require_in_extent=False)
    facets = [r for r in raw if r.kind in ("VF", "FV")]
    assert facets
    assert all(r.exact_area_squared == 16*s**4 for r in facets), "exact area certificate"
    assert C.enumerate_covers3(A, B, window=0) == []


def test_face_area_rounds_final_value_and_rejects_unrepresentable_output():
    from eab.kernel3d.geom3 import Polyhedron
    s = F(1, 2**1074)
    p = Polyhedron([(0, 0, 0), (1, 0, 0), (1, 3*s, 0)], [(0, 1, 2)])
    assert p.face_area(0) == float(2*s), "area tie rounds once to even"
    p.verts[2] = (1, s/4, 0)
    with pytest.raises(ArithmeticError, match="below binary64"):
        p.face_area(0)
