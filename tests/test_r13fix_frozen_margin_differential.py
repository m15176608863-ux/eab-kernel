"""Final frozen values/jets and margin fields, independently parameterised.

Oracle: Cartesian planes/lines and rational 3-4-5 projection derivatives.
Only the test-owned Fraction-to-float reference constructs expected views;
no production normal, projection, Newell, distance or derivative helper does.
"""
from fractions import Fraction as F
import inspect
import math

import pytest

from construction_oracle import scalar_exact
from eab.dual import Dual
from eab.kernel3d.geom3 import Polyhedron
from eab.kernel3d import frozen
from eab import margin


@pytest.mark.parametrize("exponent", [-1074, -600, 0, 600, 1018])
@pytest.mark.parametrize("kind", ["VF", "FV", "EE", "VV3", "VE3", "EV3"])
def test_frozen_public_gap_normal_and_jets_match_rational_values(exponent, kind):
    s = F(2)**exponent
    zero = (0, 0, 0)
    if kind in ("VF", "FV"):
        point = Polyhedron([(0, 0, Dual(scalar_exact(3*s), (scalar_exact(2*s),)))], [])
        plane = Polyhedron([(0, 0, 0), (s, 0, 0), (0, s, 0)], [(0, 1, 2)])
        A, B = (point, plane) if kind == "VF" else (plane, point)
        label = (kind, ("V", 0), ("F", 0)) if kind == "VF" else (kind, ("F", 0), ("V", 0))
        n, dn, gap, dg = (0, 0, 1 if kind == "VF" else -1), (0, 0, 0), 3*s, 2*s
    elif kind == "EE":
        z = Dual(scalar_exact(3*s), (scalar_exact(2*s),))
        A, B = Polyhedron([(0, 0, z), (s, 0, z)], []), Polyhedron([(0, 0, 0), (0, s, 0)], [])
        label = (kind, ("E", 0, 1), ("E", 0, 1))
        n, dn, gap, dg = (0, 0, 1), (0, 0, 0), 3*s, 2*s
    elif kind == "VV3":
        A = Polyhedron([(Dual(scalar_exact(3*s), (scalar_exact(5*s),)), 4*s, 0)], [])
        B, label = Polyhedron([zero], []), (kind, ("V", 0), ("V", 0))
        n, dn, gap, dg = (F(3, 5), F(4, 5), 0), (F(16, 25), -F(12, 25), 0), 5*s, 3*s
    else:
        point = Polyhedron([(s, 3*s, Dual(scalar_exact(4*s), (scalar_exact(5*s),)))], [])
        line = Polyhedron([zero, (2*s, 0, 0)], [])
        A, B = (point, line) if kind == "VE3" else (line, point)
        label = (kind, ("V", 0), ("E", 0, 1)) if kind == "VE3" else (kind, ("E", 0, 1), ("V", 0))
        sign = 1 if kind == "VE3" else -1
        n = (0, sign*F(3, 5), sign*F(4, 5))
        dn, gap, dg = (0, -sign*F(12, 25), sign*F(9, 25)), 5*s, 4*s
    actual_n = frozen.frozen_normal(A, B, label, ee_sign=-1)
    for component, expected, derivative in zip(actual_n, n, dn):
        value = component.v if isinstance(component, Dual) else component
        channels = component.e if isinstance(component, Dual) else (0.0,)
        assert value == scalar_exact(expected), "frozen normal final coordinate"
        assert channels == (scalar_exact(derivative),), "frozen normal final derivative"
    actual_g = frozen.frozen_gap(A, B, label, zero, ee_sign=-1, delta=s)
    assert actual_g.v == scalar_exact(gap-s), "frozen gap complete expression"
    assert actual_g.e == (scalar_exact(dg),), "frozen gap final derivative"
    wrapped = margin.margin_gap_from_frozen_cover(A, B, label, zero, s, ee_sign=-1)
    assert wrapped == actual_g, "margin frozen entry point is value-bound"


@pytest.mark.parametrize("exponent", [-1074, -600, 0, 600, 1018])
def test_face_edge_normals_and_frozen_lift_have_independent_extreme_jets(exponent):
    s = F(2)**exponent
    bend = Dual(0.0, (scalar_exact(s),))
    triangle = Polyhedron([(0, 0, 0), (s, 0, bend), (0, s, 0)], [(0, 1, 2)])
    try:
        normal = frozen.face_normal_generic(triangle, 0)
    except ArithmeticError as error:
        raise AssertionError("representable face jet must survive intermediate scale") from error
    assert tuple(c.v for c in normal) == (0.0, 0.0, 1.0), "face jet primal"
    assert tuple(c.e[0] for c in normal) == (-1.0, 0.0, 0.0), "face jet derivative"
    edge = Polyhedron([(0, 0, 0), (s, 0, bend)], [])
    other = Polyhedron([(0, 0, 0), (0, s, 0)], [])
    normal = frozen.ee_normal_generic(edge, (0, 1), other, (0, 1), sign=-1)
    assert tuple(c.v for c in normal) == (0.0, 0.0, 1.0), "edge jet primal"
    assert tuple(c.e[0] for c in normal) == (-1.0, 0.0, 0.0), "edge jet derivative"
    plane = Polyhedron([(0, 0, 0), (s, 0, 0), (0, s, 0)], [(0, 1, 2)])
    point = Polyhedron([(0, 0, 3*s)], [])
    label = ("VF", ("V", 0), ("F", 0))
    assert frozen.frozen_lift(point, plane, label, (0, 0, 0)) == -3*s, "exact frozen lift ratio"
    lifted = frozen.frozen_lift(point, plane, label, (0, 0, Dual(0.0, (scalar_exact(2*s),))))
    assert lifted.v == scalar_exact(-3*s) and lifted.e == (scalar_exact(-2*s),), "lift final jet"


@pytest.mark.parametrize("exponent", [-1074, -600, 0, 600, 1018])
def test_margin_public_distance_projection_normal_and_gap_are_value_bound(exponent):
    s = F(2)**exponent
    point = (3*s, 4*s, 0)
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    corners = [(0, -1, -1), (1, -1, -1), (1, 1, -1), (0, 1, -1),
               (0, -1, 1), (1, -1, 1), (1, 1, 1), (0, 1, 1)]
    # Closed surfaces; unlike the earlier exploratory singleton input these
    # satisfy body_distance's nonempty-surface precondition. Unit face areas
    # remain expressible while the independently known separation is extreme.
    A = Polyhedron([(F(x)+s, y, z) for x, y, z in corners], list(faces))
    B = Polyhedron([(x-1, y, z) for x, y, z in corners], list(faces))
    distance, label = margin.body_distance(A, B)
    assert distance == scalar_exact(s), "body distance final value"
    contacts = margin.margin_contacts(A, B, delta=s)
    assert contacts, "nonempty contact grid"
    for contact in contacts:
        assert contact.distance == scalar_exact(s), "margin distance final value"
        assert contact.margin_gap == 0.0 and contact.closed, "margin difference final value"
        assert contact.exact_distance_squared == s*s, "margin independent distance certificate"
        assert contact.normal == (1.0, 0.0, 0.0), "margin final direction"
        assert contact.point_a[0] == scalar_exact(s) and contact.point_b[0] == 0.0, "margin point fields"
        assert contact.point_a[1:] == contact.point_b[1:], "margin nearest witness binding"
    E = Polyhedron([(0, 0, 0)], [])
    assert margin.distance_to_convex_entrance(E, point) == scalar_exact(5*s), "convex distance"
    assert margin.nearest_point_on_convex_entrance(E, point) == (0., 0., 0.), "convex projection display"
    assert margin.nearest_point_on_convex_entrance(E, point, exact=True) == (0, 0, 0), "convex projection exact"
    assert margin.inflated_normal(E, point) == (scalar_exact(F(3, 5)), scalar_exact(F(4, 5)), 0.), "convex direction"


def test_frozen_differential_gate_rejects_internal_early_raw_rounding(monkeypatch):
    source = inspect.getsource(frozen._unit_jet)
    needle = "nn = dot(n, n)"
    assert source.count(needle) == 1
    source = source.replace(needle, "n = tuple(float(c) for c in n)\n    nn = sum(c*c for c in n)")
    scope = dict(vars(frozen))
    exec(compile(source, "<r13-unit-jet-rounded-raw>", "exec"), scope)
    monkeypatch.setattr(frozen, "_unit_jet", scope["_unit_jet"])
    with pytest.raises(AssertionError, match="representable face jet must survive intermediate scale"):
        test_face_edge_normals_and_frozen_lift_have_independent_extreme_jets(-1074)
