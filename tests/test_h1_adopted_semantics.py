"""Three adopted semantic gates plus the independently checked A-ring mirror.

Oracle primitives: explicit rational square overlap, expanded determinants,
and m5d_c1_oracle's independent Cartesian-difference hull. They do not call
production certificate geometry to compute expected answers. No archived
mutation machinery, ledger or adequacy gate is imported.
"""
from fractions import Fraction as F
from pathlib import Path
import sys

from eab.adapters import bdda2d_motion as motion
from eab.kernel2d import m5d_exit_certificate as c1
from eab.kernel2d import model_robustness as r2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import m5b_robust_replay as replay
from m5d_c1_oracle import exit_oracle


def test_replay_box_shortcut_adds_independent_radii_before_certifying_separation():
    def _paths(ring, velocity=(0, 0)):
        return tuple(((F(x), F(velocity[0])), (F(y), F(velocity[1])), (F(1),))
                     for x, y in ring)

    radius, gap = F(1, 100), F(3, 200)
    a = ((0, 0), (1, 0), (1, 1), (0, 1))
    b = tuple((x+1+gap, y) for x, y in a)
    prepared = []
    for start in (a, b):
        paths = _paths(start)
        prepared.append(dict(start=start, end=start, motion=motion.DDAAnchoredMotion(),
                             ids=tuple(range(4)), radius=radius, paths1=paths, paths2=paths,
                             box1=r2.swept_axis_bounds(paths), box2=r2.swept_axis_bounds(paths)))
    # A+r and B-r have an explicit positive-width overlap while staying in
    # their respective coordinate boxes. No overlap predicate is the oracle.
    assert (1+radius)-(1+gap-radius) == F(1, 200), "the independent tube boxes contain overlapping squares"
    result = replay.compare_pair(*prepared)
    assert result["classification"] == "MODEL_SENSITIVE_OR_UNPROVED", \
        "replay box shortcut must add both independent block radii"


def test_c1_ranking_must_include_other_feature_family_competitors():
    a = ((-1, F(1, 4)), (F(1, 5), -F(3, 5)), (1, 1))
    b = ((-6, 4), (4, -6), (F(7, 5), F(7, 5)))
    radius = F(11, 200)
    nominal = exit_oracle(a, b)
    shifted_a = tuple((x+radius, y-radius) for x, y in a)
    shifted_b = tuple((x-radius, y+radius) for x, y in b)
    moved = exit_oracle(shifted_a, shifted_b)
    assert nominal["labels"] == (("VE", 1, 2),) and moved["labels"] == (("EV", 0, 2),)
    assert nominal["inside"] and moved["inside"], "cross-family witness remains an interior exit problem"
    result = c1.exit_order_certificate(a, b, radius, radius)
    assert result["status"] == "UNPROVED", "C1 must compare the VE winner against EV competitors"
    assert result["reason"] == "EXIT_ORDER_UNPROVED"


def test_c1_b_ring_convexity_uses_b_radius_when_a_is_exact():
    def _turn(p, q, r):
        return p[0]*q[1]+q[0]*r[1]+r[0]*p[1]-p[1]*q[0]-q[1]*r[0]-r[1]*p[0]

    a = ((-20, -10), (30, -9), (-10, 30))
    offset = (F(2001, 200), -F(29999, 1000))
    b = tuple((F(x)-offset[0], F(y)-offset[1]) for x, y in
              ((0, 0), (F(1, 100), -F(1, 10000)), (10, 0), (0, 10)))
    radius = F(8379977, 167772160000)*F(101, 100)
    moved = tuple((x, y+sign*radius) for (x, y), sign in zip(b, (-1, 1, -1, 0)))
    assert _turn(*b[:3]) > 0 and _turn(*moved[:3]) < 0, "the B-only box contains an actual reflected vertex"
    assert exit_oracle(a, b)["labels"] == (("VE", 2, 0),)
    result = c1.exit_order_certificate(a, b, 0, radius)
    assert result["status"] == "UNPROVED", "C1 B convexity must use B radius even when A radius is zero"
    assert result["reason"] == "TUBE_CONVEXITY_UNPROVED" and result["ring"] == "B"


def test_c1_a_ring_convexity_uses_a_radius_when_b_is_exact():
    def _turn(p, q, r):
        return p[0]*q[1]+q[0]*r[1]+r[0]*p[1]-p[1]*q[0]-q[1]*r[0]-r[1]*p[0]

    offset = (F(2001, 200), -F(29999, 1000))
    a = tuple((F(x)-offset[0], F(y)-offset[1]) for x, y in
              ((0, 0), (F(1, 100), -F(1, 10000)), (10, 0), (0, 10)))
    b = ((-20, -10), (30, -9), (-10, 30))
    radius = F(8379977, 167772160000)*F(101, 100)
    moved = tuple((x, y+sign*radius) for (x, y), sign in zip(a, (-1, 1, -1, 0)))
    assert _turn(*a[:3]) > 0 and _turn(*moved[:3]) < 0, "the A-only box contains an actual reflected vertex"
    assert exit_oracle(a, b)["labels"] == (("EV", 0, 2),)
    result = c1.exit_order_certificate(a, b, radius, 0)
    assert result["status"] == "UNPROVED", "C1 A convexity must use A radius even when B radius is zero"
    assert result["reason"] == "TUBE_CONVEXITY_UNPROVED" and result["ring"] == "A"
