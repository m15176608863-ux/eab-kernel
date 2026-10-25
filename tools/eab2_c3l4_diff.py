"""Independent original-geometry C3-L4 seed and certificate differential.

The arithmetic oracle uses Fraction elimination and polynomial differentiation,
not C++ helpers or Python production sensitivity helpers. Production Python is
the separately compared referee; frozen dA/db/dc are derived expectations only.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
from fractions import Fraction as Q
import gzip
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src/eab").is_dir())
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
from eab2_c3l1_diff import (FORMAL, _private_ids, decode_assembly, differences,
    geometry_dofs, rational, read_json, require, vec, mat, dot, verify_optimum)
from eab2_c3l3_diff import (compare as compare_l3, determinant_solve, exact_wire,
    p_eval, rebuilt_problem, require_python_proof_floor, verify_branch, verify_critical, verify_limit)

T1B = ROOT / "tests/data/eab2_c3l4_t1b_expected.json"
T1B_SHA256 = "7bef75f7d2e8f690ff80687138bb9759201dbf630241258257bce23d547c8d94"
SLOPES = ("directional_derivative", "right_derivative", "left_derivative")
WITNESSES = ("forward_certificate", "reverse_certificate", "primal_recession_ray",
             "dual_recession_ray", "selected_piece", "implicit_components", "piece_jacobians", "branch_certificate")


def formal_cases(selection=None):
    """Load all fragments and target bindings; never silently drop a query."""
    manifest = read_json(FORMAL / "manifest.json")
    for entry in manifest["cases"]:
        if selection is not None and entry["case_id"] not in selection:
            continue
        source, queries, family = None, {}, None
        for part in entry["parts"]:
            raw = gzip.decompress((FORMAL / (part["path"] + ".gz")).read_bytes())
            require(len(raw) == part["bytes"] and hashlib.sha256(raw).hexdigest() == part["sha256"],
                    "formal integrity: " + part["path"])
            record = read_json(raw)
            require(record["case_id"] == entry["case_id"], "formal case ID")
            require(source is None or source == record["assembly"], "fragment assembly mismatch")
            source, family = record["assembly"], record["family_parameters"]["family"]
            require(len(part["query_indices"]) == len(record["queries"]), "fragment query count")
            for index, query in zip(part["query_indices"], record["queries"]):
                require(index not in queries, "duplicate query index")
                queries[index] = query
        require(set(queries) == set(range(entry["query_count"])), "incomplete formal queries")
        model = decode_assembly(source)
        ids = [b.body_id for b in model.bodies]
        contacts = next(_private_ids(q["result"], ids) for q in queries.values() if q["kind"] == "assembly")
        bases = {q["kind"]: q for q in queries.values() if q["kind"] in ("limit", "critical")}
        selected = [(i, q) for i, q in sorted(queries.items()) if q["kind"] == "sensitivity"]
        for _, query in selected:
            target = target_kind(query)
            require(target in bases and query.get("assembly_ref") == bases[target]["assembly_ref"]
                    and query.get("contact_set_ref") == bases[target]["contact_set_ref"], "sensitivity target binding")
            if target == "critical":
                require(query["threshold_certificate_ref"] == dict(query="critical", field="result.threshold_certificate"),
                        "threshold certificate binding")
        yield dict(case_id=entry["case_id"], family="formal/" + family,
                   model=model, contacts=contacts, bases=bases, queries=selected)


def target_kind(query):
    limit, critical = query.get("limit_query_ref"), query.get("threshold_query_ref")
    require((limit == "limit") != (critical == "critical"), "exactly one sensitivity target")
    require(limit in (None, "limit") and critical in (None, "critical"), "unknown sensitivity binding")
    return "limit" if limit else "critical"


def geometry_jet(model, parameter, vertex_values):
    """Pack supplied original-vertex jets, without producing any LP derivative."""
    by_body = {body.body_id: values for body, values in zip(model.bodies, vertex_values)}
    bodies = sorted(model.bodies, key=lambda body: body.body_id)
    ids = [[b.body_id, i] for b in bodies for i in range(len(b.original_vertices or b.vertices))]
    return dict(parameters=[parameter], vertex_ids=ids, body_ids=[b.body_id for b in bodies],
        vertices=[[exact_wire(by_body[name][i]) for name, i in ids]],
        dead=[[["0/1"] * 3 for _ in bodies]], live=[[["0/1"] * 3 for _ in bodies]],
        dof_anchor=[[["0/1"] * 2 for _ in bodies]], mu=["0/1"])


def rebuilt_seed(model, contacts, mu, jet, index=0, labels=None):
    """Differentiate original force-at-anchor rows, including moving anchors.

    No production seed builder is imported. Tangent orientation follows the
    original labelled CCW source body, not an exported tangent/normal field.
    """
    bodies = sorted(model.bodies, key=lambda b: b.body_id)
    ids = [[b.body_id, i] for b in bodies for i in range(len(b.original_vertices or b.vertices))]
    require(set(jet) == {"parameters", "vertex_ids", "body_ids", "vertices", "dead", "live", "dof_anchor", "mu"},
            "geometry jet fields")
    require(jet["vertex_ids"] == ids and jet["body_ids"] == [b.body_id for b in bodies], "geometry seed ID order")
    parameters = jet["parameters"]
    require(len(parameters) == len(set(parameters)) and all(isinstance(p, str) and p for p in parameters),
            "geometry parameter identities")
    require(0 <= index < len(parameters), "geometry channel index")
    for key, size, width in (("vertices", len(ids), 2), ("dead", len(bodies), 3),
                            ("live", len(bodies), 3), ("dof_anchor", len(bodies), 2)):
        require(len(jet[key]) == len(parameters), "geometry channel dimensions")
        for table in jet[key]:
            require(len(table) == size and all(len(row) == width for row in table), "geometry jet dimensions")
            for row in table:
                vec(row)
    require(len(jet["mu"]) == len(parameters), "mu channel dimensions")
    vertices = {tuple(identity): vec(value) for identity, value in zip(ids, jet["vertices"][index])}
    loads = {key: dict(zip(jet["body_ids"], map(vec, jet[key][index]))) for key in ("dead", "live", "dof_anchor")}
    dmu = vec(jet["mu"])[index]
    shared = {}
    for body in model.bodies:
        for i, raw in enumerate(body.original_vertices or body.vertices):
            point, velocity = tuple(map(Q, raw)), vertices[body.body_id, i]
            require(point not in shared or shared[point] == velocity, "shared vertex seed mismatch")
            shared[point] = velocity
    dofs = geometry_dofs(model)
    def cross(a, b):
        return a[0] * b[1] - a[1] * b[0]
    columns, natural_labels = [], []
    for contact in contacts["constraints"]:
        a, b = contact["a"], contact["b"]
        point = vec(contact["point"])
        source, (first, last) = contact["label"][-2:]
        body = next(body for body in model.bodies if body.body_id == source)
        raw = body.original_vertices or body.vertices
        sense = 1 if model.bodies[a].body_id == source else -1
        require(source in (model.bodies[a].body_id, model.bodies[b].body_id), "edge source body")
        tangent = tuple(sense * (Q(raw[last][k]) - Q(raw[first][k])) for k in (0, 1))
        dt = tuple(sense * (vertices[source, last][k] - vertices[source, first][k]) for k in (0, 1))
        require(point in shared, "contact point requires an original vertex jet")
        for sign in (-1, 1):
            force = (-tangent[1] + sign * mu * tangent[0], tangent[0] + sign * mu * tangent[1])
            df = (-dt[1] + sign * (dmu * tangent[0] + mu * dt[0]),
                   dt[0] + sign * (dmu * tangent[1] + mu * dt[1]))
            column = []
            for i, k in dofs:
                target = model.bodies[i]
                side = int(i == a) - int(i == b)
                arm = tuple(point[j] - target.dof_anchor[j] for j in (0, 1))
                velocity = tuple(shared[point][j] - loads["dof_anchor"][target.body_id][j] for j in (0, 1))
                derivative = df[k] if k < 2 else cross(velocity, force) + cross(arm, df)
                column.append(side * derivative)
            columns.append(tuple(column))
            natural_labels.append([contact["label"], sign])
    def load_derivative(body, key, coordinate):
        derivative, value = loads[key][body.body_id], getattr(body, key)
        if coordinate < 2:
            return derivative[coordinate]
        offset = tuple(body.dof_anchor[k] - body.reference_point[k] for k in (0, 1))
        return derivative[2] - cross(offset, derivative) - cross(loads["dof_anchor"][body.body_id], value)
    columns.append(tuple(load_derivative(model.bodies[i], "live", k) for i, k in dofs))
    natural_labels.append(["alpha", 1])
    if labels is not None:
        key = lambda x: json.dumps(x, separators=(",", ":"), ensure_ascii=True)
        indexed = dict(zip(map(key, natural_labels), columns))
        require(Counter(map(key, labels)) == Counter(indexed.keys()), "seed physical column labels")
        columns = [indexed[key(label)] for label in labels]
    return dict(dA=tuple(tuple(column[i] for column in columns) for i in range(len(dofs))),
        db=tuple(-load_derivative(model.bodies[i], "dead", k) for i, k in dofs),
        dc=(Q(0),) * len(columns), parameter=parameters[index])


def unit_mu_jet(jet):
    result = copy.deepcopy(jet)
    result["parameters"] = ["mu"]
    for name, width, count in (("vertices", 2, len(jet["vertex_ids"])), ("dead", 3, len(jet["body_ids"])),
                              ("live", 3, len(jet["body_ids"])), ("dof_anchor", 2, len(jet["body_ids"]))):
        result[name] = [[["0/1"] * width for _ in range(count)]]
    result["mu"] = ["1/1"]
    return result


def directional_values(result):
    return dict(D_plus=result["right_derivative"],
                D_minus=None if result["left_derivative"] is None else exact_wire(-rational(result["left_derivative"])))


def solve_square(A, b):
    determinant, answer = determinant_solve(A, b)
    require(determinant != 0, "sensitivity singular basis")
    return answer


def stable_basis(base, problem):
    A, c = problem["A"], problem["c"]
    m, n = len(A), len(c)
    basis = base["basis"]
    if len(basis) != m or len(set(basis)) != m or any(type(j) is not int or not 0 <= j < n for j in basis):
        return False
    B = tuple(tuple(row[j] for j in basis) for row in A)
    if not determinant_solve(B, problem["b"])[0] or any(rational(base["exact_x"][j]) <= 0 for j in basis):
        return False
    y = vec(base["exact_y"])
    return all(dot(tuple(row[j] for row in A), y) != c[j] for j in range(n) if j not in basis)


def verify_limit_sensitivity(problem, seed, base, query, result):
    """Independent witness equations for fixed-basis, recession and Mills LPs."""
    if base["mathematical_status"] != "OPTIMAL":
        require(result["differentiability"] == "unresolved" and result["reason"] == "finite_optimum_required",
                "nonfinite sensitivity contract")
        require(all(result[k] is None for k in SLOPES), "nonfinite certified slope")
        return
    A, b, c = problem["A"], problem["b"], problem["c"]
    dA, db, dc = seed["dA"], seed["db"], seed["dc"]
    m, n = len(b), len(c)
    method = result["method"]
    domain = query["direction_domain"]
    if method == "stable_basis":
        require(stable_basis(base, problem), "stable-basis formula used on an unstable basis")
        x, y = vec(base["exact_x"]), vec(base["exact_y"])
        slope = dot(x, dc) + dot(y, tuple(db[i] - dot(dA[i], x) for i in range(m)))
        for field, direction in (("right_derivative", "positive"), ("left_derivative", "negative")):
            require(result[field] == (exact_wire(slope) if domain[direction] else None), "original unscaled dual derivative")
    elif method == "optimal_face_recession":
        primal, dual = result["primal_recession_ray"], result["dual_recession_ray"]
        require(primal is not None or dual is not None, "missing recession witness")
        if primal is not None:
            ray = vec(primal)
            require(len(ray) == n and any(ray) and all(v >= 0 for v in ray) and dot(c, ray) == 0
                    and all(dot(row, ray) == 0 for row in A), "primal recession witness")
        if dual is not None:
            ray = vec(dual)
            require(len(ray) == m and any(ray) and dot(b, ray) == 0
                    and all(dot(column, ray) >= 0 for column in zip(*A)), "dual recession witness")
        require(result["differentiability"] == "singular" and result["reason"] == "possibly_discontinuous"
                and all(result[k] is None for k in SLOPES), "recession must not certify a slope")
    elif method == "mills_freund":
        value = rational(base["exact_value"])
        for key, sign, direction, slope in (("forward_certificate", 1, "positive", "right_derivative"),
                                          ("reverse_certificate", -1, "negative", "left_derivative")):
            if not domain[direction]:
                require(result[key] is None and result[slope] is None, "invalid directional output")
                continue
            certificate = result[key]
            require(certificate is not None and len(certificate) == 2, "missing Mills certificate")
            matrix = [tuple(row) + (Q(0),) * (n + 2) for row in A] + [tuple(c) + (Q(0),) * (n + 2)]
            matrix += [tuple(sign * v for v in dA[i]) + tuple(A[i]) + (b[i], -b[i]) for i in range(m)]
            rhs = tuple(b) + (value,) + tuple(sign * v for v in db)
            objective = tuple(sign * v for v in dc) + tuple(c) + (value, -value)
            verify_optimum(matrix, rhs, objective, vec(certificate[0]), vec(certificate[1]), sign * rational(result[slope]))
        expected_kind = "smooth" if (result["right_derivative"] is not None and
            result["right_derivative"] == result["left_derivative"]) else "one_sided"
        require(result["differentiability"] == expected_kind, "Mills plus/minus differentiability")
    else:
        require(result["differentiability"] == "unresolved" and all(result[k] is None for k in SLOPES),
                "unknown successful sensitivity method")
    require(result["directional_derivative"] == result["right_derivative"], "directional/right disagreement")


def local_sign(polynomial, point, side):
    """Exact first nonzero Taylor coefficient; independent of production code."""
    polynomial, order = tuple(polynomial), 0
    while any(polynomial):
        value = p_eval(polynomial, point)
        if value:
            return (1 if value > 0 else -1) * side ** order
        polynomial = tuple(i * polynomial[i] for i in range(1, len(polynomial)))
        order += 1
    return 0


def verify_implicit(problem, seed, mu_seed, critical, query, result):
    if result["method"] != "implicit_certificate":
        require(all(result[k] is None for k in SLOPES), "unproved threshold slope")
        return
    require(critical["exact_threshold"] is not None and critical["threshold_proof"] is not None,
            "implicit derivative needs exact threshold proof")
    require(any(query["direction_domain"].values()), "implicit derivative requires a valid direction")
    dual = not critical["attained"]
    branch = critical["threshold_proof"]["lower_basis" if dual else "upper_basis"]
    require(branch is not None and branch["kind"] == ("mechanism" if dual else "improving_ray"),
            "implicit derivative must use still-valid endpoint")
    side = "lower" if dual else "upper"
    signs, interval = (critical["threshold_proof"][side + suffix] for suffix in ("_signs", "_interval"))
    require(signs is not None and (interval[0] == interval[1] or bool(signs)),
            "implicit selected basis continuation unproved")
    A, c, basis = problem["A"], problem["c"], branch["basis"]
    m = len(A)
    B = tuple(tuple(row[j] for j in basis) for row in A)
    Bt = tuple(zip(*B))
    state = solve_square(Bt, tuple(c[j] for j in basis)) if dual else solve_square(B, tuple(-row[branch["entering"]] for row in A))
    def variation(direction):
        if dual:
            rhs = tuple(direction["dc"][j] - sum(direction["dA"][i][j] * state[i] for i in range(m)) for j in basis)
            return solve_square(Bt, rhs)
        rhs = tuple(-direction["dA"][i][branch["entering"]] -
                    sum(direction["dA"][i][j] * state[k] for k, j in enumerate(basis)) for i in range(m))
        return solve_square(B, rhs)
    state_p, state_mu = variation(seed), variation(mu_seed)
    point = rational(critical["exact_threshold"])
    denominator = p_eval(vec(branch["determinant"]), point)
    require(denominator != 0, "implicit basis determinant vanishes")
    require(all(p_eval(vec(raw), point) / denominator >= 0 for raw in branch["numerators"]),
            "implicit selected basis infeasible at threshold")
    components = []
    for k, raw in enumerate(branch["numerators"]):
        polynomial = vec(raw)
        if p_eval(polynomial, point) != 0 or local_sign(polynomial, point, 1 if dual else -1) * (1 if denominator > 0 else -1) >= 0:
            continue
        if dual:
            phi_p = sum(seed["dA"][i][k] * state[i] + A[i][k] * state_p[i] for i in range(m)) - seed["dc"][k]
            phi_mu = sum(mu_seed["dA"][i][k] * state[i] + A[i][k] * state_mu[i] for i in range(m)) - mu_seed["dc"][k]
        else:
            phi_p, phi_mu = state_p[k], state_mu[k]
        require(phi_mu != 0, "zero implicit denominator cannot certify slope")
        components.append([branch["labels"][k], exact_wire(-phi_p / phi_mu), exact_wire(phi_mu), exact_wire(phi_p), k])
    require(bool(components), "no independently verified crossing component")
    require(result["implicit_components"] == components, "implicit components/phi derivatives")
    require(result["selected_piece"] == [branch["kind"], basis, branch["entering"]], "implicit selected piece binding")
    require(result["piece_jacobians"] == [[row[0], row[1]] for row in components], "implicit piece slopes")
    # Public ABI/Python contract: caller string labels are retained alongside
    # genuine crossing labels. The frozen-run restriction is separate below.
    expected_labels = query.get("declared_tied_labels", []) + [row[0] for row in components]
    require(len(result["tied_labels"]) == len(label_set(result["tied_labels"])) and
            label_set(result["tied_labels"]) == label_set(expected_labels),
            "implicit tied labels must be exactly declared and crossing labels without duplicates")
    slopes = {row[1] for row in components}
    if len(slopes) > 1:
        require(result["differentiability"] == "tie" and result["reason"] == "competing_threshold_slopes"
                and all(result[k] is None for k in SLOPES), "competing threshold slope contract")
    else:
        slope = next(iter(slopes))
        for field, direction in (("right_derivative", "positive"), ("left_derivative", "negative")):
            require(result[field] == (slope if query["direction_domain"][direction] else None), "implicit exact slope")
        kind = "smooth" if all(query["direction_domain"].values()) else "one_sided"
        require(result["differentiability"] == kind, "implicit valid direction classification")


def label_set(values):
    return sorted(set(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) for value in values))


def verify_sensitivity(model, contacts, base, query, channel, *, mu_max_binary64=None):
    result = channel["result"]
    require(set(result) == set(query["result"]), "sensitivity result fields")
    require(channel["parameter"] == query["result"]["parameter"] == result["parameter"], "sensitivity parameter binding")
    kind = target_kind(query)
    require(result["sensitivity_model"] == "ideal_exact_2d" and result["quality"] in ("exact_jet", "approximate"), "sensitivity model/quality")
    if any(result[k] is not None for k in SLOPES):
        require(result["quality"] == "exact_jet", "uncertified sensitivity value")
    require(result["right_derivative"] is None or query["direction_domain"]["positive"],
            "certified right derivative outside valid direction")
    require(result["left_derivative"] is None or query["direction_domain"]["negative"],
            "certified left derivative outside valid direction")
    required_conditions = set(query["declared_validity_conditions"]) | set(base["validity_conditions"]) | {"L1接触骨架不变"}
    require(required_conditions <= set(result["validity_conditions"]), "sensitivity validity conditions")
    method = result["method"]
    if method != "mills_freund":
        require(result["forward_certificate"] is None and result["reverse_certificate"] is None,
                "exclusive directional LP certificates")
    if method != "optimal_face_recession":
        require(result["primal_recession_ray"] is None and result["dual_recession_ray"] is None,
                "exclusive recession witnesses")
    if method not in ("stable_basis", "implicit_certificate", "branch_certificate"):
        require(result["selected_piece"] is None and result["piece_jacobians"] == []
                and result["implicit_components"] == [], "exclusive basis/implicit witnesses")
    if method == "stable_basis":
        slope = result["right_derivative"] if result["right_derivative"] is not None else result["left_derivative"]
        require(result["selected_piece"] == base["basis"] and
                result["piece_jacobians"] == [[base["basis"], slope]] and result["implicit_components"] == [],
                "stable basis witness binding")
    endpoint = base if kind == "limit" else base.get("threshold_certificate")
    problem = None
    seed = mu_seed = None
    if endpoint and endpoint.get("problem"):
        raw = endpoint["problem"]
        problem = rebuilt_problem(model, contacts, rational(raw["mu"]), raw["column_labels"])
        seed = rebuilt_seed(model, contacts, rational(raw["mu"]), query["geometry_seed"], labels=raw["column_labels"])
        require(channel["derived_seed"] == exact_wire(seed), "C++ geometry-derived seed mismatch")
        if kind == "critical":
            mu_seed = rebuilt_seed(model, contacts, rational(raw["mu"]), unit_mu_jet(query["geometry_seed"]), labels=raw["column_labels"])
            require(channel["threshold_mu_seed"] == exact_wire(mu_seed), "C++ threshold mu seed mismatch")
            if method == "implicit_certificate":
                role = "upper_basis" if base["attained"] else "lower_basis"
                # A threshold LP may use a different column permutation from
                # either bracket endpoint. Bind the chosen branch to THIS LP.
                verify_branch(model, contacts, base["threshold_proof"][role], raw["column_labels"])
    else:
        require(channel["derived_seed"] is None, "missing LP must not fabricate a derived seed")
    if kind == "limit":
        require(channel["threshold_mu_seed"] is None, "finite value must not carry threshold mu seed")
        verify_limit_sensitivity(problem, seed, base, query, result)
    elif method == "branch_certificate" and result.get("branch_certificate") is not None:
        from eab2_branch_verify import verify_certificate
        require(problem is not None, "branch proof needs an exact threshold LP")
        verify_certificate(raw_bodies(model), contacts["constraints"], query["geometry_seed"],
                           endpoint["problem"]["column_labels"], base, result, mu_max_binary64=mu_max_binary64)
    else:
        verify_implicit(problem, seed, mu_seed, base, query, result)
    require(result["directional_derivative"] == result["right_derivative"], "directional/right contract")
    finite = any(result[field] is not None for field in SLOPES)
    require(result["display_status"] == ("EXACT" if finite else "NOT_APPLICABLE"), "sensitivity display contract")
    return problem, seed


def semantic_sensitivity(result):
    value = {key: item for key, item in result.items() if key not in WITNESSES}
    for key in ("tied_labels", "near_labels", "validity_conditions"):
        value[key] = label_set(value[key])
    return value


def compare_sensitivity(case, base, query, channel, dispositions=None):
    kind = target_kind(query)
    expected_base = attached_base(case["bases"][kind])
    if kind == "critical":
        # Both sides are independently certified from original geometry. A
        # matching pair of invented labels/slopes must not validate itself.
        verify_critical(case["model"], case["contacts"], expected_base)
        verify_critical(case["model"], case["contacts"], base)
    verify_sensitivity(case["model"], case["contacts"], expected_base, query, expected_channel(query), mu_max_binary64=case["bases"][kind].get("mu_max_bits"))
    problem, seed = verify_sensitivity(case["model"], case["contacts"], base, query, channel, mu_max_binary64=case["bases"][kind].get("mu_max_bits"))
    expected = query["result"]
    if query["seed"] is not None:
        expected_base = case["bases"][target_kind(query)]["result"]
        expected_endpoint = expected_base if target_kind(query) == "limit" else expected_base["threshold_certificate"]
        raw = expected_endpoint.get("problem") or case["bases"][target_kind(query)].get("problem")
        natural = rebuilt_seed(case["model"], case["contacts"], rational(raw["mu"]), query["geometry_seed"], labels=raw["column_labels"])
        require(exact_wire(natural) == query["seed"], "frozen derived seed mismatch")
        if target_kind(query) == "critical":
            unit = rebuilt_seed(case["model"], case["contacts"], rational(raw["mu"]), unit_mu_jet(query["geometry_seed"]), labels=raw["column_labels"])
            require(exact_wire(unit) == query["threshold_mu_seed"], "frozen threshold mu seed mismatch")
    require(query["directional_values"] == directional_values(expected), "frozen directional sign contract")
    actual = channel["result"]
    left, right = semantic_sensitivity(expected), semantic_sensitivity(actual)
    cpp_enrichment = (kind == "critical" and expected_base["exact_threshold"] is None
                      and base["exact_threshold"] is not None and actual.get("branch_certificate") is not None)
    if cpp_enrichment:
        # An independently verified C++-only threshold may carry a K jet;
        # absent Python proof is not a numerical disagreement. The floor is
        # still applied below and never permits losing a Python-certified jet.
        affected = (*SLOPES, "differentiability", "quality", "reason", "method", "display_status", "tied_labels")
        for key in affected:
            left[key] = right[key] = "independently verified C++ threshold branch enrichment"
        if dispositions is not None:
            dispositions.append(dict(classification="verified_cpp_only_threshold_branch_enrichment",
                exact_threshold=base["exact_threshold"], attained=base["attained"], normalized_fields=list(affected),
                verification="original_geometry_complete_polynomials_K_dual_point_ray_and_original_domain",
                python={key: expected[key] for key in affected}, cpp={key: actual[key] for key in affected}))
    slope_enrichment = []
    if (kind == "critical" and not cpp_enrichment and expected.get("method") == "branch_certificate"
            and actual.get("method") == "branch_certificate" and expected.get("branch_certificate")
            and actual.get("branch_certificate")):
        for direction in ("forward", "reverse"):
            if (expected["branch_certificate"][direction]["status"] != "certified"
                    and actual["branch_certificate"][direction]["status"] == "certified"):
                slope_enrichment.append(direction)
    if slope_enrichment:
        # The C++ certificate of this direction was re-verified in K by
        # verify_sensitivity above; a direction the referee left unresolved
        # is a capability difference and is logged, never a disagreement. The
        # floor below still forbids the opposite (a Python jet lost by C++).
        affected = (*SLOPES, "differentiability", "quality", "reason", "display_status", "tied_labels")
        for key in affected:
            left[key] = right[key] = "independently verified C++-only branch slope"
        if dispositions is not None:
            dispositions.append(dict(classification="verified_cpp_only_branch_slope", directions=list(slope_enrichment),
                exact_threshold=base["exact_threshold"], attained=base["attained"], normalized_fields=list(affected),
                verification="original_geometry_complete_polynomials_K_dual_point_ray_original_domain_and_recorded_probe",
                python={key: expected[key] for key in affected}, cpp={key: actual[key] for key in affected}))
    basis_dependent = (kind == "critical" and not cpp_enrichment and expected["method"] == actual["method"]
        and (actual["method"] == "implicit_certificate" or (actual["method"] == "branch_certificate"
             and expected.get("branch_certificate") is not None and actual.get("branch_certificate") is not None)))
    if basis_dependent:
        # Owner clarification: these are labels of the independently verified
        # selected critical basis, not a canonical cross-backend semantic set.
        del left["tied_labels"], right["tied_labels"]
    delta = differences(left, right)
    if not cpp_enrichment:
        python_values, cpp_values = dict(query["directional_values"]), dict(directional_values(channel["result"]))
        for direction, key in (("forward", "D_plus"), ("reverse", "D_minus")):
            if direction in slope_enrichment:
                python_values[key] = cpp_values[key] = "independently verified C++-only branch slope"
        delta += differences(python_values, cpp_values, "directional_values")
    if kind == "critical":
        if not cpp_enrichment:
            delta += differences({key: expected_base[key] for key in ("exact_threshold", "attained")},
                                 {key: base[key] for key in ("exact_threshold", "attained")}, "threshold")
    if basis_dependent and label_set(expected["tied_labels"]) != label_set(actual["tied_labels"]) and dispositions is not None:
        fields = ("selected_piece", "tied_labels", "implicit_components", "piece_jacobians")
        dispositions.append(dict(classification="verified_basis_dependent_threshold_labels",
            exact_threshold=base["exact_threshold"], attained=base["attained"],
            semantic_fields_equal=not delta,
            verification=("both_original_geometry_full_polynomial_K_brackets_and_all_candidate_root_labels"
                          if actual["method"] == "branch_certificate" else
                          "both_original_geometry_LP_polynomial_identities_one_sided_Sturm_and_all_crossing_slopes"),
            python={key: expected[key] for key in fields}, cpp={key: actual[key] for key in fields}))
    try:
        floor = require_python_proof_floor("sensitivity", expected, channel["result"])
    except ValueError as regression:
        # A capability regression is this query's mismatch; the case goes on
        # so one weaker channel cannot hide the other channels' results.
        delta = delta + [dict(path="proof_capability_floor", expected="frozen Python proof capability",
                              actual=str(regression))]
        floor = dict(required_fields=[], checked=0, exceptions=[str(regression)])
    return delta, floor


def raw_bodies(model):
    """Plain-data boundary; the independent K checker imports no eab code."""
    return [dict(body_id=b.body_id, vertices=exact_wire(b.original_vertices or b.vertices),
                 dof_anchor=exact_wire(b.dof_anchor), reference_point=exact_wire(b.reference_point),
                 dof_mask=list(b.dof_mask), boundary_type=b.boundary_type,
                 dead=exact_wire(b.dead), live=exact_wire(b.live)) for b in model.bodies]


def referee_seed(problem, jet):
    """Supply raw affine primitives to the referee, independently of dA."""
    from eab.kernel2d.sensitivity import build_limit_seed2
    model = problem.assembly
    velocities = dict(zip(map(tuple, jet["vertex_ids"]), map(vec, jet["vertices"][0])))
    shared = {tuple(map(Q, point)): velocities[body.body_id, i]
              for body in model.bodies for i, point in enumerate(body.original_vertices or body.vertices)}
    seeds = {}
    for contact in problem.contact_set.constraints:
        source, (first, last) = contact.label[-2:]
        sense = 1 if source == model.bodies[contact.a].body_id else -1
        dt = tuple(sense * (velocities[source, last][k] - velocities[source, first][k]) for k in (0, 1))
        seeds[contact.label] = shared[tuple(contact.point)], dt
    by_body = {kind: dict(zip(jet["body_ids"], map(vec, jet[kind][0]))) for kind in ("dead", "live", "dof_anchor")}
    return build_limit_seed2(problem, mu_seed=rational(jet["mu"][0]), contact_seeds=seeds,
                            dead_seeds=by_body["dead"], live_seeds=by_body["live"],
                            anchor_seeds=by_body["dof_anchor"], parameter=jet["parameters"][0])


def referee_sensitivity_wire(result):
    """Canonicalize exact numeric rays, not integer basis/label identities."""
    encoded = exact_wire(result)
    for field in ("primal_recession_ray", "dual_recession_ray"):
        values = getattr(result, field)
        if values is not None:
            require(all(type(value) in (int, Q) for value in values), "exact referee recession coordinates")
            encoded[field] = [exact_wire(Q(value)) for value in values]
    return encoded


def refresh_case(case):
    """Compare repaired live Python; keep frozen records for explicit errata."""
    from eab.kernel2d.contacts import assemble_contact_set2
    from eab.kernel2d.sensitivity import build_limit_seed2, evaluate_sensitivity2
    from eab2_c3l3_diff import python_result
    case = dict(case, bases=copy.deepcopy(case["bases"]), queries=copy.deepcopy(case["queries"]))
    contacts = assemble_contact_set2(case["model"])
    for index, query in case["queries"]:
        if query.get("generated_channel") or query.get("seed") is None:
            continue
        frozen = attached_base(case["bases"][target_kind(query)])
        endpoint = frozen if target_kind(query) == "limit" else frozen.get("threshold_certificate")
        require(endpoint and endpoint.get("problem"), "frozen derived seed needs its original LP")
        raw = endpoint["problem"]
        derived = rebuilt_seed(case["model"], case["contacts"], rational(raw["mu"]),
                               query["geometry_seed"], labels=raw["column_labels"])
        require(exact_wire(derived) == query["seed"], "frozen geometry-derived seed mismatch: " + str(index))
        query["frozen_derived_seed_verified"] = True
    actual_bases = {}
    for kind in {target_kind(q) for _, q in case["queries"]}:
        base_query = case["bases"][kind]
        base = python_result(case["model"], base_query, contacts)
        actual_bases[kind] = base
        exported = exact_wire(base)
        if kind == "limit":
            exported["problem"] = exact_wire(base.problem)
        else:
            for name in ("lower_certificate", "upper_certificate", "threshold_certificate"):
                if getattr(base, name) is not None:
                    exported[name]["problem"] = exact_wire(getattr(base, name).problem)
        base_query["result"] = exported
    for _, query in case["queries"]:
        original = query["result"]
        kind, parameter = target_kind(query), original["parameter"]
        base = actual_bases[kind]
        endpoint = base if kind == "limit" else base.threshold_certificate
        seed = referee_seed(endpoint.problem, query["geometry_seed"]) if endpoint and endpoint.problem else None
        mu_seed = build_limit_seed2(endpoint.problem, mu_seed=1) if seed is not None and kind == "critical" else None
        before = time.perf_counter()
        print(json.dumps(dict(stage="live_referee_begin", case_id=case["case_id"], parameter=parameter)), flush=True)
        result = evaluate_sensitivity2(base, seed, parameter=parameter,
            threshold_mu_seed=mu_seed, tied_labels=query.get("declared_tied_labels", ()),
            positive_direction_valid=query["direction_domain"]["positive"],
            negative_direction_valid=query["direction_domain"]["negative"],
            validity_conditions=query["declared_validity_conditions"])
        query.update(result=referee_sensitivity_wire(result), seed=exact_wire(seed), threshold_mu_seed=exact_wire(mu_seed),
                     python_wallclock=dict(seconds=time.perf_counter() - before),
                     expectation_source="repaired live Python; frozen values retained as errata baseline")
        print(json.dumps(dict(stage="live_referee_end", case_id=case["case_id"], parameter=parameter,
                              seconds=time.perf_counter() - before)), flush=True)
        query["directional_values"] = directional_values(query["result"])
        contract = ("differentiability", "right_derivative", "left_derivative", "reason", "quality", "validity_conditions")
        old, new = ({key: source[key] for key in contract} for source in (original, query["result"]))
        if old != new and not query.get("generated_channel"):
            query["erratum"] = dict(old=old, new=new, proof=query["result"].get("branch_certificate"),
                                    reason="WO-C3L4-fix branch-complete/domain certificate contract")
    return case


def attached_base(query):
    result = copy.deepcopy(query["result"])
    if query["kind"] == "limit" and "problem" not in result:
        result["problem"] = query.get("problem")
    return result


def expected_channel(query):
    return dict(parameter=query["result"]["parameter"], result=query["result"],
                derived_seed=query["seed"], threshold_mu_seed=query.get("threshold_mu_seed"))


def t1b_cases(selection=None, thickness=False, prepare_only=False):
    """Rebuild inputs; frozen morphology slopes are never regenerated truth.

    Thickness archives froze thresholds, not slopes: their fresh unchanged
    Python sensitivity referee is explicitly distinguished in row provenance.
    """
    from eab.adapters.tia2d import g1_morphology, g1_morphology_seed
    from eab.kernel2d.contacts import assemble_contact_set2
    from eab.kernel2d.sensitivity import build_limit_seed2, evaluate_sensitivity2
    from eab.kernel2d.statics import critical_parameter
    from eab2_c3l3_thickness import input_domain_failures
    if thickness:
        from eab2_c3l3_thickness import _records, _parameters
        entries, _ = _records()
        specs = [(name, _parameters(metadata["parameters"]), metadata, None) for name, _, metadata in entries]
    else:
        require(hashlib.sha256(T1B.read_bytes()).hexdigest() == T1B_SHA256, "T1b frozen expectation integrity")
        frozen = read_json(T1B)
        require(frozen["format"] == "eab2.c3l4.t1b.frozen.v1" and len(frozen["rows"]) == 36, "T1b frozen inventory")
        specs = []
        for i, row in enumerate(frozen["rows"]):
            parameters = {key: row[key] if key == "family" else int(row[key]) if key == "periods" else Q(row[key])
                          for key in ("family", "amplitude", "wavelength", "height", "tilt", "phase", "asymmetry", "periods")}
            specs.append((f"t1b/{i:02d}", parameters,
                dict(source=frozen["source"], source_sha256=frozen["source_sha256"], row_index=i), row))
    for name, parameters, metadata, frozen_row in specs:
        if selection is not None and name not in selection:
            continue
        geometry = g1_morphology(**parameters)
        model = geometry.assembly
        require(not input_domain_failures(model), "selected T1b geometry outside exact binary64 domain")
        contacts = assemble_contact_set2(model)
        before = time.perf_counter()
        base = critical_parameter(model, contact_set=contacts, max_steps=64 if thickness else 48)
        primal_seconds = time.perf_counter() - before
        base_wire = exact_wire(base)
        for field in ("lower_certificate", "upper_certificate", "threshold_certificate"):
            certificate = getattr(base, field)
            if certificate is not None:
                base_wire[field]["problem"] = exact_wire(certificate.problem)
        threshold = metadata["expected_threshold"] if thickness else frozen_row["mu_exact"]
        attained = metadata["expected_attained"] if thickness else frozen_row["attained"]
        require(base_wire["exact_threshold"] == threshold and base_wire["attained"] == attained, "T1b frozen exact threshold")
        if prepare_only:
            yield dict(case_id=name, family="thickness" if thickness else "t1b", model=model,
                contacts=exact_wire(contacts), bases=dict(critical=dict(kind="critical", max_steps=64 if thickness else 48,
                mu_max_bits="3ff0000000000000", result=base_wire)), queries=[], source=metadata)
            continue
        queries = []
        for index, parameter in enumerate(("amplitude", "tilt")):
            seed = None if base.threshold_certificate is None else g1_morphology_seed(base.threshold_certificate.problem, geometry, parameter)
            mu_seed = None if seed is None else build_limit_seed2(base.threshold_certificate.problem, mu_seed=1)
            valid = geometry.amplitude > 0 or parameter == "tilt"
            conditions = ["L1 contact skeleton unchanged", "fixed A/t parameter direction"]
            before = time.perf_counter()
            result = evaluate_sensitivity2(base, seed, parameter=parameter, threshold_mu_seed=mu_seed,
                positive_direction_valid=valid, negative_direction_valid=valid, validity_conditions=conditions)
            seconds = time.perf_counter() - before
            result = exact_wire(result)
            if frozen_row:
                expected = frozen_row["derivatives"][parameter]
                observed = dict(status=result["differentiability"], left=result["left_derivative"],
                    right=result["right_derivative"], reason=result["reason"])
            jets = geometry.vertex_seeds_amplitude if parameter == "amplitude" else geometry.vertex_seeds_tilt
            query = dict(kind="sensitivity", threshold_query_ref="critical", result=result,
                seed=exact_wire(seed), threshold_mu_seed=exact_wire(mu_seed),
                geometry_seed=geometry_jet(model, parameter, jets),
                direction_domain=dict(positive=valid, negative=valid), declared_validity_conditions=conditions,
                directional_values=directional_values(result), python_wallclock=dict(seconds=seconds),
                expectation_source="fresh Python referee; frozen threshold only" if thickness else "frozen T1b slopes and fresh Python full contract")
            queries.append((index, query))
            if frozen_row and observed != expected:
                query["erratum"] = dict(old=expected, new=observed, proof=result.get("branch_certificate"),
                                        reason="WO-C3L4-fix branch-complete/domain certificate contract")
        yield dict(case_id=name, family="thickness" if thickness else "t1b", model=model, contacts=exact_wire(contacts),
            bases=dict(critical=dict(kind="critical", max_steps=64 if thickness else 48,
                mu_max_bits="3ff0000000000000", result=base_wire)), queries=queries,
            source=metadata, python_primal_seconds=primal_seconds)


def verify_batch(batch, queries):
    count = len(queries)
    require(set(batch) == {"sensitivity_model", "parameter_count", "output_count", "channel_count", "jacobian_layout", "jacobian_shape", "channels", "jacobian"},
            "sensitivity batch fields")
    require(batch["sensitivity_model"] == "ideal_exact_2d", "sensitivity batch model")
    require(batch["parameter_count"] == batch["channel_count"] == count and batch["output_count"] == 1,
            "sensitivity batch dimensions")
    require(batch["jacobian_layout"] == "output_major_channel_minor" and batch["jacobian_shape"] == [1, count],
            "sensitivity Jacobian row-major shape")
    require(len(batch["channels"]) == len(batch["jacobian"]) == count, "sensitivity batch output sizes")
    for query, channel, value in zip(queries, batch["channels"], batch["jacobian"]):
        require(set(channel) == {"parameter", "result", "derived_seed", "threshold_mu_seed"}, "sensitivity channel fields")
        result = channel["result"]
        expected = result["directional_derivative"] if result["differentiability"] == "smooth" and result["quality"] == "exact_jet" else None
        require(value == expected, "unavailable or non-smooth Jacobian must be null")
        require(channel["parameter"] == query["result"]["parameter"], "batch channel order")


def check_frozen_implicit_query(query, channel):
    """Inventory precondition, not a restriction of the public caller ABI."""
    sides = sum(result["method"] == "implicit_certificate" for result in (query["result"], channel["result"]))
    if sides:
        require(not query.get("declared_tied_labels", []), "frozen implicit inventory requires empty caller tied labels")
    return sides


def run(dll, cases, output, selection=None):
    hashes = {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in [T1B] + list((ROOT / "tools").glob("eab2*.py"))
              + list((ROOT / "src/eab").rglob("*.py"))}
    start = time.perf_counter()
    rows, mismatches, families, kinds, label_dispositions = [], [], Counter(), Counter(), []
    errata, certificate_counts = [], {}
    proof_path = output.with_suffix(".certificates.jsonl")
    require(not proof_path.exists(), "use a fresh output for a complete differential run")
    proof_path.write_text("", encoding="utf-8")
    proof_count = 0
    verified_implicit_queries = verified_implicit_sides = 0
    seen = set()
    for case in cases:
        if case["family"].startswith(("formal/", "asymmetric/")):
            case = refresh_case(case)
        require(case["case_id"] not in seen, "duplicate selected sensitivity case")
        seen.add(case["case_id"])
        ah = ch = None
        tokens, actual_bases, completed = {}, {}, set()
        try:
            if dll:
                ah, ch = dll.assembly(case["model"]), None
                ch = dll.contacts(ah)
            for target in sorted({target_kind(q) for _, q in case["queries"]}):
                base_query = case["bases"][target]
                expected = attached_base(base_query)
                before = time.perf_counter()
                if dll:
                    tokens[target], actual = dll.base_query(ch, case["model"], base_query)
                else:
                    actual = expected
                cpp_primal_seconds = time.perf_counter() - before if dll else None
                # Some frozen limit queries keep problem beside result.
                base_dispositions = []
                delta = compare_l3(target, case["model"], case["contacts"], expected, actual, base_query, base_dispositions)
                require(not delta, "L4 bound primal/critical semantics: " + str(delta[:3]))
                floor = require_python_proof_floor(target, expected, actual)
                actual_bases[target] = actual
                selected = [(i, q) for i, q in case["queries"] if target_kind(q) == target]
                queries = [q for _, q in selected]
                before = time.perf_counter()
                if dll:
                    batch = dll.sensitivity(tokens[target], queries)
                    verify_batch(batch, queries)
                    channels = batch["channels"]
                else:
                    channels = [expected_channel(q) for q in queries]
                cpp_derivative_seconds = time.perf_counter() - before if dll else None
                for (index, query), channel in zip(selected, channels):
                    implicit_sides = check_frozen_implicit_query(query, channel)
                    dispositions = []
                    delta, derivative_floor = compare_sensitivity(case, actual, query, channel, dispositions)
                    verified_implicit_queries += bool(implicit_sides)
                    verified_implicit_sides += implicit_sides
                    for disposition in dispositions:
                        label_dispositions.append(dict(case_id=case["case_id"], query_index=index,
                            parameter=query["result"]["parameter"], **disposition))
                    result = channel["result"]
                    proof_refs = {}
                    for backend, value, proof_base in (("python", query["result"], expected), ("cpp", result, actual)):
                        if value.get("branch_certificate") is not None:
                            proof_count += 1
                            proof_refs[backend] = dict(file=proof_path.name, line=proof_count)
                            record = dict(case_id=case["case_id"], query_index=index, backend=backend,
                                bodies=raw_bodies(case["model"]), contacts=case["contacts"]["constraints"],
                                jet=query["geometry_seed"], labels=proof_base["threshold_certificate"]["problem"]["column_labels"],
                                critical=proof_base, result=value, mu_max_binary64=base_query["mu_max_bits"])
                            with proof_path.open("a", encoding="utf-8", newline="\n") as stream:
                                stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
                    red_flags = None
                    if query.get("asymmetric_probe"):
                        from eab2_c3l4_asymmetric import red_flag_check
                        red_flags = red_flag_check(case, query, result)
                    if "erratum" in query:
                        correction = {k: v for k, v in query["erratum"].items() if k != "proof"}
                        errata.append(dict(case_id=case["case_id"], query_index=index,
                                           parameter=result["parameter"], proof_reference=proof_refs.get("python"), **correction))
                    counts = certificate_counts.setdefault(case["family"], Counter())
                    for backend, value in (("python", query["result"]), ("cpp", result)):
                        certificate = value.get("branch_certificate")
                        if certificate is not None:
                            for direction in ("forward", "reverse"):
                                branch = certificate[direction]
                                counts[backend + "/candidates"] += branch.get("candidate_count", 0)
                                counts[backend + "/attempts"] += branch.get("attempts", 0)
                                counts[backend + "/" + branch["status"]] += 1
                                if branch.get("reason"):
                                    counts[backend + "/reason/" + branch["reason"]] += 1
                    row = dict(case_id=case["case_id"], family=case["family"], query_index=index,
                        parameter=result["parameter"], target=target, differentiability=result["differentiability"],
                        quality=result["quality"], method=result["method"], reason=result["reason"],
                        directional_values=directional_values(result), differences=delta,
                        exact_difference_quotient_red_flags=red_flags,
                        branch_proof_references=proof_refs,
                        frozen_derived_seed_verified=query.get("frozen_derived_seed_verified", False),
                        threshold_proof_dispositions=base_dispositions,
                        threshold_label_disposition=dispositions[0]["classification"] if dispositions else None,
                        proof_capability_floor=derivative_floor,
                        python_seconds=query.get("python_wallclock", {}).get("seconds"),
                        python_timing="same-process live sensitivity with prebuilt primal/critical result",
                        cpp_primal_seconds=cpp_primal_seconds, cpp_batch_seconds=cpp_derivative_seconds,
                        cpp_batch_channels=len(queries), expectation_source=query.get("expectation_source", "frozen tia2d-2"))
                    rows.append(row)
                    families[case["family"]] += 1
                    kinds[result["differentiability"]] += 1
                    completed.add(index)
                    if delta:
                        mismatches.append(dict(case_id=case["case_id"], query_index=index, differences=delta))
        except Exception as error:
            mismatches.append(dict(case_id=case["case_id"], error=type(error).__name__ + ": " + str(error)))
        finally:
            if dll:
                for token in tokens.values():
                    dll.check(dll.result_destroy(dll.context, token), "base result destroy")
                if ch is not None:
                    dll.check(dll.contact_set2_destroy(dll.context, ch), "contact_set2_destroy")
                if ah is not None:
                    dll.check(dll.assembly2_destroy(dll.context, ah), "assembly2_destroy")
        if len(completed) != len(case["queries"]):
            mismatches.append(dict(case_id=case["case_id"], error="selected sensitivity query omitted",
                                   expected=len(case["queries"]), actual=len(completed)))
        progress = dict(case_id=case["case_id"], queries=len(rows), mismatch=len(mismatches), seconds=time.perf_counter() - start)
        output.with_suffix(".progress.json").write_text(json.dumps(progress) + "\n", encoding="utf-8")
        print(json.dumps(progress), flush=True)
    unchanged = all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest for name, digest in hashes.items())
    if not seen or (selection is not None and seen != selection):
        mismatches.append(dict(error="missing selected sensitivity cases", expected=sorted(selection or ()), actual=sorted(seen)))
    if not unchanged:
        mismatches.append(dict(error="source changed during run; invalid evidence"))
    exclusions = []
    if families["thickness"]:
        from eab2_c3l3_thickness import thickness_inventory
        inventory = thickness_inventory()
        exclusions = [dict(classification="ABI_INPUT_DOMAIN_EXCLUSION", source_summary=inventory["source_summary"],
            input_fixture=inventory["input_fixture"], **entry) for entry in inventory["excluded"]]
    last = ("C3L4_DIFF" if dll else "C3L4_FIXTURE_AUDIT") + f" sensitivity={len(rows)} mismatch={len(mismatches)}"
    summary = dict(format="eab2.c3l4.differential.v1", complete=True, cpp_executed=dll is not None,
        dll_sha256=dll.sha256 if dll else None, build_identity=dll.identity if dll else None,
        source_sha256=hashes, source_pre_post_equal=unchanged, family_counts=dict(families),
        branch_proof_archive=dict(file=proof_path.name, records=proof_count, sha256=hashlib.sha256(proof_path.read_bytes()).hexdigest()),
        branch_certificate_statistics={key: dict(value) for key, value in certificate_counts.items()}, errata=errata,
        differentiability_counts=dict(kinds), queries=rows, mismatches=mismatches,
        threshold_label_comparison=dict(scope="critical branch_certificate (historical implicit candidates separately verified)", non_threshold_labels="strict",
            verified_implicit_queries=verified_implicit_queries, verified_sides=verified_implicit_sides,
            caller_tied_labels="empty in frozen implicit queries; public ABI caller-label contract unchanged",
            disposition_count=len(label_dispositions), dispositions=label_dispositions),
        abi_input_domain_exclusions=exclusions,
        proof_capability_floor=dict(checked_fields=sum(row["proof_capability_floor"]["checked"] for row in rows), exceptions=[]),
        timing_scope="Informational: prebuilt-contact primal separately from live batched derivative ABI+JSON; not a standalone cold-start benchmark",
        seconds=time.perf_counter() - start, last_line=last)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(last, flush=True)
    return int(bool(mismatches))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dll", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--family", choices=("formal", "t1b", "thickness", "branch", "asymmetric", "all"), default="all")
    parser.add_argument("--case", action="append")
    parser.add_argument("--fixture-audit-only", action="store_true")
    args = parser.parse_args()
    require(args.dll is not None or args.fixture_audit_only, "--dll required")
    selection = set(args.case) if args.case else None
    args.output.parent.mkdir(parents=True, exist_ok=True)
    def cases():
        # Exercise the new branch/asymmetric coverage before the long frozen
        # replay. Every selected family still runs exactly once in an all run.
        if args.family in ("asymmetric", "all"):
            from eab2_c3l4_asymmetric import asymmetric_cases
            yield from asymmetric_cases(selection=selection)
        if args.family in ("branch", "all"):
            from eab2_c3l4_branches import branch_cases
            yield from branch_cases(selection)
        if args.family in ("formal", "all"):
            yield from formal_cases(selection)
        if args.family in ("t1b", "all"):
            yield from t1b_cases(selection)
        if args.family in ("thickness", "all"):
            yield from t1b_cases(selection, thickness=True)
    dll = None
    try:
        if not args.fixture_audit_only:
            from eab2_c3l4_abi import C3L4Dll
            dll = C3L4Dll(args.dll)
        return run(dll, cases(), args.output, selection)
    finally:
        if dll is not None:
            dll.close()


if __name__ == "__main__":
    raise SystemExit(main())
