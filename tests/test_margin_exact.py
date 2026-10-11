"""E5b exact/default and explicit-window gates, with raw-coordinate oracles.

Oracles use interval products and Fraction coordinate differences only; no
production relation, cover, normal, distance, hull or tolerance primitive.
"""
from fractions import Fraction as F
import inspect
import math

import pytest

import eab.margin as M
from eab.kernel3d.geom3 import Polyhedron, box, tetra


def _pair(gap):
    return box((0, 0, 1+gap), (.5, .5, .5)), box(half=(.5, .5, .5))


def _signed_gap(A, B):
    return min(F(p[2]) for p in A.verts)-max(F(p[2]) for p in B.verts)


def _assert_window_contract():
    # Binary-exact separations: boundary on both sides is tested, not merely
    # values comfortably inside the window.
    w = 2.**-24
    for ratio in (-2, -1, -.5, 0, .5, 1, 2):
        A, B = _pair(ratio*w)
        gap = _signed_gap(A, B)
        assert gap == F(ratio)*F(w)
        d, label = M.body_distance(A, B, contact_window=w)
        expected = M.INSIDE if gap < -F(w) else M.OUTSIDE if gap > F(w) else M.ON_BOUNDARY
        assert M.inflated_membership(A, B, delta=0, contact_window=w) == expected, ("explicit-window", gap, w)
        assert (label == (M.PENETRATING,)) == (gap < -F(w)), ("explicit-window", gap, label)
        assert d == (float(gap) if gap > F(w) else 0), ("explicit-window", gap, d)
        contacts = M.margin_contacts(A, B, delta=0, contact_window=w)
        assert bool(contacts) == (gap <= F(w)), ("explicit-window", gap, contacts)
        if contacts:
            assert all(c.closed and c.distance == 0 for c in contacts)


def _assert_default_contract():
    for gap0 in (-2.**-35, 0, 2.**-35):
        A, B = _pair(gap0)
        gap = _signed_gap(A, B)
        expected = M.INSIDE if gap < 0 else M.OUTSIDE if gap > 0 else M.ON_BOUNDARY
        d, label = M.body_distance(A, B)
        assert M.inflated_membership(A, B, delta=0) == expected, ("default-exact", gap)
        assert (label == (M.PENETRATING,)) == (gap < 0), ("default-exact", gap, label)
        assert d == max(0, float(gap)), ("default-exact", gap, d)
        assert bool(M.margin_contacts(A, B, delta=0)) == (gap <= 0)


def test_explicit_window_matches_exact_interval_oracle():
    _assert_window_contract()


def test_default_has_no_hidden_contact_resolution():
    _assert_default_contract()


def test_margin_window_and_default_guards_have_internal_mutation_teeth(monkeypatch):
    original = inspect.getsource(M._resolve)
    def mutant(source):
        namespace = dict(M.__dict__)
        exec(compile(source, "<E5b internal margin mutation>", "exec"), namespace)
        return namespace["_resolve"]
    ignored = original.replace("ctol = _contact_window(contact_window)", "ctol = Fraction(0)")
    assert ignored != original
    monkeypatch.setattr(M, "_resolve", mutant(ignored))
    with pytest.raises(AssertionError, match="explicit-window"):
        _assert_window_contract()
    implicit = original.replace("ctol = _contact_window(contact_window)",
                                "ctol = _contact_window(contact_resolution(A, B) if contact_window is None else contact_window)")
    assert implicit != original
    monkeypatch.setattr(M, "_resolve", mutant(implicit))
    with pytest.raises(AssertionError, match="default-exact"):
        _assert_default_contract()


@pytest.mark.parametrize("bad", [-1, math.inf, -math.inf, math.nan])
def test_contact_window_rejects_nonfinite_or_negative_values(bad):
    A, B = _pair(1)
    with pytest.raises(ValueError, match="contact_window"):
        M.body_distance(A, B, contact_window=bad)


def test_inflated_boundary_comparison_does_not_use_a_float_sqrt_or_implicit_band():
    A = box((2., 2., 0.), (.5, .5, .5))
    B = box(half=(.5, .5, .5))
    # Exact distance² = 2; float sqrt(2) lies strictly above the true distance.
    delta = math.sqrt(2.)
    assert F(delta)**2 > 2
    assert M.inflated_membership(A, B, delta=delta) == M.INSIDE
    assert M.inflated_membership(A, B, delta=math.nextafter(delta, 0.)) == M.OUTSIDE


def test_entrance_block_forms_differences_before_any_float_rounding():
    A = box((2.**54, 0, 0), (8, 1, 1))
    B = box((1., 0, 0), (.5, .5, .5))
    E = M.entrance_block_convex(A, B)
    differences = [tuple(F(b[k])-F(a[k]) for k in range(3)) for a in A.verts for b in B.verts]
    axes = [(1, 0, 0), (-1, 0, 0), (1, 2, 3), (3, -5, 2)]
    assert any(F(float(p[0])) != p[0] for p in differences)
    for n in axes:
        want = max(sum(n[k]*p[k] for k in range(3)) for p in differences)
        got = max(sum(n[k]*F(p[k]) for k in range(3)) for p in E.verts)
        assert got == want


def test_folded_source_ring_distance_uses_the_actual_surface_triangle():
    B0 = box()
    vertices = list(B0.verts)
    vertices[6] = (1., 1., 1.5)
    B = Polyhedron(vertices, B0.faces)
    A = tetra((0., -.5, 1.2), (.1, -.5, 2.2), (0., -.4, 2.2), (-.1, -.6, 2.2))
    # Ear (7,4,5) is exactly z=1; the tip projection is strictly in it.
    # The other top ear lies on x+y>=0; all other sides are farther away.
    expected = F(1.2)-1
    d, label = M.body_distance(A, B)
    assert d == float(expected)
    assert label[0] == "VF" and label[2][2] == "triangle"
    assert set(label[2][3:]) == {7, 4, 5}
    assert M.inflated_membership(A, B, delta=float(expected)) == M.ON_BOUNDARY
    assert M.inflated_membership(A, B, delta=math.nextafter(d, 0.)) == M.OUTSIDE
    assert M.inflated_membership(A, B, delta=math.nextafter(d, math.inf)) == M.INSIDE
    assert M.margin_gap_from_frozen_cover(A, B, label, (0, 0, 0), 0) == d
    # The obsolete Newell plane is only about 0.0123 away. An explicit 0.05
    # window must not mistake that non-surface descriptor for real contact.
    assert M.body_distance(A, B, contact_window=.05)[0] == d
    assert M.inflated_membership(A, B, delta=0, contact_window=.05) == M.OUTSIDE
    assert M.margin_contacts(A, B, delta=.1, contact_window=.05) == []


def test_closed_is_exact_when_the_display_gap_underflows_to_zero():
    # Both bodies have macroscopic size; only their exact rational separation
    # is below binary64. No geometry predicate may read the rounded display.
    gap = F(1, 2**1075)
    A = box((0, 0, F(1)+gap), (F(1, 2),)*3)
    B = box(half=(F(1, 2),)*3)
    assert _signed_gap(A, B) == gap > 0
    assert M.inflated_membership(A, B, delta=0) == M.OUTSIDE
    assert M.margin_contacts(A, B, delta=0) == []
    contacts = M.margin_contacts(A, B, delta=0, band=1)
    first = contacts[0]
    assert first.distance == first.margin_gap == 0
    assert not first.closed


def test_explicit_local_shell_window_does_not_require_global_rigid_escape():
    w = F(1, 2**20)
    e = w/4
    A = box(half=(F(1),)*3)
    left = box((-F(3, 2)+e/2, 0, 0), (F(1, 2)+e/2, 2, 2))
    right = box((F(3, 2)-e/2, 0, 0), (F(1, 2)+e/2, 2, 2))
    B = Polyhedron([*left.verts, *right.verts],
                   [*left.faces, *(tuple(i+8 for i in f) for f in right.faces)])
    # Independent product-interval certificates: penetration exists on both
    # sides; radius-L1=3 makes A's inner core [-1+w/3,1-w/3]^3 disjoint.
    assert max(F(v[0]) for v in left.verts) == -1+e
    assert min(F(v[0]) for v in right.verts) == 1-e
    assert -1+w/3 > -1+e and 1-w/3 < 1-e
    assert M.body_distance(A, B) == (0., (M.PENETRATING,))
    assert M.inflated_membership(A, B, delta=0, contact_window=w) == M.ON_BOUNDARY
    d, label = M.body_distance(A, B, contact_window=w)
    assert d == 0 and label != (M.PENETRATING,)
    assert M.margin_contacts(A, B, delta=0, contact_window=w)


def test_content_cache_is_value_identical_to_the_uncached_exact_path(monkeypatch):
    """Equivalent optimization gate: full reports, not merely relation votes."""
    cached = M._resolved
    for scale in (.001, 1., 1000.):
        for shift in (0., 1e5):
            for gap in (-.2, 0., .2):
                A = box((shift, shift, shift+scale*(1+gap)), (.5*scale,)*3)
                B = box((shift, shift, shift), (.5*scale,)*3)
                for window in (None, 0., .25*scale):
                    def report():
                        return (M.body_distance(A, B, contact_window=window),
                                M.inflated_membership(A, B, delta=.1*scale, contact_window=window),
                                M.margin_contacts(A, B, delta=.1*scale, band=.2*scale, contact_window=window))
                    monkeypatch.setattr(M, "_resolved", M._resolve)
                    uncached = report()
                    monkeypatch.setattr(M, "_resolved", cached)
                    assert report() == uncached
                    assert report() == uncached
