"""C3-L3 checker unit gates; mandatory DLL differential is a separate CLI.

The primary arithmetic oracle reconstructs wrenches from raw polygon edges.
Malformed certificate tests exercise this verifier, not production mutations;
the separate source-mutation gate is required for claims about C++ guard teeth.
"""
import copy
from fractions import Fraction as Q
from pathlib import Path
import random
import sys

import pytest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src/eab").is_dir())
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(ROOT / "tools"))
from eab2_c3l3_diff import (bits, branch_signs, checked_problem, compare, endpoint,
    exact_wire, formal_query as formal, implication_box, metamorphic_cases, p_div, p_eval,
    rebuilt_problem, regression_cases, reparameterize_reference, root_count,
    semantic, t1b_cases, verify_branch, verify_critical, verify_limit,
    wide_cases, wide_enhancement_targets, wide_g1_specs)

@pytest.mark.parametrize("name,value", [("regression_d_flush_mu0", Q(0)),
                                       ("regression_d_flush_mu025", Q(1, 2))])
def test_c3l3_original_geometry_reconstructs_flush_regression_capacity(name, value):
    model, contacts, query, result = formal(name)
    problem = verify_limit(model, contacts, model.mu, result, query["problem"])
    assert Q(result["exact_value"]) == value
    assert len(problem["b"]) == 10 and len(problem["c"]) == 17
    assert not compare("limit", model, contacts, result, result, query)


@pytest.mark.parametrize("field", ["exact_x", "exact_y"])
def test_c3l3_original_geometry_rejects_false_primal_dual_witness(field):
    model, contacts, query, result = formal("regression_d_flush_mu025")
    bad = copy.deepcopy(result)
    bad[field] = ["0/1"] * len(bad[field])
    with pytest.raises(ValueError):
        verify_limit(model, contacts, model.mu, bad, query["problem"])


def test_c3l3_exported_geometry_and_matrices_are_not_trusted():
    model, contacts, query, result = formal("regression_d_flush_mu025")
    corrupted = copy.deepcopy(contacts)
    corrupted["constraints"][0]["tangent"][1] = "42/1"
    with pytest.raises(ValueError, match="tangent"):
        rebuilt_problem(model, corrupted, model.mu)
    problem = copy.deepcopy(query["problem"])
    problem["A"][0][0] = "42/1"
    with pytest.raises(ValueError, match="original geometry problem mismatch"):
        checked_problem(model, contacts, model.mu, problem)


def test_c3l3_extra_cpp_mechanism_attachment_is_checked_not_blindly_ignored():
    model, contacts, query, result = formal("regression_d_flush_mu025")
    actual = copy.deepcopy(result)
    actual["mechanism"] = actual["exact_y"]
    assert not compare("limit", model, contacts, result, actual, query)
    actual["mechanism"] = ["0/1"] * len(actual["exact_y"])
    with pytest.raises(ValueError, match="mechanism attachment"):
        compare("limit", model, contacts, result, actual, query)


def test_c3l3_farkas_from_raw_geometry_requires_normalized_separation():
    model, contacts, query, result = formal("coverage_farkas_free_dead")
    assert result["mathematical_status"] == "INFEASIBLE"
    verify_limit(model, contacts, model.mu, result, query["problem"])
    bad = copy.deepcopy(result)
    bad["farkas"] = ["0/1"] * len(bad["farkas"])
    with pytest.raises(ValueError, match="Farkas normalization"):
        verify_limit(model, contacts, model.mu, bad)


def test_c3l3_unbounded_requires_both_point_and_alpha_one_ray():
    model, contacts, _, critical = formal("g1_koureas_h0_t0", "critical")
    result, mu = critical["upper_certificate"], endpoint(critical, "mu_hi")
    assert result["mathematical_status"] == "UNBOUNDED"
    verify_limit(model, contacts, mu, result)
    bad = copy.deepcopy(result)
    bad["improving_ray"][-1] = "0/1"
    with pytest.raises(ValueError):
        verify_limit(model, contacts, mu, bad)
    bad = copy.deepcopy(result)
    bad["feasible_point"] = None
    with pytest.raises(TypeError):
        verify_limit(model, contacts, mu, bad)


def test_c3l3_unresolved_geometry_is_not_zero_capacity():
    model, contacts, _, result = formal("regression_b_bare_vv")
    assert result["mathematical_status"] == "MECHANICAL_UNRESOLVED"
    verify_limit(model, contacts, model.mu, result)
    bad = copy.deepcopy(result)
    bad["exact_value"] = "0/1"
    with pytest.raises(ValueError, match="unresolved is not zero"):
        verify_limit(model, contacts, model.mu, bad)


def test_c3l3_exact_open_threshold_and_binary64_fields_are_independent():
    model, contacts, _, result = formal("g1_koureas_h0_t0", "critical")
    verify_critical(model, contacts, result)
    assert result["exact_threshold"] == "0/1" and result["attained"] is False
    assert result["reason"] == result["bisection_termination"] == "iteration_limit"
    assert result["threshold_proof_reason"] == "exact_basis_continuation"
    bad = copy.deepcopy(result)
    bad["attained"] = True
    with pytest.raises(ValueError, match="openness/certificate"):
        verify_critical(model, contacts, bad)
    bad = copy.deepcopy(result)
    bad["mu_hi"] = "1/3"
    with pytest.raises(ValueError, match="bits/rational"):
        verify_critical(model, contacts, bad)


def test_c3l3_polynomial_identity_rejects_sample_only_agreement():
    model, contacts, _, result = formal("g1_koureas_h0_t0", "critical")
    branch = copy.deepcopy(result["critical_polynomials"][0])
    verify_branch(model, contacts, branch)
    sample = Q(branch["sample_parameter"])
    polynomial = [Q(v) for v in branch["numerators"][0]]
    while len(polynomial) < 2:
        polynomial.append(Q(0))
    polynomial[0] -= sample
    polynomial[1] += 1
    branch["numerators"][0] = exact_wire(polynomial)
    assert p_eval(polynomial, sample) / p_eval(tuple(Q(x) for x in branch["determinant"]), sample) == Q(branch["sample_values"][0])
    with pytest.raises(ValueError, match="Cramer polynomial identity"):
        verify_branch(model, contacts, branch)


def test_c3l3_bracket_only_result_cannot_drop_its_polynomial_list():
    model, contacts, _, result = formal("g1_koureas_h0_t0", "critical")
    # Project a valid certificate to bracket-only reporting. This constructs
    # a null-threshold wire case; it does not claim that the root is irrational.
    expected = copy.deepcopy(result)
    for field in ("exact_threshold", "attained", "threshold_certificate", "threshold_proof", "threshold_proof_reason"):
        expected[field] = None
    verify_critical(model, contacts, expected)
    bad = copy.deepcopy(expected)
    bad["critical_polynomials"] = []
    assert compare("critical", model, contacts, expected, bad)
    del bad["critical_polynomials"]
    with pytest.raises(ValueError, match="polynomial list is required"):
        compare("critical", model, contacts, expected, bad)


def test_c3l3_branch_sample_is_bound_to_the_corresponding_bracket_endpoint():
    model, contacts, _, result = formal("g1_koureas_h0_t0", "critical")
    bad = copy.deepcopy(result)
    branch = bad["critical_polynomials"][0]
    sample = 2 * Q(branch["sample_parameter"])
    branch["sample_parameter"] = exact_wire(sample)
    denominator = p_eval(tuple(Q(v) for v in branch["determinant"]), sample)
    branch["sample_values"] = exact_wire(tuple(p_eval(tuple(Q(v) for v in p), sample) / denominator
                                               for p in branch["numerators"]))
    verify_branch(model, contacts, branch)
    with pytest.raises(ValueError, match="sample must equal its certified endpoint"):
        verify_critical(model, contacts, bad)


def test_c3l3_sturm_counts_roots_and_removes_only_endpoint_factors():
    assert root_count((Q(-2), Q(0), Q(1)), Q(1), Q(2)) == 1
    assert root_count((Q(-2), Q(0), Q(1)), Q(2), Q(3)) == 0
    assert p_div((Q(0), Q(-1), Q(1)), (Q(0), Q(1))) == ((Q(-1), Q(1)), (Q(0),))
    good = dict(determinant=["0/1", "1/1"], numerators=[["0/1", "1/1"]])
    assert branch_signs(good, Q(0), Q(1)) == [["denominator", [1, 0], "1/2"], [0, [1, 0], "1/1"]]
    pole = dict(determinant=["-1/2", "1/1"], numerators=[["1/1"]])
    assert branch_signs(pole, Q(0), Q(1)) is None
    negative = dict(determinant=["1/1"], numerators=[["-1/1"]])
    assert branch_signs(negative, Q(0), Q(1)) is None


@pytest.mark.parametrize("value", [Q(1, 3), Q(1, 2**1075), Q(2**1024)])
def test_c3l3_transport_rejects_inexact_binary64(value):
    with pytest.raises((ValueError, OverflowError)):
        bits(value)


def test_c3l3_reference_shift_preserves_actual_equilibrium_columns():
    from eab.adapters.tia2d import g5
    from eab.kernel2d.contacts import assemble_contact_set2
    model = g5(n=3, height=1, pressure=1, width=1, mu=Q(2), dof_mask=(1, 0, 1))
    shifted = reparameterize_reference(model, (Q(100000), Q(-1000)))
    left = rebuilt_problem(model, exact_wire(assemble_contact_set2(model)), Q(2))
    right = rebuilt_problem(shifted, exact_wire(assemble_contact_set2(shifted)), Q(2))
    assert (left["A"], left["b"], left["c"]) == (right["A"], right["b"], right["c"])
    assert model.bodies[-1].dof_anchor == shifted.bodies[-1].dof_anchor


def test_c3l3_actual_transformed_geometry_obeys_exact_translation_norm_schedule():
    from eab.adapters.tia2d import g1
    base = g1(t=Q(3, 32), height=Q(1, 16), mu=Q(1, 4))
    generator = random.Random(6033)
    rotations = [(Q(1), Q(0), 1)]
    for _ in range(3):
        m = generator.randint(3, 11)
        n = generator.randint(1, m - 1)
        denominator = m*m + n*n
        rotations.append((Q(m*m - n*n, denominator), Q(2*m*n, denominator), denominator))
    seen = set()
    for name, _, model, _, _ in metamorphic_cases():
        if not name.startswith("meta/g1/"):
            continue
        _, _, index, distance = name.split("/")
        distance = Q(distance)
        cosine, sine, denominator = rotations[int(index)]
        unit = {Q(0): Q(1), Q(1000): Q(8), Q(100000): Q(1, 1024)}[distance]
        source = base.bodies[0].original_vertices[0]
        target = model.bodies[0].original_vertices[0]
        rotated = (cosine * source[0] - sine * source[1], sine * source[0] + cosine * source[1])
        offset = tuple(target[i] - unit * denominator * rotated[i] for i in range(2))
        assert offset == (Q(3, 5) * distance, Q(4, 5) * distance)
        assert sum(v*v for v in offset) == distance*distance
        assert all(isinstance(bits(x), int) for b in model.bodies for p in b.vertices for x in p)
        seen.add((int(index), distance))
    assert seen == {(i, Q(t)) for i in range(4) for t in (0, 1000, 100000)}


def test_c3l3_regressions_include_two_released_plate_counterexamples_and_g1_orientations():
    cases = list(regression_cases())
    plates = [queries[0][1]["expected_value"] for _, family, _, _, queries in cases if family == "plate"]
    assert plates == ["2/3", "4/3"]
    assert sum(family == "closed_g1" for _, family, _, _, _ in cases) == 9


def test_c3l3_nonunique_coordinates_are_semantic_but_status_is_not():
    left = dict(exact_x=["0/1", "1/1"], exact_y=["1/1"], basis=[0], exact_value="1/1", mathematical_status="OPTIMAL")
    right = dict(exact_x=["1/1", "0/1"], exact_y=["2/1"], basis=[1], exact_value="1/1", mathematical_status="OPTIMAL")
    assert semantic(left) == semantic(right)
    right["mathematical_status"] = "UNBOUNDED"
    assert semantic(left) != semantic(right)


@pytest.mark.parametrize("proved_side", ["python", "cpp"])
def test_c3l3_nonunique_threshold_enrichment_requires_independent_proof(proved_side):
    model, contacts, _, proved = formal("coverage_resolution_bracket", "critical")
    conservative = copy.deepcopy(proved)
    for field in ("exact_threshold", "attained", "threshold_certificate", "threshold_proof", "threshold_proof_reason"):
        conservative[field] = None
    left, right = (proved, conservative) if proved_side == "python" else (conservative, proved)
    dispositions = []
    assert not compare("critical", model, contacts, left, right, dispositions=dispositions)
    assert len(dispositions) == 1 and dispositions[0]["proved_side"] == proved_side
    assert dispositions[0]["threshold_certificate_contract_verified"] is True
    assert dispositions[0]["exact_threshold"] == "15/128"
    assert dispositions[0]["normalized_fields"] == ["exact_threshold", "attained", "threshold_certificate", "threshold_proof_reason"]


def test_c3l3_threshold_enrichment_does_not_ignore_unrelated_fields():
    model, contacts, _, proved = formal("coverage_resolution_bracket", "critical")
    conservative = copy.deepcopy(proved)
    for field in ("exact_threshold", "attained", "threshold_certificate", "threshold_proof", "threshold_proof_reason"):
        conservative[field] = None
    changed = copy.deepcopy(proved)
    changed["reason"] = "not_the_actual_bisection_termination"
    assert compare("critical", model, contacts, conservative, changed)
    changed = copy.deepcopy(proved)
    changed["critical_polynomials"] = []
    assert compare("critical", model, contacts, conservative, changed)
    changed = copy.deepcopy(proved)
    changed["mu_hi"] = "1/3"
    with pytest.raises(ValueError):
        compare("critical", model, contacts, conservative, changed)


@pytest.mark.parametrize("name,side,message", [
    ("coverage_resolution_bracket", "lower", "closed threshold needs bounded continuation"),
    ("g1_koureas_h0_t0", "upper", "open threshold needs feasible point and improving continuation"),
])
def test_c3l3_threshold_enrichment_rejects_missing_required_continuation(name, side, message):
    model, contacts, _, proved = formal(name, "critical")
    bad = copy.deepcopy(proved)
    bad["threshold_proof"][side + "_basis"] = None
    bad["threshold_proof"][side + "_signs"] = None
    conservative = copy.deepcopy(proved)
    for field in ("exact_threshold", "attained", "threshold_certificate", "threshold_proof", "threshold_proof_reason"):
        conservative[field] = None
    dispositions = []
    with pytest.raises(ValueError, match=message):
        compare("critical", model, contacts, conservative, bad, dispositions=dispositions)
    assert dispositions == []


@pytest.mark.parametrize("bad_field", ["threshold_proof_reason", "proof_reason", "null_reason"])
def test_c3l3_threshold_enrichment_cannot_waive_false_proof_reason(bad_field):
    model, contacts, _, proved = formal("coverage_resolution_bracket", "critical")
    conservative = copy.deepcopy(proved)
    for field in ("exact_threshold", "attained", "threshold_certificate", "threshold_proof", "threshold_proof_reason"):
        conservative[field] = None
    bad = copy.deepcopy(proved)
    if bad_field == "proof_reason":
        bad["threshold_proof"]["reason"] = "not_a_continuation_proof"
    elif bad_field == "null_reason":
        conservative["threshold_proof_reason"] = "not_a_null_proof"
    else:
        bad["threshold_proof_reason"] = "not_a_continuation_proof"
    with pytest.raises(ValueError, match="continuation reason|uncertified threshold"):
        compare("critical", model, contacts, conservative, bad)


def test_c3l3_two_nonnull_thresholds_and_openness_remain_strict():
    model, contacts, _, proved = formal("coverage_resolution_bracket", "critical")
    for field, wrong in (("exact_threshold", "1/8"), ("attained", False)):
        bad = copy.deepcopy(proved)
        bad[field] = wrong
        assert semantic(proved) != semantic(bad)
        with pytest.raises(ValueError):
            compare("critical", model, contacts, proved, bad)


@pytest.mark.parametrize("field,value", [
    ("call_status", "INVALID_INPUT"), ("display_status", "INVALID_DISPLAY"),
    ("validity_conditions", ["invented_condition"]), ("sensitivity_model", "invented_model"),
    ("reason", "invented_reason"), ("exact_x", ["0/1"]), ("exact_y", ["123/1"]),
    ("farkas", ["0/1"]), ("invented_field", None),
])
def test_c3l3_threshold_enrichment_cannot_hide_certificate_contract_corruption(field, value):
    model, contacts, _, proved = formal("coverage_resolution_bracket", "critical")
    conservative = copy.deepcopy(proved)
    for key in ("exact_threshold", "attained", "threshold_certificate", "threshold_proof", "threshold_proof_reason"):
        conservative[key] = None
    bad = copy.deepcopy(proved)
    bad["threshold_certificate"][field] = value
    dispositions = []
    with pytest.raises(ValueError, match="threshold certificate contract"):
        compare("critical", model, contacts, conservative, bad, dispositions=dispositions)
    assert dispositions == []


def test_c3l3_open_threshold_enrichment_cannot_carry_an_unbounded_payload():
    model, contacts, _, proved = formal("g1_koureas_h0_t0", "critical")
    conservative = copy.deepcopy(proved)
    for field in ("exact_threshold", "attained", "threshold_certificate", "threshold_proof", "threshold_proof_reason"):
        conservative[field] = None
    bad = copy.deepcopy(proved)
    bad["threshold_certificate"]["improving_ray"] = ["0/1"]
    with pytest.raises(ValueError, match="threshold certificate contract: exclusive payload"):
        compare("critical", model, contacts, conservative, bad)


@pytest.mark.parametrize("field,value", [("threshold_proof_reason", "invented_reason"), ("threshold_proof", {})])
def test_c3l3_direct_closed_zero_cannot_invent_a_continuation_proof(field, value):
    model, contacts, _, proved = formal("g1_koureas_h0_t1", "critical")
    assert proved["exact_threshold"] == "0/1" and proved["attained"] is True
    verify_critical(model, contacts, proved)
    conservative = copy.deepcopy(proved)
    for key in ("exact_threshold", "attained", "threshold_certificate", "threshold_proof", "threshold_proof_reason"):
        conservative[key] = None
    bad = copy.deepcopy(proved)
    bad[field] = value
    with pytest.raises(ValueError, match="direct closed zero must not invent"):
        compare("critical", model, contacts, conservative, bad)


def test_c3l3_wide_grid_preserves_steps_maxima_and_twenty_review_instances():
    specs = list(wide_g1_specs())
    assert len(specs) == len(set(specs)) == 2310
    assert {row[0] for row in specs} == {"koureas", "unreversed", "reverse_i1"}
    assert {row[3] for row in specs} == {Q(1, 8), Q(1, 4), Q(3, 8), Q(1, 2), Q(3, 4), Q(1), Q(3, 2), Q(2), Q(3), Q(4)}
    assert {row[4] for row in specs} == set(range(7))
    targets = wide_enhancement_targets()
    assert len(targets) == len(set(targets.values())) == 20
    assert set(targets) <= set(specs)
    assert ("koureas", Q(3, 32), Q(1, 16), Q(3, 4), 4) in specs
    assert ("koureas", Q(3, 8), Q(1, 4), Q(3, 8), 1) in specs


def test_c3l3_wide_generated_queries_include_named_major_farkas_and_quadratic_controls():
    # Generator-only coverage: no solver calls and no 2310-query pytest replay.
    counts, named, enhancement_ids = {}, {}, set()
    for _, family, model, _, queries in wide_cases():
        counts[family] = counts.get(family, 0) + len(queries)
        assert all(isinstance(bits(v), int) for b in model.bodies for p in b.vertices for v in p)
        for _, query, expected in queries:
            assert expected is None
            if "named_regression" in query:
                named[query["named_regression"]] = query["reference_threshold"]
                assert query["expected_threshold"] is None
            if "acceptance_enhancement_id" in query:
                enhancement_ids.add(query["acceptance_enhancement_id"])
            if family == "wide_incline":
                assert query["expected_lower_status"] == "INFEASIBLE"
                assert query["reference_open_threshold"] in ("0/1", "1/13")
            if family == "wide_quadratic":
                assert query["expected_root_polynomial"] == ["-1/1", "2/1", "1/1"]
    assert counts == {"wide_g1": 2310, "wide_incline": 16, "wide_quadratic": 6}
    assert named == {"major_closed_lower_continuation_2039_over_32768": "2039/32768",
                     "major_closed_lower_continuation_119_over_512": "119/512"}
    assert enhancement_ids == set(wide_enhancement_targets().values())


def test_c3l3_thickness_inventory_is_binary64_exact_and_distinguishes_source_duplicates():
    from eab2_c3l3_thickness import input_domain_failures, thickness_cases, thickness_inventory
    cases = list(thickness_cases())
    inventory = thickness_inventory()
    assert len(cases) == 25 and inventory["binary64_samples"] == 7 and inventory["thick_controls"] == 18
    assert len(inventory["excluded"]) == inventory["outside_binary64_domain"] == 32
    assert inventory["unique_models"] == 19 and inventory["duplicate_source_models"] == 6
    counts, fingerprints, nonzero = {}, set(), []
    for _, model, queries in cases:
        assert input_domain_failures(model) == []
        for query in queries:
            counts[query["kind"]] = counts.get(query["kind"], 0) + 1
            fingerprints.add(query["thickness_source"]["input_sha256"])
            if query["kind"] == "critical" and query["expected_threshold"] != "0/1":
                nonzero.append(query["expected_threshold"])
    assert counts == {"limit": 75, "critical": 25}
    assert len(fingerprints) == 19 and nonzero == ["253/16384"]
