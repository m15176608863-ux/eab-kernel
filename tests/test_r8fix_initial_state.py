"""G6H-01: classify topological E, not strict intersection of body interiors.

Primary oracle: a U solid is the union of three Cartesian rectangles; their
Minkowski interval unions below use only Fraction arithmetic. No production
triangulation, membership, hull, angular-sector or cone primitive is shared.
"""
from construction_oracle import scalar_exact, sqrt_exact
from fractions import Fraction as F

import pytest

from eab.kernel2d import covers, entrance


def _tight_pair(asymmetric=False):
    left, right, bottom, low, height = ((2, 3, F(3, 4), F(1, 4), F(1, 2))
                                       if asymmetric else (1, 1, 1, F(1, 2), 1))
    A = [(0, low), (1, low), (1, low+height), (0, low+height)]
    B = [(-left, -bottom), (1+right, -bottom), (1+right, 2),
         (1, 2), (1, 0), (0, 0), (0, 2), (-left, 2)]
    # B's left/right-arm E cells join at x=0. The bottom E cell overlaps
    # their full width, so their exact union is this single rectangle.
    cells = [(-left-1, 1+right, -bottom-low-height, -low),
             (-left-1, 0, -low-height, 2-low),
             (0, 1+right, -low-height, 2-low)]
    assert cells[1][1] == cells[2][0]
    assert cells[1][2:] == cells[2][2:]
    assert cells[0][3] > cells[1][2]
    return A, B, (F(-left-1), F(1+right), -bottom-low-height, 2-low)


def _rect_state(rect, p):
    x0, x1, y0, y1 = rect
    x, y = p
    if x < x0 or x > x1 or y < y0 or y > y1:
        return -1
    return 1 if x0 < x < x1 and y0 < y < y1 else 0


def _assert_tight_seam_exit(A, B, direction):
    got = entrance.first_entrance(A, B, (0, 0), direction)
    assert got.kind == 'exit', ('topological interior must use exit policy', got)
    # Existing shortest_exit is explicitly local VE/EV selection, not global PD.
    assert got == entrance.shortest_exit(A, B, (0, 0))


@pytest.mark.parametrize('asymmetric', [False, True])
@pytest.mark.parametrize('scale', [2.**-8, 1., 2.**8])
@pytest.mark.parametrize('offset', [0., 1e6])
@pytest.mark.parametrize('rotated', [False, True])
def test_tight_fit_interior_uses_shortest_exit_not_zero_time_entrance(asymmetric, scale, offset, rotated):
    A, B, rect = _tight_pair(asymmetric)
    assert _rect_state(rect, (0, 0)) == 1
    def transform(p):
        x, y = p
        if rotated:
            x, y = -y, x
        return scalar_exact(offset+scale*x), scalar_exact(-2*offset+scale*y)
    A, B = list(map(transform, A)), list(map(transform, B))
    _assert_tight_seam_exit(A, B, (-scale, 0) if rotated else (0, scale))


@pytest.mark.parametrize('asymmetric', [False, True])
def test_nonconvex_membership_reports_topological_interior_at_tight_seam(asymmetric):
    A, B, rect = _tight_pair(asymmetric)
    # Boundary points, strict-overlap points, tight seams and both separated sides.
    cases = [(0, 0), (F(1, 8), 0), (0, rect[3]), (rect[0], 0),
             (0, rect[3]+F(1, 2**80)), (rect[0]-F(1, 2**80), 0)]
    for p in cases:
        want = _rect_state(rect, p)
        assert covers.membership_convex(A, B, p) == want, ('E topology mismatch', p, want)
    # Explicit report windows still require a true E-boundary witness, not a
    # body-contact seam. All four axis samples remain strictly inside the E box.
    assert covers.membership_convex(A, B, (0, 0), tol=F(1, 16)) == 1
    top = (0, rect[3])
    got = entrance.first_entrance(A, B, top, (0, 1))
    assert got.kind == 'entrance' and got.t_exact == 0


def test_initial_state_gate_kills_restored_body_overlap_classifier(monkeypatch):
    from eab.kernel2d.exact import polygons_overlap_exact
    A, B, _ = _tight_pair()
    monkeypatch.setattr(entrance, 'entrance_membership_exact', polygons_overlap_exact)
    with pytest.raises(AssertionError, match='topological interior must use exit policy'):
        _assert_tight_seam_exit(A, B, (0, 1))


def test_membership_gate_kills_restored_body_overlap_classifier(monkeypatch):
    from eab.kernel2d.exact import polygons_overlap_exact
    A, B, _ = _tight_pair()
    monkeypatch.setattr(covers, 'entrance_membership_exact', polygons_overlap_exact)
    with pytest.raises(AssertionError, match='E topology mismatch'):
        assert covers.membership_convex(A, B, (0, 0)) == 1, 'E topology mismatch'


@pytest.mark.parametrize('width', [F(1)-F(1, 2**80), F(1), F(1)+F(1, 2**80)])
def test_initial_topology_resolves_exact_tight_fit_threshold(width):
    """Interval oracle: narrower touches one wall; exact/full width is int E."""
    A, B, _ = _tight_pair()
    A = [(width*x, y) for x, y in A]
    want = 0 if width < 1 else 1
    assert covers.membership_convex(A, B, (0, 0)) == want
    got = entrance.first_entrance(A, B, (0, 0), (0, 1))
    assert got.kind == ('entrance' if want == 0 else 'exit')


@pytest.mark.parametrize('shear', [0, 2**40])
def test_initial_topology_preserves_a_narrow_true_exterior_sector(shear):
    """L-shaped rectangle union has a true concave E corner, even under shear.

    At x=(0,0) the square touches both arms of the L. A small
    displacement (epsilon,epsilon) separates both Cartesian cells. Invertible
    shear preserves this exterior sector, whose angle becomes very small.
    """
    B = [(0, 0), (3, 0), (3, 1), (1, 1), (1, 3), (0, 3)]
    A = [(1, 1), (F(3, 2), 1), (F(3, 2), F(3, 2)), (1, F(3, 2))]
    def transform(p):
        return (scalar_exact(p[0]+shear*p[1]), scalar_exact(p[1]))
    A, B = list(map(transform, A)), list(map(transform, B))
    assert covers.membership_convex(A, B, (0, 0)) == 0
    assert entrance.first_entrance(A, B, (0, 0), (1, 1)).kind == 'entrance'


@pytest.mark.parametrize('exponent', [20, 40, 50])
def test_2d_analytic_gap_keeps_unit_determinant_under_large_tangential_span(exponent):
    """Scan gate: integer determinant (M+1)(M-1)-M*M=-1, Decimal root.

    No production dot/cross/normal/square-root primitive is used by the oracle.
    The current 2D analytic paths already form the determinant before rounding
    the normal; this guards them against the analogous G6H-02 regression.
    """
    from decimal import Decimal, localcontext
    M = 2**exponent
    A = [(scalar_exact(M), scalar_exact(M-2)), (scalar_exact(M+1), scalar_exact(M-2)), (scalar_exact(M), scalar_exact(M-1))]
    B = [(0., 0.), (scalar_exact(M+1), scalar_exact(M)), (0., 1.)]
    want = sqrt_exact(F(1, (M+1)**2+M*M))
    assert covers.facet_gap(A, B, ('VE', 2, 0), (0, 0)) == want
    assert covers.ve_cover(A, 2, B, 0).gap == want
    assert entrance._contact_report(A, B, ('VE', 2, 0), (F(0), F(0)))[3] == want


@pytest.mark.parametrize('exponent', [-600, 0, 600])
def test_2d_cone_width_survives_intermediate_product_range(exponent):
    """Oracle: atan2(1,3), invariant under a common exact power-of-two scale."""
    import math
    s = 2.**exponent
    assert covers.cone_width(((s, s), (s, 2*s))) == math.atan2(1, 3)


@pytest.mark.parametrize('reverse', [False, True])
def test_2d_cone_width_keeps_representable_angle_after_product_cancellation(reverse):
    """Oracle: the exact binary64 input determinant is -2**-106, not zero."""
    import math
    eps = 2.**-53
    lo, hi = (1., 1.-eps), (1.-eps, 1.-2*eps)
    determinant = -F(2)**-106
    scalar = F(1-eps)+F(1-eps)*F(1-2*eps)
    want = math.atan2(scalar_exact(determinant/scalar), 1.)
    if reverse:
        lo, hi, want = hi, lo, -want
    assert covers.cone_width((lo, hi)) == want


def test_cone_width_gate_kills_restored_float_products(monkeypatch):
    import math
    def old_width(cone):
        lo, hi = cone
        return math.atan2(lo[0]*hi[1]-lo[1]*hi[0], lo[0]*hi[0]+lo[1]*hi[1])
    monkeypatch.setattr(covers, 'cone_width', old_width)
    with pytest.raises(AssertionError):
        test_2d_cone_width_keeps_representable_angle_after_product_cancellation(False)


def test_2d_cone_width_unrepresentable_nonzero_angle_fails_loud():
    with pytest.raises(ArithmeticError, match='nonzero cone width below binary64 output range'):
        covers.cone_width(((1, 0), (1, F(2)**-2000)))


@pytest.mark.parametrize('exponent', [20, 40, 50])
def test_2d_point_side_keeps_exact_unit_determinant(exponent):
    from eab.kernel2d.geom import point_side
    M = 2.**exponent
    assert point_side((M, M-1), (0., 0.), (M+1, M)) == -1., 'signed determinant lost'


def test_2d_point_side_preserves_exact_rational_callers_and_cancels_overflow():
    from eab.kernel2d.geom import point_side
    tiny = F(2)**-2000
    assert point_side((0, tiny), (0, 0), (1, 0)) == tiny
    assert point_side((1e200, 1e200), (0., 0.), (1e200, 1e200)) == 0.
    with pytest.raises(ArithmeticError):
        point_side((0., 1e-200), (0., 0.), (1e-200, 0.))


def test_point_side_gate_kills_restored_float_products(monkeypatch):
    from eab.kernel2d import geom
    def premature(p, a, b):
        return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
    monkeypatch.setattr(geom, 'point_side', premature)
    with pytest.raises(AssertionError, match='signed determinant lost'):
        test_2d_point_side_keeps_exact_unit_determinant(40)
