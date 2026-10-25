"""Independent Fraction/polynomial checker gates; no production solver oracle.

These small identities check the verifier itself. Production mutations are
separately injected into the implementations by the work-order runner.
"""
import ast
import copy
from fractions import Fraction as Q
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import eab2_branch_verify as check


def test_checker_import_boundary_is_standard_library_only():
    tree = ast.parse(Path(check.__file__).read_text(encoding="utf-8"))
    imports = [n.module if isinstance(n, ast.ImportFrom) else alias.name
               for n in ast.walk(tree) if isinstance(n, (ast.ImportFrom, ast.Import))
               for alias in (n.names if isinstance(n, ast.Import) else [None])]
    assert set(imports) <= {"fractions", "json", "struct", "argparse", "pathlib"}


def test_epsilon_then_eta_sign_not_eta_first_and_no_fixed_truncation():
    assert check.sign({(0, 3): Q(1), (1, 0): Q(-1)}) == 1
    assert check.sign({(2, 9): Q(-1), (3, 0): Q(100)}) == -1
    assert check.sign({(1024, 0): Q(-1)}) == -1
    assert check.sign({}) == 0


def test_full_polynomial_determinant_uses_exact_division():
    one, epsilon, eta = check.const(1), {(1, 0): Q(1)}, {(0, 1): Q(1)}
    A = [[one, epsilon, eta], [eta, one, epsilon], [epsilon, eta, one]]
    expected = check.add(one, check.add(check.mul(epsilon, check.mul(epsilon, epsilon)), check.mul(eta, check.mul(eta, eta))))
    expected = check.sub(expected, check.mul(check.const(3), check.mul(epsilon, eta)))
    assert check.determinant(A) == expected


def test_sparse_polynomial_cannot_hide_duplicate_or_zero_terms():
    with pytest.raises(AssertionError, match="duplicates"):
        check.read_poly([[0, 0, "1"], [0, 0, "-1"]])
    with pytest.raises(AssertionError, match="zero term"):
        check.read_poly([[0, 0, "0"]])


def test_raw_primitives_keep_cubic_moment_and_quadratic_load_terms():
    bodies = [dict(body_id="a", vertices=[[2, 3], [3, 3], [3, 4], [2, 4]],
                   dof_anchor=[Q(1, 2), Q(-3, 4)], reference_point=[0, 0], dof_mask=[1, 1, 1],
                   dead=[0, 0, 0], live=[1, 2, 3], boundary_type="MOVING_BODY"),
              dict(body_id="b", vertices=[[8, 0], [9, 0], [9, 1], [8, 1]],
                   dof_anchor=[0, 0], reference_point=[0, 0], dof_mask=[0, 0, 0],
                   dead=[0, 0, 0], live=[0, 0, 0], boundary_type="FIXED_BODY")]
    label = ["a", "b", ["2/1", "3/1"], "a", [0, 1]]
    contacts = [dict(a=0, b=1, point=[2, 3], label=label)]
    labels = [[label, -1], [label, 1], ["alpha", 1]]
    jet = dict(parameters=["raw"], body_ids=["a", "b"], vertex_ids=[[b, i] for b in ("a", "b") for i in range(4)],
               vertices=[[[1, 1], [-1, 2], [0, 0], [0, 0]] + [[0, 0]] * 4],
               dof_anchor=[[[0, 0], [0, 0]]], dead=[[[0, 0, 0], [0, 0, 0]]],
               live=[[[2, -3, 5], [0, 0, 0]]], mu=[0])
    mu = check.add(check.const(Q(1, 4)), {(1, 1): Q(1)})
    A, _, _ = check.raw_matrix(bodies, contacts, jet, labels, mu)
    assert A[2][0][3, 1] == -3
    assert A[2][1][3, 1] == 3
    jet["dof_anchor"][0][0] = [3, 4]
    A, _, _ = check.raw_matrix(bodies, contacts, jet, labels, mu)
    assert A[2][2][2, 0] == 17


def test_lower_feasibility_alone_cannot_certify_without_upper_ray():
    # A=[1,-mu], c=(0,1): lower dual is feasible at negative mu,
    # but this does not license fabricating an upper ray.
    A, b, c = [[check.const(1), check.const(-1)]], [check.const(0)], [check.const(0), check.const(1)]
    zero = dict(denominator=[[0, 0, "1"]], numerators=[[], []], basis=[], rows=[], labels=[],
                probe=dict(epsilon="1/16", eta="1/4"))
    with pytest.raises(AssertionError, match="normalization"):
        check.verify_primal(A, b, c, zero, zero)
    ray = copy.deepcopy(zero)
    ray.update(numerators=[[[0, 0, "1"]], [[0, 0, "1"]]], basis=[0], rows=[0])
    check.verify_primal(A, b, c, zero, ray)
    ray["numerators"][0] = [[0, 0, "1"], [7, 0, "-1"]]
    with pytest.raises(AssertionError, match="equality"):
        check.verify_primal(A, b, c, zero, ray)


def test_original_domain_bits_not_narrowed_bracket_binding():
    domain = dict(mu_min=0, mu_max=1, exact_mu_min="0/1", exact_mu_max="1/1",
                  mu_min_binary64="0000000000000000", mu_max_binary64="3ff0000000000000")
    check.check_domain(domain)
    domain["exact_mu_max"] = "1/2"
    with pytest.raises(AssertionError, match="binding"):
        check.check_domain(domain)


@pytest.mark.parametrize("direction", ["forward", "reverse"])
def test_full_raw_geometry_positive_and_each_side_extra_missing_wrong_root_gates(direction):
    from eab2_c3l4_diff import formal_cases, refresh_case, raw_bodies
    case = refresh_case(next(formal_cases({"g1_unreversed_t2"})))
    query = next(q for _, q in case["queries"] if q["result"]["parameter"] == "t")
    base = case["bases"]["critical"]["result"]
    certified_input = (raw_bodies(case["model"]), case["contacts"]["constraints"], query["geometry_seed"],
                       base["threshold_certificate"]["problem"]["column_labels"], base, query["result"])
    assert check.verify_certificate(*certified_input, mu_max_binary64="3ff0000000000000") == 2
    for defect in ("extra_tied_label", "missing_tied_label", "missing_component", "wrong_component_slope", "missing_upper_ray"):
        args = copy.deepcopy(certified_input)
        result = args[-1]
        branch = result["branch_certificate"][direction]
        if defect == "extra_tied_label":
            result["tied_labels"].append(["invented", 991])
        elif defect == "missing_tied_label":
            assert result["tied_labels"]
            result["tied_labels"].pop()
        elif defect == "missing_component":
            assert branch["candidate_branches"][0]["components"]
            branch["candidate_branches"][0]["components"].pop()
        elif defect == "wrong_component_slope":
            branch["candidate_branches"][0]["components"][0]["s"] = "1234567/1"
        else:
            branch["upper"]["ray"]["numerators"] = [[] for _ in args[3]]
        with pytest.raises(AssertionError, match="tied labels|root components|root slope|normalization"):
            check.verify_certificate(*args, mu_max_binary64="3ff0000000000000")


def test_singular_leading_candidate_labels_are_complete_and_coefficients_are_checked():
    from eab2_c3l4_branches import branch_cases
    from eab2_c3l4_diff import raw_bodies
    case = next(branch_cases({"branch/open_1/4"}))
    query = case["queries"][0][1]
    base = case["bases"]["critical"]["result"]
    args = (raw_bodies(case["model"]), case["contacts"]["constraints"], query["geometry_seed"],
            base["threshold_certificate"]["problem"]["column_labels"], base, query["result"])
    assert check.verify_certificate(*args, mu_max_binary64="3ff0000000000000") == 2
    branches = query["result"]["branch_certificate"]["forward"]["candidate_branches"]
    assert any(v.get("singular") and v["components"] for v in branches)
    for defect in ("missing", "extra", "wrong_slope", "wrong_coefficient", "wrong_order",
                   "float_order", "bool_order", "integer_singular_flag", "float_index"):
        damaged = copy.deepcopy(args)
        branch = next(v for v in damaged[-1]["branch_certificate"]["forward"]["candidate_branches"] if v.get("singular"))
        if defect == "missing":
            branch["components"].pop()
        elif defect == "extra":
            branch["components"].append(copy.deepcopy(branch["components"][0]))
        elif defect == "wrong_slope":
            branch["components"][0]["s"] = "99/1"
        elif defect == "wrong_coefficient":
            branch["components"][0]["leading_polynomial"][0] = "99/1"
        elif defect == "wrong_order":
            branch["components"][0]["leading_epsilon_order"] += 1
        elif defect == "float_order":
            branch["components"][0]["leading_epsilon_order"] = 1.0
        elif defect == "bool_order":
            branch["components"][0]["leading_epsilon_order"] = True
        elif defect == "integer_singular_flag":
            branch["singular"] = 1
        else:
            branch["components"][0]["index"] = 1.0
        with pytest.raises(AssertionError, match="singular candidate|candidate singular|candidate component"):
            check.verify_certificate(*damaged, mu_max_binary64="3ff0000000000000")


def test_unresolved_branch_cannot_claim_exact_quality_or_latent_certificate():
    domain = dict(mu_min=0, mu_max=1, exact_mu_min="0/1", exact_mu_max="1/1",
                  mu_min_binary64="0000000000000000", mu_max_binary64="3ff0000000000000")
    empty = dict(status="unresolved", reason="threshold_branch_certificate_unavailable",
                 s=None, lower=None, upper=None, candidate_branches=[], candidate_count=0, attempts=0)
    certificate = dict(version=1, order="epsilon_then_eta", search_domain=domain,
                       forward=copy.deepcopy(empty), reverse=copy.deepcopy(empty))
    result = dict(branch_certificate=certificate, right_derivative=None, left_derivative=None,
                  directional_derivative=None, tied_labels=[], differentiability="unresolved", quality="approximate",
                  call_status="OK", mathematical_status="CERTIFIED", parameter="p", method="branch_certificate",
                  display_status="NOT_APPLICABLE", reason="threshold_branch_certificate_unavailable")
    critical = dict(search_domain=domain, exact_threshold="1/2", call_status="OK", mathematical_status="CERTIFIED")
    jet = dict(parameters=["p"])
    assert check.verify_certificate([], [], jet, [], critical, result, mu_max_binary64="3ff0000000000000") == 0
    result["quality"] = "exact_jet"
    with pytest.raises(AssertionError, match="uncertified branch"):
        check.verify_certificate([], [], jet, [], critical, result, mu_max_binary64="3ff0000000000000")
    result["quality"] = "approximate"
    certificate["forward"]["s"] = "0/1"
    with pytest.raises(AssertionError, match="unproved branch"):
        check.verify_certificate([], [], jet, [], critical, result, mu_max_binary64="3ff0000000000000")
    certificate["forward"]["s"] = None
    certificate["forward"]["candidate_branches"] = {}
    with pytest.raises(AssertionError, match="candidate branch array"):
        check.verify_certificate([], [], jet, [], critical, result, mu_max_binary64="3ff0000000000000")
    certificate["forward"]["candidate_branches"] = []
    for reason in (None, "invented_reason"):
        certificate["forward"]["reason"] = reason
        with pytest.raises(AssertionError, match="unproved branch reason"):
            check.verify_certificate([], [], jet, [], critical, result, mu_max_binary64="3ff0000000000000")
    certificate["forward"]["reason"] = "threshold_search_domain_boundary"
    with pytest.raises(AssertionError, match="aggregate reason"):
        check.verify_certificate([], [], jet, [], critical, result, mu_max_binary64="3ff0000000000000")
    result["reason"] = "threshold_search_domain_boundary"
    assert check.verify_certificate([], [], jet, [], critical, result, mu_max_binary64="3ff0000000000000") == 0
    certificate["forward"]["reason"] = "threshold_branch_certificate_unavailable"
    result.update(differentiability="singular", reason="critical_basis_singular")
    assert check.verify_certificate([], [], jet, [], critical, result, mu_max_binary64="3ff0000000000000") == 0
    result["reason"] = "zero_implicit_denominator"
    assert check.verify_certificate([], [], jet, [], critical, result, mu_max_binary64="3ff0000000000000") == 0
    certificate["forward"]["reason"] = "threshold_search_domain_boundary"
    with pytest.raises(AssertionError, match="singular diagnostic"):
        check.verify_certificate([], [], jet, [], critical, result, mu_max_binary64="3ff0000000000000")


def _simple_raw_certificate():
    """Hand oracle A=(-t-mu,-t+mu,-1), t=1/2+p, b=0: mucrit=t.

    No production LP or geometry call: y=-1 below, r=(0,1/(eta*eps),1)
    above, x0=0. Each direction is certified by explicit full polynomials.
    """
    bodies = [dict(body_id="a", vertices=[[0, 0], [1, "1/2"], [1, 1], [0, 1]],
                   dof_anchor=[0, 0], reference_point=[0, 0], dof_mask=[1, 0, 0],
                   dead=[0, 0, 0], live=[-1, 0, 0], boundary_type="MOVING_BODY"),
              dict(body_id="b", vertices=[[-1, -1], [0, 0], [-1, 1]],
                   dof_anchor=[0, 0], reference_point=[0, 0], dof_mask=[0, 0, 0],
                   dead=[0, 0, 0], live=[0, 0, 0], boundary_type="FIXED_BODY")]
    label = ["a", "b", ["0/1", "0/1"], "a", [0, 1]]
    contacts = [dict(a=0, b=1, point=[0, 0], label=label)]
    labels = [[label, -1], [label, 1], ["alpha", 1]]
    jet = dict(parameters=["p"], body_ids=["a", "b"],
               vertex_ids=[["a", i] for i in range(4)] + [["b", i] for i in range(3)],
               vertices=[[[0, 0], [0, 1], [0, 0], [0, 0]] + [[0, 0]] * 3],
               dof_anchor=[[[0, 0], [0, 0]]], dead=[[[0, 0, 0], [0, 0, 0]]],
               live=[[[0, 0, 0], [0, 0, 0]]], mu=[0])
    domain = dict(mu_min=0, mu_max=1, exact_mu_min="0/1", exact_mu_max="1/1",
                  mu_min_binary64="0000000000000000", mu_max_binary64="3ff0000000000000")
    cert = dict(version=1, order="epsilon_then_eta", search_domain=domain)
    for name, direction in (("forward", "1/1"), ("reverse", "-1/1")):
        lower = dict(denominator=[[0, 0, "1/1"]], numerators=[[[0, 0, "-1/1"]]],
                     basis=[2], rows=[0], labels=[labels[2]], probe=dict(epsilon="1/16", eta="1/4"))
        point = dict(denominator=[[0, 0, "1/1"]], numerators=[[], [], []],
                     basis=[], rows=[], labels=[], probe=dict(epsilon="1/16", eta="1/4"))
        ray = dict(denominator=[[1, 1, "1/1"]], numerators=[[], [[0, 0, "1/1"]], [[1, 1, "1/1"]]],
                   basis=[1], rows=[0], labels=[labels[1]], probe=dict(epsilon="1/16", eta="1/4"))
        candidate = dict(kind="dual", rows=[0], basis=[2], components=[dict(
            index=1, label=labels[1], s=direction, partial_mu="-1/1", partial_parameter=direction)])
        cert[name] = dict(status="certified", reason=None, s=direction, lower=lower,
                         upper=dict(point=point, ray=ray), candidate_count=1, attempts=1,
                         candidate_branches=[candidate])
    critical = dict(search_domain=domain, exact_threshold="1/2", call_status="OK", mathematical_status="CERTIFIED")
    result = dict(branch_certificate=cert, call_status="OK", mathematical_status="CERTIFIED",
                  display_status="EXACT", method="branch_certificate", parameter="p", reason=None,
                  differentiability="smooth", quality="exact_jet", tied_labels=[labels[1]],
                  right_derivative="1/1", left_derivative="1/1", directional_derivative="1/1")
    return bodies, contacts, jet, labels, critical, result


def test_equal_fraction_values_cannot_be_misclassified_by_string_spelling():
    args = _simple_raw_certificate()
    assert check.verify_certificate(*args, mu_max_binary64="3ff0000000000000") == 2
    args[-1]["left_derivative"] = "2/2"
    args[-1]["directional_derivative"] = "3/3"
    assert check.verify_certificate(*args, mu_max_binary64="3ff0000000000000") == 2
    args[-1]["differentiability"] = "one_sided"
    with pytest.raises(AssertionError, match="classification"):
        check.verify_certificate(*args, mu_max_binary64="3ff0000000000000")
    args[-1].update(differentiability="smooth", left_derivative="2/1")
    with pytest.raises(AssertionError, match="sign mapping"):
        check.verify_certificate(*args, mu_max_binary64="3ff0000000000000")


@pytest.mark.parametrize("defect", ["negative_row", "bool_row", "float_row", "row_overflow",
    "negative_basis", "bool_basis", "float_basis", "basis_overflow", "duplicate_basis",
    "normalized_alpha_ray", "integer_singular", "bool_component", "float_component",
    "float_label", "component_shape", "candidate_shape"])
def test_regular_candidate_index_shape_and_metadata_poison_is_rejected(defect):
    args = _simple_raw_certificate()
    branch = args[-1]["branch_certificate"]["forward"]
    candidate = branch["candidate_branches"][0]
    if defect in ("negative_row", "bool_row", "float_row", "row_overflow"):
        candidate["rows"] = [{"negative_row": -1, "bool_row": False, "float_row": 0.0, "row_overflow": 1}[defect]]
    elif defect in ("negative_basis", "bool_basis", "float_basis", "basis_overflow"):
        candidate["basis"] = [{"negative_basis": -1, "bool_basis": True, "float_basis": 2.0, "basis_overflow": 3}[defect]]
    elif defect == "duplicate_basis":
        candidate.update(rows=[0, 0], basis=[2, 2])
    elif defect == "normalized_alpha_ray":
        candidate["kind"] = "ray"
    elif defect == "integer_singular":
        candidate["singular"] = 0
    elif defect in ("bool_component", "float_component"):
        candidate["components"][0]["index"] = True if defect == "bool_component" else 1.0
    elif defect == "float_label":
        candidate["components"][0]["label"] = [args[3][1][0], 1.0]
    elif defect == "component_shape":
        candidate["components"] = {}
    else:
        branch["candidate_branches"] = {}
    with pytest.raises(AssertionError, match="basis|candidate"):
        check.verify_certificate(*args, mu_max_binary64="3ff0000000000000")


@pytest.mark.parametrize("defect", ["bool_version", "wrong_parameter", "multiple_parameters", "call_status",
    "mathematical_status", "display_status", "method", "top_reason", "certified_reason",
    "bool_count", "negative_attempts"])
def test_certified_branch_envelope_and_typed_counts_are_not_advisory(defect):
    args = _simple_raw_certificate()
    result = args[-1]
    branch = result["branch_certificate"]["forward"]
    if defect == "bool_version":
        result["branch_certificate"]["version"] = True
    elif defect == "wrong_parameter":
        result["parameter"] = "other"
    elif defect == "multiple_parameters":
        args[2]["parameters"].append("other")
    elif defect in ("call_status", "mathematical_status", "display_status", "method"):
        result[defect] = "wrong"
    elif defect == "top_reason":
        result["reason"] = "threshold_search_domain_boundary"
    elif defect == "certified_reason":
        branch["reason"] = "threshold_search_domain_boundary"
    elif defect == "bool_count":
        branch["candidate_count"] = True
    else:
        branch["attempts"] = -1
    with pytest.raises(AssertionError, match="branch"):
        check.verify_certificate(*args, mu_max_binary64="3ff0000000000000")


@pytest.mark.parametrize("forgery", ["F4a_narrow", "F4b_widen", "missing_request"])
def test_archive_caller_domain_forgery_is_rejected_by_independent_checker(forgery):
    """Oracle: caller requested 1; mutually consistent returned domains cannot replace it."""
    args = _simple_raw_certificate()
    record = dict(zip(("bodies", "contacts", "jet", "labels", "critical", "result"), args))
    record["mu_max_binary64"] = "3ff0000000000000"
    assert check.verify_record(record) == 2
    if forgery == "missing_request":
        del record["mu_max_binary64"]
    else:
        maximum, exact, bits = ((Q(3, 4), "3/4", "3fe8000000000000") if forgery == "F4a_narrow"
                                else (Q(2), "2/1", "4000000000000000"))
        # F4a/F4b change BOTH returned copies with internally valid bits/exact
        # values. A self-consistency check alone accepts the forged domain.
        for domain in (record["critical"]["search_domain"], record["result"]["branch_certificate"]["search_domain"]):
            domain.update(mu_max=maximum, exact_mu_max=exact, mu_max_binary64=bits)
            check.check_domain(domain)
    with pytest.raises(AssertionError, match="caller mu_max_binary64"):
        check.verify_record(record)


@pytest.mark.parametrize("missing", ["lower", "upper", "point", "ray"])
def test_certified_null_witness_has_explicit_need_message_not_typeerror(missing):
    args = _simple_raw_certificate()
    branch = args[-1]["branch_certificate"]["forward"]
    if missing in ("lower", "upper"):
        branch[missing] = None
    else:
        branch["upper"][missing] = None
    with pytest.raises(AssertionError, match="certified branch needs .*witness"):
        check.verify_certificate(*args, mu_max_binary64="3ff0000000000000")


def test_certificate_archive_writer_binds_the_original_caller_request(tmp_path):
    import json
    from eab2_c3l4_branches import branch_cases
    from eab2_c3l4_diff import run
    case = next(branch_cases({"branch/open_1/4"}))
    output = tmp_path / "caller_binding.json"
    assert run(None, [case], output, {case["case_id"]}) == 0
    records = [json.loads(line) for line in output.with_suffix(".certificates.jsonl").read_text("utf-8").splitlines()]
    assert records and all(row["mu_max_binary64"] == case["bases"]["critical"]["mu_max_bits"] for row in records)
    assert all(check.verify_record(row) == 2 for row in records)
