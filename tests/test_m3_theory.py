"""M3 object/semantic gates with an independent Cartesian interval oracle.

The oracle below uses only Fraction interval arithmetic for three explicitly
listed rectangles. It imports no cover, triangulation, convolution, global
entrance construction, or production geometric primitive. Existing production
APIs are queried only as the objects under test. This file does not certify
the new 2D/3D construction implementation or claim independent G6 closure.
"""
from fractions import Fraction as F
from pathlib import Path

import pytest

from eab.kernel2d.exact import entrance_membership_exact, polygons_overlap_exact
from eab.kernel2d import g0_oracle


A = ((-1, 0), (1, 0), (1, 1), (-1, 1))
B = ((-2, -1), (2, -1), (2, 3), (1, 3),
     (1, 0), (-1, 0), (-1, 3), (-2, 3))
# Exact Cartesian differences of each wall rectangle with the moving pin.
PAIR_SUMS = ((-3, 3, -2, 0), (-3, 0, -1, 3), (0, 3, -1, 3))


def _cartesian_state(q):
    x, y = q
    if any(left < x < right and bottom < y < top
           for left, right, bottom, top in PAIR_SUMS):
        return 1
    return 0 if any(left <= x <= right and bottom <= y <= top
                    for left, right, bottom, top in PAIR_SUMS) else -1


def _cartesian_topology(q):
    x, y = q
    if -3 < x < 3 and -2 < y < 3:
        return 1
    return 0 if -3 <= x <= 3 and -2 <= y <= 3 else -1


@pytest.mark.parametrize('q,physical,topology', [
    ((F(0), F(1)), 0, 1),
    ((F(1, 8), F(1)), 1, 1),
    ((F(-1, 8), F(1)), 1, 1),
    ((F(0), F(9, 8)), 0, 1),
    ((F(0), F(7, 8)), 0, 1),
    ((F(0), F(3)), 0, 0),
    ((F(0), F(25, 8)), -1, -1),
])
@pytest.mark.parametrize('scale,shift,quarter_turn', [
    (F(1, 1000), (F(10**6), F(-10**6)), True),
    (F(1), (F(0), F(0)), False),
    (F(1000), (F(-10**5), F(1000)), True),
])
def test_m3_tight_fit_distinguishes_body_relation_from_entrance_topology(
        q, physical, topology, scale, shift, quarter_turn):
    """Closed-form pin/slot oracle, including scales and exact rigid motions."""
    def linear(p):
        x, y = (F(value)*scale for value in p)
        return (-y, x) if quarter_turn else (x, y)
    def body(poly):
        return tuple((x+shift[0], y+shift[1]) for x, y in map(linear, poly))
    moving, fixed, translation = body(A), body(B), linear(q)
    assert _cartesian_state(q) == physical
    assert _cartesian_topology(q) == topology
    assert polygons_overlap_exact(moving, fixed, translation) == physical, 'physical O state'
    assert entrance_membership_exact(moving, fixed, translation) == topology, 'topological int E state'
    translated = tuple((p[0]+translation[0], p[1]+translation[1]) for p in moving)
    assert g0_oracle.overlap(translated, fixed) == physical, 'independent winding body state'
    if physical == 0:
        assert g0_oracle.boundary_has_exterior(translated, fixed) == (topology == 0), 'contact seam is not E boundary'


def test_m3_open_pair_sum_union_is_not_the_interior_of_closed_union():
    """Independent rectangle witnesses distinguish both sides of T1."""
    for x in (F(-4), F(-3), F(-1), F(0), F(1), F(3), F(4)):
        for y in (F(-3), F(-2), F(-1), F(0), F(1), F(3), F(4)):
            closed_union = any(a <= x <= b and c <= y <= d for a, b, c, d in PAIR_SUMS)
            assert closed_union == (-3 <= x <= 3 and -2 <= y <= 3)
    assert _cartesian_state((0, 1)) == 0
    assert _cartesian_topology((0, 1)) == 1
    # E is the closure of O even though O omits this interior contact seam.
    for exponent in (1, 10, 100):
        epsilon = F(1, 2**exponent)
        assert _cartesian_state((epsilon, 1)) == 1
        assert _cartesian_state((-epsilon, 1)) == 1


def test_m3_closed_separation_depth_and_nonpenetration_depth_are_different():
    """At (1/8,1), rho=1/8 is attained, PD_closed=2 is not attained."""
    q = (F(1, 8), F(1))
    # Any displacement shorter than 1/8 stays inside the right open rectangle;
    # the displacement (-1/8,0) attains the tight-fit nonpenetration state.
    right_open_margins = (q[0], 3-q[0], q[1]+1, 3-q[1])
    rho = min(right_open_margins)
    assert rho == F(1, 8)
    assert _cartesian_state((q[0]-rho, q[1])) == 0
    closed_margins = (q[0]+3, 3-q[0], q[1]+2, 3-q[1])
    pd_closed = min(closed_margins)
    assert pd_closed == 2 > rho
    assert _cartesian_state((q[0], q[1]+pd_closed)) == 0
    for epsilon in (F(1, 8), F(1, 2**80)):
        assert _cartesian_state((q[0], q[1]+pd_closed+epsilon)) == -1


def test_m3_theory_design_is_readable_utf8_and_names_both_contracts():
    text = (Path(__file__).resolve().parents[1]/'docs/m3_global_entrance_design.md').read_text(encoding='utf-8')
    assert sum('\u4e00' <= ch <= '\u9fff' for ch in text) > 500, 'theory document Chinese was lost in encoding'
    for required in ('E\\O', 'int E', 'closure(O)', 'PD_closed', 'rho', 'T1', 'T2'):
        assert required in text, ('missing explicit theory contract', required)
