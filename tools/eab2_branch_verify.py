"""Independent, standard-library-only checker for ordered-field brackets.

Oracle primitives: sparse Fraction polynomials, fraction-free determinants,
and full polynomial identities. No production geometry, LP, sensitivity or
C++ helper is imported. All coefficients are retained; there is no truncation.
The supplied raw vertex/anchor/load path is rebuilt here, not from dA/db/dc.
"""
from fractions import Fraction as Q
import json
import struct


def need(condition, message):
    if not condition:
        raise AssertionError(message)


def const(value):
    value = Q(value)
    return {(0, 0): value} if value else {}


def add(a, b):
    out = dict(a)
    for key, value in b.items():
        out[key] = out.get(key, Q(0)) + value
        if not out[key]:
            del out[key]
    return out


def neg(a):
    return {key: -value for key, value in a.items()}


def sub(a, b):
    return add(a, neg(b))


def mul(a, b):
    out = {}
    for (i, j), x in a.items():
        for (k, l), y in b.items():
            key = i + k, j + l
            out[key] = out.get(key, Q(0)) + x * y
            if not out[key]:
                del out[key]
    return out


def sign(poly):
    """epsilon is the OUTER infinitesimal; eta orders its coefficients."""
    return (1 if poly[min(poly)] > 0 else -1) if poly else 0


def divide_exact(numerator, denominator):
    need(denominator, "zero exact polynomial divisor")
    remainder, quotient = dict(numerator), {}
    (di, dj), dc = max(denominator.items())
    while remainder:
        (ni, nj), nc = max(remainder.items())
        need(ni >= di and nj >= dj, "non-polynomial Bareiss quotient")
        term = {(ni - di, nj - dj): nc / dc}
        quotient = add(quotient, term)
        remainder = sub(remainder, mul(term, denominator))
    return quotient


def determinant(matrix):
    n = len(matrix)
    need(all(len(row) == n for row in matrix), "nonsquare basis")
    if not n:
        return const(1)
    a = [[dict(v) for v in row] for row in matrix]
    previous, parity = const(1), 1
    for k in range(n - 1):
        pivot = next((i for i in range(k, n) if a[i][k]), None)
        if pivot is None:
            return {}
        if pivot != k:
            a[k], a[pivot] = a[pivot], a[k]
            parity = -parity
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                a[i][j] = divide_exact(sub(mul(a[k][k], a[i][j]),
                                             mul(a[i][k], a[k][j])), previous)
        previous = a[k][k]
        for i in range(k + 1, n):
            a[i][k] = {}
    return a[-1][-1] if parity > 0 else neg(a[-1][-1])


def read_poly(raw):
    need(isinstance(raw, list), "polynomial must be a complete sparse list")
    out = {}
    previous = None
    for row in raw:
        need(isinstance(row, list) and len(row) == 3, "polynomial term width")
        i, j, value = row
        need(type(i) is int and type(j) is int and i >= 0 and j >= 0, "polynomial nonnegative degrees")
        key = i, j
        need(previous is None or previous < key, "polynomial term order/duplicates")
        value = Q(value)
        need(value != 0, "zero term in sparse polynomial")
        out[key], previous = value, key
    return out


def polynomial_value(poly, epsilon, eta):
    return sum((value * epsilon ** i * eta ** j for (i, j), value in poly.items()), Q(0))


def affine(value, derivative, direction):
    coefficient = direction * Q(derivative)
    return add(const(value), {(1, 0): coefficient}) if coefficient else const(value)


def cross(a, b):
    return sub(mul(a[0], b[1]), mul(a[1], b[0]))


def dot(a, b):
    need(len(a) == len(b), "polynomial dot dimensions")
    out = {}
    for x, y in zip(a, b):
        out = add(out, mul(x, y))
    return out


def label_key(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def raw_matrix(bodies, contacts, jet, labels, mu, direction=1, channel=0):
    """Return full A,b,c polys from plain original-body and contact records."""
    ordered = sorted(bodies, key=lambda body: body["body_id"])
    identities = [[body["body_id"], i] for body in ordered for i in range(len(body["vertices"]))]
    need(jet["vertex_ids"] == identities and jet["body_ids"] == [b["body_id"] for b in ordered], "raw seed identities")
    count = len(jet["parameters"])
    need(0 <= channel < count and len(jet["mu"]) == count, "raw channel count")
    for kind, size, width in (("vertices", len(identities), 2), ("dead", len(bodies), 3),
                              ("live", len(bodies), 3), ("dof_anchor", len(bodies), 2)):
        need(len(jet[kind]) == count and all(len(table) == size and all(len(row) == width for row in table)
                                           for table in jet[kind]), "raw primitive seed dimensions")
    need(Q(jet["mu"][channel]) == 0, "threshold mu seed is forbidden")
    velocities = dict(zip(map(tuple, identities), jet["vertices"][channel]))
    shared = {}
    for body in bodies:
        for i, point in enumerate(body["vertices"]):
            key = tuple(map(Q, point))
            velocity = tuple(map(Q, velocities[body["body_id"], i]))
            need(key not in shared or shared[key] == velocity, "shared original vertex path")
            shared[key] = velocity
    seeds = {kind: dict(zip(jet["body_ids"], jet[kind][channel])) for kind in ("dead", "live", "dof_anchor")}
    anchors = {body["body_id"]: tuple(affine(v, d, direction) for v, d in
               zip(body["dof_anchor"], seeds["dof_anchor"][body["body_id"]])) for body in bodies}
    dofs = [(i, k) for i, body in enumerate(bodies) if body.get("boundary_type") != "FIXED_BODY"
            for k, free in enumerate(body["dof_mask"]) if free]
    columns, natural_labels = [], []
    for contact in contacts:
        a, b = contact["a"], contact["b"]
        source, (first, last) = contact["label"][-2:]
        body = next(body for body in bodies if body["body_id"] == source)
        sense = 1 if bodies[a]["body_id"] == source else -1
        need(source in (bodies[a]["body_id"], bodies[b]["body_id"]), "edge belongs to neither contact body")
        tangent = tuple(affine(sense * (Q(body["vertices"][last][k]) - Q(body["vertices"][first][k])),
                      sense * (Q(velocities[source, last][k]) - Q(velocities[source, first][k])), direction) for k in (0, 1))
        point_key = tuple(map(Q, contact["point"]))
        need(point_key in shared, "contact needs an original affine vertex")
        point = tuple(affine(v, d, direction) for v, d in zip(point_key, shared[point_key]))
        for side in (-1, 1):
            force = (add(neg(tangent[1]), mul(const(side), mul(mu, tangent[0]))),
                     add(tangent[0], mul(const(side), mul(mu, tangent[1]))))
            column = []
            for i, k in dofs:
                orientation = int(i == a) - int(i == b)
                arm = tuple(sub(point[j], anchors[bodies[i]["body_id"]][j]) for j in (0, 1))
                value = force[k] if k < 2 else cross(arm, force)
                column.append(mul(const(orientation), value))
            columns.append(column)
            natural_labels.append([contact["label"], side])
    def load(body, kind, coordinate):
        values = tuple(affine(v, d, direction) for v, d in zip(body[kind], seeds[kind][body["body_id"]]))
        if coordinate < 2:
            return values[coordinate]
        arm = tuple(sub(anchors[body["body_id"]][j], const(body["reference_point"][j])) for j in (0, 1))
        return sub(values[2], cross(arm, values))
    columns.append([load(bodies[i], "live", k) for i, k in dofs])
    natural_labels.append(["alpha", 1])
    indexed = dict(zip(map(label_key, natural_labels), columns))
    need(len(indexed) == len(labels) and set(indexed) == set(map(label_key, labels)), "full polynomial column identities")
    columns = [indexed[label_key(label)] for label in labels]
    matrix = [[column[i] for column in columns] for i in range(len(dofs))]
    rhs = [neg(load(bodies[i], "dead", k)) for i, k in dofs]
    objective = [const(label == ["alpha", 1]) for label in labels]
    return matrix, rhs, objective


def vector(record, size):
    need(isinstance(record, dict), "missing ordered-field vector")
    denominator = read_poly(record["denominator"])
    numerators = [read_poly(value) for value in record["numerators"]]
    need(denominator and len(numerators) == size, "vector denominator/dimensions")
    probe = record["probe"]
    need(Q(probe["epsilon"]) > 0 and Q(probe["eta"]) > 0, "positive rational probe")
    return denominator, numerators


def verify_dual(A, c, record):
    denominator, numerators = vector(record, len(A))
    need(all(len(row) == len(c) for row in A), "dual matrix dimensions")
    slacks = [sub(dot([row[j] for row in A], numerators), mul(value, denominator)) for j, value in enumerate(c)]
    need(all(sign(value) * sign(denominator) >= 0 for value in slacks), "lower K dual inequality")
    basis, rows = record["basis"], record["rows"]
    check_basis(A, basis, rows)
    need(all(not numerators[i] for i in range(len(A)) if i not in rows), "dual outside basis rows")
    need(all(not slacks[j] for j in basis), "dual basis formula")
    probe_signs(record, denominator, slacks, "lower rational probe dual inequality")
    return slacks


def check_indices(A, basis, rows):
    """Reject Python negative/bool index aliases before any matrix indexing."""
    need(isinstance(basis, list) and isinstance(rows, list), "basis index arrays")
    need(all(type(i) is int and 0 <= i < len(A) for i in rows), "basis row bounds")
    columns = len(A[0]) if A else 0
    need(all(type(j) is int and 0 <= j < columns for j in basis), "basis column bounds")
    need(len(basis) == len(rows) and len(set(basis)) == len(basis) and len(set(rows)) == len(rows), "basis dimensions/uniqueness")


def check_basis(A, basis, rows):
    check_indices(A, basis, rows)
    need(determinant([[A[i][j] for j in basis] for i in rows]), "singular K basis formula")


def verify_primal(A, b, c, point, ray):
    denominator, numerators = vector(point, len(c))
    need(all(sign(value) * sign(denominator) >= 0 for value in numerators), "upper K point nonnegativity")
    need(all(dot(row, numerators) == mul(value, denominator) for row, value in zip(A, b)), "upper K point equality")
    check_basis(A, point["basis"], point["rows"])
    need(all(not numerators[j] for j in range(len(c)) if j not in point["basis"]), "point outside basis")
    probe_signs(point, denominator, numerators, "upper rational probe point inequality")
    denominator, numerators = vector(ray, len(c))
    need(all(sign(value) * sign(denominator) >= 0 for value in numerators), "upper K ray nonnegativity")
    need(all(not dot(row, numerators) for row in A), "upper K ray equality")
    need(dot(c, numerators) == denominator, "upper K ray alpha normalization")
    check_basis(A, ray["basis"], ray["rows"])
    alpha = next(j for j, v in enumerate(c) if v == const(1))
    need(alpha not in ray["basis"], "ray basis must exclude normalized alpha")
    need(all(not numerators[j] for j in range(len(c)) if j not in ray["basis"] and j != alpha), "ray outside basis")
    probe_signs(ray, denominator, numerators, "upper rational probe ray inequality")


def probe_signs(record, denominator, numerators, message):
    epsilon, eta = (Q(record["probe"][key]) for key in ("epsilon", "eta"))
    value = polynomial_value(denominator, epsilon, eta)
    need(value != 0 and all(polynomial_value(v, epsilon, eta) * value >= 0 for v in numerators), message)


def singular_components(bodies, contacts, jet, labels, threshold, candidate, direction, slope):
    """Independent Cramer determinants, not the production Bareiss solver."""
    A, _, c = raw_matrix(bodies, contacts, jet, labels,
                         add(const(threshold), {(1, 1): Q(1)}), direction)
    rows, basis = candidate["rows"], candidate["basis"]
    check_basis(A, basis, rows)
    B = [[A[i][j] for j in basis] for i in rows]
    if candidate["kind"] == "dual":
        matrix, rhs = list(map(list, zip(*B))), [c[j] for j in basis]
    else:
        need(candidate["kind"] == "ray", "singular candidate kind")
        alpha = next(j for j, value in enumerate(c) if value == const(1))
        need(alpha not in basis, "singular candidate normalized alpha")
        matrix, rhs = B, [neg(A[i][alpha]) for i in rows]
    denominator = determinant(matrix)
    need(not denominator.get((0, 0), Q(0)), "singular candidate must be singular at origin")
    values = []
    for k in range(len(basis)):
        replaced = [[rhs[i] if j == k else value for j, value in enumerate(row)] for i, row in enumerate(matrix)]
        values.append(determinant(replaced))
    if candidate["kind"] == "dual":
        polynomials = [(j, sub(dot([A[i][j] for i in rows], values), mul(c[j], denominator))) for j in range(len(c))]
    else:
        polynomials = list(zip(basis, values))
    output = []
    for index, polynomial in polynomials:
        if not polynomial:
            continue
        order = min(i for i, _ in polynomial)
        terms = {j: value for (i, j), value in polynomial.items() if i == order}
        degree = max(terms)
        if degree == 0 or sum(value * slope ** j for j, value in terms.items()) != 0:
            continue
        monic = [terms.get(j, Q(0)) / terms[degree] for j in range(degree + 1)]
        output.append((index, labels[index], order, monic))
    return output


def check_domain(domain):
    need(isinstance(domain, dict), "missing original search domain binding")
    for name in ("mu_min", "mu_max"):
        value = struct.unpack(">d", bytes.fromhex(domain[name + "_binary64"]))[0]
        display = domain[name]
        if isinstance(display, dict):
            need(display["bits"] == domain[name + "_binary64"], "codec original domain bits")
            display = display["exact"]
        need(Q(value) == Q(display) and Q(value) == Q(domain["exact_" + name]), "original domain binary64/exact binding")
    need(Q(domain["exact_mu_min"]) == 0 and Q(domain["exact_mu_max"]) >= 0, "original search domain endpoints")


def solve_rational(A, b):
    n = len(b)
    need(len(A) == n and all(len(row) == n for row in A), "candidate basis dimensions")
    work = [list(map(Q, row)) + [Q(v)] for row, v in zip(A, b)]
    for j in range(n):
        pivot = next((i for i in range(j, n) if work[i][j]), None)
        need(pivot is not None, "candidate basis singular at origin")
        work[j], work[pivot] = work[pivot], work[j]
        factor = work[j][j]
        work[j] = [v / factor for v in work[j]]
        for i in range(n):
            if i != j:
                factor = work[i][j]
                work[i] = [a - factor * b for a, b in zip(work[i], work[j])]
    return [row[-1] for row in work]


def verify_candidates(bodies, contacts, jet, labels, threshold, branch, direction):
    """Recompute ALL matching first-order roots of every claimed basis."""
    path, _, cpoly = raw_matrix(bodies, contacts, jet, labels, const(threshold), direction)
    mupath, _, _ = raw_matrix(bodies, contacts, jet, labels,
                              add(const(threshold), {(1, 0): Q(1)}), 0)
    A = [[v.get((0, 0), Q(0)) for v in row] for row in path]
    dA = [[v.get((1, 0), Q(0)) for v in row] for row in path]
    uA = [[v.get((1, 0), Q(0)) for v in row] for row in mupath]
    c = [v.get((0, 0), Q(0)) for v in cpoly]
    alpha = next(i for i, v in enumerate(c) if v == 1)
    slope = Q(branch["s"])
    found_labels = []
    candidates = branch["candidate_branches"]
    need(isinstance(candidates, list), "candidate branch array")
    for candidate in candidates:
        need(isinstance(candidate, dict), "candidate object")
        need(type(candidate.get("singular", False)) is bool, "candidate singular boolean")
        rows, basis = candidate["rows"], candidate["basis"]
        check_indices(A, basis, rows)
        B = [[A[i][j] for j in basis] for i in rows]
        actual = candidate["components"]
        need(isinstance(actual, list) and all(isinstance(v, dict) for v in actual), "candidate component array")
        need(all(type(v["index"]) is int and 0 <= v["index"] < len(labels) for v in actual),
             "candidate component integer index")
        if candidate.get("singular", False):
            components = singular_components(bodies, contacts, jet, labels, threshold, candidate, direction, slope)
            need(all(type(v["leading_epsilon_order"]) is int and v["leading_epsilon_order"] >= 0
                     and isinstance(v["leading_polynomial"], list) for v in actual), "singular candidate leading metadata")
            need(len(actual) == len(components) and len({v["index"] for v in actual}) == len(actual),
                 "singular candidate all matching root components (missing/extra)")
            for record, (index, label, order, polynomial) in zip(sorted(actual, key=lambda v: v["index"]), sorted(components)):
                need(record["index"] == index and label_key(record["label"]) == label_key(label) and Q(record["s"]) == slope,
                     "singular candidate crossing label/index/slope")
                need(record["leading_epsilon_order"] == order and list(map(Q, record["leading_polynomial"])) == polynomial,
                     "singular candidate exact leading polynomial")
                found_labels.append(label)
            continue
        if candidate["kind"] == "dual":
            transpose = list(zip(*B))
            state = solve_rational(transpose, [c[j] for j in basis])
            def derivative(matrix):
                return solve_rational(transpose, [-sum(matrix[i][j] * state[k] for k, i in enumerate(rows)) for j in basis])
            dp, dm = derivative(dA), derivative(uA)
            components = []
            for j in range(len(c)):
                value = sum(A[i][j] * state[k] for k, i in enumerate(rows)) - c[j]
                pp = sum(dA[i][j] * state[k] + A[i][j] * dp[k] for k, i in enumerate(rows))
                pm = sum(uA[i][j] * state[k] + A[i][j] * dm[k] for k, i in enumerate(rows))
                if value == 0 and pm < 0 and -pp / pm == slope:
                    components.append((j, labels[j], pp, pm))
        else:
            need(candidate["kind"] == "ray" and alpha not in basis, "candidate branch kind")
            state = solve_rational(B, [-A[i][alpha] for i in rows])
            def derivative(matrix):
                return solve_rational(B, [-matrix[i][alpha] - sum(matrix[i][j] * state[k] for k, j in enumerate(basis)) for i in rows])
            dp, dm = derivative(dA), derivative(uA)
            components = [(j, labels[j], dp[k], dm[k]) for k, j in enumerate(basis)
                          if state[k] == 0 and dm[k] > 0 and -dp[k] / dm[k] == slope]
        need(len(actual) == len(components), "candidate all matching root components (missing/extra)")
        need(len({v["index"] for v in actual}) == len(actual), "candidate duplicate component")
        for record, (index, label, pp, pm) in zip(sorted(actual, key=lambda v: v["index"]), sorted(components)):
            need(record["index"] == index and label_key(record["label"]) == label_key(label), "candidate crossing label/index")
            need(Q(record["s"]) == slope and Q(record["partial_parameter"]) == pp and Q(record["partial_mu"]) == pm,
                 "candidate crossing root slope")
            found_labels.append(label)
    return found_labels


def verify_certificate(bodies, contacts, jet, labels, critical, result, *, mu_max_binary64=None):
    """Check every certified direction; unproved values cannot be hidden."""
    cert = result.get("branch_certificate")
    need(isinstance(cert, dict) and type(cert["version"]) is int and cert["version"] == 1
         and cert["order"] == "epsilon_then_eta", "branch certificate schema/order")
    parameters = jet.get("parameters")
    need(isinstance(parameters, list) and len(parameters) == 1 and isinstance(parameters[0], str)
         and parameters[0] and result["parameter"] == parameters[0], "branch parameter binding")
    need(critical["call_status"] == "OK" and result["call_status"] == "OK"
         and result["mathematical_status"] == critical["mathematical_status"], "branch status envelope")
    need(result["method"] == "branch_certificate", "branch method envelope")
    domain = critical["search_domain"]
    check_domain(domain)
    need(isinstance(mu_max_binary64, str) and mu_max_binary64 == domain["mu_max_binary64"],
         "caller mu_max_binary64 must equal original search domain")
    need(cert["search_domain"] == domain, "branch binds ORIGINAL search domain")
    threshold = Q(critical["exact_threshold"])
    maximum = Q(domain["exact_mu_max"])
    certified, tied, reasons = 0, [], []
    for name, direction, field in (("forward", 1, "right_derivative"), ("reverse", -1, "left_derivative")):
        branch = cert[name]
        need(isinstance(branch, dict), "direction branch object")
        need(isinstance(branch["candidate_branches"], list), "candidate branch array")
        need(all(type(branch[key]) is int and branch[key] >= 0 for key in ("candidate_count", "attempts")),
             "branch count integer metadata")
        if branch["status"] != "certified":
            need(branch["status"] == "unresolved" and result[field] is None, "unproved branch emitted a derivative")
            # Exactly the three reasons emitted after a structured branch
            # certificate exists; earlier input/path failures have no such cert.
            need(branch["reason"] in ("threshold_search_domain_boundary", "threshold_branch_certificate_unavailable",
                                       "direction_outside_validity_conditions", "internal_certificate_shape"), "unproved branch reason")
            reasons.append(branch["reason"])
            need(all(branch.get(key) is None for key in ("s", "lower", "upper")) and not branch.get("candidate_branches"),
                 "unproved branch must not carry claimed values or certificates")
            continue
        need(branch["reason"] is None, "certified branch reason")
        need(isinstance(branch.get("lower"), dict), "certified branch needs lower dual witness")
        need(isinstance(branch.get("upper"), dict), "certified branch needs upper witness object")
        need(isinstance(branch["upper"].get("point"), dict), "certified branch needs upper point witness")
        need(isinstance(branch["upper"].get("ray"), dict), "certified branch needs upper ray witness")
        slope = Q(branch["s"])
        lower_mu = add(const(threshold), {(1, 0): slope}) if slope else const(threshold)
        upper_mu = add(lower_mu, {(1, 1): Q(1)})
        lower_mu = add(lower_mu, {(1, 1): Q(-1)})
        need(sign(lower_mu) >= 0 and sign(sub(const(maximum), upper_mu)) >= 0, "K search domain boundary")
        lower_A, _, lower_c = raw_matrix(bodies, contacts, jet, labels, lower_mu, direction)
        upper_A, upper_b, upper_c = raw_matrix(bodies, contacts, jet, labels, upper_mu, direction)
        verify_dual(lower_A, lower_c, branch["lower"])
        verify_primal(upper_A, upper_b, upper_c, branch["upper"]["point"], branch["upper"]["ray"])
        for record in (branch["lower"], branch["upper"]["point"], branch["upper"]["ray"]):
            need(label_key(record["labels"]) == label_key([labels[j] for j in record["basis"]]), "K basis column labels")
        tied.extend(verify_candidates(bodies, contacts, jet, labels, threshold, branch, direction))
        need(Q(result[field]) == direction * slope, "certified directional sign mapping")
        certified += 1
    need(isinstance(result["tied_labels"], list) and len(result["tied_labels"]) == len(set(map(label_key, result["tied_labels"]))) and
         set(map(label_key, result["tied_labels"])) == set(map(label_key, tied)),
         "branch tied labels must equal all matching candidate roots")
    right, left, directional = result["right_derivative"], result["left_derivative"], result["directional_derivative"]
    need((right is None and directional is None) or (right is not None and directional is not None
         and Q(directional) == Q(right)), "right/directional mapping")
    reason = ("threshold_search_domain_boundary" if "threshold_search_domain_boundary" in reasons else
              reasons[0] if reasons else None)
    if not certified and result["differentiability"] == "singular":
        need(reason == "threshold_branch_certificate_unavailable" and result["reason"] in
             ("critical_basis_singular", "zero_implicit_denominator"), "uncertified singular diagnostic reason")
    else:
        need(result["reason"] == reason, "branch aggregate reason")
    need(result["display_status"] == ("EXACT" if certified else "NOT_APPLICABLE"), "branch display envelope")
    if certified:
        need(result["quality"] == "exact_jet", "certified branch quality")
        expected = "smooth" if certified == 2 and Q(right) == Q(left) else "one_sided"
        need(result["differentiability"] == expected, "branch classification")
    else:
        need(result["differentiability"] in ("unresolved", "singular"), "uncertified branch classification")
        need(result["quality"] == "approximate", "uncertified branch cannot claim exact_jet")
    return certified


def verify_record(record):
    """Bind archive proof to the separately recorded caller request, not itself."""
    return verify_certificate(*(record[key] for key in
        ("bodies", "contacts", "jet", "labels", "critical", "result")),
        mu_max_binary64=record.get("mu_max_binary64"))


if __name__ == "__main__":
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    arguments = parser.parse_args()
    records = directions = 0
    with arguments.archive.open(encoding="utf-8") as stream:
        for line in stream:
            record = json.loads(line)
            directions += verify_record(record)
            records += 1
    need(records > 0, "empty branch certificate archive")
    print(f"C3L4_BRANCH_INDEPENDENT_VERIFY records={records} certified_directions={directions} mismatch=0", flush=True)
