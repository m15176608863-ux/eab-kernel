"""C3-L3 independent geometry/certificate differential gate.

The frozen reader parses original binary64 bits, not an encoder shared with
C++. Contact selection is supplied by the accepted Python referee. Force
columns are reconstructed from labelled original CCW edges and physical DOF
anchors; exported tangents and matrices are never the arithmetic oracle.
Nonunique primal/dual/ray and polynomial bases are checked mathematically.
"""
from __future__ import annotations

import argparse
from collections import Counter
import ctypes as C
from dataclasses import replace
from fractions import Fraction as Q
import gzip
import hashlib
import json
import math
from pathlib import Path
import random
import struct
import sys
import time

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src/eab").is_dir())
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
from eab2_c3l1_diff import (FORMAL, _private_ids, decode_assembly, differences,
    double_bits, geometry_constraint_rows, geometry_dofs, geometry_velocity_row,
    rational, read_json, require, vec, mat, wire, dot, verify_optimum, verify_cone)
from eab2_c3l1_abi import (AbiInfo, Dll, ExactResult, Handle, HEADER, U32, U64,
                         initialized, mathematical_status)


def exact_wire(value):
    if isinstance(value, float):
        return exact_wire(Q(value))
    result = wire(value)
    if isinstance(result, dict):
        if {"mu_min_binary64", "mu_max_binary64", "exact_mu_min", "exact_mu_max"} <= set(result):
            # Original binary64 input values are display fields, not derived
            # rational quantities. Preserve them alongside their exact binding.
            return {k: v if k in ("mu_min", "mu_max") else exact_wire(v) for k, v in result.items()}
        return {k: exact_wire(v) for k, v in result.items()}
    if isinstance(result, list):
        return [exact_wire(v) for v in result]
    return result


def formal_cases(selection=None):
    """Read every selected original record, checking hashes and fragment cover."""
    manifest = read_json(FORMAL / "manifest.json")
    for entry in manifest["cases"]:
        if selection is not None and entry["case_id"] not in selection:
            continue
        source, queries = None, {}
        for part in entry["parts"]:
            raw = gzip.decompress((FORMAL / (part["path"] + ".gz")).read_bytes())
            require(len(raw) == part["bytes"] and hashlib.sha256(raw).hexdigest() == part["sha256"],
                    "formal integrity: " + part["path"])
            record = read_json(raw)
            require(record["case_id"] == entry["case_id"], "formal case ID")
            require(source is None or source == record["assembly"], "fragment input mismatch")
            source = record["assembly"]
            require(len(part["query_indices"]) == len(record["queries"]), "fragment count")
            for index, query in zip(part["query_indices"], record["queries"]):
                require(index not in queries, "duplicate query index")
                queries[index] = query
        require(set(queries) == set(range(entry["query_count"])), "missing formal query")
        model = decode_assembly(source)
        ids = [body.body_id for body in model.bodies]
        contacts = next(_private_ids(q["result"], ids) for q in queries.values() if q["kind"] == "assembly")
        selected = []
        for index, query in sorted(queries.items()):
            if query["kind"] in ("limit", "critical"):
                selected.append((index, query, query["result"]))
        require(len(selected) == 2, "formal must contain limit and critical")
        family = record.get("family_parameters", {}).get("family", "coverage")
        yield entry["case_id"], "formal/" + str(family), model, contacts, selected


def formal_query(name, kind="limit"):
    """I/O-only convenience loader, not an exemption of a numerical oracle.

    Original bits/rational parsing stays in formal_cases/decode_assembly;
    independent wrench, LP and polynomial arithmetic stays in the verifiers.
    """
    _, _, model, contacts, queries = next(formal_cases({name}))
    query = next(q for _, q, _ in queries if q["kind"] == kind)
    return model, contacts, query, query["result"]


def rebuilt_problem(model, contacts, mu, column_labels=None):
    """Reconstruct exact A,b,c from raw polygon edges and anchor kinematics.

    The accepted L1 labels select a contact. Its tangent is derived again from
    original vertex IDs; both bodies receive opposite wrenches. For rotation,
    using (p-anchor) cross g is algebraically the projection of the wrench
    about the frozen reference, avoiding either implementation's projector.
    """
    constraints = contacts["constraints"]
    geometry_constraint_rows(model, constraints)
    dofs = geometry_dofs(model)
    natural_labels, natural_columns = [], []
    for item in constraints:
        a, b = item["a"], item["b"]
        point = vec(item["point"])
        edge_body, edge_ids = item["label"][-2:]
        side = a if model.bodies[a].body_id == edge_body else b
        body = model.bodies[side]
        k = body.vertex_ids.index(edge_ids[0])
        p, q = body.vertices[k], body.vertices[(k + 1) % len(body.vertices)]
        tangent = (q[0] - p[0], q[1] - p[1])
        if side == b:
            tangent = (-tangent[0], -tangent[1])
        for sign in (-1, 1):
            g = (-tangent[1] + sign * mu * tangent[0], tangent[0] + sign * mu * tangent[1])
            natural_columns.append(geometry_velocity_row(model, a, b, point, g, dofs))
            natural_labels.append([item["label"], sign])
    live, dead = [], []
    for i, k in dofs:
        body = model.bodies[i]
        for load, target in ((body.live, live), (body.dead, dead)):
            value = load[k]
            if k == 2:
                offset = tuple(a - o for a, o in zip(body.dof_anchor, body.reference_point))
                value -= offset[0] * load[1] - offset[1] * load[0]
            target.append(Q(value))
    natural_columns.append(tuple(live))
    natural_labels.append(["alpha", 1])
    labels = natural_labels if column_labels is None else column_labels
    def label_key(label):
        return json.dumps(label, separators=(",", ":"), ensure_ascii=True)
    indexed = {label_key(label): col for label, col in zip(natural_labels, natural_columns)}
    require(len(indexed) == len(natural_labels), "duplicate physical column label")
    require(Counter(map(label_key, labels)) == Counter(indexed.keys()), "column labels differ from original contacts")
    columns = tuple(indexed[label_key(label)] for label in labels)
    return dict(A=tuple(tuple(col[i] for col in columns) for i in range(len(dofs))),
                b=tuple(-v for v in dead),
                c=tuple(Q(label == ["alpha", 1]) for label in labels),
                row_labels=[[model.bodies[i].body_id, k] for i, k in dofs],
                column_labels=labels,
                reference_points=exact_wire(tuple(b.reference_point for b in model.bodies)),
                dof_anchors=exact_wire(tuple(b.dof_anchor for b in model.bodies)),
                mu=mu, profile="profile1", sensitivity_model="ideal_exact_2d")


def checked_problem(model, contacts, mu, exported=None):
    problem = rebuilt_problem(model, contacts, Q(mu), exported.get("column_labels") if exported else None)
    if exported is not None:
        for key, expected in problem.items():
            require(key in exported and exported[key] == exact_wire(expected), "original geometry problem mismatch: " + key)
        require(set(exported) == set(problem), "unknown problem field")
    return problem


def verify_limit(model, contacts, mu, result, exported=None):
    status = result["mathematical_status"]
    if status not in ("OPTIMAL", "INFEASIBLE", "UNBOUNDED"):
        require(result.get("exact_value") is None, "unresolved is not zero capacity")
        require(all(result.get(k) is None for k in ("exact_x", "exact_y", "feasible_point", "improving_ray", "farkas")),
                "unresolved must not carry a mechanical certificate")
        require(result.get("mechanism") is None, "unresolved must not carry a mechanism")
        return None
    require(contacts["mathematical_status"] == "RESOLVED" and model.completeness == "complete", "unresolved mechanical solve")
    problem = checked_problem(model, contacts, mu, result.get("problem", exported))
    A, b, c = problem["A"], problem["b"], problem["c"]
    if status == "OPTIMAL":
        x, y = vec(result["exact_x"]), vec(result["exact_y"])
        verify_optimum(A, b, c, x, y, rational(result["exact_value"]))
        if "mechanism" in result:
            require(result["mechanism"] == result["exact_y"], "mechanism attachment must equal verified exact dual")
        alpha = c.index(Q(1))
        require(sum(A[i][alpha] * y[i] for i in range(len(b))) >= 1, "mechanism drive must be at least one")
    elif status == "UNBOUNDED":
        require(result.get("mechanism") is None, "unbounded must not carry a bounded mechanism")
        x, ray = vec(result["feasible_point"]), vec(result["improving_ray"])
        require(len(x) == len(c) == len(ray), "unbounded dimensions")
        require(all(v >= 0 for v in x + ray), "unbounded nonnegative point/ray")
        require(all(dot(row, x) == rhs for row, rhs in zip(A, b)), "unbounded feasible point")
        require(all(dot(row, ray) == 0 for row in A), "unbounded kernel ray")
        require(dot(c, ray) == 1, "unbounded alpha normalization")
        require(result["exact_value"] is None, "unbounded is not finite capacity")
    else:
        require(result.get("mechanism") is None, "infeasible must not carry a mechanism")
        y = vec(result["farkas"])
        require(len(y) == len(b) and dot(b, y) == 1, "Farkas normalization")
        require(all(sum(A[i][j] * y[i] for i in range(len(b))) <= 0 for j in range(len(c))), "Farkas columns")
    return problem


def p_trim(p):
    p = tuple(p)
    while len(p) > 1 and p[-1] == 0:
        p = p[:-1]
    return p or (Q(0),)


def p_eval(p, x):
    value = Q(0)
    for a in reversed(p):
        value = value * x + a
    return value


def p_div(a, b):
    a, b = list(p_trim(a)), p_trim(b)
    require(any(b), "zero polynomial divisor")
    quotient = [Q(0)] * max(1, len(a) - len(b) + 1)
    while any(a) and len(a) >= len(b):
        j, factor = len(a) - len(b), a[-1] / b[-1]
        quotient[j] += factor
        for i, value in enumerate(b):
            a[i + j] -= factor * value
        a = list(p_trim(a))
    return p_trim(quotient), p_trim(a)


def root_count(poly, lo, hi):
    """Independent rational Sturm chain, only nonroot open endpoints."""
    poly = p_trim(poly)
    require(p_eval(poly, lo) != 0 and p_eval(poly, hi) != 0, "Sturm endpoint root")
    if len(poly) == 1:
        return 0
    chain = [poly, p_trim(tuple(Q(i) * poly[i] for i in range(1, len(poly))))]
    while any(chain[-1]):
        _, remainder = p_div(chain[-2], chain[-1])
        if not any(remainder):
            break
        chain.append(tuple(-v for v in remainder))
    def variations(x):
        signs = []
        for p in chain:
            v = p_eval(p, x)
            if v:
                signs.append(v > 0)
        return sum(a != b for a, b in zip(signs, signs[1:]))
    return variations(lo) - variations(hi)


def determinant_solve(matrix, rhs):
    """Numeric Fraction Gaussian elimination, unrelated to production LP."""
    n = len(matrix)
    work = [list(row) + [rhs[i]] for i, row in enumerate(matrix)]
    determinant = Q(1)
    for k in range(n):
        p = next((i for i in range(k, n) if work[i][k]), None)
        if p is None:
            return Q(0), None
        if p != k:
            work[k], work[p] = work[p], work[k]
            determinant = -determinant
        value = work[k][k]
        determinant *= value
        work[k] = [v / value for v in work[k]]
        for i in range(n):
            if i != k:
                factor = work[i][k]
                work[i] = [v - factor * w for v, w in zip(work[i], work[k])]
    return determinant, tuple(row[-1] for row in work)


def verify_branch(model, contacts, branch, labels=None):
    """Certify polynomial identities at more exact points than their degree.

    One independent rational elimination per point supplies both determinant
    and all Cramer ratios. Degree bounds plus m+2 distinct nonzero-det samples
    prove identities, not approximate agreement at the exported sample.
    """
    zero = rebuilt_problem(model, contacts, Q(0), labels)
    one = rebuilt_problem(model, contacts, Q(1), labels)
    A0, A1, c = zero["A"], one["A"], zero["c"]
    m, n = len(A0), len(c)
    basis = branch["basis"]
    require(len(basis) == m and len(set(basis)) == m and all(type(j) is int and 0 <= j < n for j in basis), "critical basis dimensions")
    determinant, numerators = vec(branch["determinant"]), tuple(vec(p) for p in branch["numerators"])
    require(any(determinant) and len(p_trim(determinant)) <= m + 1, "critical determinant degree")
    require(all(len(p_trim(p)) <= m + 2 for p in numerators), "critical numerator degree")
    kind = branch["kind"]
    require(kind in ("mechanism", "improving_ray"), "critical branch kind")
    if kind == "mechanism":
        require(branch["entering"] is None and len(numerators) == n, "mechanism polynomial shape")
        require(branch["labels"] == zero["column_labels"], "mechanism labels")
    else:
        entering = branch["entering"]
        require(type(entering) is int and entering == c.index(Q(1)) and entering not in basis, "improving entering alpha")
        require(len(numerators) == m, "ray polynomial shape")
        require(branch["labels"] == [zero["column_labels"][j] for j in basis], "ray labels")
    accepted = 0
    for parameter in range(2 * m + 4):
        A = tuple(tuple(a + parameter * (b - a) for a, b in zip(row, other)) for row, other in zip(A0, A1))
        B = tuple(tuple(row[j] for j in basis) for row in A)
        if kind == "mechanism":
            transposed = tuple(tuple(B[i][j] for i in range(m)) for j in range(m))
            det, y = determinant_solve(transposed, tuple(c[j] for j in basis))
            values = None if y is None else tuple(sum(A[i][j] * y[i] for i in range(m)) - c[j] for j in range(n))
        else:
            det, values = determinant_solve(B, tuple(-row[entering] for row in A))
        require(p_eval(determinant, Q(parameter)) == det, "critical determinant identity")
        if not det:
            continue
        require(all(p_eval(p, Q(parameter)) == value * det for p, value in zip(numerators, values)), "critical Cramer polynomial identity")
        accepted += 1
        if accepted == m + 2:
            break
    require(accepted == m + 2, "insufficient exact polynomial identity samples")
    sample = rational(branch["sample_parameter"])
    denominator = p_eval(determinant, sample)
    require(denominator != 0, "critical sample pole")
    values = tuple(p_eval(p, sample) / denominator for p in numerators)
    require(vec(branch["sample_values"]) == values and all(v >= 0 for v in values), "critical branch sample values")


def branch_signs(branch, lo, hi):
    if branch is None or lo > hi:
        return None
    if lo == hi:
        return []
    sample = (lo + hi) / 2
    polynomials = [vec(branch["determinant"])] + [vec(p) for p in branch["numerators"]]
    denominator = p_eval(polynomials[0], sample)
    proofs = []
    for index, polynomial in enumerate(polynomials):
        if not any(polynomial):
            if index == 0:
                return None
            proofs.append([index - 1, [0, 0], "0/1"])
            continue
        orders, reduced = [], polynomial
        for point in (lo, hi):
            order = 0
            while len(reduced) > 1 and p_eval(reduced, point) == 0:
                reduced, remainder = p_div(reduced, (-point, Q(1)))
                require(not any(remainder), "endpoint exact factor")
                order += 1
            orders.append(order)
        if root_count(reduced, lo, hi):
            return None
        value = p_eval(polynomial, sample) if index == 0 else p_eval(polynomial, sample) / denominator
        if index and value < 0:
            return None
        proofs.append(["denominator" if index == 0 else index - 1, orders, exact_wire(value)])
    return proofs


def endpoint(result, name):
    value, bits = result.get(name), result.get(name + "_bits")
    if bits is not None:
        q = Q(double_bits(bits))
        require(value is None or rational(value) == q, "critical endpoint bits/rational disagreement")
        return q
    if value is None:
        return None
    q = rational(value)
    require(math.isfinite(float(q)) and Q(float(q)) == q, "critical endpoint is not binary64")
    return q


def verify_critical(model, contacts, result):
    if "search_domain" in result:
        from eab2_branch_verify import check_domain
        check_domain(result["search_domain"])
    lo, hi = endpoint(result, "mu_lo"), endpoint(result, "mu_hi")
    if lo is not None and hi is not None:
        require(Q(0) <= lo <= hi, "invalid critical bracket order")
        require(result.get("upper_certificate") is not None
                and result["upper_certificate"]["mathematical_status"] == "UNBOUNDED",
                "critical upper endpoint needs an unbounded certificate")
        if lo < hi:
            require(result.get("lower_certificate") is not None
                    and result["lower_certificate"]["mathematical_status"] in ("OPTIMAL", "INFEASIBLE"),
                    "critical lower endpoint needs a bounded or Farkas certificate")
    for key, parameter in (("lower_certificate", lo), ("upper_certificate", hi)):
        if result.get(key) is not None:
            require(parameter is not None, "certificate without endpoint")
            verify_limit(model, contacts, parameter, result[key])
    labels = None
    for key in ("lower_certificate", "upper_certificate"):
        cert = result.get(key)
        if cert and cert.get("problem"):
            labels = cert["problem"]["column_labels"]
            break
    require("critical_polynomials" in result and isinstance(result["critical_polynomials"], list),
            "critical polynomial list is required")
    roles = set()
    for branch in result["critical_polynomials"]:
        role = branch["kind"]
        require(role not in roles, "duplicate critical polynomial role")
        roles.add(role)
        sample_endpoint = lo if role == "mechanism" else hi if role == "improving_ray" else None
        require(sample_endpoint is not None and rational(branch["sample_parameter"]) == sample_endpoint,
                "critical branch sample must equal its certified endpoint")
        verify_branch(model, contacts, branch, labels)
    threshold = result.get("exact_threshold")
    if threshold is None:
        require(result["attained"] is None and result.get("threshold_certificate") is None
                and result.get("threshold_proof") is None and result.get("threshold_proof_reason") is None,
                "uncertified threshold must retain null openness")
        return
    threshold = rational(threshold)
    require(type(result["attained"]) is bool, "exact threshold openness")
    require(lo is not None and hi is not None and lo <= threshold <= hi, "threshold outside certified bracket")
    cert = result["threshold_certificate"]
    require(cert is not None, "exact threshold needs original LP certificate")
    verify_limit(model, contacts, threshold, cert)
    require(cert["mathematical_status"] == ("UNBOUNDED" if result["attained"] else "OPTIMAL"), "threshold openness/certificate disagreement")
    proof = result.get("threshold_proof")
    if lo == hi == threshold == 0 and result["attained"]:
        require(proof is None and result.get("threshold_proof_reason") is None,
                "direct closed zero must not invent a continuation proof")
        return
    require(proof is not None and rational(proof["exact_threshold"]) == threshold and proof["attained"] == result["attained"], "threshold proof header")
    require(proof.get("reason") == result.get("threshold_proof_reason") == "exact_basis_continuation",
            "threshold continuation reason")
    require(vec(proof["lower_interval"]) == (lo, threshold) and vec(proof["upper_interval"]) == (threshold, hi), "threshold proof intervals")
    for side, start, end in (("lower", lo, threshold), ("upper", threshold, hi)):
        branch = proof[side + "_basis"]
        if branch is not None:
            require(branch["kind"] == ("mechanism" if side == "lower" else "improving_ray"),
                    "threshold continuation branch role")
            require(rational(branch["sample_parameter"]) == (lo if side == "lower" else hi),
                    "threshold continuation sample endpoint")
            verify_branch(model, contacts, branch, labels)
        require(proof[side + "_signs"] == branch_signs(branch, start, end), "threshold one-sided Sturm signs")
    if result["attained"]:
        require(threshold == 0 or proof["lower_signs"] is not None, "closed threshold needs bounded continuation")
    else:
        require(not any(rebuilt_problem(model, contacts, 0)["b"]) and threshold < hi and proof["upper_signs"] is not None,
                "open threshold needs feasible point and improving continuation")


NONUNIQUE = {"exact_x", "exact_y", "feasible_point", "improving_ray", "farkas"}


def semantic(value):
    if not isinstance(value, dict):
        return value
    result = {}
    for key, item in value.items():
        if key in ("basis", "queries", "problem", "mu_lo_bits", "mu_hi_bits", "threshold_proof", "mechanism"):
            continue
        if key == "critical_polynomials":
            result[key] = bool(item)
        elif key in NONUNIQUE:
            result[key] = "verified" if item is not None else None
        elif key in ("lower_certificate", "upper_certificate", "threshold_certificate"):
            result[key] = semantic(item)
        elif key == "validity_conditions":
            result[key] = sorted(item)
        elif key == "search_domain" and item is not None:
            # JSON's 1 and 1.0 denote the same exactly bound display number;
            # bit patterns and exact endpoints were independently checked.
            result[key] = {name: exact_wire(Q(value)) if name in ("mu_min", "mu_max") else value
                           for name, value in item.items()}
        elif key not in ("mu_lo", "mu_hi"):
            result[key] = item
    if "attained" in value:
        result["mu_lo"], result["mu_hi"] = exact_wire(endpoint(value, "mu_lo")), exact_wire(endpoint(value, "mu_hi"))
    return result


def verify_threshold_certificate_contract(contacts, certificate):
    """Guard only the metadata hidden by a one-sided proof-availability waiver.

    Arithmetic has already passed verify_critical/verify_limit on the original
    geometry. These are the successful profile1 wire contract and mutually
    exclusive payloads, not a second arithmetic oracle or a basis equality gate.
    """
    fields = {"call_status", "mathematical_status", "display_status", "exact_value",
        "exact_x", "exact_y", "feasible_point", "improving_ray", "farkas", "problem",
        "reason", "basis", "sensitivity_model", "validity_conditions"}
    require(fields <= set(certificate) <= fields | {"mechanism"}, "threshold certificate contract: fields")
    status = certificate["mathematical_status"]
    require(status in ("OPTIMAL", "UNBOUNDED"), "threshold certificate contract: status")
    require(certificate["call_status"] == "OK", "threshold certificate contract: call_status")
    require(certificate["display_status"] == ("EXACT" if status == "OPTIMAL" else "NOT_APPLICABLE"),
            "threshold certificate contract: display_status")
    require(certificate["sensitivity_model"] == "ideal_exact_2d", "threshold certificate contract: sensitivity_model")
    require(certificate["reason"] is None, "threshold certificate contract: reason")
    conditions = ["true_vv_excluded_from_statics"] if any(
        point["fp_type"] == "REDUNDANT_PROVED" for point in contacts["points"]) else []
    require(certificate["validity_conditions"] == conditions, "threshold certificate contract: validity_conditions")
    require(certificate["problem"] is not None, "threshold certificate contract: problem")
    excluded = ("feasible_point", "improving_ray", "farkas") if status == "OPTIMAL" else ("exact_x", "exact_y", "farkas")
    require(all(certificate[field] is None for field in excluded), "threshold certificate contract: exclusive payload")


def compare(kind, model, contacts, expected, actual, query=None, dispositions=None):
    if kind == "limit":
        mu = model.mu
        if query and "mu" in query:
            mu = Q(query["mu"])
        verify_limit(model, contacts, mu, expected, (query or {}).get("problem"))
        verify_limit(model, contacts, mu, actual)
    else:
        if query is not None:
            # Frozen pre-fix records have no additive original-domain field.
            # Bind that field from the frozen INPUT, never the C++ bracket.
            domain = original_search_domain(query)
            if "search_domain" not in expected:
                expected = dict(expected, search_domain=domain)
            require(expected["search_domain"] == domain, "Python original search domain input binding")
            require(actual.get("search_domain") == domain, "C++ original search domain input binding")
        verify_critical(model, contacts, expected)
        verify_critical(model, contacts, actual)
    left, right = semantic(expected), semantic(actual)
    if kind == "critical" and ((expected["exact_threshold"] is None) != (actual["exact_threshold"] is None)):
        # Proof availability depends on a nonunique LP basis. This is a local,
        # evidence-backed comparison disposition, never a blanket status waiver.
        proved_side = "python" if expected["exact_threshold"] is not None else "cpp"
        proved = expected if proved_side == "python" else actual
        verify_threshold_certificate_contract(contacts, proved["threshold_certificate"])
        affected = ("exact_threshold", "attained", "threshold_certificate", "threshold_proof_reason")
        disposition = dict(classification="verified_nonunique_basis_enrichment", proved_side=proved_side,
            exact_threshold=proved["exact_threshold"], attained=proved["attained"],
            verification="original_geometry_LP_polynomial_identities_and_one_sided_Sturm",
            threshold_certificate_contract_verified=True,
            normalized_fields=list(affected),
            python_threshold=expected["exact_threshold"], cpp_threshold=actual["exact_threshold"],
            python_attained=expected["attained"], cpp_attained=actual["attained"],
            mu_lo=exact_wire(endpoint(proved, "mu_lo")), mu_hi=exact_wire(endpoint(proved, "mu_hi")))
        for field in affected:
            left[field] = right[field] = "independently verified proof availability"
        if dispositions is not None:
            dispositions.append(disposition)
    return differences(left, right)


def original_search_domain(query):
    encoded = query.get("mu_max_bits", "3ff0000000000000").lower()
    maximum = double_bits(encoded)
    return dict(mu_min=0.0, mu_max=maximum, exact_mu_min="0/1", exact_mu_max=exact_wire(Q(maximum)),
                mu_min_binary64="0000000000000000", mu_max_binary64=encoded)


def require_python_proof_floor(kind, expected, actual):
    """Keep frozen proof capability, separately from symmetric proof validity.

    Call only after independent certificate verification. Nonunique witnesses
    may differ, but a previously certified exact threshold/directional slope
    must not silently become null. No blanket or wildcard exception exists.
    """
    fields = ("exact_threshold",) if kind == "critical" else (
        "directional_derivative", "right_derivative", "left_derivative") if kind == "sensitivity" else ()
    required = [field for field in fields if expected.get(field) is not None
                and (kind != "sensitivity" or expected.get("quality") == "exact_jet")]
    for field in required:
        require(actual.get(field) is not None, "frozen Python proof capability regression: " + field)
    if required and kind == "sensitivity":
        require(actual.get("quality") == "exact_jet", "frozen Python proof capability regression: quality")
    return dict(required_fields=required, checked=len(required), exceptions=[])


class BodyLoad(C.Structure):
    _fields_ = [("dead_bits", U64 * 3), ("live_bits", U64 * 3)]


class LimitInput(C.Structure):
    _fields_ = HEADER + [("mu_bits", U64), ("body_count", U64), ("body_stride", U64), ("loads", C.POINTER(BodyLoad))]


class CriticalInput(C.Structure):
    _fields_ = HEADER + [("mu_max_bits", U64), ("max_steps", U64), ("body_count", U64), ("body_stride", U64),
                        ("loads", C.POINTER(BodyLoad)), ("parameter", U32), ("reserved", U32)]


class C3L3Info(C.Structure):
    _fields_ = HEADER + [(name, U32) for name in ("body_load2_size", "limit2_input_size", "critical_parameter_input_size", "reserved")]


def bits(value):
    f = float(value)
    require(math.isfinite(f) and Q(f) == Q(value), "ABI input must be exactly binary64")
    return struct.unpack(">Q", struct.pack(">d", f))[0]


class C3L3Dll(Dll):
    def __init__(self, path):
        super().__init__(path)
        for name, args in (("get_c3l3_abi_info", [C.POINTER(C3L3Info)]),
                           ("solve_limit2", [Handle, Handle, C.POINTER(LimitInput), C.POINTER(ExactResult)]),
                           ("critical_parameter", [Handle, Handle, C.POINTER(CriticalInput), C.POINTER(ExactResult)])):
            f = getattr(self.lib, "eab2_" + name)
            f.argtypes, f.restype = args, U32
            setattr(self, name, f)
        info = initialized(AbiInfo)
        info.requested_capabilities = 16384 | 32768
        self.check(self.get_abi_info(C.byref(info)), "get_abi_info")
        require(info.unsupported_capabilities == 0, "missing C3-L3 capabilities")
        sizes = initialized(C3L3Info)
        self.check(self.get_c3l3_abi_info(C.byref(sizes)), "get_c3l3_abi_info")
        require(sizes.body_load2_size == C.sizeof(BodyLoad) and sizes.limit2_input_size == C.sizeof(LimitInput)
                and sizes.critical_parameter_input_size == C.sizeof(CriticalInput), "C3-L3 ABI size mismatch")

    def exact(self, function, *args):
        output = initialized(ExactResult)
        self.check(function(self.context, *args, C.byref(output)), function.__name__)
        try:
            require(output.data and output.byte_count > 0, "empty exact output")
            result = read_json(C.string_at(output.data, output.byte_count))
            self.check(output.call_status, "exact result")
            state = result.get("mathematical_status", result.get("status"))
            expected = 1 if state == "CERTIFIED" else mathematical_status(state)
            require(output.mathematical_status == expected, "ABI mathematical status mismatch")
            return result
        finally:
            self.check(self.result_destroy(self.context, output.result), "result_destroy")

    def l3_query(self, contacts, model, query):
        loads = (BodyLoad * len(model.bodies))(*(BodyLoad((U64 * 3)(*(bits(x) for x in body.dead)),
                     (U64 * 3)(*(bits(x) for x in body.live))) for body in model.bodies))
        if query["kind"] == "limit":
            request = initialized(LimitInput)
            request.mu_bits = bits(Q(query.get("mu", model.mu)))
            function = self.solve_limit2
        else:
            request = initialized(CriticalInput)
            request.mu_max_bits = int(query.get("mu_max_bits", "3ff0000000000000"), 16)
            request.max_steps = query.get("max_steps", 64)
            request.parameter = 1 if query.get("param", "mu") == "mu" else 0
            function = self.critical_parameter
        request.body_count, request.body_stride, request.loads = len(loads), C.sizeof(BodyLoad), loads
        if query["kind"] == "critical" and query.get("param", "mu") != "mu":
            output = initialized(ExactResult)
            C.memset(C.byref(output), 0xA5, C.sizeof(output))
            output.struct_size, output.abi_version = C.sizeof(output), 1
            before = bytes(output)
            status = function(self.context, contacts, C.byref(request), C.byref(output))
            require(status == 3, "unsupported parameter must return ABI UNSUPPORTED")
            require(bytes(output) == before, "unsupported request changed output or published token")
            return dict(abi_call_status=status, output_unchanged=True, result_published=False)
        return self.exact(function, contacts, C.byref(request))


def fresh_case(name, family, model, queries):
    from eab.kernel2d.contacts import assemble_contact_set2
    contacts = assemble_contact_set2(model)
    return name, family, model, exact_wire(contacts), [(i, query, None) for i, query in enumerate(queries)]


def t1b_cases(selection=None):
    from eab.adapters.tia2d import g1_morphology
    from tia2d_t1b_morphology import scan_parameters
    mandatory = {1, 2, 5, 8, 10, 11, 13, 14, 16, 17, 19, 22, 30}
    exact_targets = {8: ("1/16", False), 13: ("131009/2097408", True),
                     16: ("98283/2097664", True), 17: ("7/128", False),
                     30: ("326839/6291456", True)}
    bracket_targets = {1, 2, 5, 10, 11, 14, 19, 22}
    for i, parameters in enumerate(scan_parameters()):
        if selection == "required" and i not in mandatory:
            continue
        model = g1_morphology(**parameters).assembly
        query = dict(kind="critical", max_steps=48)
        if i in exact_targets:
            query["expected_threshold"], query["expected_attained"] = exact_targets[i]
        if i in bracket_targets:
            query["expected_threshold"], query["expected_attained"] = None, None
            query["expected_max_bracket_width"] = "1/1099511627776"
        yield fresh_case(f"t1b/{i:02d}", "t1b", model, [dict(kind="limit"), query])


def wide_enhancement_targets():
    """The 20 MINOR-1 instances from the accepted adversarial sweep.

    These stable IDs/parameters are persistent inputs, not dependencies on the
    reviewer's temporary directory. Provenance hashes live in repair evidence.
    """
    targets = {}
    settings = ((Q(1), "1.0", 0), (Q(1), "1.0", 2), (Q(1, 2), "0.5", 1),
                (Q(4), "4.0", 0), (Q(4), "4.0", 1), (Q(4), "4.0", 2))
    for orientation in ("koureas", "unreversed", "reverse_i1"):
        for maximum, label, steps in settings:
            targets[orientation, Q(0), Q(1), maximum, steps] = (
                f"sweep/g1/{orientation}/0/1/mumax={label}/steps={steps}")
    for maximum, label, steps in ((Q(1), "1.0", 2), (Q(1, 2), "0.5", 1)):
        targets["unreversed", Q(1, 4), Q(1, 2), maximum, steps] = (
            f"sweep/g1/unreversed/1/4/1/2/mumax={label}/steps={steps}")
    return targets


def wide_g1_specs():
    """Exact 2310-query grid used to expose the missing continuation guard."""
    shapes = ((Q(0), Q(1)), (Q(1, 8), Q(1)), (Q(3, 16), Q(1)),
              (Q(1, 4), Q(1)), (Q(1, 4), Q(1, 2)), (Q(1, 3), Q(3, 8)),
              (Q(1, 3), Q(3, 16)), (Q(3, 32), Q(1, 16)), (Q(1, 2), Q(1)),
              (Q(3, 8), Q(1, 4)), (Q(5, 16), Q(1, 2)))
    maxima = (Q(1, 8), Q(1, 4), Q(3, 8), Q(1, 2), Q(3, 4), Q(1), Q(3, 2), Q(2), Q(3), Q(4))
    for orientation in ("koureas", "unreversed", "reverse_i1"):
        for tilt, height in shapes:
            for maximum in maxima:
                for steps in range(7):
                    yield orientation, tilt, height, maximum, steps


def incline_model(numerator, denominator):
    """Persistent reviewer geometry: Farkas lower end and an open threshold.

    For s=n/d, the large-load force ratio is (4s-1)/(s+4). With the
    nonzero dead load, equality is infeasible, giving open thresholds 0 and
    1/13 for slopes 1/4 and 1/3. Production conservatively returns a bracket.
    """
    from eab.kernel2d.assembly import Assembly2, Body2
    slope = Q(numerator, denominator)
    x0, x1 = Q(3, 4) * denominator, Q(9, 4) * denominator
    wedge = Body2.from_vertices("wedge", ((0, 0), (4 * denominator, 0), (4 * denominator, 4 * numerator)),
        boundary_type="FIXED_BODY", dof_mask=(0, 0, 0))
    reference = ((x0 + x1) / 2, slope * (x0 + x1) / 2 + Q(1, 2))
    block = Body2.from_vertices("block", ((x0, slope * x0), (x1, slope * x1),
        (x1, slope * x1 + 1), (x0, slope * x0 + 1)), reference_point=reference,
        dead=(0, -1, 0), live=(1, -4, 0))
    return Assembly2((wedge, block), ((0, 1),), "complete", "profile1", Q(0))


def quadratic_model(mask):
    """Floor/45-degree-ceiling wedge with root mu^2+2mu-1, no rounded root."""
    from eab.kernel2d.assembly import Assembly2, Body2
    floor = Body2.from_vertices("floor", ((-4, -1), (8, -1), (8, 0), (-4, 0)),
        boundary_type="FIXED_BODY", dof_mask=(0, 0, 0))
    ceiling = Body2.from_vertices("ceiling", ((Q(3, 2), Q(1, 2)), (Q(3, 2), 4), (-1, 4), (-1, 3)),
        boundary_type="FIXED_BODY", dof_mask=(0, 0, 0))
    reference = (Q(1, 2), Q(1, 2))
    block = Body2.from_vertices("block", ((0, 0), (1, 0), (1, 1), (0, 2)),
        reference_point=reference, dof_anchor=reference, live=(-1, 0, 0), dof_mask=mask,
        boundary_type=None if mask == (1, 1, 1) else "FORCE_CONTROLLED_PLATE")
    return Assembly2((floor, ceiling, block), ((0, 1), (0, 2), (1, 2)), "complete", "profile1", Q(0))


def wide_cases():
    from eab.adapters.tia2d import g1, g1_threshold
    targets = wide_enhancement_targets()
    grouped = {}
    for orientation, tilt, height, maximum, steps in wide_g1_specs():
        key = orientation, tilt, height
        truth, attained = g1_threshold(t=tilt, height=height, orientation=orientation)
        query = dict(kind="critical", mu_max_bits=f"{bits(maximum):016x}", max_steps=steps,
            reference_threshold=exact_wire(truth), reference_attained=attained,
            input_parameters=dict(orientation=orientation, t=exact_wire(tilt), h=exact_wire(height),
                                  mu_max=exact_wire(maximum), max_steps=steps))
        identity = orientation, tilt, height, maximum, steps
        if identity in targets:
            query["acceptance_enhancement_id"] = targets[identity]
        if identity == ("koureas", Q(3, 32), Q(1, 16), Q(3, 4), 4):
            query["named_regression"] = "major_closed_lower_continuation_2039_over_32768"
            query["expected_threshold"], query["expected_attained"] = None, None
        if identity == ("koureas", Q(3, 8), Q(1, 4), Q(3, 8), 1):
            query["named_regression"] = "major_closed_lower_continuation_119_over_512"
            query["expected_threshold"], query["expected_attained"] = None, None
        grouped.setdefault(key, []).append(query)
    for (orientation, tilt, height), queries in grouped.items():
        model = g1(t=tilt, height=height, orientation=orientation)
        yield fresh_case(f"wide/g1/{orientation}/{tilt}/{height}", "wide_g1", model, queries)
    for denominator, threshold in ((4, Q(0)), (3, Q(1, 13))):
        queries = [dict(kind="critical", max_steps=steps, expected_lower_status="INFEASIBLE",
            expected_threshold=None, expected_attained=None, reference_open_threshold=exact_wire(threshold))
            for steps in (0, 1, 2, 3, 4, 5, 6, 64)]
        yield fresh_case(f"wide/incline/1/{denominator}", "wide_incline", incline_model(1, denominator), queries)
    for mask in ((1, 1, 0), (1, 1, 1)):
        queries = [dict(kind="critical", max_steps=steps, expected_threshold=None, expected_attained=None,
            expected_root_polynomial=["-1/1", "2/1", "1/1"]) for steps in (3, 48, 64)]
        yield fresh_case("wide/quadratic/" + "".join(str(v) for v in mask), "wide_quadratic", quadratic_model(mask), queries)


def thickness_cases():
    from eab2_c3l3_thickness import thickness_cases as source_cases
    for name, model, queries in source_cases():
        yield fresh_case(name, "thickness", model, queries)


def regression_cases():
    from eab.adapters.tia2d import g1, g1_threshold, g5
    for n, mu, h, p in ((3, Q(0), 1, 1), (3, Q(1, 4), 1, 1), (3, Q(2), 1, 1),
                         (5, Q(2), 1, 1), (7, Q(2), 1, 1), (3, Q(3, 8), Q(3, 2), Q(5, 4))):
        model = g5(n=n, height=h, pressure=p, width=1, mu=mu)
        expected = min(2 * mu * p, Q(4) * p * h / (n - 1))
        yield fresh_case(f"closed_g5/{n}/{mu}/{h}/{p}", "closed_g5", model,
                         [dict(kind="limit", expected_value=exact_wire(expected))])
    base = g5(n=3, height=1, pressure=1, width=1, mu=Q(2))
    for mask, expected in (((1, 1, 0), Q(2, 3)), ((1, 0, 1), Q(4, 3))):
        plate = replace(base.bodies[-1], dof_mask=mask)
        model = replace(base, bodies=base.bodies[:-1] + (plate,))
        yield fresh_case("plate/" + str(mask), "plate", model,
                         [dict(kind="limit", expected_value=exact_wire(expected))])
    for orientation in ("koureas", "unreversed", "reverse_i1"):
        for tilt, height in ((Q(0), Q(1)), (Q(3, 32), Q(1, 16)), (Q(1, 4), Q(1))):
            model = g1(t=tilt, height=height, orientation=orientation)
            threshold, attained = g1_threshold(t=tilt, height=height, orientation=orientation)
            yield fresh_case(f"closed_g1/{orientation}/{tilt}/{height}", "closed_g1", model,
                             [dict(kind="critical", max_steps=48, expected_threshold=exact_wire(threshold), expected_attained=attained)])


def transform_model(model, cosine, sine, scale, offset, force_unit):
    """Exact rational rotations; callers choose units cancelling denominators."""
    from eab.kernel2d.assembly import Body2
    def rotate(v):
        return cosine * v[0] - sine * v[1], sine * v[0] + cosine * v[1]
    def point(p):
        x, y = rotate(p)
        return scale * x + offset[0], scale * y + offset[1]
    bodies = []
    for body in model.bodies:
        loads = []
        for load in (body.dead, body.live):
            x, y = rotate(load)
            loads.append((force_unit * x, force_unit * y, force_unit * scale * load[2]))
        mask = body.dof_mask
        if mask[0] != mask[1]:
            require(cosine == 0 or sine == 0, "axis mask cannot encode general rotated constraints")
            if cosine == 0:
                mask = (mask[1], mask[0], mask[2])
        bodies.append(Body2.from_vertices(body.body_id, tuple(point(p) for p in body.vertices),
            reference_point=point(body.reference_point), dof_anchor=point(body.dof_anchor),
            dof_mask=mask, boundary_type=body.boundary_type, dead=loads[0], live=loads[1]))
    return replace(model, bodies=tuple(bodies))


def reparameterize_reference(model, offset):
    bodies = []
    for body in model.bodies:
        reference = tuple(a + b for a, b in zip(body.reference_point, offset))
        loads = []
        for load in (body.dead, body.live):
            loads.append((load[0], load[1], load[2] - offset[0] * load[1] + offset[1] * load[0]))
        bodies.append(replace(body, reference_point=reference, dead=loads[0], live=loads[1]))
    return replace(model, bodies=tuple(bodies))


def metamorphic_cases():
    from eab.adapters.tia2d import g1, g1_threshold, g5
    base = g1(t=Q(3, 32), height=Q(1, 16), mu=Q(1, 4))
    threshold, attained = g1_threshold(t=Q(3, 32), height=Q(1, 16))
    generator = random.Random(6033)
    rotations = [(Q(1), Q(0), 1)]
    for _ in range(3):
        m = generator.randint(3, 11)
        n = generator.randint(1, m - 1)
        denominator = m*m + n*n
        rotations.append((Q(m*m - n*n, denominator), Q(2*m*n, denominator), denominator))
    for r, (cosine, sine, denominator) in enumerate(rotations):
        for t, unit in ((Q(0), Q(1)), (Q(1000), Q(8)), (Q(100000), Q(1, 2**10))):
            offset = (Q(3, 5) * t, Q(4, 5) * t)
            require(offset[0] * offset[0] + offset[1] * offset[1] == t * t,
                    "metamorphic translation norm schedule")
            model = transform_model(base, cosine, sine, unit * denominator,
                                    offset, Q(denominator))
            for body in model.bodies:
                for point in body.vertices:
                    for x in point:
                        bits(x)
            yield fresh_case(f"meta/g1/{r}/{t}", "metamorphic", model,
                [dict(kind="limit", expected_status="UNBOUNDED"),
                 dict(kind="critical", max_steps=48, expected_threshold=exact_wire(threshold), expected_attained=attained)])
    plate = g5(n=3, height=1, pressure=1, width=1, mu=Q(2), dof_mask=(1, 0, 1))
    for i, (cosine, sine) in enumerate(((Q(1), Q(0)), (Q(0), Q(1)), (Q(-1), Q(0)), (Q(0), Q(-1)))):
        model = transform_model(plate, cosine, sine, Q(1, 2), (Q(100000), Q(-100000)), Q(2))
        yield fresh_case(f"meta/plate/{i}", "metamorphic", model,
                         [dict(kind="limit", expected_value="4/3")])
    for i, offset in enumerate(((Q(0), Q(0)), (Q(17, 8), Q(-29, 16)), (Q(2**17), Q(-2**10)))):
        yield fresh_case(f"meta/reference/{i}", "metamorphic", reparameterize_reference(plate, offset),
                         [dict(kind="limit", expected_value="4/3")])


def implication_box(kind, live=(0, 0, 0), dead=(0, 0, 0), mu=0):
    from eab.kernel2d.assembly import Assembly2, Body2
    rings = (((0, 0), (1, 0), (1, 1), (0, 1)),
             ((-1, 0), (0, 0), (0, 1), (-1, 1)),
             ((1, 0), (2, 0), (2, 1), (1, 1)),
             ((0, -1), (1, -1), (1, 0), (0, 0)),
             ((0, 1), (1, 1), (1, 2), (0, 2)))
    indices = {"free": (0,), "plane": (0, 3), "seam": (0, 1, 2), "cage": (0, 1, 2, 3, 4)}[kind]
    bodies = tuple(Body2.from_vertices(str(i), rings[i], reference_point=(Q(3, 8), Q(-5, 8)),
        dof_anchor=(Q(3, 8), Q(-5, 8)), boundary_type="FIXED_BODY" if i else None,
        dof_mask=(0, 0, 0) if i else (1, 1, 1), live=live if i == 0 else (0, 0, 0),
        dead=dead if i == 0 else (0, 0, 0)) for i in indices)
    pairs = tuple((i, j) for i in range(len(bodies)) for j in range(i + 1, len(bodies)))
    return Assembly2(bodies, pairs, "complete", mu=Q(mu))


def single_moving(model, moving):
    return replace(model, bodies=tuple(body if i == moving else
        replace(body, boundary_type="FIXED_BODY", dof_mask=(0, 0, 0), dead=(Q(0),) * 3, live=(Q(0),) * 3)
        for i, body in enumerate(model.bodies)))


def implication_cases():
    from eab.adapters.tia2d import g1, g5
    for mu in (Q(0), Q(1, 4), Q(5, 2)):
        for i, (live, dead) in enumerate((((1, 2, 3), (0, 0, 0)),
                    ((Q(-3, 8), Q(5, 4), Q(-7, 16)), (Q(1, 4), Q(-3, 2), Q(3, 8))))):
            model = implication_box("cage", live, dead, mu)
            yield fresh_case(f"implication1/{mu}/{i}", "implication1", model,
                [dict(kind="limit", expected_status="UNBOUNDED", expected_zero_cone=True, symbolic_normal_basis=True)])
    for kind in ("free", "plane", "seam", "cage"):
        for k in range(3):
            for sign in (-1, 1):
                live = tuple(Q(sign * (j == k)) for j in range(3))
                model = implication_box(kind, live=live)
                yield fresh_case(f"implication2/{kind}/{k}/{sign}", "implication2", model,
                    [dict(kind="limit", expected_zero_cone=kind == "cage", implication2_group=kind)])
    for orientation, mu in (("koureas", Q(0)), ("unreversed", Q(1, 2)), ("reverse_i1", Q(1, 4))):
        model = g1(t=Q(1, 4), height=1, orientation=orientation, mu=mu)
        for name, value in (("multi", model), ("single", single_moving(model, 2))):
            yield fresh_case(f"implication3/{orientation}/{name}", "implication3", value,
                [dict(kind="limit", expected_status="UNBOUNDED")])
    for mu, expected in ((Q(1, 4), "1/2"), (Q(2), "2/1")):
        model = g5(n=3, height=1, pressure=1, width=1, mu=mu)
        yield fresh_case(f"converse/{mu}/multi", "converse", model,
            [dict(kind="limit", expected_value=expected)])
        yield fresh_case(f"converse/{mu}/single", "converse", single_moving(model, 2),
            [dict(kind="limit", expected_status="UNBOUNDED", expected_zero_cone=False)])


def verify_implication1(model, contacts, result, mobility):
    p = rebuilt_problem(model, contacts, model.mu)
    G = mat(mobility["matrix"])
    for j, normal in enumerate(G):
        require(all(p["A"][k][2*j] + p["A"][k][2*j+1] == 2 * normal[k] for k in range(len(p["b"]))),
                "opposite friction generators must average to exact normal")
    certificate = {(row["coordinate"], row["sign"]): vec(row["multipliers"]) for row in mobility["zero_certificates"]}
    def reaction(target):
        weights = [Q(0)] * len(G)
        for k, value in enumerate(target):
            if value:
                source = certificate[k, 1 if value > 0 else -1]
                weights = [a + abs(value) * b for a, b in zip(weights, source)]
        return tuple(v / 2 for w in weights for v in (w, w))
    x = reaction(p["b"]) + (Q(0),)
    ray = reaction(tuple(-row[-1] for row in p["A"])) + (Q(1),)
    require(all(v >= 0 for v in x + ray), "symbolic normal basis nonnegative")
    require(all(dot(row, x) == b and dot(row, ray) == 0 for row, b in zip(p["A"], p["b"])),
            "symbolic normal basis arbitrary dead/live wrench construction")


def python_result(model, query, contacts):
    from eab.kernel2d.statics import critical_parameter, limit_load_ideal_exact_2d
    if query["kind"] == "limit":
        return limit_load_ideal_exact_2d(model, contacts, mu=Q(query.get("mu", model.mu)))
    return critical_parameter(model, query.get("param", "mu"),
        mu_max=double_bits(query.get("mu_max_bits", "3ff0000000000000")),
        max_steps=query.get("max_steps", 64), contact_set=contacts)


def run(dll, cases, output):
    from eab.kernel2d.contacts import assemble_contact_set2
    from eab2_c3l3_thickness import SUMMARY as thickness_fixture
    counts, families, mismatches, rows = Counter(), Counter(), [], []
    implication2, enhancement_records = {}, []
    source_files = [Path(__file__)] + [ROOT / name for name in (
        "tools/eab2_c3l1_diff.py", "tools/eab2_c3l1_abi.py", "tools/tia2d_t1b_morphology.py",
        "src/eab/kernel2d/statics.py", "src/eab/kernel2d/critical.py", "src/eab/kernel2d/contacts.py",
        "src/eab/kernel2d/assembly.py", "src/eab/lp.py", "src/eab/adapters/tia2d.py")]
    source_files.extend((ROOT / "tools/eab2_c3l3_thickness.py", thickness_fixture))
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
    start = time.perf_counter()
    for name, family, model, contacts, queries in cases:
        ah = ch = None
        completed = 0
        try:
            ah = dll.assembly(model) if dll else None
            ch = dll.contacts(ah) if dll else None
            referee_contacts = None
            if any(expected is None for _, _, expected in queries):
                referee_contacts = assemble_contact_set2(model)
            for index, query, expected in queries:
                t = time.perf_counter()
                if expected is None:
                    expected = exact_wire(python_result(model, query, referee_contacts))
                    py_seconds = time.perf_counter() - t
                else:
                    py_seconds = query.get("python_wallclock", {}).get("seconds")
                t = time.perf_counter()
                actual = dll.l3_query(ch, model, query) if dll else expected
                cpp_seconds = time.perf_counter() - t if dll else None
                call_error = expected["call_status"] != "OK"
                dispositions = []
                if call_error and dll:
                    require(expected["call_status"] == "UNSUPPORTED" and actual == dict(abi_call_status=3, output_unchanged=True, result_published=False),
                            "Python call error/ABI failure mapping mismatch")
                    delta = []
                else:
                    delta = compare(query["kind"], model, contacts, expected, actual, query, dispositions)
                proof_floor = None
                if not call_error and (family.startswith("formal/") or family == "t1b"):
                    proof_floor = require_python_proof_floor(query["kind"], expected, actual)
                if "expected_value" in query:
                    require(actual["exact_value"] == query["expected_value"], "independent closed G5/plate formula")
                if "expected_threshold" in query:
                    require(actual["exact_threshold"] == query["expected_threshold"] and actual["attained"] == query["expected_attained"], "independent closed G1 formula")
                if "expected_max_bracket_width" in query:
                    require(endpoint(actual, "mu_hi") - endpoint(actual, "mu_lo") <= Q(query["expected_max_bracket_width"]),
                            "T1b irrational case must retain certified narrow bracket")
                if "reference_threshold" in query and actual.get("exact_threshold") is not None:
                    require(actual["exact_threshold"] == query["reference_threshold"]
                            and actual["attained"] == query["reference_attained"],
                            "wide G1 exact threshold disagrees with independent closed form")
                if "expected_lower_status" in query:
                    require(actual["lower_certificate"]["mathematical_status"] == query["expected_lower_status"],
                            "wide incline lower endpoint must retain Farkas certificate")
                if "reference_open_threshold" in query:
                    truth = Q(query["reference_open_threshold"])
                    require(endpoint(actual, "mu_lo") <= truth < endpoint(actual, "mu_hi"),
                            "Farkas bracket must contain the independent open threshold")
                if "expected_root_polynomial" in query:
                    polynomial = vec(query["expected_root_polynomial"])
                    require(p_eval(polynomial, endpoint(actual, "mu_lo")) < 0
                            and p_eval(polynomial, endpoint(actual, "mu_hi")) > 0,
                            "quadratic bracket must straddle the independent root")
                if "expected_status" in query:
                    require(actual["mathematical_status"] == query["expected_status"], "metamorphic/implication status")
                if "expected_zero_cone" in query:
                    if dll:
                        mobility = dll.exact(dll.first_order_mobility, ch)
                    else:
                        from eab.kernel2d.mobility import first_order_free_twists
                        mobility = exact_wire(first_order_free_twists(model, referee_contacts))
                    verify_cone("first_order", mobility, assembly=model, contacts=referee_contacts)
                    require(mobility["cone_is_zero"] == query["expected_zero_cone"], "independent mobility oracle")
                    if query.get("symbolic_normal_basis"):
                        verify_implication1(model, contacts, actual, mobility)
                    if "implication2_group" in query:
                        group = query["implication2_group"]
                        implication2.setdefault(group, []).append(actual["mathematical_status"] == "UNBOUNDED")
                row = dict(case_id=name, family=family, query_index=index, kind=query["kind"],
                           mathematical_status=actual.get("mathematical_status"), differences=delta,
                           python_seconds=py_seconds, cpp_seconds=cpp_seconds,
                           python_timing="frozen original" if family.startswith("formal/") else "cold query with prebuilt contacts")
                if proof_floor is not None:
                    row["proof_capability_floor"] = proof_floor
                if query["kind"] == "critical" and not call_error:
                    row["mu_lo"] = exact_wire(endpoint(actual, "mu_lo"))
                    row["mu_hi"] = exact_wire(endpoint(actual, "mu_hi"))
                    row["python_threshold"] = expected["exact_threshold"]
                    row["python_attained"] = expected["attained"]
                    row["python_queries"] = expected["queries"]
                    row["cpp_queries"] = actual["queries"]
                    row["proof_dispositions"] = dispositions
                for metadata in ("input_parameters", "named_regression", "thickness_source"):
                    if metadata in query:
                        row[metadata] = query[metadata]
                if "acceptance_enhancement_id" in query:
                    row["acceptance_enhancement_id"] = query["acceptance_enhancement_id"]
                    require(len(dispositions) == 1 and dispositions[0]["proved_side"] == "cpp",
                            "recorded MINOR-1 instance did not reproduce independently verified enrichment")
                    enhancement_records.append(dict(acceptance_id=query["acceptance_enhancement_id"],
                        case_id=name, query_index=index, input_parameters=query["input_parameters"],
                        disposition=dispositions[0], semantic_mismatches=len(delta)))
                if call_error and dll:
                    row["comparison"] = "Python UNSUPPORTED mapped to atomic ABI call error; no mathematical JSON produced"
                    row["transport_outcome"] = actual
                for key in ("exact_value", "exact_threshold", "attained", "reason", "bisection_termination", "threshold_proof_reason"):
                    if key in actual:
                        row[key] = actual[key]
                rows.append(row)
                completed += 1
                counts[query["kind"]] += 1
                families[family + "/" + query["kind"]] += 1
                if delta:
                    mismatches.append(dict(case_id=name, query_index=index, differences=delta))
        except Exception as error:
            mismatches.append(dict(case_id=name, error=type(error).__name__ + ": " + str(error)))
        finally:
            if dll and ch is not None:
                dll.check(dll.contact_set2_destroy(dll.context, ch), "contact_set2_destroy")
            if dll and ah is not None:
                dll.check(dll.assembly2_destroy(dll.context, ah), "assembly2_destroy")
        if completed != len(queries):
            mismatches.append(dict(case_id=name, error="selected query omitted", expected=len(queries), actual=completed))
        progress = dict(case_id=name, queries=len(rows), mismatch=len(mismatches), seconds=time.perf_counter() - start)
        output.with_suffix(".progress.json").write_text(json.dumps(progress) + "\n", encoding="utf-8")
        print(json.dumps(progress), flush=True)
    for group, answers in implication2.items():
        if len(answers) != 6 or all(answers) != (group == "cage"):
            mismatches.append(dict(error="six basis loads equivalence", group=group, answers=answers))
    if families["wide_g1/critical"]:
        target_ids = set(wide_enhancement_targets().values())
        actual_ids = [row["acceptance_id"] for row in enhancement_records]
        if len(actual_ids) != len(target_ids) or set(actual_ids) != target_ids:
            mismatches.append(dict(error="recorded MINOR-1 instances incomplete", expected=len(target_ids),
                                   actual=len(actual_ids), missing=sorted(target_ids - set(actual_ids))))
    unchanged = all(hashlib.sha256(p.read_bytes()).hexdigest() == hashes[str(p.relative_to(ROOT))] for p in source_files)
    if not unchanged:
        mismatches.append(dict(error="source changed during run; invalid evidence"))
    last = ("C3L3_DIFF" if dll else "C3L3_FIXTURE_AUDIT") + f" limit={counts['limit']} critical={counts['critical']} mismatch={len(mismatches)}"
    result = dict(schema="eab2.c3l3.differential.v1", cpp_executed=dll is not None,
        build_identity=dll.identity if dll else None, dll_sha256=dll.sha256 if dll else None,
        source_sha256=hashes, source_pre_post_equal=unchanged, counts=dict(counts),
        family_counts=dict(families), mismatches=mismatches, queries=rows,
        acceptance_enhancements=enhancement_records,
        proof_capability_floor=dict(scope="frozen formal and T1b", exceptions=[],
            checked_fields=sum(row.get("proof_capability_floor", {}).get("checked", 0) for row in rows)),
        comparison_notes=["C++ mechanism attachment equals independently verified exact_y; no Python duplicate field required",
            "Critical basis polynomials are nonunique; identities and exact one-sided Sturm continuation are verified instead of coefficient equality",
            "A null/non-null critical proof availability difference is allowed only after independent proof verification, with a per-instance disposition; endpoints and other semantics remain strict",
            "Unsupported parameter compares atomic ABI call error and unchanged output; no mathematical JSON is fabricated"],
        timing_scope="Informational only; C++ ABI+JSON query with prebuilt contacts; formal Python timing is frozen source-era, not same-machine cold comparison",
        seconds=time.perf_counter() - start, last_line=last)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(last, flush=True)
    return int(bool(mismatches))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dll", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--family", choices=("formal", "t1b", "regression", "metamorphic", "implication", "wide", "thickness", "all"), default="all")
    parser.add_argument("--case", action="append")
    parser.add_argument("--t1b-required", action="store_true")
    parser.add_argument("--fixture-audit-only", action="store_true")
    args = parser.parse_args()
    require(args.fixture_audit_only or args.dll is not None, "--dll required for production differential")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    def cases():
        if args.family in ("formal", "all"):
            yield from formal_cases(set(args.case) if args.case else None)
        if args.family in ("t1b", "all"):
            yield from t1b_cases("required" if args.t1b_required else None)
        if args.family in ("regression", "all"):
            yield from regression_cases()
        if args.family in ("metamorphic", "all"):
            yield from metamorphic_cases()
        if args.family in ("implication", "all"):
            yield from implication_cases()
        if args.family in ("wide", "all"):
            yield from wide_cases()
        if args.family in ("thickness", "all"):
            yield from thickness_cases()
    dll = None if args.fixture_audit_only else C3L3Dll(args.dll)
    try:
        return run(dll, cases(), args.output)
    finally:
        if dll:
            dll.close()


if __name__ == "__main__":
    raise SystemExit(main())
