"""Independent statics oracles: elementary force/moment balance and G5 formulas.

Hand-written endpoint records isolate the new statics layer from geometry;
they do NOT establish completeness of production contact enumeration. The
tests recheck raw exact matrices and primal/dual witnesses independently.
"""
from dataclasses import replace
from fractions import Fraction as Q
from itertools import combinations
from math import nextafter

import pytest

from eab.kernel2d.assembly import Assembly2, Body2
from eab.kernel2d.contacts import ContactSet2, ExactContact2
from eab.kernel2d.statics import (LimitProblem2, build_limit_problem2,
                                critical_parameter, limit_load_ideal_exact_2d,
                                solve_limit_problem2)


def _rectangle(x0, x1, h):
    return ((x0, 0), (x1, 0), (x1, h), (x0, h))


def _beam(n=3, mu=Q(1, 4), h=Q(1), P=Q(1), mask=(1, 0, 0),
          anchor=None, reference=(Q(5, 8), -Q(3, 8))):
    """Exact G5 endpoints; force application points are not DOF anchors."""
    mu, h, P = Q(mu), Q(h), Q(P)
    if anchor is None:
        anchor = (Q(n), h / 2)
    bodies = [Body2("left", _rectangle(-1, 0, h), reference,
                    "FIXED_BODY", (0, 0, 0), reference)]
    for i in range(n):
        live = (0, -1, -(Q(n, 2) - reference[0])) if i == n // 2 else (0, 0, 0)
        bodies.append(Body2(str(i), _rectangle(i, i + 1, h), reference, dof_anchor=reference, live=live))
    bodies.append(Body2("right", _rectangle(n, n + 1, h), reference,
                        "FORCE_CONTROLLED_PLATE", mask, anchor,
                        (-P, 0, (h / 2 - reference[1]) * P)))
    assembly = Assembly2(tuple(bodies), tuple(combinations(range(n + 2), 2)), "complete", mu=mu)
    constraints = tuple(ExactContact2(a=face + 1, b=face, point=(Q(face), y),
                                     tangent=(Q(0), -h), label=(face, y), sources=())
                        for face in range(n + 1) for y in (Q(0), h))
    contacts = ContactSet2(assembly=assembly, constraints=constraints, points=(), raw_sources=(),
                           unresolved=(), redundancy_certificates=(), status="RESOLVED",
                           call_status="OK", mathematical_status="RESOLVED",
                           completeness="complete", reason=None)
    return assembly, contacts


def _verify(result):
    A, b, c = result.problem.A, result.problem.b, result.problem.c
    if result.status == "OPTIMAL":
        x, y = result.exact_x, result.exact_y
        assert all(v >= 0 for v in x)
        assert [sum(a * v for a, v in zip(row, x)) for row in A] == list(b)
        assert all(sum(A[i][j] * y[i] for i in range(len(b))) >= c[j] for j in range(len(c)))
        assert sum(a * v for a, v in zip(c, x)) == result.exact_value == sum(a * v for a, v in zip(b, y))
    elif result.status == "UNBOUNDED":
        assert all(v >= 0 for v in result.feasible_point + result.improving_ray)
        assert all(sum(a * x for a, x in zip(row, result.feasible_point)) == rhs for row, rhs in zip(A, b))
        assert all(sum(a * x for a, x in zip(row, result.improving_ray)) == 0 for row in A)
        assert sum(ci * x for ci, x in zip(c, result.improving_ray)) == 1
    else:
        assert result.status == "INFEASIBLE"
        assert all(sum(A[i][j] * result.farkas[i] for i in range(len(b))) <= 0 for j in range(len(c)))
        assert sum(v * y for v, y in zip(b, result.farkas)) == 1


@pytest.mark.parametrize("n,mu,h,P", [(3, Q(0), Q(1), Q(1)), (3, Q(1, 4), Q(1), Q(1)),
                                        (3, Q(2), Q(1), Q(1)), (5, Q(2), Q(1), Q(1)),
                                        (7, Q(2), Q(1), Q(1)), (3, Q(3, 8), Q(3, 2), Q(5, 4))])
def test_g5_closed_form_and_exact_certificates(n, mu, h, P):
    assembly, contacts = _beam(n, mu, h, P)
    result = limit_load_ideal_exact_2d(assembly, contacts)
    assert result.call_status == "OK" and result.status == "OPTIMAL"
    assert result.exact_value == min(2 * mu * P, 4 * P * h / (n - 1))
    assert result.display_status == "EXACT"
    _verify(result)


@pytest.mark.parametrize("mask,anchor,expected", [((1, 1, 0), (Q(3), Q(1, 2)), Q(2, 3)),
                                                 ((1, 0, 1), (Q(0), Q(0)), Q(1, 3)),
                                                 ((1, 0, 1), (Q(3), Q(1, 2)), Q(4, 3)),
                                                 ((1, 0, 1), (Q(5, 8), -Q(3, 8)), Q(8, 19))])
def test_g5_released_masks_require_physical_anchor(mask, anchor, expected):
    assembly, contacts = _beam(mu=Q(2), mask=mask, anchor=anchor)
    result = limit_load_ideal_exact_2d(assembly, contacts)
    assert result.exact_value == expected
    _verify(result)


def test_reference_reparameterization_does_not_move_physical_constraint():
    values = []
    for reference in ((Q(0), Q(0)), (Q(5, 8), -Q(3, 8)), (Q(2**17), -Q(2**10))):
        assembly, contacts = _beam(mu=Q(2), mask=(1, 0, 1), anchor=(Q(0), Q(0)), reference=reference)
        result = limit_load_ideal_exact_2d(assembly, contacts)
        _verify(result)
        values.append(result.exact_value)
    assert values == [Q(1, 3)] * 3


def test_unnormalized_generators_and_live_column_are_preserved():
    assembly, contacts = _beam(h=Q(2), mu=Q(1, 4))
    problem = build_limit_problem2(assembly, contacts, Q(1, 4))
    assert problem.A[0][:2] == (Q(2), Q(2))
    assert problem.A[1][:2] == (Q(1, 2), -Q(1, 2))
    assert problem.A[4][-1] == -1
    assert problem.A[5][-1] == -(Q(3, 2) - Q(5, 8))


def _problem(A, b, c):
    return LimitProblem2(tuple(tuple(Q(v) for v in row) for row in A), tuple(Q(v) for v in b), tuple(Q(v) for v in c),
                         (), (), (), (), Q(0), None, None)


@pytest.mark.parametrize("A,b,c,status", [([[1, -1]], [2], [0, 1], "UNBOUNDED"),
                                         ([[1, 1]], [-1], [0, 1], "INFEASIBLE"),
                                         ([], [], [1], "UNBOUNDED")])
def test_auxiliary_certificates_do_not_decode_float_rays(A, b, c, status):
    result = solve_limit_problem2(_problem(A, b, c))
    assert result.status == status
    _verify(result)


def test_unresolved_incomplete_and_mismatched_inputs_do_not_become_zero():
    assembly, contacts = _beam()
    contacts = replace(contacts, status="MECHANICAL_UNRESOLVED", mathematical_status="MECHANICAL_UNRESOLVED")
    result = limit_load_ideal_exact_2d(assembly, contacts)
    assert result.status == "MECHANICAL_UNRESOLVED" and result.exact_value is None
    contacts = replace(contacts, status="RESOLVED", mathematical_status="RESOLVED", completeness="completeness_unknown")
    assert limit_load_ideal_exact_2d(assembly, contacts).status == "UNPROVED"
    contacts = replace(contacts, completeness="complete")
    assert limit_load_ideal_exact_2d(replace(assembly, mu=Q(1)), contacts).call_status == "INVALID_INPUT"
    assert limit_load_ideal_exact_2d(assembly, contacts, mu=-1).call_status == "INVALID_INPUT"


def test_invalid_assembly_and_contact_record_types_return_call_errors():
    """Bad public input types must not escape as AttributeError or fake zero."""
    assembly, contacts = _beam()
    for bad_assembly, bad_contacts in ((object(), contacts), (assembly, object())):
        result = limit_load_ideal_exact_2d(bad_assembly, bad_contacts)
        assert result.call_status == "INVALID_INPUT"
        assert result.mathematical_status is None and result.exact_value is None
        critical = critical_parameter(bad_assembly, contact_set=bad_contacts)
        assert critical.call_status == "INVALID_INPUT"
        assert critical.exact_threshold is None
        assert critical.mu_lo is None and critical.mu_hi is None


def test_g5_critical_is_bounded_on_declared_domain_not_switch():
    assembly, contacts = _beam()
    result = critical_parameter(assembly, mu_max=Q(4), contact_set=contacts)
    assert result.reason == "bounded_on_domain" and result.mu_hi is None
    assert result.lower_certificate.exact_value == 2 and result.attained is None
    _verify(result.lower_certificate)
    assert critical_parameter(assembly, "height", contact_set=contacts).call_status == "UNSUPPORTED"
    assert critical_parameter(assembly, mu_max=Q(1, 3), contact_set=contacts).call_status == "INVALID_INPUT"
    assert critical_parameter(assembly, mu_max=float("inf"), contact_set=contacts).call_status == "INVALID_INPUT"


def test_binary64_critical_search_keeps_adjacent_certified_endpoints(monkeypatch):
    """A one-row exact LP, not a fake status, places the switch at 1/3."""
    import eab.kernel2d.statics as statics
    assembly, contacts = _beam()
    def query(assembly, contact_set, *, mu):
        return solve_limit_problem2(_problem([[Q(1, 3) - mu, 1]], [0], [1, 0]))
    monkeypatch.setattr(statics, "limit_load_ideal_exact_2d", query)
    result = critical_parameter(assembly, mu_max=1.0, max_steps=80, contact_set=contacts)
    assert Q(result.mu_lo) < Q(1, 3) < Q(result.mu_hi)
    assert nextafter(result.mu_lo, result.mu_hi) == result.mu_hi
    assert result.attained is None and result.exact_threshold is None
    assert result.reason == "input_resolution_limit"
    _verify(result.lower_certificate)
    _verify(result.upper_certificate)


def test_exact_binary64_grid_handles_subnormals_binades_and_maximum():
    from eab.kernel2d.statics import _binary_midpoint, _is_binary64
    least = Q(1, 2**1074)
    assert _binary_midpoint(Q(0), least) is None
    assert _binary_midpoint(Q(0), 2 * least) == least
    assert _binary_midpoint(Q(1), Q(1) + Q(1, 2**52)) is None
    assert _binary_midpoint(Q(1) - Q(1, 2**53), Q(1) + Q(1, 2**52)) == 1
    maximum = Q(2**1024 - 2**971)
    assert _is_binary64(maximum)
    assert not _is_binary64(Q(2**1024))
    assert _binary_midpoint(maximum - Q(2**971), maximum) is None
    assert not _is_binary64(Q(1, 3))


def test_real_contact_path_matches_independent_g5_endpoint_model():
    assembly, contacts = _beam(mu=Q(1, 4))
    actual = limit_load_ideal_exact_2d(assembly)
    expected = limit_load_ideal_exact_2d(assembly, contacts)
    assert actual.status == "OPTIMAL" and actual.exact_value == expected.exact_value == Q(1, 2)
    assert len(actual.problem.contact_set.constraints) == 8
    _verify(actual)


@pytest.mark.parametrize("n,mu", [(3, Q(0)), (3, Q(1, 4)), (3, Q(2)), (5, Q(2)), (7, Q(2))])
def test_g5_two_bidirectional_guides_independently_match_mask(n, mu):
    """Old all-DOF assembly uses four frictionless guide contacts, not row deletion.

Two separated +/-ey pairs constrain plate y and rotation through their
actual velocity inequalities. Axis normals are exactly unit vectors, so
the older model's normal-rounding distinction does not affect this oracle.
"""
    from eab.limit import LimitContact
    from eab.limit_multi import LimitBody, BodyContact, limit_load_multi, check_duality_multi
    assembly, contacts = _beam(n=n, mu=mu)
    expected = limit_load_ideal_exact_2d(assembly, contacts)
    origin = (Q(5, 8), -Q(3, 8))
    bodies = [LimitBody(list(body.dead), list(body.live)) for body in assembly.bodies[1:]]
    model = []
    for face in range(n + 1):
        for y in (Q(0), Q(1)):
            model.append(BodyContact(LimitContact((Q(face), y), (1, 0), mu),
                                     face, face - 1 if face else None))
    for x in (Q(n), Q(n + 1)):
        for sign in (-1, 1):
            model.append(BodyContact(LimitContact((x, Q(1, 2)), (0, sign), Q(0)), n, None))
    result = limit_load_multi(bodies, model, dim=2, origin=origin)
    assert result.status == "optimal"
    assert result.alpha.exact == expected.exact_value
    assert check_duality_multi(result, bodies, model, dim=2, origin=origin)["ok"]


@pytest.mark.parametrize("t,h,orientation,threshold,attained", [
    (Q(1, 4), Q(1, 4), "koureas", Q(15, 128), True),
    (Q(1, 4), Q(1), "unreversed", Q(1, 4), False),
    (Q(1, 4), Q(1), "reverse_i1", Q(1, 4), True),
    (Q(0), Q(1), "koureas", Q(0), False),
    (Q(1, 3), Q(1, 4), "koureas", Q(7, 36), True),
])
def test_g1_thresholds_are_certified_from_basis_polynomials(t, h, orientation, threshold, attained):
    """Closed-form threshold is an independent oracle, never a query input."""
    from eab.adapters.tia2d import g1
    from eab.kernel2d.algebraic import p_eval
    result = critical_parameter(g1(t=t, height=h, orientation=orientation), max_steps=20)
    assert result.exact_threshold == threshold and result.attained is attained
    assert result.threshold_proof_reason == "exact_basis_continuation"
    assert result.reason == result.bisection_termination
    assert Q(result.mu_lo) <= threshold <= Q(result.mu_hi)
    assert result.critical_polynomials and result.threshold_proof
    assert result.threshold_certificate.problem.mu == threshold
    _verify(result.lower_certificate)
    _verify(result.upper_certificate)
    _verify(result.threshold_certificate)
    for branch in result.critical_polynomials:
        denominator = p_eval(branch.determinant, branch.sample_parameter)
        assert denominator != 0
        assert tuple(p_eval(p, branch.sample_parameter) / denominator for p in branch.numerators) == branch.sample_values
        assert all(v >= 0 for v in branch.sample_values)
    if threshold == Q(7, 36):
        assert Q(result.mu_lo) < threshold < Q(result.mu_hi)


def test_g1_zero_threshold_respects_empty_unbounded_set_on_zero_domain():
    from eab.adapters.tia2d import g1
    closed = critical_parameter(g1(t=Q(1, 4)), mu_max=0)
    assert closed.exact_threshold == 0 and closed.attained is True
    assert closed.lower_certificate is None
    result = critical_parameter(g1(t=Q(0)), mu_max=0)
    assert result.reason == "bounded_on_domain" and result.mu_hi is None
    assert result.exact_threshold is None and result.attained is None


def test_polynomial_continuation_rejects_interior_poles_and_negative_ray():
    from eab.kernel2d.critical import CriticalBasis2, branch_signs2
    positive = CriticalBasis2("improving_ray", (0,), 1, (Q(0), Q(1)), ((Q(1),),), (), Q(1), (Q(1),))
    assert branch_signs2(positive, Q(0), Q(1)) is not None  # 1/mu, open at zero.
    pole = replace(positive, determinant=(-Q(1, 2), Q(1)))
    assert branch_signs2(pole, Q(0), Q(1)) is None
    negative = replace(positive, numerators=((-Q(1),),))
    assert branch_signs2(negative, Q(0), Q(1)) is None


def test_unbounded_certificate_ignores_poisoned_float_ray(monkeypatch):
    import eab.kernel2d.statics as statics
    original = statics.lp.maximize
    def poison(*args, **kwargs):
        result = original(*args, **kwargs)
        if result.status == "unbounded":
            result.ray = [123.0] * len(result.x)
        return result
    monkeypatch.setattr(statics.lp, "maximize", poison)
    result = solve_limit_problem2(_problem([[1, -1]], [2], [0, 1]))
    _verify(result)
    assert result.improving_ray == (Q(1), Q(1))
