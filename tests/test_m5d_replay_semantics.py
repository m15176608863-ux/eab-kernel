"""M5d replay semantic oracles use Fraction identities, no SUT geometry.

Imports of eab/replay are subjects and input adapters, never expected-answer
primitives. Mutation support compiles actual changed internal function bodies.
"""
from fractions import Fraction as F
from math import comb
from pathlib import Path
import sys

import pytest
from mutation_support import replace_module_callable
from eab.kernel2d import model_robustness as rob
from eab.adapters.bdda2d_motion import DDAAnchoredMotion

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import m5b_robust_replay as replay


def _prepared(start, finish, motion: DDAAnchoredMotion, ids, radius):
    one = rob.chord_paths(start, finish)
    two = []
    for point in start:
        numerators, denominator = motion.coordinate_polynomials(point)
        two.append((*numerators, denominator))
    two = tuple(two)
    return dict(start=start, end=finish, motion=motion, ids=ids, radius=radius,
                paths1=one, paths2=two, box1=rob.swept_axis_bounds(one),
                box2=rob.swept_axis_bounds(two))


def _rotate(point, u):
    c, s = (1-u*u)/(1+u*u), 2*u/(1+u*u)
    return c*point[0]-s*point[1], s*point[0]+c*point[1]


def test_replay_r1_requires_p2_tube_even_when_both_nominal_paths_are_separated():
    """Oracle: rational rotation, radius squares and open rectangle only."""
    a = ((F(10), F(-1, 2)), (F(-5), F(1)), (F(-5), F(-1, 2)))
    b = ((F(501, 50), F(-1, 1000)), (F(401, 40), F(-1, 1000)),
         (F(401, 40), F(1, 1000)), (F(501, 50), F(1, 1000)))
    radius, u = F(1, 100), F(1, 20)
    end = tuple(_rotate(p, u) for p in a)
    assert a[0][0] == end[0][0] == 10
    assert max(p[0] for p in a+end)+radius < b[0][0], "P1 entire tube is separated"
    assert max(x*x+y*y for x, y in a) < b[0][0]**2, "P2 nominal rotation is separated"
    midpoint = _rotate(a[0], u/2)
    assert midpoint == (F(16030, 1601), F(1, 3202))
    # dx(s)=4*r*s*(1-s) is continuous, zero at both ends, and <=r.
    witness = midpoint[0]+radius, midpoint[1]
    assert b[0][0] < witness[0] < b[1][0] and b[0][1] < witness[1] < b[2][1]
    aa = _prepared(a, end, DDAAnchoredMotion(u1=u), (1, 2, 3), radius)
    bb = _prepared(b, b, DDAAnchoredMotion(), (4, 5, 6, 7), F(0))
    assert min(replay.box_gap(aa[key], bb[key]) for key in ("box1", "box2")) <= radius
    assert rob.separation_certificate(aa["paths1"], bb["paths1"], radius, 0, panels=2) is not None
    assert rob.separation_certificate(aa["paths2"], bb["paths2"], radius, 0, panels=2) is None
    result = replay.compare_pair(aa, bb)
    assert result["p1"]["status"] == result["p2"]["status"] == "no_contact"
    assert result["comparison_basis"] == "EXPLICIT_TRAJECTORY"
    assert result["classification"] != "ROBUST_NO_CONTACT", "R1 both-path tube gate rejects P1-only certification"


def test_internal_replay_r1_p1_only_dies_on_both_path_tube_semantics(monkeypatch):
    before = 'panels=2)\n                        for key in ("paths1", "paths2")]'
    after = 'panels=2)\n                        for key in ("paths1",)]'
    # Match only the no-contact branch (the first-cover branch is deeper).
    replace_module_callable(monkeypatch, replay, "compare_pair", [(before, after)])
    with pytest.raises(AssertionError, match="R1 both-path tube gate"):
        test_replay_r1_requires_p2_tube_even_when_both_nominal_paths_are_separated()


def _compose_linear(coefficients, origin, width):
    return tuple(sum(coefficients[k]*comb(k, j)*(-origin)**(k-j)/width**k
                     for k in range(j, len(coefficients))) for j in range(len(coefficients)))


@pytest.mark.parametrize("width", (F(1, 100), F(1, 10000)))
def test_r2_mild_early_truncation_rejects_a_short_prior_penetration(width):
    """Oracle: explicit cubic and height ordering, no production predicates."""
    diamond = ((-2, 0), (-1, F(-1, 2)), (0, 0), (-1, F(1, 2)))
    wall = ((1, -2), (3, -2), (3, 2), (1, 2))
    origin = F(3, 5)*(1-width)
    # Compress the entire earlier excursion immediately before the nominated
    # crossing. Its first event can lie in the last 0.1% of the early window.
    x = _compose_linear((F(-47), F(296), F(-600), F(400)), origin, width)
    y = _compose_linear((F(-11), F(20)), origin, width)
    aa = tuple(((F(px)/10+x[0],)+x[1:], (F(py)+y[0],)+y[1:], (F(1),))
               for px, py in diamond)
    bb = rob.chord_paths(wall, wall)
    lo, hi = origin+width*F(59, 100), origin+width*F(61, 100)
    first_time = origin+width*F(17, 40)
    first_point = (sum(c*first_time**k for k, c in enumerate(x))-F(1, 10),
                   sum(c*first_time**k for k, c in enumerate(y))+F(1, 2))
    assert first_point == (F(33, 32), F(-2))
    assert F(99, 100)*lo < first_time < lo
    if width == F(1, 10000):
        assert F(999, 1000)*lo < first_time < lo
    # Prior to first_time every A vertex is below the bottom wall edge.
    assert ("VE", 3, 0) != ("VE", 2, 3)
    witness_time = origin+width*F(43, 100)
    witness = (sum(c*witness_time**k for k, c in enumerate(x))-F(1, 10),
               sum(c*witness_time**k for k, c in enumerate(y))+F(1, 2))
    assert 1 < witness[0] < 3 and -2 < witness[1] < 2
    result = rob.single_cover_certificate(aa, bb, ("VE", 2, 3), (lo, hi))
    assert result is None, "R2 mild early-window shortening misses a prior different first cover"


@pytest.mark.parametrize("factor,width", ((F(99, 100), F(1, 100)),
                                         (F(999, 1000), F(1, 10000))))
def test_internal_r2_mild_early_window_mutations_die_on_semantics(monkeypatch, factor, width):
    replace_module_callable(monkeypatch, rob, "single_cover_certificate", [
        ("hi=lo, panels=panels)", f"hi=lo*F({factor.numerator},{factor.denominator}), panels=panels)")])
    with pytest.raises(AssertionError, match="R2 mild early-window shortening"):
        test_r2_mild_early_truncation_rejects_a_short_prior_penetration(width)


def test_replay_single_cover_keeps_both_tubes_and_the_full_radius_at_the_threshold():
    """Oracle: two exact translation times and an allowed constant tube shift.

    This refutes the certificate's bracket, not the label in this particular
    parallel-translation family. P1 and P2 do have the same nominal first label.
    """
    a = ((-2, 0), (-1, F(-1, 2)), (0, 0), (-1, F(1, 2)))
    b = ((1, -2), (3, -2), (3, 2), (1, 2))
    delta = F(1, 1000)
    # Independent floor arithmetic reproduces the public 20-bit bracket
    # contract, without calling its bisection or either first-entrance solver.
    first1, first2 = 1/(2+delta), F(1, 2)
    lo = F((first1*2**20).__floor__(), 2**20)-F(1, 256)
    hi = first2+F(1, 2**20)+F(1, 256)
    p1_margin = min(1-(2+delta)*lo, (2+delta)*hi-1)
    p2_margin = min(1-2*lo, 2*hi-1)
    radius = (p1_margin+p2_margin)/2
    assert delta < radius and p2_margin < radius < p1_margin
    assert (1+radius)/2 > hi, "allowed P2 shift puts its first time outside the largest bracket"
    assert F(99, 100)*radius < p2_margin, "one-percent undercharge hides that actual tube trajectory"
    aa = _prepared(a, tuple((x+2+delta, y) for x, y in a),
                   DDAAnchoredMotion(translation=(F(2), F(0))), (1, 2, 3, 4), radius)
    bb = _prepared(b, b, DDAAnchoredMotion(), (5, 6, 7, 8), F(0))
    bracket = (lo, hi)
    assert rob.single_cover_certificate(aa["paths1"], bb["paths1"], ("VE", 2, 3), bracket, radius, 0)
    assert rob.single_cover_certificate(aa["paths2"], bb["paths2"], ("VE", 2, 3), bracket, radius, 0) is None
    result = replay.compare_pair(aa, bb)
    assert result["same"] and result["p1"]["status"] == result["p2"]["status"] == "contact"
    assert result["p1"]["features"] == result["p2"]["features"] == (("VE", 3, 5, 8),)
    assert result["classification"] != "ROBUST_SINGLE_FIRST_COVER", \
        "R2 replay single-cover wiring must retain both full-radius tubes"


@pytest.mark.parametrize("variant", ("any_path", "p1_only", "radius_99_percent"))
def test_internal_single_cover_mild_wiring_mutations_die_on_semantics(monkeypatch, variant):
    if variant == "any_path":
        replacements = [('if all(certificates):\n            result.update(classification="ROBUST_SINGLE_FIRST_COVER"',
                         'if any(certificates):\n            result.update(classification="ROBUST_SINGLE_FIRST_COVER"')]
    elif variant == "p1_only":
        replacements = [('panels=4)\n                        for key in ("paths1", "paths2")]',
                         'panels=4)\n                        for key in ("paths1",)]')]
    else:
        replacements = [('a["radius"], b["radius"], panels=4)',
                         'a["radius"]*F(99,100), b["radius"]*F(99,100), panels=4)')]
    replace_module_callable(monkeypatch, replay, "compare_pair", replacements)
    with pytest.raises(AssertionError, match="R2 replay single-cover wiring"):
        test_replay_single_cover_keeps_both_tubes_and_the_full_radius_at_the_threshold()
