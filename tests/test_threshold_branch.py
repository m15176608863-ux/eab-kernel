"""Branch oracles use hand max-of-beams and individual-face root derivatives.

These expectations do not call the production candidate generator. Polynomial
sign examples use explicit lexicographic monomials, and a mixed anchor/load
example has a hand-computed quadratic term invisible to a first-order jet.
"""
from dataclasses import replace
from fractions import Fraction as Q
from functools import lru_cache

import pytest

from eab.adapters.tia2d import g1, g1_morphology, g1_morphology_seed
from eab.kernel2d.assembly import Assembly2, Body2
from eab.kernel2d.branch_field import (constant, add, sub, mul, sign,
                                      polynomial_family, solve_polynomial)
from eab.kernel2d.branch_certificate import _verify_primal, _verify_dual
import eab.kernel2d.branch_certificate as branch_engine
from eab.kernel2d.sensitivity import LimitSeed2, build_limit_seed2, evaluate_sensitivity2
from eab.kernel2d.statics import critical_parameter


def _assembly(bodies):
    return Assembly2(tuple(bodies), tuple((i, j) for i in range(len(bodies))
                                        for j in range(i + 1, len(bodies))), "complete")


@lru_cache(None)
def _critical(tilt=Q(1, 8), orientation="unreversed"):
    return critical_parameter(g1(t=tilt, height=Q(1), orientation=orientation), max_steps=16)


def _seed(problem, tilt, face=None, factors=(Q(1), Q(1))):
    jets = {}
    for contact in problem.contact_set.constraints:
        if face is not None and sorted((contact.a, contact.b)) != [face - 1, face]:
            continue
        body = problem.assembly.bodies[contact.a]
        group = int(body.body_id[:2] == "Q_")
        y_offset = Q(3) if group else Q(0)
        factor = factors[group]
        dp = (factor * contact.tangent[0] / contact.tangent[1] / tilt
              * (contact.point[1] - y_offset - Q(1, 2)), Q(0))
        dt = (factor * contact.tangent[0] / tilt, Q(0))
        jets[contact.label] = dp, dt
    return build_limit_seed2(problem, contact_seeds=jets, parameter="shape")


def _assert_certified(result, right, left):
    assert result.right_derivative == right and result.left_derivative == left
    assert result.differentiability == ("smooth" if right == left else "one_sided")
    assert result.quality == "exact_jet" and result.method == "branch_certificate"
    assert result.reason is None
    for name, slope in (("forward", right), ("reverse", -left)):
        proof = result.branch_certificate[name]
        assert proof["status"] == "certified" and Q(proof["s"]) == slope
        assert proof["lower"] and proof["upper"]["point"] and proof["upper"]["ray"]


def test_g1_unreversed_t2_face2_missing_branch_regression():
    critical = _critical(Q(1, 4))
    result = evaluate_sensitivity2(critical, _seed(critical.threshold_certificate.problem,
                                                  Q(1, 4), face=2))
    _assert_certified(result, Q(1, 2), Q(0))
    branches = result.branch_certificate["forward"]["candidate_branches"]
    singular = [branch for branch in branches if branch.get("singular", False)]
    # Several acquired bases (own probes and the screening probe) may expose
    # the same singular branch; none of them may be hidden and every listed
    # component must carry the exact leading root 1/2 and a tied label.
    assert singular and any([component["index"] for component in branch["components"]] == [12, 14]
                            for branch in singular)
    for branch in singular:
        for component in branch["components"]:
            assert component["leading_epsilon_order"] == 1
            assert tuple(Q(v) for v in component["leading_polynomial"]) == (-Q(1, 2), Q(1))
            assert Q(component["s"]) == Q(1, 2) and component["label"] in result.tied_labels


@pytest.mark.parametrize("face", (1, 2, 3, 4))
def test_g1_one_eighth_each_face_is_one_sided_not_single_basis_smooth(face):
    critical = _critical()
    _assert_certified(evaluate_sensitivity2(critical, _seed(critical.threshold_certificate.problem,
                                                         Q(1, 8), face=face)), Q(1, 2), Q(0))


def test_g1_one_eighth_all_faces_symmetric_smooth_is_preserved():
    critical = _critical()
    _assert_certified(evaluate_sensitivity2(critical, _seed(critical.threshold_certificate.problem,
                                                         Q(1, 8))), Q(1), Q(1))


@lru_cache(None)
def _two_beams(orientation):
    source = g1(t=Q(1, 4), height=Q(1), orientation=orientation)
    bodies = []
    for group, shift in (("P_", (Q(0), Q(0))), ("Q_", (Q(16), Q(3)))):
        for body in source.bodies:
            bodies.append(Body2.from_vertices(group + body.body_id,
                tuple(tuple(point[k] + shift[k] for k in range(2)) for point in body.original_vertices),
                reference_point=tuple(body.reference_point[k] + shift[k] for k in range(2)),
                dof_anchor=tuple(body.dof_anchor[k] + shift[k] for k in range(2)),
                dof_mask=body.dof_mask, boundary_type=body.boundary_type, live=body.live, dead=body.dead))
    return critical_parameter(_assembly(bodies), max_steps=16)


@pytest.mark.parametrize("factors,right,left", [((1, 0), 1, 0), ((0, 1), 1, 0), ((1, 2), 2, 1)])
@pytest.mark.slow
def test_two_open_beams_envelope_directional_slopes(factors, right, left):
    critical = _two_beams("unreversed")
    assert critical.exact_threshold == Q(1, 4) and critical.attained is False
    seed = _seed(critical.threshold_certificate.problem, Q(1, 4), factors=factors)
    _assert_certified(evaluate_sensitivity2(critical, seed), Q(right), Q(left))


@pytest.mark.parametrize("factors,right,left", [((1, 0), 1, 0), ((0, 1), 1, 0), ((1, 2), 2, 1)])
@pytest.mark.slow
def test_two_closed_beams_envelope_directional_slopes(factors, right, left):
    critical = _two_beams("reverse_i1")
    assert critical.exact_threshold == Q(1, 4) and critical.attained is True
    seed = _seed(critical.threshold_certificate.problem, Q(1, 4), factors=factors)
    _assert_certified(evaluate_sensitivity2(critical, seed), Q(right), Q(left))


def test_t1b03_single_point_ray_basis_does_not_replace_neighbourhood_proof():
    shape = g1_morphology(amplitude=Q(1, 2048), tilt=Q(3, 32))
    critical = critical_parameter(shape.assembly, max_steps=32)
    assert critical.attained is True
    # Direct Fraction polynomial evaluation/differentiation is independent of
    # the production continuation classifier. Two vanishing ray coordinates
    # have opposite nonzero first derivatives: this basis is feasible only at
    # the threshold locally, not on either adjacent open interval.
    old, threshold = critical.threshold_proof, critical.exact_threshold
    assert old.upper_interval == (threshold, threshold)
    branch = old.upper_basis
    denominator = sum(v * threshold ** i for i, v in enumerate(branch.determinant))
    assert denominator != 0
    values = tuple(sum(v * threshold ** i for i, v in enumerate(poly)) / denominator
                   for poly in branch.numerators)
    assert all(value >= 0 for value in values)
    assert values[4] == values[5] == 0
    derivatives = tuple(sum(i * poly[i] * threshold ** (i - 1) for i in range(1, len(poly)))
                        / denominator for poly in (branch.numerators[4], branch.numerators[5]))
    assert derivatives[0] < 0 < derivatives[1]
    for parameter, slope in (("amplitude", -Q(2043, 64)), ("tilt", Q(2043, 2048))):
        seed = g1_morphology_seed(critical.threshold_certificate.problem, shape, parameter)
        _assert_certified(evaluate_sensitivity2(critical, seed), slope, slope)


def _upper_boundary():
    bodies = [Body2.from_vertices("moving", ((2, 3), (3, 3), (3, 4), (2, 4)),
               reference_point=(0, 0), dof_anchor=(0, 0), dof_mask=(1, 1, 0), live=(1, -1, 0)),
              Body2.from_vertices("fixed", ((2, 2), (3, 2), (3, 3), (2, 3)),
               reference_point=(0, 0), dof_anchor=(0, 0), dof_mask=(0, 0, 0), boundary_type="FIXED_BODY")]
    return critical_parameter(_assembly(bodies), mu_max=Q(1), max_steps=8)


def test_original_upper_search_domain_excludes_outside_sandwich_but_keeps_inward_side():
    critical = _upper_boundary()
    assert critical.exact_threshold == 1 and critical.attained is True
    assert critical.search_domain["exact_mu_max"] == "1/1"
    assert critical.search_domain["mu_max_binary64"] == "3ff0000000000000"
    seed = build_limit_seed2(critical.threshold_certificate.problem, live_seeds={"moving": (0, 1, 0)})
    result = evaluate_sensitivity2(critical, seed)
    assert result.right_derivative is None and result.left_derivative == 1
    assert result.differentiability == "one_sided"
    assert result.reason == "threshold_search_domain_boundary"
    assert result.branch_certificate["forward"]["status"] == "unresolved"
    assert result.branch_certificate["reverse"]["status"] == "certified"


def test_zero_threshold_zero_candidate_is_conservatively_unresolved():
    critical = critical_parameter(g1(t=Q(0)), max_steps=8)
    seed = build_limit_seed2(critical.threshold_certificate.problem, parameter="zero")
    result = evaluate_sensitivity2(critical, seed)
    assert result.differentiability == "unresolved"
    assert result.reason == "threshold_search_domain_boundary"
    assert result.quality != "exact_jet"
    assert result.left_derivative is None and result.right_derivative is None


def test_threshold_mu_channel_is_invalid_not_a_derivative_of_its_own_threshold():
    critical = _critical()
    seed = build_limit_seed2(critical.threshold_certificate.problem, mu_seed=1)
    result = evaluate_sensitivity2(critical, seed)
    assert result.call_status == "INVALID_INPUT" and result.reason == "threshold_mu_seed_not_allowed"


def test_original_domain_binding_preserves_signed_binary64_zero_and_not_bracket_hi():
    boundary = critical_parameter(g1(t=Q(1, 8)), mu_max=-0.0, max_steps=0)
    assert boundary.search_domain["exact_mu_max"] == "0/1"
    assert boundary.search_domain["mu_max_binary64"] == "8000000000000000"
    interior = _critical()
    assert interior.mu_hi < 1 and interior.search_domain["exact_mu_max"] == "1/1"


def test_first_order_matrix_only_or_tampered_jet_cannot_certify_raw_geometry_path():
    critical = _critical()
    seed = _seed(critical.threshold_certificate.problem, Q(1, 8))
    naked = LimitSeed2(seed.dA, seed.db, seed.dc, seed.parameter)
    result = evaluate_sensitivity2(critical, naked)
    assert result.reason == "threshold_affine_primitives_required" and result.quality != "exact_jet"
    bad = replace(seed, db=tuple(Q(1) for _ in seed.db))
    assert evaluate_sensitivity2(critical, bad).reason == "affine_seed_mismatch"


def test_order_is_epsilon_then_eta_and_all_coefficients_are_retained():
    assert sign({(1, 0): -1, (0, 7): 1}) == 1
    assert sign({(7, 0): -1, (7, 1): 100}) == -1
    assert sign({(19, 0): -1}) == -1  # Truncating to degree 18 must not declare zero.
    assert sign({}) == 0


def test_upper_certificate_checks_both_primal_feasibility_and_improving_ray():
    matrix = [[constant(1), constant(1), constant(0)]]
    # A lower dual certificate by itself cannot prove threshold crossing.
    assert _verify_dual(matrix, [constant(0), constant(0), constant(0)],
                        (constant(1), [constant(0)], {}))
    negative_point = (constant(1), [constant(-1), constant(2), constant(0)], {})
    assert not _verify_primal(matrix, [constant(1)], negative_point)
    wrong_null_ray = (constant(1), [constant(1), constant(0), constant(1)], {})
    assert not _verify_primal(matrix, [constant(0)], wrong_null_ray, 2)
    unnormalized_ray = (constant(1), [constant(0), constant(0), constant(2)], {})
    assert not _verify_primal(matrix, [constant(0)], unnormalized_ray, 2)


def test_late_exact_coefficient_must_not_be_truncated_and_called_zero():
    assert sign({(64, 0): Q(-7, 13), (65, 0): Q(1)}) == -1
    assert sign({(0, 64): Q(1), (1, 0): Q(-1)}) == 1


def test_singular_selected_certificate_is_diagnostic_only_after_no_k_value(monkeypatch):
    critical = _critical()
    seed = _seed(critical.threshold_certificate.problem, Q(1, 8))
    branch = critical.threshold_proof.lower_basis
    duplicate = (branch.basis[0],) * len(branch.basis)
    changed = replace(critical, threshold_proof=replace(critical.threshold_proof,
                                                       lower_basis=replace(branch, basis=duplicate)))
    monkeypatch.setattr(branch_engine, "CANDIDATE_LIMIT", 0)
    result = evaluate_sensitivity2(changed, seed)
    assert result.differentiability == "singular" and result.reason == "critical_basis_singular"
    assert result.left_derivative is None and result.right_derivative is None
    assert result.quality != "exact_jet"


def test_zero_implicit_denominator_is_diagnosed_without_returning_a_slope(monkeypatch):
    critical = _critical()
    seed = _seed(critical.threshold_certificate.problem, Q(1, 8))
    branch, p = critical.threshold_proof.lower_basis, critical.exact_threshold
    # -(mu-p)^3 / det has a true outgoing crossing and zero first derivative.
    determinant = Q(1)
    numerator = (p ** 3, -3 * p * p, 3 * p, -Q(1))
    changed = replace(critical, threshold_proof=replace(critical.threshold_proof,
                    lower_basis=replace(branch, determinant=(determinant,), numerators=(numerator,))))
    monkeypatch.setattr(branch_engine, "CANDIDATE_LIMIT", 0)
    result = evaluate_sensitivity2(changed, seed)
    assert result.differentiability == "singular" and result.reason == "zero_implicit_denominator"
    assert result.left_derivative is None and result.right_derivative is None


def test_valid_k_proof_takes_priority_over_singular_selected_basis_metadata():
    critical = _critical()
    branch = critical.threshold_proof.lower_basis
    changed = replace(critical, threshold_proof=replace(critical.threshold_proof,
                    lower_basis=replace(branch, determinant=(-critical.exact_threshold, Q(1)))))
    seed = _seed(critical.threshold_certificate.problem, Q(1, 8))
    _assert_certified(evaluate_sensitivity2(changed, seed), Q(1), Q(1))


def test_fraction_free_basis_solve_has_exact_full_polynomial_residual():
    e, h = {(1, 0): Q(1)}, {(0, 1): Q(1)}
    matrix = [[add(constant(1), mul(e, h)), e], [h, sub(constant(1), e)]]
    rhs = [add(constant(1), mul(e, e)), sub(h, mul(mul(e, e), e))]
    denominator, values = solve_polynomial(matrix, rhs)
    assert denominator
    for row, b in zip(matrix, rhs):
        residual = {}
        for a, v in zip(row, values):
            residual = add(residual, mul(a, v))
        assert not sub(residual, mul(b, denominator))


def test_full_anchor_load_moment_quadratic_is_not_reconstructed_from_jet():
    critical = _critical()
    problem = critical.threshold_certificate.problem
    name = problem.assembly.bodies[2].body_id
    seed = build_limit_seed2(problem, anchor_seeds={name: (2, 3)}, live_seeds={name: (5, 7, 11)})
    matrix, _, _ = polynomial_family(seed.affine_path, critical.exact_threshold, Q(0), 0, 1)
    moment_row = problem.row_labels.index((name, 2))
    # -(da x dF) = -(2*7 - 3*5) = +1, independent of any first jet.
    assert matrix[moment_row][-1][(2, 0)] == 1


def test_singular_candidate_metadata_retains_multiplicity_and_all_matching_labels(monkeypatch):
    """Explicit polynomial matrices fix the complete leading-root oracle."""
    critical = _critical()
    seed = _seed(critical.threshold_certificate.problem, Q(1, 8))
    epsilon, root = {(1, 0): Q(1)}, {(0, 0): -Q(1, 2), (0, 1): Q(1)}
    zero, one = constant(0), constant(1)
    matrix = [[epsilon, zero, zero, zero],
              [zero, mul(epsilon, root), mul(epsilon, mul(root, root)), one]]
    monkeypatch.setattr(branch_engine, "polynomial_family",
                        lambda path, threshold, slope, side, direction: (matrix, [zero, zero],
                                                                       [zero, zero, zero, one]))
    # Candidate discovery may run out of resources; it must not erase a real
    # label once the same slope is independently certified from another basis.
    monkeypatch.setattr(branch_engine, "_rational_roots", lambda poly, lower, upper: ())
    roots, branch = branch_engine._singular_candidates(seed, Q(1, 8), (0, 1), (0, 3), "dual", 1)
    assert roots == () and branch["singular"] is True
    matching = branch_engine._matching_components(branch, Q(1, 2))
    assert [component["index"] for component in matching] == [1, 2]
    assert [component["leading_epsilon_order"] for component in matching] == [2, 2]
    assert [tuple(Q(v) for v in component["leading_polynomial"]) for component in matching] == [
        (-Q(1, 2), Q(1)), (Q(1, 4), -Q(1), Q(1))]
    assert branch_engine._matching_components(branch, Q(0)) == []


def test_singular_ray_candidate_metadata_never_includes_normalization_alpha(monkeypatch):
    critical = _critical()
    seed = _seed(critical.threshold_certificate.problem, Q(1, 8))
    epsilon, root = {(1, 0): Q(1)}, {(0, 0): -Q(1, 2), (0, 1): Q(1)}
    zero, one = constant(0), constant(1)
    matrix = [[epsilon, sub(zero, mul(epsilon, mul(root, root)))]]
    monkeypatch.setattr(branch_engine, "polynomial_family",
                        lambda path, threshold, slope, side, direction: (matrix, [zero], [zero, one]))
    roots, branch = branch_engine._singular_candidates(seed, Q(1, 8), (0,), (0,), "ray", 1)
    assert roots == (Q(1, 2),)
    matching = branch_engine._matching_components(branch, Q(1, 2))
    assert len(matching) == 1 and matching[0]["index"] == 0
    assert matching[0]["leading_epsilon_order"] == 1
    assert tuple(Q(v) for v in matching[0]["leading_polynomial"]) == (Q(1, 4), -Q(1), Q(1))


def test_original_domain_public_replacement_or_missing_binding_cannot_certify():
    critical = _critical()
    seed = _seed(critical.threshold_certificate.problem, Q(1, 8))
    original = critical.search_domain
    altered = []
    for key, value in (("mu_max_binary64", "4000000000000000"), ("exact_mu_max", "2/1"),
                       ("mu_max", 2.0), ("exact_mu_min", "1/16"), ("mu_max", float("inf"))):
        altered.append(replace(critical, search_domain=dict(original, **{key: value})))
    # All public fields consistently changed to the narrowed bracket still do
    # not match the internally saved original search input.
    narrowed = dict(original, mu_max=critical.mu_hi, exact_mu_max="8193/65536",
                    mu_max_binary64="3fc0008000000000")
    assert Q(critical.mu_hi) == Q(8193, 65536)
    altered.extend((replace(critical, search_domain=narrowed), replace(critical, search_domain=None),
                    replace(critical, search_domain={}), replace(critical, _search_domain_binding=()),
                    replace(critical, _search_domain_binding=None)))
    for changed in altered:
        result = evaluate_sensitivity2(changed, seed)
        assert result.reason == "threshold_branch_certificate_unavailable"
        assert result.differentiability == "unresolved" and result.quality != "exact_jet"
        assert result.right_derivative is None and result.left_derivative is None


def test_threshold_nonzero_mu_seed_is_rejected_before_missing_proof_or_invalid_directions():
    critical = _critical()
    seed = build_limit_seed2(critical.threshold_certificate.problem, mu_seed=1)
    absent = replace(critical, exact_threshold=None, threshold_certificate=None, search_domain=None)
    for source in (critical, absent):
        result = evaluate_sensitivity2(source, seed, positive_direction_valid=False,
                                       negative_direction_valid=False)
        assert result.call_status == "INVALID_INPUT"
        assert result.reason == "threshold_mu_seed_not_allowed"


@pytest.mark.parametrize("channel", ("single_face", "single_vertex"))
def test_zero_threshold_domain_invalid_initial_candidate_still_discovers_inward_branch(channel):
    # Oracle: at the straight beam the single face's first-order tilt is
    # -1/16, giving the two inward roots +1/32. Neither the initial s=0 nor
    # the legacy selected basis proves them; full independent K replay does.
    from eab2_c3l4_asymmetric import seed_channels
    from eab2_c3l4_diff import formal_cases, referee_seed, raw_bodies, exact_wire
    from eab2_branch_verify import verify_certificate
    source = next(formal_cases({"g1_koureas_h0_t0"}))
    critical = critical_parameter(source["model"], max_steps=8)
    assert critical.exact_threshold == 0 and critical.attained is False
    jet = next(jet for name, jet in seed_channels(source) if name == channel)
    problem = critical.threshold_certificate.problem
    result = evaluate_sensitivity2(critical, referee_seed(problem, jet), parameter=jet["parameters"][0])
    _assert_certified(result, Q(1, 32), -Q(1, 32))
    for name in ("forward", "reverse"):
        budget = branch_engine.CANDIDATE_LIMIT * len(branch_engine.PROBE_ETA) * len(branch_engine.PROBE_EXPONENTS)
        assert 0 < result.branch_certificate[name]["attempts"] <= budget
        assert 1 < result.branch_certificate[name]["candidate_count"] <= branch_engine.CANDIDATE_LIMIT
    exported = exact_wire(critical)
    exported["threshold_certificate"]["problem"] = exact_wire(problem)
    assert verify_certificate(raw_bodies(source["model"]), source["contacts"]["constraints"], jet,
                              exact_wire(problem.column_labels), exported, exact_wire(result),
                              mu_max_binary64=source["bases"]["critical"]["mu_max_bits"]) == 2


def test_zero_threshold_true_zero_candidate_keeps_domain_failure_after_actual_probing():
    critical = critical_parameter(g1(t=Q(0)), max_steps=8)
    result = evaluate_sensitivity2(critical, build_limit_seed2(critical.threshold_certificate.problem,
                                                             parameter="zero_after_probes"))
    assert result.reason == "threshold_search_domain_boundary"
    assert result.differentiability == "unresolved" and result.quality == "approximate"
    assert result.right_derivative is result.left_derivative is None
    for name in ("forward", "reverse"):
        proof = result.branch_certificate[name]
        budget = branch_engine.CANDIDATE_LIMIT * len(branch_engine.PROBE_ETA) * len(branch_engine.PROBE_EXPONENTS)
        assert 0 < proof["attempts"] <= budget and proof["s"] is None
        assert proof["status"] == "unresolved" and proof["reason"] == result.reason
        assert proof["lower"] is proof["upper"] is None and proof["candidate_branches"] == []


def test_certified_direction_without_witnesses_is_never_a_value(monkeypatch):
    """A value with no K witnesses must not be emitted (acceptance 2026-10-24).

    The owner's certified output shape is lower + point + ray; a backend that
    reports certified without them has no proof, and the referee must refuse
    the jet rather than trust the status string.
    """
    from eab.kernel2d import branch_certificate, sensitivity
    critical = _critical(Q(1, 4))
    seed = _seed(critical.threshold_certificate.problem, Q(1, 4), face=2)
    monkeypatch.setattr(branch_certificate, "certify_direction",
                        lambda *args, **kwargs: {"status": "certified", "reason": None, "s": "1/2", "lower": None,
                                                 "upper": None, "candidate_count": 1, "attempts": 1,
                                                 "candidate_branches": []})
    result = sensitivity.evaluate_sensitivity2(critical, seed)
    assert result.differentiability == "unresolved" and result.quality == "approximate"
    assert result.right_derivative is None and result.left_derivative is None
    assert result.reason == "internal_certificate_shape"
    assert result.branch_certificate["forward"]["status"] == "unresolved"


def test_rational_roots_repeated_zero_does_not_hide_seven_over_128():
    """Hand factorization v^2(v-7/128): exactly two distinct rational roots."""
    polynomial = (Q(0), Q(0), -Q(7, 128), Q(1))
    for lower, upper in ((Q(-1), Q(1)), (Q(0), Q(1, 8))):
        roots = branch_engine._rational_roots(polynomial, lower, upper)
        assert len(roots) == 2 and set(roots) == {Q(0), Q(7, 128)}


@pytest.mark.parametrize("maximum", (Q(1), Q(1, 4)))
def test_probe_threshold_candidates_uses_original_domain_not_narrowed_mu_hi(monkeypatch, maximum):
    """The caller interval is [0, mu_max], not the final narrow primal bracket."""
    critical = critical_parameter(g1(t=Q(1, 8), orientation="unreversed"), mu_max=maximum, max_steps=8)
    assert Q(critical.mu_hi) < maximum
    seed = _seed(critical.threshold_certificate.problem, Q(1, 8))
    observed = []
    original = branch_engine._unbounded_at

    def recording(A0, A1, b, c, mu):
        observed.append(mu)
        return original(A0, A1, b, c, mu)

    monkeypatch.setattr(branch_engine, "_unbounded_at", recording)
    slopes = branch_engine._probe_threshold_candidates(seed, critical.exact_threshold,
                                                      critical.search_domain, 1)
    assert slopes == [Q(1)]
    assert observed[0] == maximum and observed[1] == 0
    assert all(Q(0) <= value <= maximum for value in observed)
    assert any(value > Q(critical.mu_hi) for value in observed)


def test_reused_basis_positive_in_k_but_negative_at_probe_is_skipped(monkeypatch):
    """Independent polynomial 1-32 epsilon: positive in K, -1 at epsilon=1/16."""
    matrix, rhs = [[constant(Q(1))]], [{(0, 0): Q(1), (1, 0): -Q(32)}]
    good_probe, bad_probe = dict(epsilon="1/64", eta="1/4"), dict(epsilon="1/16", eta="1/4")
    args = matrix, rhs, (0,), (0,), "point", 0, ("x",)
    good = branch_engine._vector(*args, good_probe)
    assert good is not None and _verify_primal(matrix, rhs, good)
    assert branch_engine._value_at(good[1][0], Q(1, 64), Q(1, 4)) == Q(1, 2)
    assert branch_engine._value_at(good[1][0], Q(1, 16), Q(1, 4)) == -1
    assert branch_engine._vector(*args, bad_probe) is None
    # Internal fault injection proves the fixture reaches the guard: without
    # it, the exact same reused basis is accepted by the separate K check.
    monkeypatch.setattr(branch_engine, "_probe_consistent", lambda *unused: True)
    unchecked = branch_engine._vector(*args, bad_probe)
    assert unchecked is not None and _verify_primal(matrix, rhs, unchecked)


def test_exhausted_candidates_stay_unresolved_and_probe_threshold_route_runs(monkeypatch):
    """When no ordered-field dual witness exists the direction is unresolved.

    The probe-threshold candidate route must have been tried (it is the last
    resort on an interior threshold) and must never turn into a value.
    """
    from eab.kernel2d import branch_certificate, sensitivity
    critical = _critical(Q(1, 4))
    seed = _seed(critical.threshold_certificate.problem, Q(1, 4), face=2)
    calls = []
    original = branch_certificate._probe_threshold_candidates

    def counted(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)
    monkeypatch.setattr(branch_certificate, "_verify_dual", lambda *args, **kwargs: False)
    monkeypatch.setattr(branch_certificate, "_probe_threshold_candidates", counted)
    result = sensitivity.evaluate_sensitivity2(critical, seed)
    assert result.differentiability == "unresolved" and result.quality == "approximate"
    assert result.right_derivative is None and result.left_derivative is None
    assert result.reason == "threshold_branch_certificate_unavailable"
    assert calls, "the probe-threshold candidate route was not exercised"
    for direction in ("forward", "reverse"):
        branch = result.branch_certificate[direction]
        assert branch["status"] == "unresolved" and branch["s"] is None and not branch["candidate_branches"]

