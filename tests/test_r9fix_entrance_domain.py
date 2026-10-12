"""R9 finite contact-domain gates, independent raw-coordinate Fraction oracle.

The oracle uses only inline coordinate differences, determinants and closed
interval products, not production Minkowski, cone, segment or witness helpers.
"""
from fractions import Fraction as F

import pytest

from eab.kernel2d.entrance import first_entrance


POSES = [(F(1), (F(1), F(0)), (F(0), F(0))),
         (F(1, 10**9), (F(1), F(0)), (F(0), F(0))),
         (F(10**8), (F(1), F(0)), (F(0), F(0))),
         (F(1), (F(3, 5), F(4, 5)), (F(10**8), F(-10**8)))]


def _pose(points, scale, rotation, translation=(0, 0)):
    c, s = rotation
    return [(scale*(c*F(x)-s*F(y))+translation[0],
             scale*(s*F(x)+c*F(y))+translation[1]) for x, y in points]


def _finite_contact(A, B, x, label):
    """Independent closed point/segment or collinear segment intersection."""
    A = [(F(p[0])+x[0], F(p[1])+x[1]) for p in A]
    B = [tuple((F(_r12_item) for _r12_item in p)) for p in B]
    kind, ai, bj = label
    def on(p, a, b):
        return ((b[0]-a[0])*(p[1]-a[1]) == (b[1]-a[1])*(p[0]-a[0])
                and all(min(a[i], b[i]) <= p[i] <= max(a[i], b[i]) for i in range(2)))
    if kind == 'VE':
        return on(A[ai], B[bj], B[(bj+1) % len(B)])
    if kind == 'EV':
        return on(B[bj], A[ai], A[(ai+1) % len(A)])
    assert kind == 'FF'
    a, b = A[ai], A[(ai+1) % len(A)]
    c, d = B[bj], B[(bj+1) % len(B)]
    return on(a, c, d) or on(b, c, d) or on(c, a, b) or on(d, a, b)


def _assert_contact_labels(A, B, x, result):
    assert result.kind == 'entrance'
    assert result.label in result.tied_labels
    assert all(_finite_contact(A, B, x, lab) for lab in result.tied_labels), (
        'every exact tie must have finite source-feature contact', result)
    assert result.point_a == result.point_b, ('entrance witnesses must coincide', result)


@pytest.mark.parametrize('pose', POSES)
@pytest.mark.parametrize('swapped', [False, True])
@pytest.mark.parametrize('horizontal', [F(1, 2), F(1), F(3, 2)])
def test_collinear_support_chooses_only_contacting_source_edge(pose, swapped, horizontal):
    """At t=1 the unique low triangle vertex hits the raw B top interval."""
    scale, rotation, translation = pose
    A = _pose([(0, 0), (1, 1), (0, 2)], scale, rotation, translation)
    B = _pose([(0, 0), (3, 0), (3, 1), (1, 1), (0, 1)], scale, rotation, translation)
    x0 = _pose([(horizontal, 2)], scale, rotation)[0]
    direction = _pose([(0, -1)], scale, rotation)[0]
    kind = 'VE'
    if swapped:
        A, B = B, A
        x0, direction = tuple(-v for v in x0), tuple(-v for v in direction)
        kind = 'EV'
    result = first_entrance(A, B, x0, direction)
    assert result.t_exact == 1
    x = tuple(x0[i]+direction[i] for i in range(2))
    expected_edges = {3} if horizontal < 1 else ({2} if horizontal > 1 else {2, 3})
    expected = {(kind, 0, j) if kind == 'VE' else (kind, j, 0) for j in expected_edges}
    assert set(result.tied_labels) == expected, ('finite source edge labels', result, expected)
    assert result.label in expected, ('selected label must lie in finite contact domain', result)
    _assert_contact_labels(A, B, x, result)


@pytest.mark.parametrize('pose', POSES)
def test_flat_chain_boundary_ff_has_a_real_overlapping_segment(pose):
    """Independent rectangle intervals touch only at transformed (1,1)."""
    scale, rotation, translation = pose
    A = _pose([(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (0, 0)],
              scale, rotation, translation)
    B = _pose([(-1, 0), (0, 0), (1, 0), (1, 1), (0, 1), (-1, 1)],
              scale, rotation, translation)
    x = _pose([(1, 2)], scale, rotation)[0]
    direction = _pose([(2, 1)], scale, rotation)[0]
    result = first_entrance(A, B, x, direction)
    assert result.t_exact == 0
    _assert_contact_labels(A, B, x, result)


@pytest.mark.parametrize('horizontal', [F(-1), F(-1, 2), F(0), F(1, 2), F(1), F(2), F(3)])
def test_unequal_flat_chains_remap_all_selected_and_tied_ff_domains(horizontal):
    """Raw rectangles [-x,4-x] and [0,3] first meet at their y=1 planes."""
    A = [(0, 0), (1, 0), (4, 0), (4, 2), (0, 2)]
    B = [(0, 0), (3, 0), (3, 1), (2, 1), (F(1, 2), 1), (0, 1)]
    x0, direction = (horizontal, F(2)), (F(0), F(-1))
    result = first_entrance(A, B, x0, direction)
    assert result.t_exact == 1
    _assert_contact_labels(A, B, (horizontal, F(1)), result)


def test_finite_domain_gate_has_teeth_inside_the_selected_feature_path(monkeypatch):
    """Remove production's exact finite-domain predicate, not output records."""
    from eab.kernel2d import entrance as E
    monkeypatch.setattr(E, '_facet_in_domain', lambda *args: True)
    with pytest.raises(AssertionError, match='finite source edge labels'):
        test_collinear_support_chooses_only_contacting_source_edge(POSES[0], False, F(1, 2))
