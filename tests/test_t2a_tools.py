"""Small proposal/diagnostic smoke gates, never escape acceptance gates.

No configuration-space grid is scanned here. Rational path construction is
checked by the explicit Cayley endpoint formula; diagnostic distances use a
hand-calculated translating-square example. Only tools may use NumPy.
"""
from fractions import Fraction as F

from eab.kernel2d.se2 import SE2Motion, rotate_rational
from t2_performance import dovetail_workload, star_workload
from t2_se2_diagnostics import array, segment_diagnostic
from t2_se2_grid import rationalize


def test_grid_rationalization_starts_exactly_and_merges_same_direction():
    center = (F(1, 7), F(2, 5))
    local = ((F(-1), F(-1)), (F(1), F(-1)), (F(1), F(1)), (F(-1), F(1)))
    spec = dict(n=10, step=F(1, 50), centre=center, local=local)
    nodes = ((0, 0, 0), (0, 1, 0), (0, 2, 0), (1, 2, 0), (2, 2, 0))
    pieces = rationalize(nodes, spec)
    assert len(pieces) == 2
    assert pieces[0]["start"] == tuple((center[0]+x, center[1]+y) for x, y in local)
    assert pieces[0]["translation"] == (F(1, 25), 0)
    assert pieces[1]["u1"] == F(1, 5)
    assert pieces[0]["end"] == pieces[1]["start"]
    for piece in pieces:
        motion = SE2Motion(piece["u1"], piece["translation"], piece["center"])
        assert tuple(motion.endpoint(p) for p in piece["start"]) == piece["end"]


def test_grid_rotation_merge_splits_at_cayley_quarter_turn_limit():
    local = ((F(-1), F(-1)), (F(1), F(-1)), (F(1), F(1)), (F(-1), F(1)))
    spec = dict(n=4, step=F(1, 50), centre=(F(0), F(0)), local=local)
    pieces = rationalize(tuple((k, 0, 0) for k in range(-4, 5)), spec)
    assert len(pieces) == 2
    assert [piece["u1"] for piece in pieces] == [1, 1]
    assert pieces[0]["start"] == tuple(rotate_rational(p, -1) for p in local)
    assert pieces[0]["end"] == pieces[1]["start"] == local
    assert pieces[-1]["end"] == tuple(rotate_rational(p, 1) for p in local)


def test_bottleneck_diagnostic_is_approximate_and_labels_both_feature_directions():
    piece = dict(start=(("0", "0"), ("1", "0"), ("1", "1"), ("0", "1")),
                 u1="0", translation=("1/2", "0"), center=("0", "0"))
    obstacles = (array((("2", "0"), ("3", "0"), ("3", "1"), ("2", "1"))),)
    result = segment_diagnostic(piece, obstacles, 9)
    assert result["sampled_local_minimum_separation"] == 0.5
    assert result["time_estimate"] == 1.0
    assert result["certified_continuous_minimum"] is False
    labels = {tuple(item["label"]) for item in result["near_feature_candidates"]}
    assert ("VE", 1, 3) in labels and ("EV", 1, 0) in labels


def test_performance_inputs_are_rational_noncentral_and_have_requested_sizes():
    a, b, ma, mb = star_workload()
    assert len(a) == len(b) == 16 and a != b
    assert all(isinstance(x, F) for ring in (a, b) for p in ring for x in p)
    assert ma.u1 != 0 and mb.u1 != 0 and ma.center != mb.center
    assert ma.center != tuple(sum(p[k] for p in a)/16 for k in (0, 1))
    moving, obstacles, motion = dovetail_workload()
    assert len(obstacles) == 3 and len(moving) == 4
    assert all(isinstance(x, F) for ring in (moving, *obstacles) for p in ring for x in p)
    assert motion.u1 != 0 and motion.translation != (0, 0)
