from construction_oracle import scalar_exact, unit_exact
from fractions import Fraction as F
import math
import sys

import pytest

from eab.kernel2d import covers, g0, geom


B_L = [(0, 0), (3, 0), (3, 1), (1, 1), (1, 3), (0, 3)]
A_PINCH = [(F(1, 2), F(3, 2)), (1, F(3, 2)), (1, 2), (F(1, 2), 2)]


def _pinch_state(t, transverse=0):
    """Oracle: two Cartesian rectangles only, zero tested geometric primitives."""
    ax0, ax1 = F(1, 2) + t + transverse, 1 + t + transverse
    ay0, ay1 = F(3, 2) - t + transverse, 2 - t + transverse
    dims = [(min(ax1, x1)-max(ax0, x0), min(ay1, y1)-max(ay0, y0))
            for x0, x1, y0, y1 in [(0, 3, 0, 1), (0, 1, 1, 3)]]
    return 1 if any(dx > 0 and dy > 0 for dx, dy in dims) else (
        0 if any(dx >= 0 and dy >= 0 for dx, dy in dims) else -1)


def test_g6g01_first_exit_checks_isolated_true_boundary_event():
    t = F(1, 2)
    assert [_pinch_state(s) for s in [0, t-F(1, 1000), t, t+F(1, 1000)]] == [1, 1, 0, 1]
    # Every positive transverse displacement separates both product cells.
    for eps in [F(1, 100), F(1, 1000), F(1, 2**80)]:
        assert _pinch_state(t, eps) == -1
    assert g0.brute_ray_exit(A_PINCH, B_L, (1, -1)) == t


def test_g6g01_missing_covers_at_first_boundary_rejected(monkeypatch):
    baseline = g0.g0_exit_completeness(A_PINCH, B_L, [(0, 0)], [(1, -1)])
    assert baseline.samples == 1 and baseline.passed
    side, vv = covers._ve_side, covers.vv_cover
    def bad_side(P, i, Q, j, *args, **kwargs):
        if min(p[0] for p in P) == 1 or min(p[0] for p in Q) == 1:
            return -1
        return side(P, i, Q, j, *args, **kwargs)
    def bad_vv(P, i, Q, j, *args, **kwargs):
        if min(p[0] for p in P) == 1 or min(p[0] for p in Q) == 1:
            return None
        return vv(P, i, Q, j, *args, **kwargs)
    monkeypatch.setattr(covers, '_ve_side', bad_side)
    monkeypatch.setattr(covers, 'vv_cover', bad_vv)
    rep = g0.g0_exit_completeness(A_PINCH, B_L, [(0, 0)], [(1, -1)])
    assert rep.samples == 1 and not rep.passed, ('first boundary missing covers escaped', rep)
    assert rep.failures[0][2] == F(1, 2)


def _vv(dx, dy, size):
    A = [(dx, dy), (dx+size, dy), (dx+size, dy+size), (dx, dy+size)]
    B = [(-size, -size), (0, -size), (0, 0), (-size, 0)]
    return covers.vv_cover(A, 0, B, 2)


@pytest.mark.parametrize('rational', [False, True])
def test_g6g02_vv_uses_exact_difference_and_independent_unit_normal(rational):
    """Oracle: rational midpoint squares for gap, independent midpoint-certified unit components."""
    from decimal import Decimal, localcontext
    q = F(2)**-1074
    dx, dy = (F(149, 100)*q, F(49, 100)*q) if rational else (math.ulp(0.0), math.ulp(0.0))
    c = _vv(dx, dy, F(2)**-600 if rational else 2.**-600)
    square = F(dx)**2 + F(dy)**2
    if rational:
        assert (F(3, 2)*q)**2 < square < (F(5, 2)*q)**2
    assert c.strict and c.gap == scalar_exact(2*q if rational else q)
    expected = unit_exact((dx, dy))
    assert c.normal == pytest.approx(expected, rel=1e-15, abs=0)
    assert math.hypot(*c.normal) == pytest.approx(1, rel=1e-15)


def test_g6g02_vv_unrepresentable_gap_fails_loud_not_inf():
    m = sys.float_info.max; h = m/2; k = m/4
    A = [(h, h), (h+k, h), (h+k, h+k), (h, h+k)]
    B = [(-h-k, -h-k), (-h, -h-k), (-h, -h), (-h-k, -h)]
    with pytest.raises((ArithmeticError, OverflowError)):
        covers.vv_cover(A, 0, B, 2)


@pytest.mark.parametrize('side', ['distance', 'exit'])
def test_g6g03_unrepresentable_diameter_does_not_disable_missing_cover_gate(side, monkeypatch):
    """Oracle: L solid product cells, distance k or rectangle exit h/8."""
    m = sys.float_info.max; h = m/2; k = m/4
    B = [(-h, -h), (h, -h), (h, 0), (0, 0), (0, h), (-h, h)]
    if side == 'distance':
        A = [(k, k), (k+k/4, k), (k+k/4, k+k/4), (k, k+k/4)]
        run = lambda: g0.g0_distance_completeness(A, B, [(0, 0)])
    else:
        A = [(-k, k), (k, k), (k, k+k/4), (-k, k+k/4)]
        run = lambda: g0.g0_exit_completeness(A, B, [(0, 0)], [(k, 0)])
    baseline = run()
    assert baseline.samples == 1 and baseline.passed, baseline
    monkeypatch.setattr(covers, '_ve_side', lambda *a, **k: -1)
    monkeypatch.setattr(covers, 'vv_cover', lambda *a, **k: None)
    rep = run()
    assert rep.samples == 1 and not rep.passed, ('infinite scale disabled gate', rep)
    assert math.isinf(rep.failures[0][1 if side == 'distance' else 3])


@pytest.mark.parametrize('vector', [(2.**-1074, 2.**-1074), (sys.float_info.max, sys.float_info.max)])
def test_r7scan_geom_unit_does_not_divide_by_rounded_or_overflowing_norm(vector):
    assert geom.unit(vector) == pytest.approx((math.sqrt(.5), math.sqrt(.5)), rel=1e-15)


@pytest.mark.parametrize('exponent', [-600, 600])
def test_r7scan_turn_angle_avoids_underflow_overflow_before_atan2(exponent):
    s = 2.**exponent
    P = [(0., 0.), (s, 0.), (s, s)]
    assert geom.turn_angle(P, 1) == math.pi/2


def test_r7scan_vertex_turn_fails_loud_instead_of_silent_underflow():
    s = 2.**-600
    with pytest.raises(ArithmeticError):
        geom.vertex_turn([(0., 0.), (s, 0.), (s, s)], 1)


def test_g6g01_tight_fit_contact_seam_is_not_topological_exit():
    """Oracle: U arms trap a unit square laterally until its bottom reaches y=2.

    At t=1/2 the body interiors cease overlapping, but all local translations
    remain in E: lateral shifts overlap an arm and vertical shifts still touch
    the closed arms. At t=5/2 every upward displacement strictly separates.
    """
    U = [(-1, -1), (2, -1), (2, 2), (1, 2), (1, 0), (0, 0), (0, 2), (-1, 2)]
    A = [(0, F(-1, 2)), (1, F(-1, 2)), (1, F(1, 2)), (0, F(1, 2))]
    assert g0.brute_ray_exit(A, U, (0, 1)) == F(5, 2)


@pytest.mark.parametrize('scale', [F(1, 2**40), F(1), F(2**40)])
@pytest.mark.parametrize('offset', [F(0), F(10**6)])
@pytest.mark.parametrize('rotated', [False, True])
def test_g6g01_pinch_first_exit_respects_exact_similarity(scale, offset, rotated):
    def transform(p):
        x, y = map(F, p)
        if rotated:
            x, y = (3*x-4*y)/5, (4*x+3*y)/5
        return offset+scale*x, -2*offset+scale*y
    direction = (F(7, 5), F(1, 5)) if rotated else (F(1), F(-1))
    direction = tuple(scale*v for v in direction)
    assert g0.brute_ray_exit(list(map(transform, A_PINCH)), list(map(transform, B_L)), direction) == F(1, 2)


def test_g6g03_nonfinite_error_rejected_independently_of_threshold():
    length2 = F(sys.float_info.max)**2*100
    for error in [math.inf, math.nan]:
        assert g0._construction_error_exceeds(error, length2, 1., 1e-9, B_L)
    assert g0._construction_error_exceeds(1e-10, F(1, 10**1000), 0., 1e-9, [(0, 0)])


def test_g6g03_public_unrepresentable_characteristic_length_fails_loud():
    h = sys.float_info.max/2
    with pytest.raises((ArithmeticError, OverflowError)):
        g0.char_length([(-h, -h), (h, h)])


def test_g6g03_nonfinite_witness_is_not_masked_by_good_candidate():
    from types import SimpleNamespace
    good = SimpleNamespace(point_a=(0., 0.), point_b=(1., 0.))
    bad = SimpleNamespace(point_a=(math.nan, 0.), point_b=(0., 0.))
    for candidates in [[good, bad], [bad, good]]:
        assert math.isinf(g0._minimum_witness_distance(candidates))


def test_r7scan_angular_report_floor_scales_before_rounding():
    q = 2.**-1074
    expected = 64*sys.float_info.epsilon
    assert geom.angle_floor(q, q) == expected
    assert geom.turn_floor([(0., 0.), (q, 0.), (q, q)], 1) == expected


def test_r7scan_entrance_report_floor_avoids_intermediate_overflow():
    from eab.kernel2d.entrance import _floor
    m = sys.float_info.max
    P = [(m, 0.)]
    # Original magnitude sum 2m overflows; final roundoff bound is finite.
    expected = scalar_exact(F(64*sys.float_info.epsilon)*2*F(m))
    assert _floor(P, [(0., 0.)], (m, 0.), (0., 0.)) == expected


def test_r7scan_exact_vector_cache_keys_follow_mutated_input():
    vector = [F(3), F(4)]
    assert geom.norm(vector) == 5 and geom.unit(vector) == (.6, .8)
    vector[0], vector[1] = F(4), F(3)
    assert geom.norm(vector) == 5 and geom.unit(vector) == (.8, .6)
    vector[:] = [F(1), F(0)]
    assert geom.norm(vector) == 1 and geom.unit(vector) == (1., 0.)


@pytest.mark.parametrize('exponent', [-1074, 0, 1023])
def test_r7scan_entrance_report_floor_has_exact_upper_bound_certificate(exponent):
    from eab.kernel2d.entrance import _floor
    q = F(2)**exponent
    got = _floor([(0, 0)], [(0, 0)], (0, 0), (q, q))
    exact_square = 2*(q*F(64)*F(2)**-52)**2
    assert isinstance(got, F) and got > 0 and got*got >= exact_square
