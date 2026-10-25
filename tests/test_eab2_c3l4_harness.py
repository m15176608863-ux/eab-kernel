"""C3-L4 independent checker gates, not production source-mutation claims.

The primary arithmetic oracle uses original vertices, Fraction elimination,
LP certificate equations and Taylor polynomial signs. It does not share the
production geometry seed helper, LP solver, or sensitivity implementation.
"""
import copy
import ctypes as C
from collections import Counter
from fractions import Fraction as Q
from pathlib import Path
import sys

import pytest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src/eab").is_dir())
sys.path.insert(0, str(ROOT / "tools"))
from eab2_c3l3_diff import compare as compare_l3, require_python_proof_floor
from eab2_c3l4_diff import (T1B, attached_base, check_frozen_implicit_query, compare_sensitivity, directional_values,
    exact_wire, expected_channel, formal_cases, read_json, rebuilt_seed, target_kind,
    t1b_cases, unit_mu_jet, verify_batch, verify_implicit, verify_limit_sensitivity, verify_sensitivity)
from eab2_c3l4_abi import C3L4Info, SensitivityInput, pack_request
from eab2_c3l3_thickness import input_fingerprint, thickness_inventory


# Dataset loading/selection/copying below is test-driver setup, not a
# separately claimed exact-construction helper. Numerical checks remain
# in the unchanged independently implemented differential verifier.
def test_c3l4_formal_inventory_has_every_bound_sensitivity_query():
    cases = list(formal_cases())
    assert len(cases) == 114
    queries = [query for case in cases for _, query in case["queries"]]
    assert len(queries) == 280
    assert Counter(target_kind(q) for q in queries) == {"limit": 160, "critical": 120}
    assert Counter(q["result"]["differentiability"] for q in queries) == {
        "smooth": 73, "one_sided": 2, "singular": 36, "unresolved": 169}


@pytest.mark.parametrize("name", ["g5_n3_mu0", "g5_n3_mu1", "g5_n3_mu2", "g5_n3_mu3",
    "g1_unreversed_t1", "g1_slender", "coverage_signed_zero_cw_frames", "coverage_redundant_vv_mu2", "coverage_overlap"])
def test_c3l4_original_geometry_seeds_and_independent_certificates(name):
    case = next(formal_cases({name}))
    for _, query in case["queries"]:
        base = attached_base(case["bases"][target_kind(query)])
        delta, floor = compare_sensitivity(case, base, query, expected_channel(query))
        assert delta == [] and floor["exceptions"] == []


@pytest.mark.parametrize("field", ["vertices", "dead", "live", "dof_anchor", "mu"])
def test_c3l4_seed_channel_shapes_are_not_silently_truncated(field):
    case = next(formal_cases({'g5_n3_mu1'}))
    query = next(q for _, q in case["queries"] if q["result"]["parameter"] == 'mu' and target_kind(q) == 'limit')
    base = attached_base(case["bases"]['limit'])
    channel = copy.deepcopy(expected_channel(query))
    jet = copy.deepcopy(query["geometry_seed"])
    jet[field] = []
    with pytest.raises(ValueError, match="dimensions"):
        rebuilt_seed(case["model"], case["contacts"], Q(1, 4), jet)


def test_c3l4_shared_original_vertex_seed_is_enforced():
    case = next(formal_cases({'g5_n3_mu1'}))
    query = next(q for _, q in case["queries"] if q["result"]["parameter"] == 'mu' and target_kind(q) == 'limit')
    base = attached_base(case["bases"]['limit'])
    channel = copy.deepcopy(expected_channel(query))
    jet = copy.deepcopy(query["geometry_seed"])
    # First body's right-bottom vertex is shared with its neighbor.
    jet["vertices"][0][1][0] = "1/1"
    with pytest.raises(ValueError, match="shared vertex"):
        rebuilt_seed(case["model"], case["contacts"], Q(1, 4), jet)


def test_c3l4_live_seed_enters_actual_A_not_only_rhs():
    case = next(formal_cases({'g5_n3_mu1'}))
    query = next(q for _, q in case["queries"] if q["result"]["parameter"] == 'mu' and target_kind(q) == 'limit')
    base = attached_base(case["bases"]['limit'])
    channel = copy.deepcopy(expected_channel(query))
    jet = copy.deepcopy(query["geometry_seed"])
    jet["mu"][0] = "0/1"
    center = next(i for i, name in enumerate(jet["body_ids"]) if name == case["model"].bodies[2].body_id)
    jet["live"][0][center][1] = "3/2"
    seed = rebuilt_seed(case["model"], case["contacts"], Q(1, 4), jet)
    assert all(v == 0 for v in seed["db"])
    assert Q(3, 2) in [row[-1] for row in seed["dA"]]
    assert any(row[-1] != 0 for row in seed["dA"])


@pytest.mark.parametrize("field", ["dA", "db", "dc"])
def test_c3l4_cpp_derived_seed_is_checked_against_original_geometry(field):
    case = next(formal_cases({'g5_n3_mu1'}))
    query = next(q for _, q in case["queries"] if q["result"]["parameter"] == 'mu' and target_kind(q) == 'limit')
    base = attached_base(case["bases"]['limit'])
    channel = copy.deepcopy(expected_channel(query))
    if field == "dA":
        channel["derived_seed"][field][0][0] = "123/1"
    else:
        channel["derived_seed"][field][0] = "123/1"
    with pytest.raises(ValueError, match="geometry-derived seed"):
        verify_sensitivity(case["model"], case["contacts"], base, query, channel)


@pytest.mark.parametrize("field", ["forward_certificate", "reverse_certificate"])
def test_c3l4_mills_nonunique_witness_still_requires_exact_optimality(field):
    case = next(formal_cases({'g5_n3_mu1'}))
    query = next(q for _, q in case["queries"] if q["result"]["parameter"] == 'mu' and target_kind(q) == 'limit')
    base = attached_base(case["bases"]['limit'])
    channel = copy.deepcopy(expected_channel(query))
    channel["result"][field][0][0] = "999/1"
    with pytest.raises(ValueError):
        verify_sensitivity(case["model"], case["contacts"], base, query, channel)


def test_c3l4_reverse_lp_value_is_not_the_left_derivative():
    case = next(formal_cases({'g5_n3_mu2'}))
    query = next(q for _, q in case["queries"] if q["result"]["parameter"] == 'mu' and target_kind(q) == 'limit')
    base = attached_base(case["bases"]['limit'])
    channel = copy.deepcopy(expected_channel(query))
    channel["result"]["left_derivative"] = "-2/1"
    with pytest.raises(ValueError):
        verify_sensitivity(case["model"], case["contacts"], base, query, channel)
    assert query["directional_values"] == {"D_plus": "0/1", "D_minus": "-2/1"}


def test_c3l4_recession_must_have_nonzero_verified_ray_and_no_slope():
    case = next(formal_cases({'g5_n3_mu0'}))
    query = next(q for _, q in case["queries"] if q["result"]["parameter"] == 'mu' and target_kind(q) == 'limit')
    base = attached_base(case["bases"]['limit'])
    channel = copy.deepcopy(expected_channel(query))
    for field in ("primal_recession_ray", "dual_recession_ray"):
        if channel["result"][field] is not None:
            channel["result"][field] = ["0/1"] * len(channel["result"][field])
    with pytest.raises(ValueError, match="recession witness"):
        verify_sensitivity(case["model"], case["contacts"], base, query, channel)
    channel = copy.deepcopy(expected_channel(query))
    channel["result"]["right_derivative"] = "2/1"
    with pytest.raises(ValueError, match="must not certify"):
        verify_sensitivity(case["model"], case["contacts"], base, query, channel)


@pytest.mark.parametrize("parameter,target_value", [("t", "15/16"), ("h", "-17/32")])
def test_c3l4_closed_threshold_implicit_derivative_uses_all_crossings(parameter, target_value):
    case = next(formal_cases({'g1_slender'}))
    query = next(q for _, q in case["queries"] if q["result"]["parameter"] == parameter and target_kind(q) == 'critical')
    base = attached_base(case["bases"]['critical'])
    channel = copy.deepcopy(expected_channel(query))
    assert channel["result"]["right_derivative"] == target_value
    verify_sensitivity(case["model"], case["contacts"], base, query, channel)
    channel["result"]["implicit_components"][0][3] = "987/1"
    with pytest.raises(ValueError, match="implicit components"):
        verify_sensitivity(case["model"], case["contacts"], base, query, channel)


def test_c3l4_open_threshold_uses_mechanism_and_preserves_tied_labels():
    case = next(formal_cases({'g1_unreversed_t1'}))
    query = next(q for _, q in case["queries"] if q["result"]["parameter"] == 't' and target_kind(q) == 'critical')
    base = attached_base(case["bases"]['critical'])
    channel = copy.deepcopy(expected_channel(query))
    assert base["attained"] is False and channel["result"]["selected_piece"][0] == "mechanism"
    channel["result"]["tied_labels"].pop()
    with pytest.raises(ValueError, match="tied labels"):
        verify_sensitivity(case["model"], case["contacts"], base, query, channel)


@pytest.mark.parametrize("condition", ["L1接触骨架不变", "true_vv_excluded_from_statics"])
def test_c3l4_statics_and_skeleton_validity_cannot_be_dropped(condition):
    case = next(formal_cases({'coverage_redundant_vv_mu2'}))
    query = next(q for _, q in case["queries"] if q["result"]["parameter"] == 'mu' and target_kind(q) == 'limit')
    base = attached_base(case["bases"]['limit'])
    channel = copy.deepcopy(expected_channel(query))
    assert condition in channel["result"]["validity_conditions"]
    channel["result"]["validity_conditions"].remove(condition)
    with pytest.raises(ValueError, match="validity conditions"):
        verify_sensitivity(case["model"], case["contacts"], base, query, channel)


def test_c3l4_fixed_basis_uses_unscaled_maximize_dual():
    p = dict(A=((Q(2), Q(1)),), b=(Q(6),), c=(Q(4), Q(1)))
    seed = dict(dA=((Q(1), Q(2)),), db=(Q(5),), dc=(Q(5), Q(7)))
    base = dict(mathematical_status="OPTIMAL", exact_x=["3/1", "0/1"], exact_y=["2/1"], basis=[0])
    query = dict(direction_domain=dict(positive=True, negative=True))
    result = dict(method="stable_basis", differentiability="smooth", directional_derivative="19/1",
                  right_derivative="19/1", left_derivative="19/1")
    verify_limit_sensitivity(p, seed, base, query, result)
    result.update(directional_derivative="17/1", right_derivative="17/1", left_derivative="17/1")
    with pytest.raises(ValueError, match="unscaled dual"):
        verify_limit_sensitivity(p, seed, base, query, result)


def test_c3l4_fixed_basis_is_rejected_for_actual_degenerate_optimum():
    case = next(formal_cases({'g5_n3_mu1'}))
    query = next(q for _, q in case["queries"] if q["result"]["parameter"] == 'mu' and target_kind(q) == 'limit')
    base = attached_base(case["bases"]['limit'])
    channel = copy.deepcopy(expected_channel(query))
    channel["result"].update(method="stable_basis", forward_certificate=None, reverse_certificate=None,
        selected_piece=base["basis"], piece_jacobians=[[base["basis"], "2/1"]])
    with pytest.raises(ValueError, match="unstable basis"):
        verify_sensitivity(case["model"], case["contacts"], base, query, channel)


def test_c3l4_frozen_threshold_floor_does_not_break_symmetric_proof_validation():
    case = next(formal_cases({"coverage_resolution_bracket"}))
    proved = attached_base(case["bases"]["critical"])
    conservative = copy.deepcopy(proved)
    for field in ("exact_threshold", "attained", "threshold_certificate", "threshold_proof", "threshold_proof_reason"):
        conservative[field] = None
    assert compare_l3("critical", case["model"], case["contacts"], proved, conservative) == []
    assert compare_l3("critical", case["model"], case["contacts"], conservative, proved) == []
    with pytest.raises(ValueError, match="capability regression"):
        require_python_proof_floor("critical", proved, conservative)
    assert require_python_proof_floor("critical", conservative, proved)["checked"] == 0


@pytest.mark.parametrize("field", ["right_derivative", "left_derivative", "directional_derivative", "quality"])
def test_c3l4_frozen_slope_capability_cannot_regress_to_null_or_approximate(field):
    case = next(formal_cases({'g5_n3_mu1'}))
    query = next(q for _, q in case["queries"] if q["result"]["parameter"] == 'mu' and target_kind(q) == 'limit')
    base = attached_base(case["bases"]['limit'])
    channel = copy.deepcopy(expected_channel(query))
    channel["result"][field] = "approximate" if field == "quality" else None
    with pytest.raises(ValueError, match="capability regression"):
        require_python_proof_floor("sensitivity", query["result"], channel["result"])


def test_c3l4_t1b_current_frozen_capability_includes_three_upgraded_points():
    rows = read_json(T1B)["rows"]
    assert len(rows) == 36
    assert sum(r["derivatives"]["amplitude"]["status"] == "smooth" for r in rows) == 26
    assert sum(r["derivatives"]["tilt"]["status"] == "smooth" for r in rows) == 28
    assert [rows[i]["mu_exact"] for i in (13, 16, 30)] == ["131009/2097408", "98283/2097664", "326839/6291456"]
    baseline = next(r for r in rows if r["amplitude"] == "1/2048" and r["tilt"] == "3/32"
                    and r["phase"] == "0/1" and r["periods"] == 1 and r["asymmetry"] == "1/2" and r["family"] == "sawtooth")
    assert baseline["derivatives"]["amplitude"]["right"] == "-2043/64"
    assert baseline["derivatives"]["tilt"]["right"] == "2043/2048"


@pytest.mark.parametrize("name", ["t1b/00", "t1b/13", "t1b/35"])
def test_c3l4_t1b_regenerated_inputs_keep_frozen_slopes_and_bound_problem(name):
    case = next(t1b_cases({name}))
    base = attached_base(case["bases"]["critical"])
    assert base["threshold_certificate"]["problem"] is not None
    for _, query in case["queries"]:
        assert compare_sensitivity(case, base, query, expected_channel(query))[0] == []


def test_c3l4_ctypes_channels_have_explicit_counts_and_row_major_seed_storage():
    case = next(formal_cases({"g5_n3_mu1"}))
    queries = [q for _, q in case["queries"]]
    request, keep = pack_request(queries)
    assert C.sizeof(C3L4Info) == 32
    assert request.parameter_count == request.channel_count == 3 and request.output_count == 1
    assert request.vertices.value_count == 3 * request.vertex_count * 2
    assert request.dead.value_count == request.live.value_count == 3 * request.body_count * 3
    assert request.dof_anchor.value_count == 3 * request.body_count * 2
    assert request.struct_size == C.sizeof(SensitivityInput) and keep
    for i, query in enumerate(queries):
        assert request.channels[i].parameter.data.decode() == query["result"]["parameter"]


def test_c3l4_batch_jacobian_does_not_invent_slope_at_one_sided_tie():
    case = next(formal_cases({'g5_n3_mu2'}))
    query = next(q for _, q in case["queries"] if q["result"]["parameter"] == 'mu' and target_kind(q) == 'limit')
    base = attached_base(case["bases"]['limit'])
    channel = copy.deepcopy(expected_channel(query))
    batch = dict(sensitivity_model="ideal_exact_2d", parameter_count=1, output_count=1, channel_count=1, jacobian_shape=[1, 1],
                 jacobian_layout="output_major_channel_minor", channels=[channel], jacobian=[None])
    verify_batch(batch, [query])
    batch["jacobian"] = ["0/1"]
    with pytest.raises(ValueError, match="Jacobian must be null"):
        verify_batch(batch, [query])


def test_c3l4_historical_alternate_basis_is_not_a_branch_complete_derivative_proof():
    # The captured basis remains a legal L3/implicit *candidate*. It must not
    # substitute for the new double-infinitesimal derivative certificate even
    # where its historical scalar slopes happen to be correct.
    case = next(t1b_cases({"t1b/00"}))
    witness = read_json(ROOT / "tests/data/eab2_c3l4_threshold_basis_witness.json")
    assert witness["format"] == "eab2.c3l4.threshold-basis-witness.v1"
    assert witness["source"]["input_sha256"] == input_fingerprint(case["model"])
    assert witness["source"]["case_id"] == case["case_id"]
    for (_, query), channel in zip(case["queries"], witness["channels"]):
        assert query["result"]["tied_labels"] != channel["result"]["tied_labels"]
        with pytest.raises(ValueError, match="sensitivity result fields"):
            compare_sensitivity(case, witness["critical"], query, channel)
        augmented = copy.deepcopy(channel)
        augmented["result"]["branch_certificate"] = None
        delta, floor = compare_sensitivity(case, witness["critical"], query, augmented)
        assert delta and any(row["path"].endswith("method") for row in delta)
        assert floor["checked"] == 3 and floor["exceptions"] == []


@pytest.mark.parametrize("side", ["python", "cpp", "both"])
@pytest.mark.parametrize("mutation", ["extra", "missing", "duplicate", "component_slope", "component_missing",
                                     "component_extra", "component_duplicate", "scalar_slope"])
def test_c3l4_each_threshold_side_rejects_false_labels_and_slopes(side, mutation):
    case = copy.deepcopy(next(formal_cases({"g1_slender"})))
    query = next(q for _, q in case["queries"] if q["result"]["parameter"] == "t")
    base = attached_base(case["bases"]["critical"])
    channel = copy.deepcopy(expected_channel(query))
    results = [query["result"], channel["result"]] if side == "both" else [
        query["result"] if side == "python" else channel["result"]]
    for result in results:
        if mutation == "extra":
            result["tied_labels"].append("not_a_crossing")
        elif mutation == "missing":
            result["tied_labels"].pop()
        elif mutation == "duplicate":
            result["tied_labels"].append(copy.deepcopy(result["tied_labels"][0]))
        elif mutation == "component_slope":
            result["implicit_components"][0][1] = "123/1"
        elif mutation == "component_missing":
            result["implicit_components"].pop()
        elif mutation == "component_extra":
            result["implicit_components"].append(["not_a_crossing", "1/1", "1/1", "-1/1", 999])
        elif mutation == "component_duplicate":
            result["implicit_components"].append(copy.deepcopy(result["implicit_components"][0]))
        else:
            result.update(directional_derivative="123/1", right_derivative="123/1", left_derivative="123/1")
    message = "implicit components/phi derivatives" if mutation.startswith("component_") else (
        "implicit exact slope" if mutation == "scalar_slope" else "implicit tied labels")
    with pytest.raises(ValueError, match=message):
        compare_sensitivity(case, base, query, channel)


@pytest.mark.parametrize("side", ["python", "cpp"])
@pytest.mark.parametrize("mutation", ["polynomial", "sturm"])
def test_c3l4_each_threshold_side_rechecks_full_critical_proof(side, mutation):
    case = copy.deepcopy(next(formal_cases({"g1_slender"})))
    query = next(q for _, q in case["queries"] if q["result"]["parameter"] == "t")
    base = attached_base(case["bases"]["critical"])
    channel = copy.deepcopy(expected_channel(query))
    critical = case["bases"]["critical"]["result"] if side == "python" else base
    if mutation == "polynomial":
        # Alter the independent endpoint polynomial record, not the selected
        # implicit branch: sensitivity-only verification cannot catch this.
        critical["critical_polynomials"][0]["determinant"][0] = "987/1"
        message = "critical determinant identity"
    else:
        critical["threshold_proof"]["lower_signs"] = []
        message = "threshold one-sided Sturm signs"
    with pytest.raises(ValueError, match=message):
        compare_sensitivity(case, base, query, channel)


@pytest.mark.parametrize("name", ["g1_slender", "g1_unreversed_t1"])
@pytest.mark.parametrize("mutation,message", [
    ("continuation", "implicit selected basis continuation unproved"),
    ("endpoint", "implicit selected basis infeasible at threshold"),
    ("direction", "implicit derivative requires a valid direction")])
def test_c3l4_selected_implicit_branch_must_still_be_valid(name, mutation, message):
    case = next(formal_cases({name}))
    query = copy.deepcopy(next(q for _, q in case["queries"] if q["result"]["parameter"] == "t"))
    base = attached_base(case["bases"]["critical"])
    problem, seed = verify_sensitivity(case["model"], case["contacts"], base, query, expected_channel(query))
    raw = base["threshold_certificate"]["problem"]
    mu_seed = rebuilt_seed(case["model"], case["contacts"], Q(raw["mu"]),
                           unit_mu_jet(query["geometry_seed"]), labels=raw["column_labels"])
    side = "upper" if base["attained"] else "lower"
    if mutation == "continuation":
        base["threshold_proof"][side + "_signs"] = None
    elif mutation == "endpoint":
        branch = base["threshold_proof"][side + "_basis"]
        branch["numerators"][0] = [exact_wire(-Q(value)) for value in branch["determinant"]]
    else:
        query["direction_domain"] = dict(positive=False, negative=False)
    with pytest.raises(ValueError, match=message):
        verify_implicit(problem, seed, mu_seed, base, query, query["result"])


def test_c3l4_selected_implicit_branch_binds_threshold_column_labels():
    case = next(formal_cases({"g1_slender"}))
    query = next(q for _, q in case["queries"] if q["result"]["parameter"] == "t")
    base = attached_base(case["bases"]["critical"])
    branch = base["threshold_proof"]["upper_basis"]
    branch["labels"][0] = "wrong_threshold_column"
    with pytest.raises(ValueError, match="ray labels"):
        verify_sensitivity(case["model"], case["contacts"], base, query, expected_channel(query))


def test_c3l4_non_threshold_tied_labels_remain_strict():
    case = next(formal_cases({"g5_n3_mu1"}))
    query = next(q for _, q in case["queries"] if q["result"]["parameter"] == "mu")
    base = attached_base(case["bases"]["limit"])
    channel = copy.deepcopy(expected_channel(query))
    channel["result"]["tied_labels"].append("not_a_limit_tie")
    delta, _ = compare_sensitivity(case, base, query, channel)
    assert delta and all(row["path"].startswith("result.tied_labels") for row in delta)


def test_c3l4_declared_threshold_labels_preserve_caller_contract():
    case = copy.deepcopy(next(formal_cases({"g1_slender"})))
    query = next(q for _, q in case["queries"] if q["result"]["parameter"] == "t")
    assert check_frozen_implicit_query(query, expected_channel(query)) == 2
    query["declared_tied_labels"] = ["caller_marker"]
    query["result"]["tied_labels"].append("caller_marker")
    base = attached_base(case["bases"]["critical"])
    channel = copy.deepcopy(expected_channel(query))
    verify_sensitivity(case["model"], case["contacts"], base, query, channel)
    assert compare_sensitivity(case, base, query, channel)[0] == []
    # Only this frozen differential inventory promises caller labels are empty;
    # a legal new caller-label input must not silently expand that inventory.
    with pytest.raises(ValueError, match="frozen implicit inventory requires empty caller tied labels"):
        check_frozen_implicit_query(query, channel)


def test_c3l4_nonbinary64_thickness_samples_are_individually_domain_excluded():
    inventory = thickness_inventory()
    assert inventory["outside_binary64_domain"] == 32
    assert len(inventory["excluded"]) == len({row["source_name"] for row in inventory["excluded"]}) == 32
    assert all(row["reason"] == "non_binary64_exact_input" and row["failed_fields"] > 0
               and row["first_failure"]["exact"] for row in inventory["excluded"])


@pytest.mark.parametrize("direction", ["positive", "negative"])
def test_branch_jet_cannot_bypass_the_declared_direction_domain(direction):
    from eab2_c3l4_diff import refresh_case
    case = refresh_case(next(formal_cases({"g1_unreversed_t2"})))
    query = next(q for _, q in case["queries"] if q["result"]["parameter"] == "t")
    base = case["bases"]["critical"]["result"]
    channel = expected_channel(query)
    verify_sensitivity(case["model"], case["contacts"], base, query, channel, mu_max_binary64=case["bases"]["critical"]["mu_max_bits"])
    query["direction_domain"][direction] = False
    with pytest.raises(ValueError, match="outside valid direction"):
        verify_sensitivity(case["model"], case["contacts"], base, query, channel, mu_max_binary64=case["bases"]["critical"]["mu_max_bits"])


def test_live_referee_integer_recession_ray_has_canonical_rational_coordinates():
    from eab2_c3l4_diff import refresh_case
    case = refresh_case(next(formal_cases({"g1_koureas_h0_t0"})))
    query = next(q for _, q in case["queries"] if target_kind(q) == "limit")
    result = query["result"]
    assert result["method"] == "optimal_face_recession"
    assert result["dual_recession_ray"] and all(isinstance(v, str) and "/" in v for v in result["dual_recession_ray"])
    base = attached_base(case["bases"]["limit"])
    verify_sensitivity(case["model"], case["contacts"], base, query, expected_channel(query))
    bad = copy.deepcopy(expected_channel(query))
    bad["result"]["dual_recession_ray"] = ["0/1"] * len(result["dual_recession_ray"])
    with pytest.raises(ValueError, match="dual recession witness"):
        verify_sensitivity(case["model"], case["contacts"], base, query, bad)


def test_referee_ray_normalization_preserves_integer_identities_and_rejects_floats():
    from eab.kernel2d.sensitivity import SensitivityResult2
    from eab2_c3l4_diff import referee_sensitivity_wire
    value = SensitivityResult2("OK", "OPTIMAL", "singular", selected_piece=(1, 2), dual_recession_ray=(1, Q(0)))
    encoded = referee_sensitivity_wire(value)
    assert encoded["selected_piece"] == [1, 2]
    assert encoded["dual_recession_ray"] == ["1/1", "0/1"]
    with pytest.raises(ValueError, match="exact referee recession coordinates"):
        referee_sensitivity_wire(SensitivityResult2("OK", "OPTIMAL", "singular", dual_recession_ray=(1.0,)))


@pytest.mark.parametrize("family", ("all", "asymmetric", "branch", "formal", "t1b", "thickness"))
def test_all_family_order_prioritizes_new_coverage_without_omitting_or_repeating_a_family(monkeypatch, tmp_path, family):
    # Driver-only oracle: distinct tokens expose omission/repetition; no solver
    # or fake mathematical result is used as certificate evidence here.
    import eab2_c3l4_diff as driver
    import eab2_c3l4_asymmetric as asymmetric
    import eab2_c3l4_branches as branches
    monkeypatch.setattr(driver, "formal_cases", lambda selection: iter(("formal",)))
    monkeypatch.setattr(driver, "t1b_cases", lambda selection, thickness=False: iter(("thickness" if thickness else "t1b",)))
    monkeypatch.setattr(asymmetric, "asymmetric_cases", lambda selection: iter(("asymmetric",)))
    monkeypatch.setattr(branches, "branch_cases", lambda selection: iter(("branch",)))
    observed = []
    def consume(dll, cases, output, selection):
        assert dll is None and selection is None
        observed.extend(cases)
        return 0
    monkeypatch.setattr(driver, "run", consume)
    monkeypatch.setattr(sys, "argv", ["eab2_c3l4_diff.py", "--fixture-audit-only", "--family", family,
                                     "--output", str(tmp_path / "driver.json")])
    assert driver.main() == 0
    assert observed == (["asymmetric", "branch", "formal", "t1b", "thickness"] if family == "all" else [family])
