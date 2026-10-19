"""Exact sensitivity oracles are hand differentiation and the G5 closed form.

No LP finite-difference slope is used as a truth oracle. The bounded-face
min/max example is solved directly on the interval x1 in [0,1].
"""
from dataclasses import replace
from fractions import Fraction as Q

import pytest

from eab.kernel2d.sensitivity import (LimitSeed2, build_limit_seed2,
                                    evaluate_sensitivity2)
from eab.kernel2d.critical import CriticalBasis2, ThresholdProof2
from eab.kernel2d.statics import (CriticalParameter2, critical_parameter,
                                limit_load_ideal_exact_2d, solve_limit_problem2)
from eab.adapters.tia2d import g1
from test_tia2d_statics import _beam, _problem


def test_nondegenerate_original_matrix_fixed_basis_formula():
    result = solve_limit_problem2(_problem([[2, 1]], [3], [4, 0]))
    seed = LimitSeed2(((Q(1), Q(0)),), (Q(2),), (Q(3), Q(0)), "p")
    derivative = evaluate_sensitivity2(result, seed, parameter="p")
    assert derivative.method == "stable_basis"
    assert derivative.differentiability == "smooth"
    assert derivative.right_derivative == derivative.left_derivative == Q(11, 2)


def test_min_max_mapping_and_reverse_query_sign_on_tied_optimum():
    # min p*x1 becomes max -p*x1. At p=0 the max right slope is 0;
    # the max left slope is -1, hence the min slopes are 0 and 1.
    result = solve_limit_problem2(_problem([[1, 1]], [1], [0, 0]))
    seed = LimitSeed2(((Q(0), Q(0)),), (Q(0),), (-Q(1), Q(0)), "p")
    derivative = evaluate_sensitivity2(result, seed, parameter="p", tied_labels=("x1", "x2"))
    assert derivative.method == "mills_freund"
    assert derivative.differentiability == "one_sided"
    assert derivative.right_derivative == 0 and derivative.left_derivative == -1
    assert -derivative.right_derivative == 0
    assert derivative.tied_labels == ("x1", "x2")


@pytest.mark.parametrize("mu,expected", [(Q(1, 4), Q(2)), (Q(2), Q(0))])
def test_g5_friction_derivative_uses_bounded_optimal_face_lp(mu, expected):
    assembly, contacts = _beam(mu=mu)
    result = limit_load_ideal_exact_2d(assembly, contacts)
    derivative = evaluate_sensitivity2(result)
    assert derivative.method == "mills_freund"
    assert derivative.differentiability == "smooth"
    assert derivative.left_derivative == derivative.right_derivative == expected
    assert "L1接触骨架不变" in derivative.validity_conditions


def test_g5_switch_retains_one_sided_friction_slopes():
    assembly, contacts = _beam(mu=Q(1))
    result = limit_load_ideal_exact_2d(assembly, contacts)
    derivative = evaluate_sensitivity2(result, tied_labels=("sliding", "hinging"))
    assert derivative.method == "mills_freund"
    assert derivative.differentiability == "one_sided"
    assert derivative.right_derivative == 0 and derivative.left_derivative == 2
    assert derivative.tied_labels == ("sliding", "hinging")


def test_g5_zero_friction_preserves_nonzero_dual_recession_and_no_slope():
    assembly, contacts = _beam(mu=Q(0))
    result = limit_load_ideal_exact_2d(assembly, contacts)
    derivative = evaluate_sensitivity2(result)
    assert derivative.differentiability == "singular"
    assert derivative.reason == "possibly_discontinuous"
    assert derivative.directional_derivative is None
    assert derivative.left_derivative is None and derivative.right_derivative is None
    ray = derivative.dual_recession_ray
    A, b = result.problem.A, result.problem.b
    assert ray and any(ray) and sum(v * q for v, q in zip(b, ray)) == 0
    assert all(sum(A[i][j] * ray[i] for i in range(len(b))) >= 0 for j in range(len(result.problem.c)))


@pytest.mark.parametrize("mu,dP,dh", [(Q(1, 4), Q(1, 2), Q(0)), (Q(2), Q(2), Q(2))])
def test_g5_pressure_and_shared_height_exact_seed_derivatives(mu, dP, dh):
    assembly, contacts = _beam(mu=mu)
    result = limit_load_ideal_exact_2d(assembly, contacts)
    plate = assembly.bodies[-1]
    pressure = build_limit_seed2(result.problem, dead_seeds={plate.body_id: plate.dead}, parameter="P")
    derivative = evaluate_sensitivity2(result, pressure, parameter="P")
    assert derivative.method == "mills_freund"
    assert derivative.right_derivative == derivative.left_derivative == dP
    # Both sides share the same interface vertex/tangent seeds. References
    # and anchors remain constant; only the physical P application point moves.
    seeds = {c.label: ((Q(0), Q(c.point[1] == 1)), (Q(0), -Q(1))) for c in contacts.constraints}
    height = build_limit_seed2(result.problem, contact_seeds=seeds,
                              dead_seeds={plate.body_id: (0, 0, Q(1, 2))}, parameter="h")
    derivative = evaluate_sensitivity2(result, height, parameter="h")
    assert derivative.method == "mills_freund"
    assert derivative.right_derivative == derivative.left_derivative == dh


def test_live_load_seed_is_not_treated_as_a_rhs_derivative():
    assembly, contacts = _beam(mu=Q(1, 4))
    result = limit_load_ideal_exact_2d(assembly, contacts)
    middle = assembly.bodies[2]
    seed = build_limit_seed2(result.problem, live_seeds={middle.body_id: middle.live}, parameter="load_scale")
    derivative = evaluate_sensitivity2(result, seed, parameter="load_scale")
    assert derivative.right_derivative == derivative.left_derivative == -Q(1, 2)
    assert any(row[-1] for row in seed.dA) and not any(seed.db)


def test_primal_optimal_recession_is_not_reported_as_a_slope():
    result = solve_limit_problem2(_problem([[1, 0]], [1], [0, 0]))
    seed = LimitSeed2(((Q(0), Q(0)),), (Q(0),), (Q(0), Q(1)))
    derivative = evaluate_sensitivity2(result, seed)
    assert derivative.differentiability == "singular"
    assert derivative.primal_recession_ray == (Q(0), Q(1))


def test_single_valid_direction_and_bad_seed_are_explicit():
    result = solve_limit_problem2(_problem([[1, 1]], [1], [0, 0]))
    seed = LimitSeed2(((Q(0), Q(0)),), (Q(0),), (-Q(1), Q(0)))
    derivative = evaluate_sensitivity2(result, seed, negative_direction_valid=False)
    assert derivative.differentiability == "one_sided"
    assert derivative.right_derivative == 0 and derivative.left_derivative is None
    bad = LimitSeed2((), (), ())
    assert evaluate_sensitivity2(result, bad).call_status == "INVALID_INPUT"


def _g1_seed(problem, t, height, parameter):
    """Differentiate the shared interface endpoints directly, not LP values."""
    seeds = {}
    for contact in problem.contact_set.constraints:
        slope = contact.tangent[0] / contact.tangent[1]
        if parameter == "t":
            dp = (slope / t * (contact.point[1] - height / 2), Q(0))
            dt = (contact.tangent[0] / t, Q(0))
        else:
            dp = (slope * (contact.point[1] / height - Q(1, 2)), contact.point[1] / height)
            dt = tuple(v / height for v in contact.tangent)
        seeds[contact.label] = (dp, dt)
    return build_limit_seed2(problem, contact_seeds=seeds, parameter=parameter)


@pytest.mark.parametrize("orientation,height,parameter,expected,kind", [
    ("unreversed", Q(1), "t", Q(1), "mechanism"),
    ("unreversed", Q(1), "h", Q(0), "mechanism"),
    ("koureas", Q(1, 4), "t", Q(15, 16), "improving_ray"),
    ("koureas", Q(1, 4), "h", -Q(17, 32), "improving_ray"),
    ("reverse_i1", Q(1), "t", Q(1), "improving_ray"),
])
def test_g1_threshold_derivative_uses_the_attained_side_certificate(
        orientation, height, parameter, expected, kind):
    """Closed forms are differentiated by hand; open threshold uses no force basis."""
    critical = critical_parameter(g1(t=Q(1, 4), height=height, orientation=orientation),
                                  mu_max=1.0, max_steps=20)
    seed = _g1_seed(critical.threshold_certificate.problem, Q(1, 4), height, parameter)
    derivative = evaluate_sensitivity2(critical, seed, parameter=parameter, tied_labels=("shared",))
    assert derivative.method == "implicit_certificate"
    assert derivative.selected_piece[0] == kind
    assert derivative.differentiability == "smooth"
    assert derivative.left_derivative == derivative.right_derivative == expected
    assert derivative.tied_labels[0] == "shared"
    assert derivative.implicit_components
    assert all(slope == expected and slope == -dp / dmu
               for label, slope, dmu, dp, index in derivative.implicit_components)
    if orientation in ("koureas", "unreversed"):
        assert len(derivative.implicit_components) >= 2


def _two_crossings(polynomial=(-Q(1), Q(1))):
    """Two independent inequalities r_i=mu-1-p_i give a max of two roots."""
    endpoint = solve_limit_problem2(_problem([[1, 0, 0], [0, 1, 0]], [0, 0], [0, 0, 1]))
    branch = CriticalBasis2("improving_ray", (0, 1), 2, (Q(1),),
                            (polynomial, polynomial), ("first", "second"), Q(2), (Q(1), Q(1)))
    from eab.kernel2d.critical import branch_signs2
    proof = ThresholdProof2(Q(1), True, None, branch, (Q(0), Q(1)),
                            (Q(1), Q(2)), None, branch_signs2(branch, Q(1), Q(2)))
    critical = CriticalParameter2("OK", "CERTIFIED", exact_threshold=Q(1), attained=True,
                                  threshold_certificate=endpoint, threshold_proof=proof)
    seed = LimitSeed2(((Q(0), Q(0), Q(1)), (Q(0), Q(0), Q(2))),
                      (Q(0), Q(0)), (Q(0), Q(0), Q(0)), "p")
    mu_seed = LimitSeed2(((Q(0), Q(0), -Q(1)), (Q(0), Q(0), -Q(1))),
                         (Q(0), Q(0)), (Q(0), Q(0), Q(0)))
    return critical, seed, mu_seed


def test_competing_threshold_components_are_not_replaced_by_first_label():
    critical, seed, mu_seed = _two_crossings()
    derivative = evaluate_sensitivity2(critical, seed, parameter="p", threshold_mu_seed=mu_seed)
    assert derivative.differentiability == "tie"
    assert derivative.reason == "competing_threshold_slopes"
    assert derivative.tied_labels == ("first", "second")
    assert derivative.piece_jacobians == (("first", Q(1)), ("second", Q(2)))
    assert derivative.directional_derivative is None


def test_zero_implicit_denominator_and_singular_critical_basis_have_no_slope():
    critical, seed, mu_seed = _two_crossings((-Q(1), Q(3), -Q(3), Q(1)))
    mu_seed = replace(mu_seed, dA=((Q(0), Q(0), Q(0)), (Q(0), Q(0), Q(0))))
    derivative = evaluate_sensitivity2(critical, seed, parameter="p", threshold_mu_seed=mu_seed)
    assert derivative.differentiability == "singular"
    assert derivative.reason == "zero_implicit_denominator"
    assert derivative.directional_derivative is None
    branch = replace(critical.threshold_proof.upper_basis, determinant=(-Q(1), Q(1)))
    critical = replace(critical, threshold_proof=replace(critical.threshold_proof, upper_basis=branch))
    derivative = evaluate_sensitivity2(critical, seed, parameter="p", threshold_mu_seed=mu_seed)
    assert derivative.reason == "critical_basis_singular"


def test_threshold_slope_needs_exact_root_and_valid_exact_seed():
    critical, seed, mu_seed = _two_crossings()
    bracket = replace(critical, exact_threshold=None, attained=None)
    derivative = evaluate_sensitivity2(bracket, seed, threshold_mu_seed=mu_seed)
    assert derivative.differentiability == "unresolved"
    assert derivative.directional_derivative is None
    bad = replace(seed, dc=(float("inf"), Q(0), Q(0)))
    assert evaluate_sensitivity2(critical, bad, threshold_mu_seed=mu_seed).call_status == "INVALID_INPUT"
    invalid = evaluate_sensitivity2(critical, seed, threshold_mu_seed=mu_seed,
                                    positive_direction_valid=False, negative_direction_valid=False)
    assert invalid.reason == "no_valid_direction"
