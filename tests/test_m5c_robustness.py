"""M5c semantic teeth: independent rational counterexamples, no hash tripwires.

Oracle imports: fractions only in m5c_teeth_oracle. Production imports are SUTs.
Mutation instrumentation edits actual internal function bodies, not outputs.
"""
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import sys

import pytest
from mutation_support import replace_module_callable
from m5c_teeth_oracle import (point_strictly_inside, rotate_rational,
                             translation_first_events)
from eab.kernel2d import model_robustness as rob
from eab.kernel2d.dda_motion import DDAAnchoredMotion

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import m5b_robust_replay as replay

DIAMOND = ((-2, 0), (-1, F(-1, 2)), (0, 0), (-1, F(1, 2)))
WALL = ((1, -2), (3, -2), (3, 2), (1, 2))


def _translated(paths, velocity):
    return tuple((x+velocity[0], y+velocity[1]) for x, y in paths)


def _static(ring):
    return rob.chord_paths(ring, ring)


def _row(start, end, z, ids):
    return dict(start=[[str(x) for x in p] for p in start],
                end=[[str(x) for x in p] for p in end],
                z=[str(x) for x in z], vertex_ids=list(ids))


def test_r2_complete_early_window_rejects_prior_penetration():
    # Rigid translation x(s)-1=400*(s-2/5)*(s-1/2)*(s-3/5),
    # y(s)=20s-11. Before 17/40 EVERY vertex is strictly below y=-2;
    # at 17/40 only the top vertex reaches the bottom edge, at x=33/32.
    # The later rightmost-vertex/wall crossing at 3/5 has a DIFFERENT label.
    coefficients = (F(-47), F(296), F(-600), F(400))
    aa = tuple(((F(x)/10+coefficients[0],)+coefficients[1:],
                (F(y)-11, F(20)), (F(1),)) for x, y in DIAMOND)
    top = max(range(len(DIAMOND)), key=lambda i: DIAMOND[i][1])
    first_time = F(9-DIAMOND[top][1], 20)
    first_point = (F(DIAMOND[top][0])/10+sum(c*first_time**k for k, c in enumerate(coefficients)),
                   DIAMOND[top][1]+20*first_time-11)
    assert (first_time, first_point) == (F(17, 40), (F(33, 32), F(-2)))
    assert WALL[0][0] < first_point[0] < WALL[1][0]
    assert ("VE", top, 0) != ("VE", 2, 3)
    witness_time = F(43, 100)
    witness = (F(DIAMOND[top][0])/10+sum(c*witness_time**k for k, c in enumerate(coefficients)),
               DIAMOND[top][1]+20*witness_time-11)
    assert point_strictly_inside(witness, WALL)
    result = rob.single_cover_certificate(aa, _static(WALL), ("VE", 2, 3),
                                         (F(59, 100), F(61, 100)))
    assert result is None, "R2 complete early window rejects prior penetration"


def test_r2_ev_competitor_precedes_nominated_ve():
    a = ((-2, -10), (0, 0), (-2, 10))
    b = ((1, 1), (3, -1), (3, 3))
    time, labels = translation_first_events(a, b, (4, 0))
    assert (time, labels) == (F(3, 10), (("EV", 1, 0),))
    result = rob.single_cover_certificate(rob.chord_paths(a, _translated(a, (4, 0))),
                                         _static(b), ("VE", 1, 0), (F(1, 4), F(11, 20)))
    assert result is None, "R2 EV competitor precedes nominated VE"


@pytest.mark.parametrize("side", (-1, 1))
def test_r2_both_edge_projection_sides_reject_line_extension(side):
    a = _translated(DIAMOND, (0, 5*side))
    assert translation_first_events(a, WALL, (2, 0)) == (None, ())
    result = rob.single_cover_certificate(rob.chord_paths(a, _translated(a, (2, 0))),
                                         _static(WALL), ("VE", 2, 3), (F(2, 5), F(3, 5)))
    assert result is None, "R2 both edge projections reject line-extension roots"


def test_r2_final_panel_rejects_departed_edge_endpoint():
    a = ((F(-198, 1000), F(1403, 1000)),
         (F(-1198, 1000), F(2403, 1000)),
         (F(-2198, 1000), F(1903, 1000)))
    assert translation_first_events(a, WALL, (2, 1)) == (None, ())
    result = rob.single_cover_certificate(rob.chord_paths(a, _translated(a, (2, 1))),
                                         _static(WALL), ("VE", 0, 3), (F(29, 50), F(3, 5)))
    assert result is None, "R2 final panel rejects a crossing beyond the edge endpoint"


def test_r2_competitor_zero_margin_is_not_strict_exclusion():
    a = ((0, 0), (F(-1, 5), 1), (F(-3, 10), -1))
    time, labels = translation_first_events(a, WALL, (2, 0))
    assert (time, labels) == (F(1, 2), (("VE", 0, 3),))
    result = rob.single_cover_certificate(rob.chord_paths(a, _translated(a, (2, 0))),
                                         _static(WALL), ("VE", 0, 3),
                                         (F(49, 100), F(3, 5)), panels=16)
    assert result is None, "R2 competing event at equality lacks strict exclusion"


def test_r2_event_error_budget_contains_each_bilinear_term():
    # Singleton boxes make the independently expanded error expression exact.
    p = (((F(3), F(3)), (F(5), F(5))),)
    q = (((F(-2), F(-2)), (F(1), F(1))),
         ((F(4), F(4)), (F(-3), F(-3))))
    result = rob._event(p, q, 0, 0, F(1, 7), F(2, 11))
    # U=(6,-4), W=(5,4), V=(-1,8), du=4/11, dw=25/77.
    expected = F(4, 11)*9+F(25, 77)*10+2*F(4, 11)*F(25, 77)
    assert result[3] == expected, "R2 W error budget preserves all bilinear terms"
    assert result[4] == expected, "R2 V error budget preserves all bilinear terms"


def test_r2_convexity_budget_is_strict_at_exact_equality():
    ring = ((0, 0), (10, 0), (10, 6), (0, 6))
    boxes = tuple(((F(x), F(x)), (F(y), F(y))) for x, y in ring)
    # min area=60; maximum exact budget=2*(20+6)+8=60.
    assert not rob._strict_convex(boxes, F(1)), "R2 convexity requires every error term and strict positivity"


def test_r2_near_threshold_certificate_matches_independent_oracle():
    a = tuple((10*x, 10*y) for x, y in DIAMOND)
    b = ((1, -20), (3, -20), (3, 20), (1, 20))
    radius = F(199999, 1000000)
    result = rob.single_cover_certificate(rob.chord_paths(a, _translated(a, (2, 0))),
                                         _static(b), ("VE", 2, 3),
                                         (F(2, 5), F(3, 5)), radius, 0)
    assert result is not None, "R2 near-threshold sufficient case remains certifiable"
    assert result["endpoints_margin"] == 8-40*radius
    assert 0 < result["endpoints_margin"]/(40*radius) < F(1, 100000)
    for dx, dy in product((-radius, F(0), radius), repeat=2):
        perturbed = _translated(a, (dx, dy))
        time, labels = translation_first_events(perturbed, b, (2, 0))
        assert labels == (result["label"],), "production certificate agrees with independent first labels"
        assert result["bracket"][0] < time < result["bracket"][1], "production bracket encloses independent first time"


@pytest.mark.parametrize("scale,offset", ((F(1), (0, 0)),
                                         (F(1, 1024), (10**6, -10**5)),
                                         (F(1024), (-10**5, 10**6))))
def test_r1_linf_tube_uses_dual_l1_normalization(scale, offset):
    a = ((0, 0), (2, 0), (0, 2))
    b = ((2, 2), (4, 2), (2, 4))
    def transform(ring):
        return tuple((offset[0]+scale*x, offset[1]+scale*y) for x, y in ring)
    # Both L-infinity tubes reach (3/2,3/2); x/y swept boxes already overlap.
    edge_midpoint = tuple(F(a[1][k]+a[2][k], 2) for k in (0, 1))
    witness = (F(3, 2), F(3, 2))
    assert all(max(abs(witness[k]-point[k]) for k in (0, 1)) <= F(3, 5)
               for point in (edge_midpoint, b[0]))
    result = rob.separation_certificate(_static(transform(a)), _static(transform(b)),
                                        scale*F(3, 5), scale*F(3, 5))
    assert result is None, "R1 coordinate tube requires L1 normalization"


def test_replay_endpoint_residual_r2_prevents_false_no_contact():
    a = ((0, 0), (1, 0), (0, 1))
    b = _translated(a, (2, 0))
    aa = replay.prepare(_row(a, _translated(a, (0, 1)), (0, 0, 0, 0, 0, 0), (1, 2, 3)))
    bb = replay.prepare(_row(b, b, (0, 0, 0, 0, 0, 0), (4, 5, 6)))
    assert aa["residual"] == 1 and aa["bound"] == aa["endpoint_parameter"] == 0
    assert translation_first_events(a, b, (1, 0))[0] == 1
    result = replay.compare_pair(aa, bb)
    assert result["classification"] != "ROBUST_NO_CONTACT", "r2 endpoint residual forbids false robust no contact"


def test_replay_p2_box_cannot_be_replaced_by_p1_box_only():
    a = ((F(10), F(-1, 2)), (F(-5), F(1)), (F(-5), F(-1, 2)))
    b = ((F(10011, 1000), F(-1, 1000)), (F(10014, 1000), F(-1, 1000)),
         (F(10014, 1000), F(1, 1000)), (F(10011, 1000), F(1, 1000)))
    u = F(1, 20)
    end = tuple(rotate_rational(p, u) for p in a)
    midpoint = rotate_rational(a[0], u/2)
    assert end[0] == (10, F(1, 2))
    assert point_strictly_inside(midpoint, b)
    def prepared(start, finish, motion, ids, radius):
        one, two = rob.chord_paths(start, finish), rob.dda_paths(start, motion)
        return dict(start=start, end=finish, motion=motion, ids=ids, radius=radius,
                    paths1=one, paths2=two, box1=rob.swept_axis_bounds(one),
                    box2=rob.swept_axis_bounds(two))
    aa = prepared(a, end, DDAAnchoredMotion(u1=u), (1, 2, 3), F(1, 1000))
    bb = prepared(b, b, DDAAnchoredMotion(), (4, 5, 6, 7), F(0))
    result = replay.compare_pair(aa, bb)
    assert result["classification"] != "ROBUST_NO_CONTACT", "P2 swept box prevents P1-only false robust no contact"
    assert not result["same"] and result["p1"]["status"] == "no_contact"


# Each entry changes real production function source, then reruns its semantic gate.
# No source-hash or frozen-summary test participates in these calls.
MUTATIONS = (
    ("early_skip", "single_cover_certificate",
     "separation_certificate(a, b, ra, rb, lo=0, hi=lo, panels=panels)", "dict(kind='omitted')",
     test_r2_complete_early_window_rejects_prior_penetration, (), "complete early window"),
    ("early_half", "single_cover_certificate",
     "hi=lo, panels=panels)", "hi=lo/2, panels=panels)",
     test_r2_complete_early_window_rejects_prior_penetration, (), "complete early window"),
    ("omit_ev", "single_cover_certificate",
     '((aa, bb, ra, rb, "VE"), (bb, aa, rb, ra, "EV"))', '((aa, bb, ra, rb, "VE"),)',
     test_r2_ev_competitor_precedes_nominated_ve, (), "EV competitor"),
    ("omit_projection_g", "single_cover_certificate", "min(g[0]-ew, h[0]-ev)", "h[0]-ev",
     test_r2_both_edge_projection_sides_reject_line_extension, (1,), "both edge projections"),
    ("omit_projection_h", "single_cover_certificate", "min(g[0]-ew, h[0]-ev)", "g[0]-ew",
     test_r2_both_edge_projection_sides_reject_line_extension, (-1,), "both edge projections"),
    ("omit_last_panel", "single_cover_certificate", "_panels(lo, hi, panels):", "_panels(lo, hi, panels)[:-1]:",
     test_r2_final_panel_rejects_departed_edge_endpoint, (), "final panel"),
    ("competitor_nonstrict", "single_cover_certificate", "if margin <= 0:", "if margin < 0:",
     test_r2_competitor_zero_margin_is_not_strict_exclusion, (), "competing event at equality"),
    ("convexity_nonstrict", "_strict_convex", "if _cross(u, v)[0] <= error:", "if _cross(u, v)[0] < error:",
     test_r2_convexity_budget_is_strict_at_exact_equality, (), "convexity requires"),
    ("norm_linf", "separation_certificate", "abs(normal[0])+abs(normal[1])", "max(abs(normal[0]),abs(normal[1]))",
     test_r1_linf_tube_uses_dual_l1_normalization, (F(1), (0, 0)), "L1 normalization"),
    ("omit_r2", "prepare", "radius=bound+residual+endpoint_parameter", "radius=bound+endpoint_parameter",
     test_replay_endpoint_residual_r2_prevents_false_no_contact, (), "r2 endpoint residual"),
    ("p1_box_only", "compare_pair", "if min(gaps) > radius:", "if gaps[0] > radius:",
     test_replay_p2_box_cannot_be_replaced_by_p1_box_only, (), "P2 swept box"),
    ("wrong_return_label", "single_cover_certificate", "label=tuple(label), bracket=(lo, hi)",
     'label=("VE", 0, 0), bracket=(lo, hi)',
     test_r2_near_threshold_certificate_matches_independent_oracle, (), "production certificate agrees"),
    ("wrong_return_bracket", "single_cover_certificate", "label=tuple(label), bracket=(lo, hi)",
     "label=tuple(label), bracket=(lo, lo)",
     test_r2_near_threshold_certificate_matches_independent_oracle, (), "production bracket encloses"),
)


@pytest.mark.parametrize("case", MUTATIONS, ids=[row[0] for row in MUTATIONS])
def test_internal_structural_mutations_die_on_named_semantics(monkeypatch, case):
    _, name, before, after, gate, args, message = case
    module = replay if name in ("prepare", "compare_pair") else rob
    replace_module_callable(monkeypatch, module, name, [(before, after)])
    with pytest.raises(AssertionError, match=message):
        gate(*args)


@pytest.mark.parametrize("which,term", product(("w", "v"), (0, 1, 2)))
def test_internal_event_error_term_deletion_dies_on_budget_semantics(monkeypatch, which, term):
    terms = [f"du*_length1({which})", "dw*_length1(u)", "2*du*dw"]
    before = f"error_{which} = "+"+".join(terms)
    after = f"error_{which} = "+"+".join(value for k, value in enumerate(terms) if k != term)
    replace_module_callable(monkeypatch, rob, "_event", [(before, after)])
    with pytest.raises(AssertionError, match=f"{which.upper()} error budget"):
        test_r2_event_error_budget_contains_each_bilinear_term()


@pytest.mark.parametrize("replacement", ("2*radius*_length1(u)+8*radius*radius",
                                        "2*radius*_length1(v)+8*radius*radius",
                                        "2*radius*(_length1(u)+_length1(v))"))
def test_internal_convexity_error_term_deletion_dies_on_semantics(monkeypatch, replacement):
    replace_module_callable(monkeypatch, rob, "_strict_convex", [
        ("2*radius*(_length1(u)+_length1(v))+8*radius*radius", replacement)])
    with pytest.raises(AssertionError, match="convexity requires"):
        test_r2_convexity_budget_is_strict_at_exact_equality()
