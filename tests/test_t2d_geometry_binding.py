"""G0 binding of exact input polygons to the support and element contracts.

Primitives are rational dot products, cross products and set symmetries;
no production geometric primitive is reused. Negative controls corrupt an
internal input provider before these geometric assertions are evaluated.
"""
from fractions import Fraction as F
import unittest
from unittest.mock import patch

import tests.t2d_knob_family_exact as exact


def verify_element_contract(element):
    vertices = exact.element_vertices(element)
    if element == "K16":
        assert len(vertices) == len(set(vertices)) == 16, "K16 must have 16 distinct vertices"
        assert all(x*x+y*y == 1 for x, y in vertices), "K16 vertex must stay on unit circle"
        assert max(x for x, _ in vertices) == F(99, 101), "K16 horizontal support changed"
        assert max(x*x+y*y for x, y in vertices) == 1, "K16 maximum support radius changed"
    points = set(vertices)
    assert points == {(-x, -y) for x, y in vertices}, "central symmetry failed"
    assert points == {(-x, y) for x, y in vertices}, "axis reflection failed"
    assert points == {(y, x) for x, y in vertices}, "diagonal reflection failed"
    hull = exact.convex_hull(vertices)
    assert len(hull) == len(vertices), "all tolerance points must be exposed vertices"
    assert all(a[0]*b[1]-a[1]*b[0] > 0 for a, b in zip(hull, hull[1:]+hull[:1])), \
        "origin must lie strictly inside the tolerance element"
    return vertices


def verify_q_support_binding(n):
    q = exact.verify_family_geometry(n)["Q"]
    candidate_edges = exact.edge_candidates(n, "square")
    supports = tuple(((sx*edge["normal"][0], edge["normal"][1]), edge["offset"])
                     for edge in candidate_edges for sx in (-1, 1))
    assert len(supports) == len(q) == 2*n
    matches = []
    for a, b in zip(q, q[1:]+q[:1]):
        active = tuple(i for i, (m, r) in enumerate(supports)
                       if m[0]*a[0]+m[1]*(a[1]-1) == r
                       and m[0]*b[0]+m[1]*(b[1]-1) == r)
        assert len(active) == 1, "every polygon edge must match exactly one listed support"
        matches.append(active[0])
    assert sorted(matches) == list(range(2*n)), "support-to-edge binding must be bijective"
    for m, r in supports:
        assert all(m[0]*x+m[1]*(y-1) <= r for x, y in q), "listed support is not outward"
    return supports


def test_t2d_elements_have_declared_exact_symmetries_and_K16_radius():
    for element in ("square", "octagon", "K16"):
        verify_element_contract(element)


def test_t2d_K16_one_vertex_numerator_mutation_is_rejected():
    original = exact.element_vertices

    def wrong_vertex(element):
        vertices = original(element)
        x, y = vertices[0]
        return ((x+F(1, 101), y),)+vertices[1:]

    with patch.object(exact, "element_vertices", wrong_vertex):
        with unittest.TestCase().assertRaisesRegex(AssertionError, "unit circle"):
            verify_element_contract("K16")


def test_t2d_Q_order_and_all_supports_bind_bijectively():
    for n in (4, 8, 16, 32, 64, 128):
        verify_q_support_binding(n)


def test_t2d_Q_internal_vertex_order_mutation_is_rejected():
    original = exact.family_geometry

    def wrong_order(n):
        geometry = original(n)
        q = geometry["Q"]
        geometry["Q"] = q[:1]+(q[2], q[1])+q[3:]
        return geometry

    with patch.object(exact, "family_geometry", wrong_order):
        with unittest.TestCase().assertRaisesRegex(AssertionError, "strictly convex"):
            verify_q_support_binding(8)
