"""INT1 missing semantic teeth, independent exact expectations, no hash oracle.

Oracle inventory: fractions.Fraction, explicit rational rotation coordinates,
integer polynomial factorizations, affine residuals annihilating the three
normal-equation columns, and literal focused-frame branch counts. None uses
production polynomial/bound/fit primitives to form numerical expectations.
The existing M5a2 Cramer-rule and component-formula guards are reused for the
three affine mutants formerly confined to an evidence script. Replay branch
tests use historical inputs, not their aggregate stats as an oracle. Source
hash callbacks are disabled before both controls and internal source mutants.
"""
from fractions import Fraction as F

import pytest

from eab.kernel2d import affine_motion as affine
from eab.kernel2d import algebraic as alg
from eab.kernel2d import se2
from mutation_support import mutated_function, replace_module_callable
import test_m5a2_affine as affine_gates
import test_m5a2_replay as replay_gates

replay = replay_gates.replay
affine_replay = affine_gates.replay


def test_quadratic_rational_branch_keeps_the_selected_se2_entrance():
    # Vertex (-1,7) hits y=5 when 2-2*s-12*s*s=0: roots -1/2,1/3.
    # The other vertices are still above y=5 at s=1/3. The first root is
    # outside the closed step, not a candidate for the public time container.
    a = ((-1, 7), (0, 8), (1, 8))
    b = ((-10, 4), (0, 4), (0, 5), (-10, 5))
    result = se2.se2_first_entrance(a, b, se2.SE2Motion(1))
    assert result.status == "contact" and result.features == (("VE", 0, 2),)
    assert result.exact_time == F(1, 3), "INT1 quadratic SE2 entrance must be 1/3, never the out-of-window -1/2"
    assert result.exact_time.rational == F(1, 3)


@pytest.mark.parametrize("u,scale,center", (
    (F(1, 100), F(1), (0, 0)),
    (F(1, 1000), F(1, 10**6), (10**6, -10**5)),
    (F(1, 10000), F(10**6), (-17, 29)),
))
def test_off_centroid_small_angle_bounds_preserve_real_contact(u, scale, center):
    # The tiny triangle is near (1,1), but rotates about arbitrary c, NOT its
    # centroid. At s=1, x=(1-2*u-u*u)/(1+u*u) < 1-2*u-u*u.
    # A max-norm radius underbounds this excursion by order u*u.
    def point(p):
        return tuple(center[k]+scale*p[k] for k in (0, 1))

    epsilon = u**3
    a = tuple(point(p) for p in ((1, 1), (1+epsilon, 1), (1, 1+epsilon)))
    right = 1-2*u-u*u
    b = tuple(point(p) for p in ((right-u*u/4, 1-u), (right, 1-u),
                                 (right, 1+3*u), (right-u*u/4, 1+3*u)))
    motion = se2.SE2Motion(u, center=center)
    result = se2.se2_first_entrance(a, b, motion)
    assert result.status == "contact", "INT1 off-centroid small-angle real contact cannot be broad-phase rejected"
    assert 0 < result.exact_time < 1
    bounds = se2._swept_bounds(se2._validated_ring(a, motion))
    for time in (F(0), F(1, 7), F(1, 2), F(1)):
        z = time*u
        for x, y in a:
            local_x, local_y = x-center[0], y-center[1]
            expected = (center[0]+((1-z*z)*local_x-2*z*local_y)/(1+z*z),
                        center[1]+(2*z*local_x+(1-z*z)*local_y)/(1+z*z))
            assert all(bounds[k][0] <= expected[k] <= bounds[k][1] for k in (0, 1)), \
                "INT1 arbitrary-center swept box contains independent rational path"


@pytest.mark.parametrize("prime", (2, 3, 5))
def test_modular_no_root_filter_skips_primes_dividing_the_leading_coefficient(prime):
    # (p*x-1)*(p*x*x+1); modulo p it is -1, yet x=1/p is a root.
    value = alg.RealAlgebraic((-1, prime, -prime, prime*prime), 0, 1)
    assert value.as_rational() == F(1, prime), "INT1 primes dividing the leading coefficient cannot exclude a rational root"


@pytest.mark.parametrize("denominator", (10000000000019, 100000000000000000039))
def test_rational_reconstruction_refines_large_denominator_away_from_farey_boundary(denominator):
    root, neighbor = F(1, denominator), F(1, denominator-1)
    gap = neighbor-root
    lower, upper = root-gap/8, root+11*gap/8
    middle = (lower+upper)/2
    # Not a tie: midpoint lies a full gap/8 beyond the Farey boundary.
    assert middle-(root+neighbor)/2 == gap/8
    assert middle.limit_denominator(denominator) == neighbor
    assert upper-lower > F(1, 2*denominator*denominator)
    # (x-root)*(x*x+1)*(x*x+2): exactly one real root.
    value = alg.RealAlgebraic((-2*root, 2, -3*root, 3, -root, 1), lower, upper)
    assert value.as_rational() == root, "INT1 quadratic-denominator refinement recovers the root away from a Farey tie"


def test_public_algebraic_constructor_retains_closed_upper_endpoint_root():
    # (3*x-1)*(x-2); only root 1/3 lies in the closed bracket [0,1/3].
    value = alg.RealAlgebraic((2, -7, 3), 0, F(1, 3))
    assert value == F(1, 3), "INT1 closed upper endpoint denotes the endpoint root"
    assert value.rational == value.lower == value.upper == F(1, 3)
    assert value.refine() == value and value.sign_polynomial(-1, 3) == 0
    with pytest.raises(ValueError, match="exactly one real root"):
        alg.RealAlgebraic((2, -7, 3), F(1, 3), 2)


@pytest.mark.parametrize("scale", (F(1, 10**100), F(1), F(10**6)))
def test_affine_delta_is_linf_not_l1_for_two_component_residuals(scale):
    # Checkerboard residuals are orthogonal to 1,x,y. Consequently the exact
    # LS map is the identity; two nonzero coordinates distinguish L-inf/L1.
    start = tuple((1000+scale*x, -10**6+scale*y) for x, y in ((0, 0), (1, 0), (1, 1), (0, 1)))
    signs = (1, -1, 1, -1)
    end = tuple((p[0]+sign*scale, p[1]+2*sign*scale) for p, sign in zip(start, signs))
    fit = affine.fit_affine(start, end)
    assert fit.matrix == ((1, 0), (0, 1))
    assert fit.residuals == tuple((sign*scale, 2*sign*scale) for sign in signs)
    assert fit.delta == 2*scale, "INT1 affine delta is coordinate L-infinity, not residual-vector L1"


def test_focused_frame_stats_count_proven_separation_omissions():
    frame, sg, eg, baseline, _ = replay_gates.real_inputs("bb03", 1, (1, 3))
    assert not baseline["pairs"]
    actual = replay.frame_result(frame, sg, eg, baseline)
    assert actual["stats"] == {"all_pairs": 1, "UNCERTIFIED_NONRIGID_ENDPOINTS": 1,
                               "omitted_proven_separated_pairs": 1}, \
        "INT1 focused omitted-pair stats conserve the certified separated branch"
    assert actual["pairs"] == []
    assert all(not phase["records"] for phase in actual["phases"].values())


@pytest.mark.parametrize("state,pair,status", ((0, (2, 3), "contact"), (1, (1, 2), "initial_overlap")))
def test_focused_frame_stats_count_initial_contact_and_overlap_reuse(state, pair, status):
    frame, sg, eg, baseline, _ = replay_gates.real_inputs("bb05", 1, pair)
    assert len(baseline["pairs"]) == 1 and baseline["pairs"][0]["initial_state"] == state
    actual = replay.frame_result(frame, sg, eg, baseline)
    assert actual["stats"] == {"all_pairs": 1, "UNCERTIFIED_NONRIGID_ENDPOINTS": 1,
                               "REUSED_IDENTICAL_INITIAL_GEOMETRY": 1,
                               "initial_"+str(state)+"_"+status: 1}, \
        "INT1 focused initial-geometry reuse stats conserve both contact and overlap"
    assert len(actual["pairs"]) == 1
    record = actual["pairs"][0]
    assert record["path"] == "REUSED_IDENTICAL_INITIAL_GEOMETRY"
    assert record["rigid"] == record["chord"] == baseline["pairs"][0]["actual"]
    assert record["pd"] == baseline["pairs"][0]["pd"]


# Every mutation edits a real internal function body before executing it.
# The messages identify the exact numerical/semantic assertion that must fail.
MUTATIONS = (
    ("quadratic_outside_interval", "INT1 quadratic SE2 entrance must be 1/3"),
    ("swept_max_norm", "INT1 off-centroid small-angle real contact"),
    ("modular_leading_coefficient", "INT1 primes dividing the leading coefficient"),
    ("refinement_linear_denominator", "INT1 quadratic-denominator refinement"),
    ("refinement_four_times_wider", "INT1 quadratic-denominator refinement"),
    ("closed_upper_endpoint", "INT1 closed upper endpoint denotes"),
    ("affine_delta_l1", "INT1 affine delta is coordinate L-infinity"),
    ("omitted_pair_stats", "INT1 focused omitted-pair stats"),
    ("initial_contact_reuse_stats", "INT1 focused initial-geometry reuse stats"),
    ("initial_overlap_reuse_stats", "INT1 focused initial-geometry reuse stats"),
    ("affine_fit_cross_sign", "affine endpoint independent normal-equation oracle"),
    ("positive_affine_residual_certified", "positive residual must not receive endpoint-exact certificate"),
    ("residual_correction_sign", "corrected path exactly closes original snapshot endpoint"),
)


def semantic_guard(kind):
    if kind == "quadratic_outside_interval":
        test_quadratic_rational_branch_keeps_the_selected_se2_entrance()
    elif kind == "swept_max_norm":
        test_off_centroid_small_angle_bounds_preserve_real_contact(F(1, 100), F(1), (0, 0))
    elif kind == "modular_leading_coefficient":
        test_modular_no_root_filter_skips_primes_dividing_the_leading_coefficient(2)
    elif kind.startswith("refinement_"):
        test_rational_reconstruction_refines_large_denominator_away_from_farey_boundary(100000000000000000039)
    elif kind == "closed_upper_endpoint":
        test_public_algebraic_constructor_retains_closed_upper_endpoint_root()
    elif kind == "affine_delta_l1":
        test_affine_delta_is_linf_not_l1_for_two_component_residuals(F(1))
    elif kind == "omitted_pair_stats":
        test_focused_frame_stats_count_proven_separation_omissions()
    elif kind == "initial_contact_reuse_stats":
        test_focused_frame_stats_count_initial_contact_and_overlap_reuse(0, (2, 3), "contact")
    elif kind == "initial_overlap_reuse_stats":
        test_focused_frame_stats_count_initial_contact_and_overlap_reuse(1, (1, 2), "initial_overlap")
    elif kind == "residual_correction_sign":
        affine_gates.test_linear_residual_correction_closes_data_without_certification()
    elif kind in ("affine_fit_cross_sign", "positive_affine_residual_certified"):
        affine_gates.test_fit_matches_independent_three_point_and_normal_equation_oracles(affine_gates.POINTS, True)
    else:
        raise AssertionError("unknown INT1 semantic mutation")


def mask_source_hashes(monkeypatch):
    monkeypatch.setattr(replay, "code_hashes", lambda: {})
    monkeypatch.setattr(replay, "file_hash", lambda path: "HASH_TRIPWIRE_DISABLED")
    monkeypatch.setattr(affine_replay, "code_hashes", lambda: {})
    monkeypatch.setattr(affine_replay, "file_hash", lambda path: "HASH_TRIPWIRE_DISABLED")


def inject_semantic_mutation(kind, monkeypatch):
    if kind in ("quadratic_outside_interval", "modular_leading_coefficient",
                "refinement_linear_denominator", "refinement_four_times_wider"):
        replacements = {
            "quadratic_outside_interval": ("if self.lower <= value <= self.upper:", "if True:"),
            "modular_leading_coefficient": ("if integers[-1] % prime == 0:", "if False:"),
            "refinement_linear_denominator": ("F(1, 2*bound*bound)", "F(1, 2*bound)"),
            "refinement_four_times_wider": ("F(1, 2*bound*bound)", "F(2, bound*bound)"),
        }
        changed = mutated_function(alg.RealAlgebraic.as_rational, alg, (replacements[kind],))
        monkeypatch.setattr(alg.RealAlgebraic, "as_rational", changed)
    elif kind == "closed_upper_endpoint":
        changed = mutated_function(alg.RealAlgebraic.__post_init__, alg, ((
            "elif not _evaluate(polynomial, upper):\n        lower = upper",
            "elif not _evaluate(polynomial, upper):\n        upper = lower"),))
        monkeypatch.setattr(alg.RealAlgebraic, "__post_init__", changed)
    elif kind == "swept_max_norm":
        replace_module_callable(monkeypatch, se2, "_swept_bounds", (("abs(x)+abs(y)", "max(abs(x),abs(y))"),))
    elif kind == "affine_delta_l1":
        changed = mutated_function(affine.AffineFit.delta.fget, affine, ((
            "max(abs(v) for row in self.residuals for v in row)",
            "max(sum(abs(v) for v in row) for row in self.residuals)"),))
        monkeypatch.setattr(affine.AffineFit, "delta", property(changed))
    elif kind == "omitted_pair_stats":
        replace_module_callable(monkeypatch, replay, "frame_result", ((
            'stats["omitted_proven_separated_pairs"] += 1',
            'stats["omitted_proven_separated_pairs"] += 2'),))
    elif kind in ("initial_contact_reuse_stats", "initial_overlap_reuse_stats"):
        replace_module_callable(monkeypatch, replay, "frame_result", ((
            "stats[path] += 1", "stats[path] += int(state < 0)"),))
    elif kind == "affine_fit_cross_sign":
        changed = replace_module_callable(monkeypatch, affine, "fit_affine", ((
            "row[0]*yy-row[1]*xy", "row[0]*yy+row[1]*xy"),))
        monkeypatch.setattr(affine_gates, "fit_affine", changed)
    elif kind == "positive_affine_residual_certified":
        changed = mutated_function(affine.AffineFit.endpoint_certificate.fget, affine, ((
            "self.delta == 0", "self.delta <= F(1, 2**52)"),))
        monkeypatch.setattr(affine.AffineFit, "endpoint_certificate", property(changed))
    elif kind == "residual_correction_sign":
        changed = mutated_function(affine.DDAAffineMotion.corrected_at, affine, ((
            "value[k]+s*residual[k]", "value[k]-s*residual[k]"),))
        monkeypatch.setattr(affine.DDAAffineMotion, "corrected_at", changed)
    else:
        raise AssertionError("unknown INT1 semantic mutation")


@pytest.mark.parametrize("kind,message", MUTATIONS)
def test_internal_int1_mutants_fail_the_designated_semantic_assertion(kind, message, monkeypatch):
    mask_source_hashes(monkeypatch)
    semantic_guard(kind)
    inject_semantic_mutation(kind, monkeypatch)
    with pytest.raises(AssertionError, match=message):
        semantic_guard(kind)
