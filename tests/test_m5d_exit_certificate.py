"""C1 semantic gates, independent oracle imports: Fraction only.

tools.m5d_c1_oracle builds a Cartesian-difference convex hull and uses an
independent determinant distance formula. It imports no production primitive.
Production and mutation_support imports below are subjects/instrumentation,
never oracle geometry. No frozen source hashes or snapshots guard these tests.
"""
from fractions import Fraction as F
import random

import pytest

from eab.kernel2d import m5d_exit_certificate as cert
from mutation_support import replace_module_callable
from tools.m5d_c1_oracle import exit_oracle


A = ((0, 0), (4, 0), (0, 3))
B = ((1, 1), (5, 2), (2, 5))


def _threshold(a, b):
    low, high = F(0), F(1)
    assert cert.exit_order_certificate(a, b, low, low)["status"] == "CERTIFIED_UNIQUE_EXIT"
    assert cert.exit_order_certificate(a, b, high, high)["status"] == "UNPROVED"
    for _ in range(32):
        mid = (low+high)/2
        if cert.exit_order_certificate(a, b, mid, mid)["status"] == "CERTIFIED_UNIQUE_EXIT":
            low = mid
        else:
            high = mid
    return low, high


def test_c1_threshold_edge_nonrigid_perturbations_match_independent_hull_oracle():
    rng = random.Random(52617)
    checked = 0
    for dx, dy in ((0, 0), (F(1, 7), F(-1, 11)), (F(-1, 5), F(1, 13))):
        b = tuple((F(x)+dx, F(y)+dy) for x, y in B)
        low, high = _threshold(A, b)
        assert high-low == F(1, 2**32), "certification threshold is bracketed, not sampled loosely"
        for r in (low*(1-F(1, 2**24)), low/2):
            result = cert.exit_order_certificate(A, b, r, r)
            assert result["status"] == "CERTIFIED_UNIQUE_EXIT"
            nominal = exit_oracle(A, b)
            assert nominal["labels"] == (result["label"],)
            assert nominal["distance2"] == result["distance2"]
            for mode in range(24):
                def perturb(ring):
                    return tuple(tuple(F(value)+r*(rng.choice((-1, 1)) if mode < 12
                                      else F(rng.randrange(-100, 101), 100)) for value in p) for p in ring)
                # Independent errors at every vertex of BOTH rings; not merely
                # a rigid translation or a repeated common perturbation.
                oracle = exit_oracle(perturb(A), perturb(b))
                assert oracle["inside"], "C1 tube must preserve initial penetration"
                assert oracle["labels"] == (result["label"],), "C1 certified global exit label must persist"
                checked += 1
    assert checked == 144, "fixed seed adversarial coverage must not shrink"


def test_c1_concavity_requires_boundary_persistence_not_just_a_distance_gap():
    concave = ((0, 0), (2, F(1, 10)), (4, 0), (0, 3))
    result = cert.exit_order_certificate(concave, B, F(1, 10000), F(1, 10000))
    assert result["status"] == "UNPROVED", "concave boundary persistence must be proved before distance ranking"
    assert result["reason"] == "RING_NOT_STRICTLY_CONVEX"


def test_c1_parallel_split_requires_normal_order_not_just_a_distance_gap():
    parallel = ((1, 1), (5, 1), (2, 5))
    result = cert.exit_order_certificate(A, parallel, F(1, 10000), F(1, 10000))
    assert result["status"] == "UNPROVED", "parallel-edge splitting must not receive a fixed-label certificate"
    assert result["reason"] == "CROSS_NORMAL_ORDER_UNPROVED"


def test_c1_original_tie_is_not_a_persistent_complete_minimizer_set():
    a = ((-2, -1), (2, -1), (2, 1), (-2, 1))
    b = ((-1, -2), (2, -1), (1, 2), (-2, 1))
    result = cert.exit_order_certificate(a, b, F(1, 10000), F(1, 10000))
    assert result["status"] == "UNPROVED", "opposite exit tie cannot be promoted to a unique label"
    assert result["reason"] == "NOMINAL_EXIT_TIE"
    assert len(exit_oracle(a, b)["labels"]) == 2


def test_c1_interior_radius_bound_is_strict():
    # eta²=2r² exactly. Touching the boundary is not strict penetration.
    assert cert._rank_guard(F(2), (F(100),), F(1)) == "INTERIOR_PERSISTENCE_UNPROVED", \
        "interior persistence requires q strictly above 2r squared"


def test_c1_ranking_checks_every_competitor_at_the_exact_boundary():
    # sqrt(8)-sqrt(2)=2sqrt(2)*(1/2): strict ranking is NOT proved.
    assert cert._rank_guard(F(2), (F(100), F(8)), F(1, 2)) == "EXIT_ORDER_UNPROVED", \
        "the final competitor at exact separation threshold must be rejected"


def test_c1_squared_rank_inequality_needs_its_positive_branch():
    # Squaring a negative distance-gap branch would incorrectly accept qj<q.
    assert cert._rank_guard(F(2), (F(1),), F(1, 10)) == "EXIT_ORDER_UNPROVED", \
        "negative h cannot be rescued by its squared inequality"


@pytest.mark.parametrize("scale,offset,u", (
    (F(1), (0, 0), F(2, 7)),
    (F(1, 2**50), (10**6, -10**6), F(-3, 8)),
    (F(2**40), (-10**5, 10**3), F(3, 5)),
))
def test_c1_global_exit_rigid_unit_covariance(scale, offset, u):
    c, s = (1-u*u)/(1+u*u), 2*u/(1+u*u)
    def transform(ring):
        return tuple((offset[0]+scale*(c*x-s*y), offset[1]+scale*(s*x+c*y)) for x, y in ring)
    radius = scale*(abs(c)+abs(s))/10000
    result = cert.exit_order_certificate(transform(A), transform(B), radius, radius)
    assert result["status"] == "CERTIFIED_UNIQUE_EXIT"
    assert result["label"] == ("EV", 1, 0)
    assert result["distance2"] == scale*scale
    oracle = exit_oracle(transform(A), transform(B))
    assert oracle["labels"] == (result["label"],) and oracle["distance2"] == scale*scale


def test_c1_parameterized_transforms_produce_distinct_geometry_and_distance_scales():
    geometries, squared = [], []
    for scale, offset, u in ((F(1), (0, 0), F(2, 7)),
                             (F(1, 2**50), (10**6, -10**6), F(-3, 8)),
                             (F(2**40), (-10**5, 10**3), F(3, 5))):
        c, s = (1-u*u)/(1+u*u), 2*u/(1+u*u)
        def transform(ring):
            return tuple((offset[0]+scale*(c*x-s*y), offset[1]+scale*(s*x+c*y)) for x, y in ring)
        aa, bb = transform(A), transform(B)
        result = cert.exit_order_certificate(aa, bb, scale/10000, scale/10000)
        assert result["status"] == "CERTIFIED_UNIQUE_EXIT"
        geometries.append((aa, bb))
        squared.append(result["distance2"])
    assert len(set(geometries)) == 3, "parameterized invariance inputs must really differ"
    assert len(set(squared)) == 3, "unit changes must yield distinct squared-distance products"


def test_c1_nonzero_query_cyclic_labels_and_independent_block_translations():
    # Independent closed-form distance to the 3-4-5 support line at x=(1,1).
    query, expected_q = (F(1), F(1)), F(144, 25)
    original = cert.exit_order_certificate(A, B, F(1, 10000), F(1, 10000), query)
    assert original["status"] == "CERTIFIED_UNIQUE_EXIT"
    assert original["label"] == ("EV", 1, 0) and original["distance2"] == expected_q
    translations = ((F(10**6), F(-10**5)), (F(-10**3), F(17)))
    aa = tuple((x+translations[0][0], y+translations[0][1]) for x, y in A[1:]+A[:1])
    bb = tuple((x+translations[1][0], y+translations[1][1]) for x, y in B[2:]+B[:2])
    shifted_query = tuple(query[k]+translations[1][k]-translations[0][k] for k in (0, 1))
    changed = cert.exit_order_certificate(aa, bb, F(1, 10000), F(1, 10000), shifted_query)
    assert changed["status"] == "CERTIFIED_UNIQUE_EXIT"
    assert changed["label"] == ("EV", 0, 1), "cyclic relabeling must permute both feature indices"
    assert changed["distance2"] == expected_q
    oracle = exit_oracle(aa, bb, shifted_query)
    assert oracle["labels"] == (changed["label"],) and oracle["distance2"] == expected_q
    assert aa != A and bb != B and shifted_query != query, "independent translations are not a no-op"


@pytest.mark.parametrize("value", (0.5, True, "1/2"))
def test_c1_exact_input_boundary_rejects_implicit_conversions(value):
    with pytest.raises(ValueError, match="exact rationals"):
        cert.exit_order_certificate(A, B, value)
    with pytest.raises(ValueError, match="exact rationals"):
        cert.exit_order_certificate(((value, 0), *A[1:]), B)


@pytest.mark.parametrize("name,replacements,gate,message", (
    ("exit_order_certificate", [("if reason:\n            return refused(reason, ring=owner, margin=margin)",
                                 "if False:\n            return refused(reason, ring=owner, margin=margin)")],
     test_c1_concavity_requires_boundary_persistence_not_just_a_distance_gap, "concave boundary persistence"),
    ("exit_order_certificate", [("if cross_margin <= 0:", "if False:")],
     test_c1_parallel_split_requires_normal_order_not_just_a_distance_gap, "parallel-edge splitting"),
    ("_rank_guard", [("if q <= 2*radius*radius:", "if q < 2*radius*radius:")],
     test_c1_interior_radius_bound_is_strict, "interior persistence requires"),
    ("_rank_guard", [("for competitor in others:", "for competitor in others[:1]:")],
     test_c1_ranking_checks_every_competitor_at_the_exact_boundary, "final competitor"),
    ("_rank_guard", [("h*h <= 32*q*radius*radius", "h*h < 32*q*radius*radius")],
     test_c1_ranking_checks_every_competitor_at_the_exact_boundary, "final competitor"),
    ("_rank_guard", [("h <= 0 or h*h", "h*h")],
     test_c1_squared_rank_inequality_needs_its_positive_branch, "negative h"),
))
def test_c1_real_internal_mutations_fail_named_semantic_assertions(monkeypatch, name, replacements, gate, message):
    replace_module_callable(monkeypatch, cert, name, replacements)
    with pytest.raises(AssertionError, match=message):
        gate()
