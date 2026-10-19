"""Approved codec gates, not the formal exported benchmark dataset.

Bits are checked against struct and integer IEEE encodings. Certificates are
rechecked by rational linear algebra over decoded JSON, not solver statuses.
Export tests use isolated output directories and the explicit approved token.
"""
from fractions import Fraction as Q
from dataclasses import replace
import json
import hashlib
import math
import struct

import pytest

from eab.adapters.tia2d import g1, g5, g5_seed
from eab.kernel2d.assembly import Assembly2, Body2
from eab.kernel2d.sensitivity import build_limit_seed2
from eab.kernel2d.statics import critical_parameter, limit_load_ideal_exact_2d
from tia2d_cases import (SCHEMA_APPROVAL, binary64, build_case, decode_bits,
                        encode_case, export_cases, input_record, input_audit, rational)


@pytest.mark.parametrize("value,bits", [(0.0, "0000000000000000"), (-0.0, "8000000000000000"),
    (Q(1, 2), "3fe0000000000000"), (2.0 ** -1074, "0000000000000001")])
def test_bits_are_lossless_big_endian_lowercase_and_signed_zero(value, bits):
    assert binary64(value) == bits
    assert struct.pack(">d", decode_bits(bits)).hex() == bits
    assert rational(value) == str(Q(value).numerator) + "/" + str(Q(value).denominator)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), Q(1, 10), Q(2) ** 2000, True])
def test_invalid_or_python_only_inputs_never_silently_round_into_cpp(value):
    with pytest.raises((ValueError, OverflowError)):
        binary64(value)


@pytest.mark.parametrize("bits", ["7ff0000000000000", "fff0000000000000", "7ff8000000000000",
                                  "3FE0000000000000", "0", "000000000000000g"])
def test_invalid_bit_strings_are_rejected(bits):
    with pytest.raises(ValueError):
        decode_bits(bits)


def test_input_original_ids_negative_zero_and_boundary_omission_survive():
    a = Body2.from_vertices("moving", ((-0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)))
    record = input_record(Assembly2((a,)))
    item = record["bodies"][0]
    assert item["vertices_xy_bits"][0][0] == "8000000000000000"
    assert item["ccw_vertex_ids"] == [3, 2, 1, 0]
    assert item["boundary_type"] is None
    assert record["adjacency"] is None and record["completeness"] == "completeness_unknown"


def test_signed_zero_is_kept_in_frames_anchors_and_loads_not_only_vertices():
    body = Body2.from_vertices("body", ((0, 0), (1, 0), (1, 1), (0, 1)),
        reference_point=(-0.0, 0.0), dof_anchor=(0.0, -0.0),
        dead=(-0.0, 0.0, -0.0), live=(0.0, -0.0, 0.0))
    item = input_record(Assembly2((body,)))["bodies"][0]
    assert item["reference_point_bits"][0] == "8000000000000000"
    assert item["dof_anchor_bits"][1] == "8000000000000000"
    assert item["load_source"]["dead_bits"][0] == item["load_source"]["dead_bits"][2] == "8000000000000000"
    assert item["load_source"]["live_bits"][1] == "8000000000000000"
    changed = replace(body, dof_anchor=(Q(1), Q(2)), live=(Q(0), Q(-1), Q(0)))
    item = input_record(Assembly2((changed,)))["bodies"][0]
    assert item["dof_anchor_bits"] == [binary64(1), binary64(2)]
    assert item["load_source"]["live_bits"][1] == binary64(-1)


def test_direct_integer_body_exact_fields_are_rationals_but_ids_stay_integers():
    body = Body2("body", ((0, 0), (1, 0), (1, 1), (0, 1)), dof_anchor=(0, 0))
    record = input_record(Assembly2((body,), (), "complete"))
    assert record["bodies"][0]["reference_point"] == ["0/1", "0/1"]
    assert record["bodies"][0]["dead"] == ["0/1"] * 3
    assert record["bodies"][0]["vertex_ids"] == [0, 1, 2, 3]


@pytest.mark.parametrize("family", ["TIA-G1", "TIA-G5"])
def test_shared_actual_input_contact_parallel_and_concavity_audit(family):
    assembly = g1(t=Q(17, 64), height=Q(3, 2)) if family == "TIA-G1" else g5(n=7)
    record = input_record(assembly)
    audit = input_audit(assembly, record)
    assert "input_audit" not in record
    states = audit["exact_pair_states"]
    assert sum(item["state"] == "CONTACT" for item in states) == len(assembly.bodies) - 1
    assert all(item["state"] != "OVERLAP" for item in states)
    assert audit["exact_parallel_edge_pairs"]
    assert audit["no_new_concave_vertices"] is True


def test_input_audit_evaluates_concavity_and_rejects_false_expected_contacts():
    body = Body2.from_vertices("A", ((0, 0), (2, 0), (2, 2), (0, 2)))
    model = Assembly2((body,), (), "complete")
    record = input_record(model)
    record["bodies"][0]["vertices_xy_bits"][2] = [binary64(Q(1, 2)), binary64(Q(1, 2))]
    audit = input_audit(model, record)
    assert audit["lossless_binary64"] is False
    assert audit["no_new_concave_vertices"] is False
    assert audit["concave_vertices_after"] == [dict(body_id="A", ccw_indices=[2])]
    with pytest.raises(ArithmeticError, match="expected CONTACT"):
        input_audit(g5(), expected_contacts=())


def test_optional_git_provenance_does_not_inherit_a_parent_checkout(tmp_path):
    from tia2d_provenance import git_provenance
    result = git_provenance(tmp_path)
    assert result == dict(git_commit=None, git_commit_reason="no_git_checkout")


def test_null_observables_never_claim_exact_display():
    from tia2d_export import materialize, registered_specs
    spec = next(value for value in registered_specs() if value["case_id"] == "regression_b_bare_vv")
    model, _ = materialize(spec)
    case = build_case(model, "null-display", include_critical=True, include_sensitivity=True)
    for query in case["queries"]:
        if query["kind"] in ("first_order", "limit", "critical", "sensitivity"):
            assert query["display_status"] == "NOT_APPLICABLE"


def test_aliases_are_explicit_while_family_seeds_are_not_part_of_assembly_hash(tmp_path):
    first = build_case(g5(), "primary-role", _family_parameters={"role_label": "one"})
    second = build_case(g5(), "alias-role", _family_parameters={"role_label": "two"})
    export_cases((first, second), tmp_path / "aliases", schema_approval=SCHEMA_APPROVAL, _output_root=tmp_path)
    assert first["role"] == "primary" and first["alias_of"] is None
    assert second["role"] == "alias" and second["alias_of"] == first["case_id"]
    assert first["assembly"] == second["assembly"]


def test_formal_export_rejects_free_text_conditions_and_lp_only_seed_probes(tmp_path):
    case = build_case(g5(mu=Q(1, 4)), "conditions", include_sensitivity=True)
    query = next(q for q in case["queries"] if q["kind"] == "sensitivity")
    query["declared_validity_conditions"] = ["unapproved free text"]
    with pytest.raises(ValueError, match="approved enum"):
        export_cases((case,), tmp_path / "bad-condition", schema_approval=SCHEMA_APPROVAL, _output_root=tmp_path)
    query["declared_validity_conditions"] = []
    query["geometry_seed"] = None
    with pytest.raises(ValueError, match="geometry_seed"):
        export_cases((case,), tmp_path / "lp-only", schema_approval=SCHEMA_APPROVAL, _output_root=tmp_path)


def _check_exact_limit(query):
    result, problem = query["result"], query["problem"]
    A = [[Q(v) for v in row] for row in problem["A"]]
    b, c = [Q(v) for v in problem["b"]], [Q(v) for v in problem["c"]]
    if query["mathematical_status"] == "OPTIMAL":
        x, y = [Q(v) for v in result["exact_x"]], [Q(v) for v in result["exact_y"]]
        assert all(v >= 0 for v in x)
        assert all(sum(u * v for u, v in zip(row, x)) == rhs for row, rhs in zip(A, b))
        assert all(sum(A[i][j] * y[i] for i in range(len(b))) >= c[j] for j in range(len(c)))
        assert sum(u * v for u, v in zip(x, c)) == sum(u * v for u, v in zip(b, y)) == Q(result["exact_value"])
    else:
        assert query["mathematical_status"] == "UNBOUNDED"
        x, r = [Q(v) for v in result["feasible_point"]], [Q(v) for v in result["improving_ray"]]
        assert all(v >= 0 for v in x + r) and r[-1] == 1
        assert all(sum(u * v for u, v in zip(row, x)) == rhs for row, rhs in zip(A, b))
        assert all(sum(u * v for u, v in zip(row, r)) == 0 for row in A)


@pytest.mark.parametrize("family", ["TIA-G1", "TIA-G5"])
def test_draft_case_certificates_nulls_and_wallclock_are_not_display_numbers(family):
    assembly = g1() if family == "TIA-G1" else g5(mu=Q(1, 4))
    case = build_case(assembly, family + "-draft-test", lock_bodies=(2,), include_critical=True)
    decoded = json.loads(encode_case(case))
    assert decoded["schema"] == "eab2.case.v1"
    assert decoded["schema_revision"] == "tia2d-2"
    for query in decoded["queries"]:
        assert set(("call_status", "mathematical_status", "display_status", "source", "observable")) <= query.keys()
        assert query["python_wallclock"]["seconds"] >= 0
        assert math.isfinite(query["python_wallclock"]["seconds"])
        assert query["assembly_ref"] == decoded["queries"][0]["assembly_ref"]
        if query["kind"] != "lock":
            assert query["contact_set_ref"] == decoded["queries"][0]["contact_set_ref"]
    assert set(decoded["provenance"]) == {"source_manifest_sha256"}
    assert len(decoded["provenance"]["source_manifest_sha256"]) == 64
    source = case._source_stamp  # In-memory guard is not an encoded case field.
    assert source["git_commit"] is None or len(source["git_commit"]) == 40
    assert source["source_manifest_basis"] == "actual_root_src_tests_tools_bytes_v1"
    source_paths = {entry["path"] for entry in source["uncommitted_source_files"]}
    assert {"src/eab/kernel2d/assembly.py", "src/eab/kernel2d/critical.py", "tools/tia2d_cases.py"} <= source_paths
    assert all("__pycache__" not in path.split("/") for path in source_paths)
    assert source["command"]
    body_ids = {body["body_id"] for body in decoded["assembly"]["bodies"]}
    contacts = decoded["queries"][0]["result"]
    for a, b, state in contacts["pair_states"]:
        assert a in body_ids and b in body_ids and state in ("OUTSIDE", "CONTACT", "OVERLAP")
    for key in ("constraints", "points", "segments", "unresolved"):
        for point in contacts[key]:
            assert point["a"] in body_ids and point["b"] in body_ids
    _check_exact_limit(next(q for q in decoded["queries"] if q["kind"] == "limit"))
    critical = next(q for q in decoded["queries"] if q["kind"] == "critical")["result"]
    assert "mu_lo_bits" in critical and "mu_lo" not in critical
    if family == "TIA-G1":
        assert critical["attained"] is True and critical["lower_certificate"] is None
    else:
        assert critical["mu_hi_bits"] is None and critical["reason"] == "bounded_on_domain"


def test_lock_sources_bind_original_vertex_edge_ids_not_normalized_positions():
    raw_a = ((0, 0), (0, 1), (1, 1), (1, 0))
    raw_b = ((1, 0), (2, 0), (2, 1), (1, 1))
    a = Body2.from_vertices("moving", raw_a)
    b = Body2.from_vertices("fixed", raw_b, boundary_type="FIXED_BODY", dof_mask=(0, 0, 0))
    case = build_case(Assembly2((a, b), ((0, 1),), "complete"), "source-test", lock_bodies=(0,))
    lock = next(q for q in case["queries"] if q["kind"] == "lock")
    assert lock["fixed_neighbors"] == ["fixed"]
    for source in lock["result"]["contact_sources"]:
        kind, moving_id, a_feature, fixed_id, b_feature = source["label"]
        assert moving_id == "moving" and fixed_id == source["neighbor_body_id"] == "fixed"
        point = tuple(Q(v) for v in source["point"])
        vertex, edge = ((raw_a[a_feature], (raw_b[b_feature[0]], raw_b[b_feature[1]])) if kind == "VE"
                        else (raw_b[b_feature], (raw_a[a_feature[0]], raw_a[a_feature[1]])))
        assert point == vertex
        u, v = edge
        assert (v[0] - u[0]) * (point[1] - u[1]) == (v[1] - u[1]) * (point[0] - u[0])


def test_zero_mu_sensitivity_exports_recession_not_closed_form_slope():
    case = build_case(g5(mu=0), "zero-mu-sensitivity", include_sensitivity=True)
    result = next(q for q in case["queries"] if q["kind"] == "sensitivity")["result"]
    assert result["differentiability"] == "singular" and result["reason"] == "possibly_discontinuous"
    assert result["dual_recession_ray"]
    assert result["directional_derivative"] is None
    assert result["left_derivative"] is None and result["right_derivative"] is None


def test_no_batch_export_without_explicit_schema_approval(tmp_path):
    with pytest.raises(PermissionError, match="confirmation"):
        export_cases((), tmp_path / "must_not_exist")
    assert not (tmp_path / "must_not_exist").exists()


def test_nonfinite_or_oversize_json_is_rejected_not_replaced_by_zero():
    with pytest.raises(ValueError):
        encode_case({"invalid": float("nan")})
    with pytest.raises(ValueError, match="1 MB"):
        encode_case({"too_large": "x" * 1_000_001})


def _qmatrix(value):
    return [[Q(v) for v in row] for row in value]


def _qvector(value):
    return [Q(v) for v in value]


def _dot(a, b):
    return sum((u * v for u, v in zip(a, b)), Q(0))


def _check_seed_encoding(seed):
    for value in [v for row in seed["dA"] for v in row] + seed["db"] + seed["dc"]:
        assert isinstance(value, str) and value == rational(Q(value))


def _check_exported_mills(case, query):
    """Rebuild both max-form LPs from JSON only; no sensitivity solver calls."""
    assert query["limit_query_ref"] == "limit"
    base = next(item for item in case["queries"] if item["kind"] == query["limit_query_ref"])
    problem, seed, result = base["problem"], query["seed"], query["result"]
    A, b, c = _qmatrix(problem["A"]), _qvector(problem["b"]), _qvector(problem["c"])
    dA, db, dc = _qmatrix(seed["dA"]), _qvector(seed["db"]), _qvector(seed["dc"])
    value = Q(base["result"]["exact_value"])
    m, n = len(b), len(c)
    _check_seed_encoding(seed)
    for key, sign, direction in (("forward_certificate", 1, "positive"), ("reverse_certificate", -1, "negative")):
        if not query["direction_domain"][direction]:
            assert result[key] is None
            continue
        x, y = (_qvector(v) for v in result[key])
        rows = [row + [Q(0)] * (n + 2) for row in A] + [c + [Q(0)] * (n + 2)]
        rows += [[sign * v for v in dA[i]] + A[i] + [b[i], -b[i]] for i in range(m)]
        rhs = b + [value] + [sign * v for v in db]
        objective = [sign * v for v in dc] + c + [value, -value]
        assert all(v >= 0 for v in x)
        assert all(_dot(row, x) == target for row, target in zip(rows, rhs))
        assert all(sum(rows[i][j] * y[i] for i in range(len(rhs))) >= objective[j]
                   for j in range(len(objective)))
        derivative = _dot(objective, x)
        assert derivative == _dot(rhs, y)
        name = "right_derivative" if sign == 1 else "left_derivative"
        assert sign * derivative == Q(result[name])
        name = "D_plus" if sign == 1 else "D_minus"
        assert derivative == Q(query["directional_values"][name])


@pytest.mark.parametrize("mu,pressure_slope,height_right,height_left", [
    (Q(1, 4), Q(1, 2), Q(0), Q(0)), (Q(2), Q(2), Q(2), Q(2)),
    (Q(1), Q(2), Q(0), Q(2)),
])
def test_extra_pressure_height_queries_export_replayable_sliding_hinging_and_tie(
        mu, pressure_slope, height_right, height_left):
    assembly = g5(mu=mu)
    problem = limit_load_ideal_exact_2d(assembly).problem
    specs = tuple(dict(seed=g5_seed(problem, parameter), problem=problem,
                       validity_conditions=("shared geometric parameter",), tied_labels=("sliding", "hinging"))
                  for parameter in ("P", "h"))
    case = json.loads(encode_case(build_case(assembly, "extra-seeds", include_sensitivity=True,
                                            _sensitivity_queries=specs)))
    queries = [q for q in case["queries"] if q["kind"] == "sensitivity"]
    assert [q["result"]["parameter"] for q in queries] == ["mu", "P", "h"]
    for query in queries:
        assert query["result"]["method"] == "mills_freund"
        _check_exported_mills(case, query)
    pressure, height = queries[1:]
    assert Q(pressure["result"]["right_derivative"]) == Q(pressure["result"]["left_derivative"]) == pressure_slope
    assert Q(height["result"]["right_derivative"]) == height_right
    assert Q(height["result"]["left_derivative"]) == height_left
    assert height["result"]["differentiability"] == ("one_sided" if mu == 1 else "smooth")
    assert height["result"]["tied_labels"] == ["sliding", "hinging"]
    assert height["declared_validity_conditions"] == ["shared geometric parameter"]
    assert "L1接触骨架不变" in height["result"]["validity_conditions"]


def test_extra_query_one_valid_direction_is_exported_not_inferred_from_zero():
    assembly = g5(mu=Q(1))
    problem = limit_load_ideal_exact_2d(assembly).problem
    spec = dict(seed=g5_seed(problem, "h"), problem=problem, positive_direction_valid=False)
    case = json.loads(encode_case(build_case(assembly, "left-only", _sensitivity_queries=(spec,))))
    query = next(q for q in case["queries"] if q["kind"] == "sensitivity")
    assert query["direction_domain"] == dict(positive=False, negative=True)
    assert query["result"]["right_derivative"] is None
    assert query["directional_values"]["D_plus"] is None
    assert query["directional_values"]["D_minus"] == "-2/1"
    _check_exported_mills(case, query)


def _solve_exact(matrix, rhs):
    """Independent Gauss-Jordan arithmetic for exported certificate replay."""
    n = len(rhs)
    rows = [list(row) + [v] for row, v in zip(matrix, rhs)]
    for j in range(n):
        pivot = next(i for i in range(j, n) if rows[i][j])
        rows[j], rows[pivot] = rows[pivot], rows[j]
        scale = rows[j][j]
        rows[j] = [v / scale for v in rows[j]]
        for i in range(n):
            if i != j:
                scale = rows[i][j]
                rows[i] = [a - scale * b for a, b in zip(rows[i], rows[j])]
    return [row[-1] for row in rows]


def _check_exported_implicit(case, query):
    """Replay -phi_p/phi_mu directly from decoded matrices and both seeds."""
    assert query["threshold_query_ref"] == "critical"
    assert query["threshold_certificate_ref"] == dict(query="critical", field="result.threshold_certificate")
    critical = next(q for q in case["queries"] if q["kind"] == "critical")["result"]
    endpoint = critical["threshold_certificate"]
    _check_exact_limit(dict(result=endpoint, problem=endpoint["problem"],
                            mathematical_status=endpoint["mathematical_status"]))
    problem, result = endpoint["problem"], query["result"]
    A, c = _qmatrix(problem["A"]), _qvector(problem["c"])
    branch = critical["threshold_proof"]["upper_basis" if critical["attained"] else "lower_basis"]
    basis, entering = branch["basis"], branch["entering"]
    m = len(A)
    B = [[row[j] for j in basis] for row in A]
    dual = not critical["attained"]
    matrix = [[B[j][i] for j in range(m)] for i in range(m)] if dual else B
    rhs = [c[j] for j in basis] if dual else [-row[entering] for row in A]
    state = _solve_exact(matrix, rhs)
    computed = []
    for key in ("threshold_mu_seed", "seed"):
        seed = query[key]
        _check_seed_encoding(seed)
        dA, dc = _qmatrix(seed["dA"]), _qvector(seed["dc"])
        rhs = ([dc[basis[k]] - sum(dA[i][basis[k]] * state[i] for i in range(m)) for k in range(m)] if dual else
               [-dA[i][entering] - sum(dA[i][basis[k]] * state[k] for k in range(m)) for i in range(m)])
        change = _solve_exact(matrix, rhs)
        computed.append([sum(dA[i][k] * state[i] + A[i][k] * change[i] for i in range(m)) - dc[k]
                         for k in range(len(c))] if dual else change)
    for label, slope, dmu, dp, index in result["implicit_components"]:
        assert label == branch["labels"][index]
        assert Q(dmu) == computed[0][index] and Q(dp) == computed[1][index]
        assert Q(slope) == -Q(dp) / Q(dmu)


@pytest.mark.parametrize("orientation,height,parameter,expected", [
    ("unreversed", Q(1), "t", Q(1)), ("koureas", Q(1, 4), "t", Q(15, 16)),
    ("koureas", Q(1, 4), "h", -Q(17, 32)),
])
def test_critical_derivative_exports_exact_seed_endpoint_and_branch_references(orientation, height, parameter, expected):
    assembly = g1(t=Q(1, 4), height=height, orientation=orientation)
    critical = critical_parameter(assembly, max_steps=20)
    problem = critical.threshold_certificate.problem
    seeds = {}
    for contact in problem.contact_set.constraints:
        slope = contact.tangent[0] / contact.tangent[1]
        if parameter == "t":
            dp, dt = (4 * slope * (contact.point[1] - height / 2), Q(0)), (4 * contact.tangent[0], Q(0))
        else:
            dp = (slope * (contact.point[1] / height - Q(1, 2)), contact.point[1] / height)
            dt = tuple(v / height for v in contact.tangent)
        seeds[contact.label] = (dp, dt)
    seed = build_limit_seed2(problem, contact_seeds=seeds, parameter=parameter)
    spec = dict(seed=seed, problem=problem, target="critical", validity_conditions=("shared interface seeds",))
    case = json.loads(encode_case(build_case(assembly, "implicit-seed", include_critical=True,
                                            _sensitivity_queries=(spec,))))
    query = next(q for q in case["queries"] if q["kind"] == "sensitivity")
    assert query["result"]["method"] == "implicit_certificate"
    assert Q(query["result"]["right_derivative"]) == Q(query["result"]["left_derivative"]) == expected
    assert query["declared_validity_conditions"] == ["shared interface seeds"]
    _check_exported_implicit(case, query)


def test_extra_seeds_reject_wrong_problem_missing_threshold_and_unknown_inputs():
    assembly = g5(mu=Q(1, 4))
    problem = limit_load_ideal_exact_2d(assembly).problem
    valid = dict(seed=g5_seed(problem, "P"), problem=problem)
    for spec, match in ((dict(valid, problem=replace(problem, mu=Q(3))), "does not match"),
                        (dict(valid, target="critical"), "threshold query"),
                        (dict(valid, arbitrary=True), "unknown")):
        with pytest.raises(ValueError, match=match):
            build_case(assembly, "bad-extra", _sensitivity_queries=(spec,))


def test_extra_seed_binary64_entries_become_exact_rationals_and_nonfinite_is_rejected():
    assembly = g5(mu=Q(1, 4))
    problem = limit_load_ideal_exact_2d(assembly).problem
    seed = g5_seed(problem, "P")
    seed = replace(seed, db=(0.0,) * (len(seed.db) - 1) + (1.0,))
    case = build_case(assembly, "numeric-seed", _sensitivity_queries=(dict(seed=seed, problem=problem),))
    query = next(q for q in case["queries"] if q["kind"] == "sensitivity")
    _check_seed_encoding(query["seed"])
    assert query["seed"]["db"][-1] == "1/1"
    bad = replace(seed, db=(float("nan"),) + seed.db[1:])
    with pytest.raises(ValueError):
        build_case(assembly, "invalid-numeric-seed", _sensitivity_queries=(dict(seed=bad, problem=problem),))


@pytest.mark.parametrize("field", ["uncommitted_source_sha256", "uncommitted_source_files", "tool_version"])
def test_batch_rejects_mixed_source_stamps_before_creating_directory(tmp_path, field):
    first = build_case(g5(), "source-a")
    second = build_case(g5(), "source-b")
    second._source_stamp[field] = [] if field == "uncommitted_source_files" else "different-source"
    target = tmp_path / "no-mixed-export"
    # The source is invalid, so no successful batch is produced by this test.
    with pytest.raises(ValueError, match="different source stamps"):
        export_cases((first, second), target, schema_approval=SCHEMA_APPROVAL)
    assert not target.exists()


def test_batch_default_output_boundary_still_rejects_outside_source_root(tmp_path):
    from tia2d_cases import ROOT
    target = ROOT.parent / ("outside-case-export-" + tmp_path.name)
    assert not target.exists()
    with pytest.raises(ValueError, match="inside the worktree"):
        export_cases((), target, schema_approval=SCHEMA_APPROVAL)
    assert not target.exists()


def test_approved_batch_has_one_source_manifest_and_lossless_ordered_query_parts(tmp_path):
    case = build_case(g5(mu=Q(1, 4)), "split-case", include_sensitivity=True)
    while len(json.dumps(case, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) <= 1_100_000:
        case["queries"] = case["queries"] * 2
    target = tmp_path / "approved-split"
    manifest = export_cases((item for item in (case,)), target,
                            schema_approval=SCHEMA_APPROVAL, _output_root=tmp_path)
    assert manifest["schema_revision"] == "tia2d-2"
    assert manifest["schema_approval"] == SCHEMA_APPROVAL
    assert json.loads((target / "manifest.json").read_text(encoding="utf-8")) == manifest
    source_record = manifest["source_manifest"]
    source_data = (target / source_record["path"]).read_bytes()
    source = json.loads(source_data)
    assert hashlib.sha256(source_data).hexdigest() == source_record["sha256"]
    assert len(source_data) == source_record["bytes"] <= 1_000_000
    assert source["approval_date"] == "2026-10-19" and (source["git_commit"] is None or len(source["git_commit"]) == 40)
    assert source["command"] and source["source_files"] and source["tool_version"]
    input_sha = hashlib.sha256(json.dumps(case["assembly"], sort_keys=True, allow_nan=False).encode()).hexdigest()
    assert source["inputs"] == [dict(case_id="split-case", input_sha256=input_sha)]
    record = manifest["cases"][0]
    assert record["input_sha256"] == input_sha and len(record["parts"]) > 1
    queries, indices = [], []
    for index, part in enumerate(record["parts"]):
        data = (target / part["path"]).read_bytes()
        assert len(data) == part["bytes"] <= 1_000_000
        assert hashlib.sha256(data).hexdigest() == part["sha256"]
        item = json.loads(data)
        assert item["provenance"] == dict(source_manifest_sha256=source_record["sha256"])
        assert item["fragment"] == dict(index=index, count=len(record["parts"]), query_indices=part["query_indices"])
        assert item["assembly"] == case["assembly"]
        assert "source_files" not in item and "_source_stamp" not in item
        queries.extend(item["queries"])
        indices.extend(part["query_indices"])
    assert indices == list(range(record["query_count"]))
    assert queries == case["queries"]


def test_batch_source_change_before_or_during_write_never_has_a_success_manifest(tmp_path, monkeypatch):
    import tia2d_cases as codec
    case = build_case(g5(), "source-change")
    base = case._source_stamp
    for change_at in (2, 3):
        calls = []
        def changing_stamp():
            calls.append(1)
            return dict(base, uncommitted_source_sha256="changed") if len(calls) >= change_at else dict(base)
        monkeypatch.setattr(codec, "_source_stamp", changing_stamp)
        target = tmp_path / ("changed-" + str(change_at))
        with pytest.raises(RuntimeError, match="source changed"):
            export_cases((case,), target, schema_approval=SCHEMA_APPROVAL, _output_root=tmp_path)
        assert not (target / "manifest.json").exists()
        if change_at == 2:
            assert not target.exists()
        else:
            assert json.loads((target / "INVALIDATED.json").read_text(encoding="utf-8"))["status"] == "INVALIDATED"


def test_single_oversize_query_is_rejected_without_truncation_or_output(tmp_path):
    case = build_case(g5(), "oversize-query")
    case["queries"][0]["result"]["reason"] = "x" * 1_000_001
    target = tmp_path / "oversize"
    with pytest.raises(ValueError, match="single query exceeds"):
        export_cases((case,), target, schema_approval=SCHEMA_APPROVAL, _output_root=tmp_path)
    assert not target.exists()


def test_private_sensitivity_factory_uses_the_already_solved_problems():
    called = []
    def factory(limit, critical):
        called.append((limit.exact_value, critical.reason))
        return (dict(seed=g5_seed(limit.problem, "P"), problem=limit.problem),)
    case = build_case(g5(mu=Q(1, 4)), "factory", include_critical=True,
                      _sensitivity_factory=factory)
    assert called == [(Q(1, 2), "bounded_on_domain")]
    query = next(item for item in case["queries"] if item["kind"] == "sensitivity")
    assert query["result"]["parameter"] == "P" and query["result"]["right_derivative"] == "1/2"


def test_automatic_mu_sensitivity_preserves_declared_mode_ties():
    case = build_case(g5(mu=Q(1)), "mu-tie", include_sensitivity=True,
                      _sensitivity_labels=("sliding", "hinging"))
    result = next(item["result"] for item in case["queries"] if item["kind"] == "sensitivity")
    assert result["differentiability"] == "one_sided"
    assert result["tied_labels"] == ["sliding", "hinging"]
    assert result["right_derivative"] == "0/1" and result["left_derivative"] == "2/1"


@pytest.mark.parametrize("steps", [10, 63, 65, 64.0, True])
def test_unrecorded_critical_budget_cannot_change_replay(steps):
    with pytest.raises(ValueError, match="critical max_steps=64"):
        build_case(g5(), "unrecorded-budget", include_critical=True, critical_max_steps=steps)
