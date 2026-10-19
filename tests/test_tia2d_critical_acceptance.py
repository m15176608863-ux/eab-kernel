"""Adversarial exact-certificate gates, independent of bisection's candidate.

The G1 truth values are hand-substituted closed forms, not adapter threshold
helpers. Polynomial tests use factored scalar polynomials and explicit LPs;
the dual recession oracle is the half-line y >= 0. No floating ray or finite
difference is a truth oracle. A separate source-copy mutation runner invokes
these same assertions after removing each production safeguard.
"""
from dataclasses import replace
from fractions import Fraction as Q

import pytest

from eab.adapters.tia2d import g1
from eab.kernel2d.assembly import Assembly2, Body2
from eab.kernel2d.contacts import ExactContact2, assemble_contact_set2
from eab.kernel2d.critical import CriticalBasis2, branch_signs2, mechanism_basis2
from eab.kernel2d.sensitivity import LimitSeed2, evaluate_sensitivity2
from eab.kernel2d.statics import (critical_parameter, limit_load_ideal_exact_2d,
                                 solve_limit_problem2)
from test_tia2d_statics import _problem, _verify
from test_tia2d_sensitivity import _two_crossings


@pytest.mark.parametrize("orientation,t,height,truth,closed", [
    ("koureas", Q(1, 3), Q(3, 16), Q(11, 48), True),
    ("unreversed", Q(3, 16), Q(1), Q(3, 16), False),
    ("reverse_i1", Q(5, 16), Q(1), Q(5, 16), True),
    ("koureas", Q(1, 8), Q(1, 16), Q(191, 2048), True),
])
@pytest.mark.parametrize("steps", [1, 2, 3, 4])
@pytest.mark.parametrize("ceiling", [Q(1, 2), Q(3, 4), Q(1)])
def test_low_budget_threshold_never_certifies_a_false_root(orientation, t, height, truth, closed, steps, ceiling):
    answer = critical_parameter(g1(t=t, height=height, orientation=orientation),
                                mu_max=ceiling, max_steps=steps)
    assert answer.status == "CERTIFIED"
    assert Q(answer.mu_lo) <= truth <= Q(answer.mu_hi)
    if answer.exact_threshold is None:
        assert answer.attained is None
    else:
        assert answer.exact_threshold == truth, "exact root requires both relevant continuation proofs"
        assert answer.attained is closed, "attained is not an endpoint-status guess"
    _verify(answer.lower_certificate)
    _verify(answer.upper_certificate)


def test_endpoint_states_do_not_replace_opposite_side_continuation():
    answer = critical_parameter(g1(t=Q(3, 16), orientation="unreversed"), max_steps=1)
    assert answer.lower_certificate.status == "OPTIMAL"
    assert answer.upper_certificate.status == "UNBOUNDED"
    assert answer.mu_hi == 0.5
    assert answer.exact_threshold is None and answer.attained is None, "upper state alone is not a closed threshold"


def test_branch_signs_rejects_interior_numerator_roots_even_when_midpoint_positive():
    # (x-1/8)(x-1/4) is positive at 1/2 but negative inside the interval.
    branch = CriticalBasis2("improving_ray", (0,), 1, (Q(1),),
                            ((Q(1, 32), -Q(3, 8), Q(1)),), ("r",), Q(1), (Q(21, 32),))
    assert branch_signs2(branch, Q(0), Q(1)) is None, "interior numerator roots must not be skipped"
    assert branch_signs2(None, Q(0), Q(0)) is None
    assert branch_signs2(branch, Q(1), Q(1)) == ()


def test_mechanism_basis_rejects_negative_reduced_costs():
    # Exact y=1 activates column 0, but slack for column 1 is 1-2=-1.
    good = solve_limit_problem2(_problem([[1, 1]], [1], [1, 2]))
    wrong_candidate = replace(good, exact_y=(Q(1),))
    matrix = (((Q(1),), (Q(1),)),)
    assert mechanism_basis2(wrong_candidate, matrix) is None, "negative dual slack is not a mechanism basis"


def test_dual_recession_requires_the_lp_witness_not_only_lineality():
    result = solve_limit_problem2(_problem([[1]], [0], [0]))
    seed = LimitSeed2(((Q(0),),), (Q(1),), (Q(0),), "rhs")
    derivative = evaluate_sensitivity2(result, seed, parameter="rhs")
    assert derivative.differentiability == "singular", "dual half-line recession must suppress a slope"
    assert derivative.reason == "possibly_discontinuous"
    assert derivative.primal_recession_ray is None
    assert derivative.dual_recession_ray == (Q(1),)
    assert derivative.directional_derivative is None
    assert derivative.display_status == "NOT_APPLICABLE"


def test_last_allowed_bisection_step_retains_resolution_reason_and_proof_reason():
    # [0,2^-1073] contains precisely one positive interior binary64 value.
    # That query consumes the only step; resolution is detected AFTER the loop.
    result = critical_parameter(g1(t=Q(0)), mu_max=Q(1, 2**1073), max_steps=1)
    assert result.bisection_termination == "input_resolution_limit", "loop-end resolution reason must survive"
    assert result.reason == result.bisection_termination
    assert result.threshold_proof_reason == "exact_basis_continuation"
    assert result.exact_threshold == 0 and result.attained is False
    assert result.mu_lo == 0 and Q(result.mu_hi) == Q(1, 2**1074)


@pytest.mark.parametrize("missing", [None, ()])
def test_threshold_derivative_declines_absent_or_empty_nondegenerate_continuation(missing):
    critical, seed, mu_seed = _two_crossings()
    proof = replace(critical.threshold_proof, upper_signs=missing)
    result = evaluate_sensitivity2(replace(critical, threshold_proof=proof), seed, threshold_mu_seed=mu_seed)
    assert result.differentiability == "unresolved"
    assert result.reason == "critical_basis_continuation_unproved"
    assert result.directional_derivative is None


def test_threshold_derivative_distinguishes_degenerate_proof_from_absence():
    critical, seed, mu_seed = _two_crossings()
    proof = replace(critical.threshold_proof, upper_signs=(), upper_interval=(Q(1), Q(1)))
    result = evaluate_sensitivity2(replace(critical, threshold_proof=proof), seed, threshold_mu_seed=mu_seed)
    assert result.differentiability == "tie" and result.implicit_components


def test_threshold_derivative_declines_negative_endpoint_ratio_and_missing_basis():
    critical, seed, mu_seed = _two_crossings()
    branch = replace(critical.threshold_proof.upper_basis, numerators=((-Q(2), Q(1)), (-Q(1), Q(1))))
    proof = replace(critical.threshold_proof, upper_basis=branch)
    result = evaluate_sensitivity2(replace(critical, threshold_proof=proof), seed, threshold_mu_seed=mu_seed)
    assert result.differentiability == "unresolved"
    assert result.reason == "critical_basis_infeasible_at_threshold"
    proof = replace(critical.threshold_proof, upper_basis=None)
    result = evaluate_sensitivity2(replace(critical, threshold_proof=proof), seed, threshold_mu_seed=mu_seed)
    assert result.differentiability == "unresolved"
    assert result.reason == "critical_basis_unavailable"


def test_zero_boundary_reason_does_not_claim_missing_threshold_or_certified_slope():
    critical = critical_parameter(g1(t=Q(1, 4)))
    assert critical.exact_threshold == 0 and critical.threshold_certificate is not None
    result = evaluate_sensitivity2(critical, parameter="height")
    assert result.reason == "threshold_on_domain_boundary_without_proof"
    assert result.differentiability == "unresolved" and result.directional_derivative is None


def _square(name, x, y, fixed=False, dead=(0, 0, 0), live=(0, 0, 0)):
    return Body2.from_vertices(name, ((x, y), (x+1, y), (x+1, y+1), (x, y+1)),
        reference_point=(0, 0), dof_anchor=(0, 0), boundary_type="FIXED_BODY" if fixed else None,
        dof_mask=(0, 0, 0) if fixed else (1, 1, 1), dead=dead, live=live)


def test_infeasible_domain_and_unresolved_contact_reasons_are_truthful():
    assembly = Assembly2((_square("A", 0, 0, dead=(1, 0, 0), live=(0, -1, 0)),), (), "complete")
    result = critical_parameter(assembly, mu_max=2)
    assert result.status == "INFEASIBLE" and result.reason == "infeasible_on_domain"
    assert result.mu_hi is None and result.lower_certificate.farkas is not None
    _verify(result.lower_certificate)
    assembly = Assembly2((_square("A", 0, 0), _square("B", 1, 1, True)), ((0, 1),), "complete")
    result = critical_parameter(assembly)
    assert result.status == "UNPROVED" and result.reason == "contact_set_unresolved"


def test_regression_c_mu_max_two_excludes_kinematically_redundant_vv_from_statics():
    assembly = Assembly2((_square("A", 0, 0, live=(0, -1, 0)), _square("B", 1, 1, True),
                         _square("C", 1, 0, True)), ((0, 1), (0, 2), (1, 2)), "complete", mu=Q(2))
    contacts = assemble_contact_set2(assembly)
    assert any(point.fp_type == "REDUNDANT_PROVED" for point in contacts.points)
    result = limit_load_ideal_exact_2d(assembly, contacts)
    assert result.status == "OPTIMAL" and result.exact_value == 0
    critical = critical_parameter(assembly, contact_set=contacts, mu_max=2)
    assert critical.reason == "bounded_on_domain" and critical.mu_hi is None
    derivative = evaluate_sensitivity2(result)
    threshold_derivative = evaluate_sensitivity2(critical)
    for answer in (result, critical, derivative, threshold_derivative):
        assert "true_vv_excluded_from_statics" in answer.validity_conditions
    # This intentionally different statics model retains the VV as two
    # frictional halfplanes. It is a diagnostic, NOT the approved profile1.
    corner = tuple(ExactContact2(0, 1, (Q(1), Q(1)), tangent, (), ("diagnostic_corner", k))
                   for k, tangent in enumerate(((Q(0), Q(1)), (-Q(1), Q(0)))))
    alternative = replace(contacts, constraints=contacts.constraints + corner)
    retained = limit_load_ideal_exact_2d(assembly, alternative)
    assert retained.status == "UNBOUNDED"
    _verify(result)
    _verify(retained)
