"""Independent reader for approved exact cases, not an alternate geometry oracle.

No codec encoders or decoders are imported. IEEE inputs are decoded by struct,
rationals by a strict Fraction parser, and every public production-result field
is compared with a fresh query on those decoded inputs. Independently written
Fraction dot products also verify LP primal/dual, ray and Farkas equations.
This is serialization/replay verification, not a second mechanics solver.
Historical source hashes bind the recorded batch; they need NOT equal today's
source. A replay failure after a deliberate algorithm change requires review.
"""
from dataclasses import fields, is_dataclass
from fractions import Fraction as Q
import argparse
import hashlib
import gzip
import json
import math
from pathlib import Path
import re
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
VALID_CONDITIONS = frozenset(("L1接触骨架不变", "axial_only_plate", "frozen_reference_points",
    "shared_interface_parameter", "nonnegative_t", "positive_h", "fixed_polygon_table",
    "positive_amplitude", "positive_wavelength", "临界证书基非奇异", "所列越零分量及方向保持有效",
    "true_vv_excluded_from_statics"))

from eab.kernel2d.assembly import Assembly2, Body2
from eab.kernel2d.contacts import assemble_contact_set2
from eab.kernel2d.exact import polygons_overlap_exact
from eab.kernel2d.lock import translation_lock_certificate
from eab.kernel2d.mobility import first_order_free_twists
from eab.kernel2d.sensitivity import LimitSeed2, build_limit_seed2, evaluate_sensitivity2
from eab.kernel2d.statics import critical_parameter, limit_load_ideal_exact_2d


def require(condition, where):
    if not condition:
        raise ValueError("readback mismatch: " + where)


def read_fraction(value):
    require(isinstance(value, str) and re.fullmatch(r"-?(0|[1-9][0-9]*)/[1-9][0-9]*", value),
            "noncanonical rational " + repr(value))
    numerator, denominator = (int(v) for v in value.split("/"))
    result = Q(numerator, denominator)
    require(value == str(result.numerator) + "/" + str(result.denominator), "unreduced rational")
    return result


def read_double(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{16}", value), "binary64 bits")
    result = struct.unpack(">d", bytes.fromhex(value))[0]
    require(math.isfinite(result), "nonfinite input")
    require(struct.pack(">d", result).hex() == value, "binary64 roundtrip")
    return result


def _no_constant(value):
    raise ValueError("nonfinite JSON constant: " + value)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key " + key)
        result[key] = value
    return result


def parse_json_bytes(raw):
    require(not raw.startswith(b"\xef\xbb\xbf"), "UTF-8 BOM")
    require(len(raw) <= 1_000_000, "file larger than 1 MB")
    return json.loads(raw.decode("utf-8"), parse_constant=_no_constant, object_pairs_hook=_unique_object)


def read_json(path):
    raw = Path(path).read_bytes()
    return parse_json_bytes(raw)


def _digest(value):
    # This is the approved semantic-hash format, not a codec function call.
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def decode_assembly(record):
    """Read input fields literally; omitted adjacency/boundaries stay omitted."""
    bodies = []
    for item in record["bodies"]:
        raw = tuple(tuple(read_double(v) for v in p) for p in item["vertices_xy_bits"])
        require(item["vertex_ids"] == list(range(len(raw))), "original vertex IDs")
        require(item["geometry_version"] == "input-1", "geometry version")
        numeric = {}
        for name, bits in (("reference_point", item["reference_point_bits"]),
                           ("dof_anchor", item["dof_anchor_bits"]),
                           ("dead", item["load_source"]["dead_bits"]),
                           ("live", item["load_source"]["live_bits"])):
            numeric[name] = tuple(read_double(v) for v in bits)
            require(tuple(Q(v) for v in numeric[name]) == tuple(read_fraction(v) for v in item[name]),
                    name + " rational versus bits")
        require(item["load_source"]["kind"] == "explicit_wrench_about_reference", "load frame")
        body = Body2.from_vertices(item["body_id"], raw, boundary_type=item["boundary_type"],
                                  dof_mask=tuple(item["dof_mask"]), **numeric)
        require(list(body.vertex_ids) == item["ccw_vertex_ids"], "CCW vertex IDs")
        bodies.append(body)
    indices = {body.body_id: i for i, body in enumerate(bodies)}
    adjacency = record["adjacency"]
    pairs = None if adjacency is None else tuple(tuple(indices[v] for v in pair) for pair in adjacency)
    result = Assembly2(tuple(bodies), pairs, record["completeness"], record["profile"],
                       Q(read_double(record["mu_bits"])))
    return result


def verify_input_audit(assembly, audit):
    """Re-evaluate rounded-input turns and pair states, never trust a true flag."""
    bodies, pairs = assembly.bodies, assembly.pairs
    require(audit["lossless_binary64"] is True and audit["no_new_concave_vertices"] is True,
            "lossless input declaration")
    states = [{"a": bodies[i].body_id, "b": bodies[j].body_id,
               "state": {-1: "OUTSIDE", 0: "CONTACT", 1: "OVERLAP"}[
                   polygons_overlap_exact(bodies[i].vertices, bodies[j].vertices)]}
              for i, j in (pairs if pairs is not None else
                           ((i, j) for i in range(len(bodies)) for j in range(i + 1, len(bodies))))]
    require(states == audit["exact_pair_states"], "decoded pair classification")
    edges = [(body.body_id, k, (body.vertices[(k + 1) % len(body.vertices)][0] - p[0],
                              body.vertices[(k + 1) % len(body.vertices)][1] - p[1]))
             for body in bodies for k, p in enumerate(body.vertices)]
    parallel = [[a, i, b, j] for ix, (a, i, u) in enumerate(edges)
                for b, j, v in edges[ix + 1:] if u[0] * v[1] == u[1] * v[0]]
    require(parallel == audit["exact_parallel_edge_pairs"], "exact parallel edges")
    turns = []
    for body in bodies:
        ring = body.vertices
        concave = []
        for k, p in enumerate(ring):
            previous, following = ring[k - 1], ring[(k + 1) % len(ring)]
            u, v = tuple(p[d] - previous[d] for d in (0, 1)), tuple(following[d] - p[d] for d in (0, 1))
            if u[0] * v[1] < u[1] * v[0]:
                concave.append(k)
        turns.append(dict(body_id=body.body_id, ccw_indices=concave))
    require(turns == audit["concave_vertices_after"] == audit["concave_vertices_before"], "concave input predicate")
    actual = sorted(sorted((v["a"], v["b"])) for v in states if v["state"] == "CONTACT")
    expected = sorted(sorted(v) for v in audit["expected_contact_pairs"])
    require(expected == actual and audit["contact_skeleton_matches"] is True, "expected CONTACT skeleton")


def _restore_indices(raw, body_ids):
    """Decode stable references to the private indices of a fresh query."""
    if isinstance(raw, list):
        return [_restore_indices(v, body_ids) for v in raw]
    if not isinstance(raw, dict):
        return raw
    value = {k: _restore_indices(v, body_ids) for k, v in raw.items()}
    if "a" in value and "b" in value and isinstance(value["a"], str) and value["a"] in body_ids:
        value["a"], value["b"] = body_ids.index(value["a"]), body_ids.index(value["b"])
    if "dofs" in value:
        value["dofs"] = [[body_ids.index(i), k] for i, k in value["dofs"]]
    if "pair_states" in value:
        mapping = {"OUTSIDE": -1, "CONTACT": 0, "OVERLAP": 1}
        value["pair_states"] = ([[body_ids.index(a), body_ids.index(b), mapping[s]] for a, b, s in value["pair_states"]]
                                if value["pair_states"] and isinstance(value["pair_states"][0], list) else
                                [mapping[s] for s in value["pair_states"]])
    return value


def _restore_lock(raw, moving, neighbors):
    for key in ("local_cells", "radius_bounds", "contact_sources"):
        for entry in raw[key]:
            neighbor = neighbors[entry["neighbor_index"]]
            require(entry.pop("neighbor_body_id") == neighbor.body_id, "lock neighbor ID")
            if key != "contact_sources":
                continue
            kind, aid, af, bid, bf = entry["label"]
            require(aid == moving.body_id and bid == neighbor.body_id, "lock incidence bodies")
            av, bv = moving.vertex_ids, neighbor.vertex_ids
            if kind == "VE":
                i, j = av.index(af), bv.index(bf[0])
                require(bf[1] == bv[(j + 1) % len(bv)], "lock edge endpoint")
            else:
                require(kind == "EV", "lock incidence kind")
                i, j = av.index(af[0]), bv.index(bf)
                require(af[1] == av[(i + 1) % len(av)], "lock edge endpoint")
            entry["label"] = [kind, i, j]
    return raw


def compare_result(raw, value, where="result", stats=None):
    """Compare each public field, exact scalar and ordered certificate entry."""
    if stats is not None:
        stats["fields_compared"] = stats.get("fields_compared", 0) + 1
    if is_dataclass(value):
        require(isinstance(raw, dict), where + " object")
        public = [f.name for f in fields(value) if not f.name.startswith("_")
                  and f.name not in ("assembly", "contact_set", "problem")]
        extra = set(raw) - set(public)
        # Endpoint problems are explicit links rather than dataclass recursion.
        require(extra <= {"problem", "mu_lo_bits", "mu_hi_bits"}, where + " unknown fields " + str(extra))
        for name in public:
            expected = getattr(value, name)
            if name in ("mu_lo", "mu_hi") and name + "_bits" in raw:
                bits = raw[name + "_bits"]
                require((bits is None and expected is None) or
                        (expected is not None and bits == struct.pack(">d", expected).hex()), where + "." + name)
            else:
                require(name in raw, where + "." + name + " missing")
                compare_result(raw[name], expected, where + "." + name, stats)
        if "problem" in raw:
            compare_result(raw["problem"], value.problem, where + ".problem", stats)
    elif isinstance(value, Q):
        require(read_fraction(raw) == value, where + " exact rational")
    elif isinstance(value, bool) or value is None:
        require(raw is value, where + " bool/null")
    elif isinstance(value, int):
        actual = read_fraction(raw) if isinstance(raw, str) and "/" in raw else raw
        require(isinstance(actual, (int, Q)) and not isinstance(actual, bool) and actual == value, where + " integer")
    elif isinstance(value, float):
        require(raw["bits"] == struct.pack(">d", value).hex() and read_fraction(raw["exact"]) == Q(value),
                where + " exact float")
    elif isinstance(value, str):
        require(raw == value, where + " string")
    elif isinstance(value, (tuple, list)):
        require(isinstance(raw, list) and len(raw) == len(value), where + " sequence length")
        for i, (actual, expected) in enumerate(zip(raw, value)):
            compare_result(actual, expected, where + "[" + str(i) + "]", stats)
    elif isinstance(value, dict):
        require(set(raw) == set(value), where + " dictionary keys")
        for name in value:
            compare_result(raw[name], value[name], where + "." + name, stats)
    else:
        raise TypeError("unhandled replay value: " + type(value).__name__)


def _vec(raw):
    return [read_fraction(v) for v in raw]


def _mat(raw):
    return [_vec(row) for row in raw]


def _dot(a, b):
    require(len(a) == len(b), "dot dimensions")
    return sum((x * y for x, y in zip(a, b)), Q(0))


def verify_lp(result, problem, stats):
    if problem is None:
        require(result["mathematical_status"] not in ("OPTIMAL", "UNBOUNDED", "INFEASIBLE"),
                "resolved result missing LP")
        return
    A, b, c = _mat(problem["A"]), _vec(problem["b"]), _vec(problem["c"])
    require(len(A) == len(b) and all(len(row) == len(c) for row in A), "LP dimensions")
    state = result["mathematical_status"]
    if state == "OPTIMAL":
        x, y = _vec(result["exact_x"]), _vec(result["exact_y"])
        _verify_optimum(A, b, c, x, y, read_fraction(result["exact_value"]))
    elif state == "UNBOUNDED":
        x, ray = _vec(result["feasible_point"]), _vec(result["improving_ray"])
        require(all(v >= 0 for v in x + ray) and ray[-1] == 1, "nonnegative point/ray alpha")
        require(all(_dot(row, x) == target for row, target in zip(A, b)), "Ax0=b")
        require(all(_dot(row, ray) == 0 for row in A) and _dot(c, ray) > 0, "improving ray")
    elif state == "INFEASIBLE":
        y = _vec(result["farkas"])
        require(_dot(b, y) == 1 and all(sum(A[i][j] * y[i] for i in range(len(b))) <= 0
                                      for j in range(len(c))), "Farkas")
    else:
        return
    stats["lp_certificates"] = stats.get("lp_certificates", 0) + 1


def _verify_optimum(A, b, c, x, y, value):
    require(len(x) == len(c) and len(y) == len(b), "solution dimensions")
    require(all(v >= 0 for v in x), "nonnegative primal")
    require(all(_dot(row, x) == target for row, target in zip(A, b)), "Ax=b")
    require(all(sum(A[i][j] * y[i] for i in range(len(b))) >= c[j] for j in range(len(c))), "dual feasibility")
    require(_dot(c, x) == _dot(b, y) == value, "primal/dual objective")


def verify_mills(query, base, stats):
    result = query["result"]
    if result["method"] != "mills_freund":
        return
    problem, seed = base["problem"], query["seed"]
    A, b, c = _mat(problem["A"]), _vec(problem["b"]), _vec(problem["c"])
    dA, db, dc = _mat(seed["dA"]), _vec(seed["db"]), _vec(seed["dc"])
    value, n = read_fraction(base["result"]["exact_value"]), len(c)
    for key, sign, direction, slope in (("forward_certificate", 1, "positive", "right_derivative"),
                                         ("reverse_certificate", -1, "negative", "left_derivative")):
        if not query["direction_domain"][direction]:
            require(result[key] is None, "invalid direction certificate")
            continue
        x, y = (_vec(v) for v in result[key])
        matrix = [row + [Q(0)] * (n + 2) for row in A] + [c + [Q(0)] * (n + 2)]
        matrix += [[sign * v for v in dA[i]] + A[i] + [b[i], -b[i]] for i in range(len(b))]
        rhs = b + [value] + [sign * v for v in db]
        cost = [sign * v for v in dc] + c + [value, -value]
        derivative = sign * read_fraction(result[slope])
        _verify_optimum(matrix, rhs, cost, x, y, derivative)
        require(derivative == read_fraction(query["directional_values"]["D_plus" if sign == 1 else "D_minus"]),
                "Mills directional sign")
        stats["mills_certificates"] = stats.get("mills_certificates", 0) + 1


def verify_cones(kind, result, stats):
    """Independent certificate equations, in addition to complete field replay."""
    if kind == "assembly":
        for proof in result["redundancy_certificates"] + result["reachable_witnesses"]:
            H, rhs = _mat(proof["matrix"]), _vec(proof["rhs"])
            if proof["unreachable"]:
                weights = _vec(proof["multipliers"])
                require(all(v >= 0 for v in weights) and _dot(rhs, weights) == 1, "VV Farkas normalization")
                require(all(_dot(col, weights) == 0 for col in zip(*H)), "VV Farkas null equation")
            else:
                twist = _vec(proof["twist"])
                require(all(_dot(row, twist) >= b for row, b in zip(H, rhs)), "VV reachable twist")
            stats["cone_certificates"] = stats.get("cone_certificates", 0) + 1
    if kind == "first_order" and result["normalization_certificate"] is not None:
        proof = result["normalization_certificate"]
        _verify_optimum(_mat(proof["matrix"]), _vec(proof["rhs"]), _vec(proof["objective"]),
                        _vec(proof["exact_x"]), _vec(proof["exact_y"]), read_fraction(result["normalized_value"]))
        G = _mat(result["matrix"])
        for item in result["zero_certificates"]:
            weights = _vec(item["multipliers"])
            require(all(v >= 0 for v in weights), "zero-cone nonnegative multipliers")
            require(all(_dot(col, weights) == (item["sign"] if k == item["coordinate"] else 0)
                        for k, col in enumerate(zip(*G))), "zero-cone coordinate combination")
        for ray in result["generators"]:
            require(any(_vec(ray)) and all(_dot(row, _vec(ray)) >= 0 for row in G), "normal cone generator")
        stats["cone_certificates"] = stats.get("cone_certificates", 0) + 1 + len(result["zero_certificates"])


def verify_recession(query, base, stats):
    result = query["result"]
    if result["method"] != "optimal_face_recession":
        return
    p = base["problem"]
    A, b, c = _mat(p["A"]), _vec(p["b"]), _vec(p["c"])
    primal, dual = result["primal_recession_ray"], result["dual_recession_ray"]
    require(primal is not None or dual is not None, "singular recession witness absent")
    if primal is not None:
        ray = _vec(primal)
        require(any(ray) and all(v >= 0 for v in ray) and _dot(c, ray) == 0
                and all(_dot(row, ray) == 0 for row in A), "primal recession")
    if dual is not None:
        ray = _vec(dual)
        require(any(ray) and _dot(b, ray) == 0 and all(_dot(col, ray) >= 0 for col in zip(*A)), "dual recession")
    require(result["left_derivative"] is None and result["right_derivative"] is None, "recession has no certified slope")
    stats["recession_certificates"] = stats.get("recession_certificates", 0) + int(primal is not None) + int(dual is not None)


def read_seed(raw):
    return None if raw is None else LimitSeed2(tuple(tuple(_vec(row)) for row in raw["dA"]),
                                               tuple(_vec(raw["db"])), tuple(_vec(raw["dc"])), raw["parameter"])


def _plain_certificate(value):
    """Plain boundary for the independent polynomial checker, not a codec."""
    if isinstance(value, Q):
        return str(value.numerator) + "/" + str(value.denominator)
    if is_dataclass(value):
        return {f.name: _plain_certificate(getattr(value, f.name)) for f in fields(value)
                if not f.name.startswith("_") and f.name not in ("assembly", "contact_set", "problem")}
    if isinstance(value, (list, tuple)):
        return [_plain_certificate(v) for v in value]
    if isinstance(value, dict):
        if set(value) == {"bits", "exact"}:
            decoded = read_double(value["bits"])
            require(Q(decoded) == read_fraction(value["exact"]), "certificate float binding")
            return decoded
        return {key: _plain_certificate(v) for key, v in value.items()}
    return value


def verify_threshold_branch(assembly, contacts, problem, query, critical, value, stats, mu_max_binary64):
    """Check full K residuals from original vertices, not the first LP jet."""
    if value.branch_certificate is None:
        require(value.right_derivative is None and value.left_derivative is None,
                "threshold derivative lacks branch certificate")
        return
    from eab2_branch_verify import verify_certificate
    bodies = [dict(body_id=b.body_id, vertices=_plain_certificate(b.original_vertices or b.vertices),
        reference_point=_plain_certificate(b.reference_point), dof_anchor=_plain_certificate(b.dof_anchor),
        dead=_plain_certificate(b.dead), live=_plain_certificate(b.live), dof_mask=list(b.dof_mask),
        boundary_type=b.boundary_type) for b in assembly.bodies]
    arguments = (bodies, _plain_certificate(contacts.constraints), query["geometry_seed"],
                 _plain_certificate(problem.column_labels), _plain_certificate(critical))
    try:
        count = verify_certificate(*arguments, _plain_certificate(value), mu_max_binary64=mu_max_binary64)
        if "branch_certificate" in query["result"]:
            verify_certificate(*arguments, _plain_certificate(query["result"]), mu_max_binary64=mu_max_binary64)
    except (AssertionError, KeyError, TypeError, ValueError) as error:
        raise ValueError("readback mismatch: branch certificate: " + str(error)) from error
    stats["branch_certified_directions"] = stats.get("branch_certified_directions", 0) + count


def legacy_result_projection(query, raw, value, stats):
    """Explicit pre-fix projection; never replace old semantic derivative values.

    Frozen files are untouched. Every replaced basis-dependent field is returned
    in the replay ledger. A changed value/category/quality/reason still fails and
    requires a separate reviewed erratum; missing K evidence never proves a value.
    """
    raw = dict(raw)
    changes = []
    if query["kind"] == "critical" and "search_domain" not in raw:
        # The fresh domain is bound to the original query input, not its bracket.
        require(value.search_domain["mu_max_binary64"] == query["mu_max_bits"], "legacy original search domain")
        raw["search_domain"] = value.search_domain
        # compare_result expects the legacy binary64 wire form, not a float.
        raw["search_domain"] = dict(raw["search_domain"])
        for name in ("mu_min", "mu_max"):
            number = raw["search_domain"][name]
            raw["search_domain"][name] = dict(bits=struct.pack(">d", number).hex(),
                exact=str(Q(number).numerator) + "/" + str(Q(number).denominator))
        changes.append(dict(field="search_domain", old=None, new=_plain_certificate(value.search_domain)))
    if query["kind"] == "sensitivity" and "branch_certificate" not in raw:
        if not query.get("threshold_query_ref"):
            require(value.branch_certificate is None, "legacy non-threshold unexpected K evidence")
            raw["branch_certificate"] = None
            changes.append(dict(field="branch_certificate", old="absent", new=None))
        else:
            require(raw["method"] == "implicit_certificate" and value.branch_certificate is not None,
                    "legacy threshold requires fresh branch certificate")
            old_conditions = set(raw["validity_conditions"])
            require(old_conditions == set(value.validity_conditions) | {
                "临界证书基非奇异", "所列越零分量及方向保持有效"}, "legacy threshold condition transition")
            # Only representation/proof-contract fields change here. In
            # particular slopes, quality, classification and reason remain raw.
            for field in ("method", "validity_conditions", "tied_labels", "implicit_components",
                          "selected_piece", "piece_jacobians", "branch_certificate"):
                new = _plain_certificate(getattr(value, field))
                changes.append(dict(field=field, old=raw.get(field), new=new))
                raw[field] = new
            # The ordinary comparator expects float wrappers inside the domain.
            for name in ("mu_min", "mu_max"):
                number = raw["branch_certificate"]["search_domain"][name]
                raw["branch_certificate"]["search_domain"][name] = dict(
                    bits=struct.pack(">d", number).hex(), exact=str(Q(number).numerator) + "/" + str(Q(number).denominator))
    if changes:
        stats.setdefault("legacy_projection_ledger", []).append(dict(
            kind=query["kind"], parameter=raw.get("parameter"), changes=changes))
    return raw


def read_label(raw):
    if isinstance(raw, list):
        return tuple(read_label(v) for v in raw)
    if isinstance(raw, str) and re.fullmatch(r"-?[0-9]+/[0-9]+", raw):
        return read_fraction(raw)
    return raw


def display_status(kind, value):
    """Independent envelope rule: absence of the reported value is not EXACT."""
    if kind == "assembly":
        present = value.mathematical_status not in (None, "UNPROVED")
    elif kind == "first_order":
        present = value.cone_is_zero is not None
    elif kind == "limit":
        present = value.exact_value is not None
    elif kind == "lock":
        present = value.status is not None
    elif kind == "critical":
        present = value.mu_lo is not None and value.mu_hi is not None
    else:
        present = any(getattr(value, k) is not None for k in
                      ("directional_derivative", "left_derivative", "right_derivative"))
    return "EXACT" if present else "NOT_APPLICABLE"


def verify_geometry_seed(assembly, query, problem=None):
    """Decode C3 input jets and independently differentiate force-at-anchor rows.

    Only original vertices, endpoint labels and exact arithmetic are used. This
    derivative oracle imports no codec/geometry-jet encoders and does not use
    build_limit_seed2. After that independent check, the public builder retains
    these original contact/load/anchor primitives for full K evaluation.
    """
    jet = query["geometry_seed"]
    require(isinstance(jet, dict), "geometry_seed required")
    ordered = sorted(assembly.bodies, key=lambda body: body.body_id)
    ids = [[b.body_id, i] for b in ordered for i in range(len(b.original_vertices or b.vertices))]
    body_ids = [b.body_id for b in ordered]
    require(jet["vertex_ids"] == ids and jet["body_ids"] == body_ids, "geometry seed stable ID ordering")
    parameters = jet["parameters"]
    require(len(parameters) == len(set(parameters)) and all(isinstance(p, str) for p in parameters), "geometry parameters")
    for key, size, width in (("vertices", len(ids), 2), ("dead", len(body_ids), 3),
                             ("live", len(body_ids), 3), ("dof_anchor", len(body_ids), 2)):
        require(len(jet[key]) == len(parameters), "geometry parameter dimensions")
        for table in jet[key]:
            require(len(table) == size and all(len(row) == width for row in table), "geometry jet dimensions")
            for row in table:
                _vec(row)
    require(len(jet["mu"]) == len(parameters), "mu seed dimensions")
    _vec(jet["mu"])
    if query["kind"] != "sensitivity":
        require(parameters == [], "non-derivative empty seed")
        return
    require(parameters == [query["result"]["parameter"]], "sensitivity geometry parameter")
    if problem is None:
        require(query["seed"] is None, "unavailable LP has no derived seed")
        return
    velocities = {tuple(key): tuple(_vec(row)) for key, row in zip(ids, jet["vertices"][0])}
    loads = {key: {name: tuple(_vec(row)) for name, row in zip(body_ids, jet[key][0])}
             for key in ("dead", "live", "dof_anchor")}
    points = {}
    for body in assembly.bodies:
        for k, raw in enumerate(body.original_vertices or body.vertices):
            point, velocity = tuple(Q(v) for v in raw), velocities[(body.body_id, k)]
            require(point not in points or points[point] == velocity, "shared vertex velocity")
            points[point] = velocity
    def cross(a, b):
        return a[0] * b[1] - a[1] * b[0]
    def projected_load(body, key):
        derivative, wrench = loads[key][body.body_id], getattr(body, key)
        offset = tuple(body.dof_anchor[k] - body.reference_point[k] for k in (0, 1))
        anchor = loads["dof_anchor"][body.body_id]
        values = (derivative[0], derivative[1], derivative[2] - cross(offset, derivative) - cross(anchor, wrench))
        return [values[k] for k, free in enumerate(body.dof_mask) if free and body.boundary_type != "FIXED_BODY"]
    columns, contact_seeds = [], {}
    dmu = read_fraction(jet["mu"][0])
    for contact in problem.contact_set.constraints:
        body = next(b for b in assembly.bodies if b.body_id == contact.label[3])
        i, j = contact.label[4]
        raw = body.original_vertices or body.vertices
        edge = tuple(Q(raw[j][k]) - Q(raw[i][k]) for k in (0, 1))
        orientation = 1 if edge == contact.tangent else -1
        require(tuple(orientation * v for v in edge) == contact.tangent, "original unnormalized edge")
        tangent = contact.tangent
        dt = tuple(orientation * (velocities[(body.body_id, j)][k] - velocities[(body.body_id, i)][k]) for k in (0, 1))
        contact_seeds[contact.label] = (points[contact.point], dt)
        for sign in (-1, 1):
            force = (-tangent[1] + sign * problem.mu * tangent[0], tangent[0] + sign * problem.mu * tangent[1])
            df = (-dt[1] + sign * (dmu * tangent[0] + problem.mu * dt[0]),
                   dt[0] + sign * (dmu * tangent[1] + problem.mu * dt[1]))
            column = []
            for index, target in enumerate(assembly.bodies):
                side = int(index == contact.a) - int(index == contact.b)
                arm = tuple(contact.point[k] - target.dof_anchor[k] for k in (0, 1))
                velocity = tuple(points[contact.point][k] - loads["dof_anchor"][target.body_id][k] for k in (0, 1))
                wrench = (side * df[0], side * df[1], side * (cross(velocity, force) + cross(arm, df)))
                column.extend(wrench[k] for k, free in enumerate(target.dof_mask) if free and target.boundary_type != "FIXED_BODY")
            columns.append(column)
    columns.append([v for body in assembly.bodies for v in projected_load(body, "live")])
    rhs = tuple(-v for body in assembly.bodies for v in projected_load(body, "dead"))
    seed = LimitSeed2(tuple(tuple(column[i] for column in columns) for i in range(len(rhs))),
                      rhs, (Q(0),) * len(problem.c), parameters[0])
    compare_result(query["seed"], seed, "geometry-derived LP seed")
    if query.get("threshold_query_ref"):
        # The second implicit seed is the unit mu direction, not another
        # caller-declared arbitrary LP perturbation. Check it independently.
        unit = dict(parameters=["mu"], vertex_ids=ids, body_ids=body_ids,
            vertices=[[["0/1", "0/1"] for _ in ids]],
            dead=[[["0/1"] * 3 for _ in body_ids]], live=[[["0/1"] * 3 for _ in body_ids]],
            dof_anchor=[[["0/1"] * 2 for _ in body_ids]], mu=["1/1"])
        verify_geometry_seed(assembly, dict(kind="sensitivity", geometry_seed=unit,
            result=dict(parameter="mu"), seed=query["threshold_mu_seed"]), problem)
    rebuilt = build_limit_seed2(problem, mu_seed=dmu, contact_seeds=contact_seeds,
        dead_seeds=loads["dead"], live_seeds=loads["live"],
        anchor_seeds=loads["dof_anchor"], parameter=parameters[0])
    compare_result(query["seed"], rebuilt, "geometry-derived production LP seed")
    return rebuilt


def verify_comparison_contract(query):
    contract = query["comparison_contract"]
    require(contract["default"] == "exact" and isinstance(contract["rules"], dict), "comparison contract")
    require(set(contract["rules"].values()) <= {"exact", "set", "verify_certificate", "informational"}, "comparison classes")
    for name in ("exact_x", "exact_y", "improving_ray", "feasible_point", "farkas", "basis"):
        require(contract["rules"].get("result.**." + name) == "verify_certificate", "nonunique certificate comparison")
    require(contract["rules"].get("python_wallclock.**") == "informational", "timing is informational")
    # Frozen per-field policy, not a caller-controlled way to turn mathematics
    # into informational output. Reconstructed here without codec imports.
    expected = {"python_wallclock.**": "informational", "display_note.**": "informational",
                "result.**.cell_index": "informational", "result.**.labels": "set",
                "result.**.sources": "set", "result.validity_conditions": "set"}
    for field in ("basis", "exact_x", "exact_y", "feasible_point", "improving_ray", "farkas", "multipliers"):
        expected["result.**." + field] = "verify_certificate"
    kind = query["kind"]
    groups = {
        "assembly": (("constraints", "points", "raw_sources", "segments", "unresolved", "pair_states"),
                     ("redundancy_certificates", "reachable_witnesses")),
        "first_order": ((), ("rays", "lineality", "generators", "zero_certificates")),
        "lock": (("contact_sources",), ("local_cells", "radius_bounds", "radius", "separation_ray", "seam_ray", "arcs")),
        "critical": ((), ("threshold_proof.**", "critical_polynomials")),
        "sensitivity": (("tied_labels", "near_labels"), ("forward_certificate", "reverse_certificate",
            "primal_recession_ray", "dual_recession_ray", "implicit_components", "selected_piece", "piece_jacobians")),
        "limit": ((), ()),
    }
    require(kind in groups, "known comparison family")
    sets, certificates = groups[kind]
    expected.update(("result." + field, "set") for field in sets)
    expected.update(("result." + field, "verify_certificate") for field in certificates)
    if kind == "sensitivity" and "branch_certificate" in query["result"]:
        expected["result.branch_certificate"] = "verify_certificate"
        if query.get("threshold_query_ref"):
            expected["result.tied_labels"] = "verify_certificate"
    if kind == "critical":
        expected["result.queries"] = "informational"
    require(contract["rules"] == expected, "frozen comparison rule map")


def verify_conditions(value):
    if isinstance(value, dict):
        for name, entry in value.items():
            if name in ("validity_conditions", "declared_validity_conditions"):
                require(isinstance(entry, list) and all(v in VALID_CONDITIONS for v in entry), "validity condition enum")
            else:
                verify_conditions(entry)
    elif isinstance(value, list):
        for entry in value:
            verify_conditions(entry)


def verify_family_parameters(assembly, metadata, queries=()):
    """Check declared family inputs from actual rings/loads, without adapters.

    Empty metadata is allowed for generic hand-built API cases. Private named
    roles without a geometric family declare only family/mu; no default beam
    geometry is inferred for them. At zero G1 slope, orientation is a role
    label rather than a distinguishable shape; an exported t jet additionally
    fixes that role and is checked against its declared orientation.
    """
    require(isinstance(metadata, dict), "family parameter record")
    if not metadata:
        return
    require({"family", "mu"} <= set(metadata) and isinstance(metadata["family"], str), "family parameter identity")
    def number(name):
        value = read_fraction(metadata[name])
        require(math.isfinite(float(value)) and Q(float(value)) == value, "binary64 family parameter " + name)
        return value
    require(number("mu") == assembly.mu, "family mu versus assembly")
    family = metadata["family"]
    base = {"family", "mu"}
    bodies = assembly.bodies
    is_g5 = family == "TIA-G5" or (family == "named_regression" and set(metadata) != base)
    if family not in ("TIA-G1", "TIA-G2", "TIA-G3", "TIA-G4") and not is_g5:
        require(set(metadata) == base, "unsupported private family parameters")
        return
    levels = {(min(p[1] for p in body.vertices), max(p[1] for p in body.vertices)) for body in bodies}
    require(len(levels) == 1, "family common height")
    low, high = next(iter(levels))
    height = high - low
    require(height > 0, "family positive height")
    faces = [sorted(set(a.vertices) & set(b.vertices), key=lambda p: (p[1], p[0]))
             for a, b in zip(bodies, bodies[1:])]
    if family == "TIA-G1":
        require(base | {"t", "h", "orientation"} <= set(metadata)
                and set(metadata) <= base | {"t", "h", "orientation", "l"}, "G1 family fields")
        require(len(bodies) == 5 and all(len(body.vertices) == 4 for body in bodies)
                and all(len(face) == 2 and face[0][1] == low and face[1][1] == high for face in faces), "G1 straight shared faces")
        require(number("h") == height, "family h versus actual height")
        centers = [(a[0] + b[0]) / 2 for a, b in faces]
        spacing = centers[1] - centers[0]
        require(spacing > 0 and all(b - a == spacing for a, b in zip(centers, centers[1:])), "G1 face spacing l")
        if "l" in metadata:
            require(number("l") == spacing, "family l versus actual face spacing")
        patterns = {"koureas": (-1, -1, 1, 1), "unreversed": (1, -1, 1, -1), "reverse_i1": (-1, -1, 1, -1)}
        require(metadata["orientation"] in patterns, "G1 orientation label")
        signs, t = patterns[metadata["orientation"]], number("t")
        slopes = tuple((b[0] - a[0]) / height for a, b in faces)
        require(t >= 0 and slopes == tuple(sign * t for sign in signs), "family t/orientation versus actual slopes")
        point_sign = {p: sign for face, sign in zip(faces, signs) for p in face}
        by_id = {body.body_id: body for body in bodies}
        for query in queries:
            jet = query.get("geometry_seed")
            if not isinstance(jet, dict) or jet.get("parameters") != ["t"]:
                continue
            for (body_id, index), raw in zip(jet["vertex_ids"], jet["vertices"][0]):
                p = tuple(Q(v) for v in (by_id[body_id].original_vertices or by_id[body_id].vertices)[index])
                require(tuple(_vec(raw)) == (point_sign.get(p, 0) * (p[1] - (low + high) / 2), Q(0)), "G1 orientation versus t geometry jet")
    elif is_g5:
        require(set(metadata) == base | {"N", "h", "P", "widths"}, "G5 family fields")
        require(number("N") == len(bodies) - 2 and len(bodies) - 2 in (3, 5, 7), "family N versus body count")
        require(number("h") == height, "family h versus actual height")
        for body in bodies:
            xs = {p[0] for p in body.vertices}
            require(len(xs) == 2 and len(body.vertices) == 4
                    and set(body.vertices) == {(x, y) for x in xs for y in (low, high)}, "G5 rectangular bodies")
        require(all(len(face) == 2 and face[0][0] == face[1][0] for face in faces), "G5 vertical shared faces")
        widths = tuple(max(p[0] for p in body.vertices) - min(p[0] for p in body.vertices) for body in bodies[1:-1])
        encoded = tuple(_vec(metadata["widths"]))
        require(encoded == widths and widths == tuple(reversed(widths)) and all(v > 0 for v in widths), "family widths versus rectangles")
        require(all(math.isfinite(float(v)) and Q(float(v)) == v for v in encoded), "binary64 family widths")
        pressure, plate = number("P"), bodies[-1]
        require(pressure >= 0 and plate.dead == (-pressure, 0, ((low + high) / 2 - plate.reference_point[1]) * pressure), "family P versus plate dead wrench")
        require(all(body.dead == (0, 0, 0) for body in bodies[:-1]), "G5 no other dead load")
    else:
        require(set(metadata) == base | {"A", "wavelength"}, "polygon family fields")
        amplitude, wavelength = number("A"), number("wavelength")
        require(amplitude >= 0 and wavelength == height and len(bodies) == 5, "family amplitude/block height")
        if family == "TIA-G2":
            table = ((Q(0), Q(0)), (Q(1, 2), Q(1)), (Q(1), Q(0)))
        else:
            ordinates = ((0, 169, 222, 248, 256, 248, 222, 169, 0) if family == "TIA-G3"
                         else (0, 181, 256, 181, 0, -181, -256, -181, 0))
            table = tuple((Q(i, 8), Q(value, 256)) for i, value in enumerate(ordinates))
        for face in faces:
            require(len(face) == len(table) and face[0][1] == low, "fixed polygon sample count")
            require(face == [(face[0][0] - amplitude * s, low + wavelength * u) for u, s in table], "family A/wavelength versus fixed polygon profile")
        for i, body in enumerate(bodies[1:-1], 1):
            require(set(body.vertices) == set(faces[i - 1]) | set(faces[i]), "polygon body shared profile identity")


def prepare_query(case, query_index):
    """Prepare inputs, then return exactly one target call for cold timing.

Required prebuilt contacts/optimal points are outside that query's clock, as
declared by scope. Each worker process calls this once and times one target.
"""
    assembly = decode_assembly(case["assembly"])
    body_ids = [body.body_id for body in assembly.bodies]
    query = case["queries"][query_index]
    kind = query["kind"]
    raw = _restore_indices(query["result"], body_ids)
    if kind == "assembly":
        return lambda: assemble_contact_set2(assembly), raw
    if kind == "lock":
        moving = assembly.bodies[body_ids.index(query["moving_body"])]
        neighbors = tuple(assembly.bodies[body_ids.index(i)] for i in query["fixed_neighbors"])
        raw = _restore_lock(raw, moving, neighbors)
        return lambda: translation_lock_certificate(moving.vertices, tuple(b.vertices for b in neighbors)), raw
    contacts = assemble_contact_set2(assembly)
    if kind == "first_order":
        return lambda: first_order_free_twists(assembly, contacts), raw
    if kind == "limit":
        return lambda: limit_load_ideal_exact_2d(assembly, contacts), raw
    if kind == "critical":
        upper = read_double(query["mu_max_bits"])
        return lambda: critical_parameter(assembly, query["param"], contact_set=contacts, mu_max=upper), raw
    require(kind == "sensitivity", "cold query kind")
    if query.get("threshold_query_ref"):
        threshold = next(q for q in case["queries"] if q["kind"] == "critical")
        target = critical_parameter(assembly, threshold["param"], contact_set=contacts, mu_max=read_double(threshold["mu_max_bits"]))
    else:
        target = limit_load_ideal_exact_2d(assembly, contacts)
    problem = (target.threshold_certificate.problem if query.get("threshold_query_ref")
               and target.threshold_certificate is not None else getattr(target, "problem", None))
    seed = verify_geometry_seed(assembly, query, problem)
    mu_seed = read_seed(query.get("threshold_mu_seed"))
    return lambda: evaluate_sensitivity2(target, seed, parameter=raw["parameter"], threshold_mu_seed=mu_seed,
        positive_direction_valid=query["direction_domain"]["positive"],
        negative_direction_valid=query["direction_domain"]["negative"],
        validity_conditions=tuple(query["declared_validity_conditions"])), raw


def verify_case(case):
    """Fresh full production replay, plus independent exact certificate checks."""
    start = time.perf_counter()
    required = {"schema", "schema_revision", "case_id", "input_version", "design_sha256", "profile",
                "assembly", "input_audit", "family_parameters", "alias_of", "role", "queries",
                "provenance", "python_wallclock"}
    require(required <= set(case) and set(case) <= required | {"fragment"}, "case top-level fields")
    require(case["schema"] == "eab2.case.v1" and case["schema_revision"] == "tia2d-2", "schema version")
    require(case["design_sha256"] == "6d174ecc4f1326d5bac21c56c8d333485fb50bbaef3a12150e94eaff14cb4dac", "design SHA")
    require(case["input_version"] == "tia2d-input-1" and case["profile"] == "profile1", "input/profile version")
    assembly = decode_assembly(case["assembly"])
    require("input_audit" not in case["assembly"], "audit outside hashed assembly")
    verify_input_audit(assembly, case["input_audit"])
    verify_family_parameters(assembly, case["family_parameters"], case["queries"])
    require((case["role"] == "primary" and case["alias_of"] is None)
            or (case["role"] == "alias" and isinstance(case["alias_of"], str)), "alias role")
    body_ids = [b.body_id for b in assembly.bodies]
    input_hash = _digest(case["assembly"])
    raw_queries = case["queries"]
    singular_kinds = [q["kind"] for q in raw_queries if q["kind"] not in ("sensitivity", "lock")]
    require(len(singular_kinds) == len(set(singular_kinds)), "unique query family reference")
    by_kind = {q["kind"]: q for q in raw_queries if q["kind"] not in ("sensitivity", "lock")}
    require("assembly" in by_kind and "limit" in by_kind and "first_order" in by_kind, "required query families")
    contact_hash = _digest(by_kind["assembly"]["result"])
    contacts = assemble_contact_set2(assembly)
    fresh = {"assembly": contacts, "first_order": first_order_free_twists(assembly, contacts),
             "limit": limit_load_ideal_exact_2d(assembly, contacts)}
    if "critical" in by_kind:
        fresh["critical"] = critical_parameter(assembly, by_kind["critical"]["param"], contact_set=contacts,
                                              mu_max=read_double(by_kind["critical"]["mu_max_bits"]))
    stats = dict(case_id=case["case_id"], status="PASS", queries=0, fields_compared=0,
                 lp_certificates=0, mills_certificates=0)
    for query in raw_queries:
        kind = query["kind"]
        verify_comparison_contract(query)
        verify_conditions(query)
        require(query["assembly_ref"] == dict(id=input_hash, version="input-1"), "assembly reference")
        require(query["source"] == "python_referee", "query source")
        if kind == "sensitivity":
            threshold = query.get("threshold_query_ref")
            require((query.get("limit_query_ref") == "limit") != (threshold == "critical"), "one sensitivity target")
            require(all(type(query["direction_domain"][side]) is bool for side in ("positive", "negative")), "direction domain booleans")
            if threshold:
                require(query["threshold_certificate_ref"] == dict(query="critical", field="result.threshold_certificate"),
                        "threshold certificate reference")
            values, answer = query["directional_values"], query["result"]
            right, left = answer["right_derivative"], answer["left_derivative"]
            require(values["D_plus"] == right, "right directional value/null")
            require((left is None and values["D_minus"] is None) or (left is not None and values["D_minus"] is not None
                    and read_fraction(values["D_minus"]) == -read_fraction(left)), "left directional sign/null")
            target = fresh[query.get("limit_query_ref", query.get("threshold_query_ref"))]
            problem = (target.threshold_certificate.problem if query.get("threshold_query_ref")
                       and target.threshold_certificate is not None else getattr(target, "problem", None))
            rebuilt_seed = verify_geometry_seed(assembly, query, problem)
        else:
            verify_geometry_seed(assembly, query)
        observables = dict(assembly="zero_window_contact_set", first_order="first_order_normal_cone",
                           limit="live_load_multiplier", lock="local_translation_separation", critical="friction_unboundedness_threshold")
        observable = (("d_mu_crit_d_" if query.get("threshold_query_ref") else "d_live_load_multiplier_d_") + query["result"]["parameter"]
                      if kind == "sensitivity" else observables.get(kind))
        require(query["observable"] == observable, "observable")
        if kind != "lock":
            require(query["contact_set_ref"] == dict(id=contact_hash, version="contact-1"), "contact reference")
        clock = query["python_wallclock"]
        scopes = dict(assembly="contact_assembly", first_order="normal_cone_with_prebuilt_contact_set",
                      limit="LP_and_exact_certificates_with_prebuilt_contact_set", lock="local_cells_angular_cover_and_radius",
                      critical="threshold_LPs_and_certificates")
        scope = ("critical_basis_implicit_derivative" if query.get("threshold_query_ref") else "optimal_face_tests_and_directional_LPs") if kind == "sensitivity" else scopes.get(kind)
        require(isinstance(clock["seconds"], (int, float)) and math.isfinite(clock["seconds"])
                and not isinstance(clock["seconds"], bool) and clock["seconds"] >= 0 and clock["clock"] == "perf_counter"
                and clock["scope"] == scope and clock["cache_state"] in ("cold", "warm")
                and type(clock["repeat_index"]) is int and clock["repeat_index"] >= 0, "wallclock")
        raw = _restore_indices(query["result"], body_ids)
        if kind == "lock":
            moving = assembly.bodies[body_ids.index(query["moving_body"])]
            neighbors = tuple(assembly.bodies[body_ids.index(i)] for i in query["fixed_neighbors"])
            value = translation_lock_certificate(moving.vertices, tuple(b.vertices for b in neighbors))
            raw = _restore_lock(raw, moving, neighbors)
        elif kind == "sensitivity":
            target = fresh[query.get("limit_query_ref", query.get("threshold_query_ref"))]
            value = evaluate_sensitivity2(target, rebuilt_seed,
                parameter=raw["parameter"], threshold_mu_seed=read_seed(query.get("threshold_mu_seed")),
                positive_direction_valid=query["direction_domain"]["positive"],
                negative_direction_valid=query["direction_domain"]["negative"],
                validity_conditions=tuple(query["declared_validity_conditions"]))
            if query.get("limit_query_ref"):
                verify_mills(query, by_kind["limit"], stats)
                verify_recession(query, by_kind["limit"], stats)
            else:
                verify_threshold_branch(assembly, contacts, problem, query, target, value, stats, by_kind["critical"]["mu_max_bits"])
        else:
            require(kind in fresh, "unknown query kind")
            value = fresh[kind]
        raw = legacy_result_projection(query, raw, value, stats)
        compare_result(raw, value, kind, stats)
        verify_cones(kind, query["result"], stats)
        require(query["call_status"] == value.call_status and query["mathematical_status"] == value.mathematical_status
                and query["display_status"] == display_status(kind, value), "status envelope")
        if kind == "limit":
            compare_result(query["problem"], value.problem, "limit.problem", stats)
            verify_lp(query["result"], query["problem"], stats)
        if kind == "critical":
            require(query["midpoint_rule"] == "exact_mean_else_floor_to_binary64_then_strict_interior_v1", "binary midpoint rule")
            for field in ("lower_certificate", "upper_certificate", "threshold_certificate"):
                certificate = query["result"][field]
                if certificate is not None:
                    verify_lp(certificate, certificate["problem"], stats)
        stats["queries"] += 1
    stats["reader_wallclock_seconds"] = time.perf_counter() - start
    return stats


def _bound_file(directory, record):
    path = (directory / record["path"]).resolve()
    require(path.is_relative_to(directory.resolve()), "manifest file path")
    if path.exists():
        raw = path.read_bytes()
    else:
        compressed = path.with_name(path.name + ".gz")
        index = read_json(directory / "gzip_index.json")
        matches = [row for row in index["files"] if row["path"] == record["path"]]
        require(len(matches) == 1, "gzip index entry")
        row = matches[0]
        require(row["gz_path"] == compressed.name, "gzip path binding")
        encoded = compressed.read_bytes()
        require(len(encoded) == row["gz_bytes"] and hashlib.sha256(encoded).hexdigest() == row["gz_sha256"], "gzip SHA")
        require(encoded[4:8] == bytes(4), "gzip mtime zero")
        raw = gzip.decompress(encoded)
        require(row["sha256"] == record["sha256"] and row["bytes"] == record["bytes"], "decompressed binding")
    require(len(raw) == record["bytes"] and hashlib.sha256(raw).hexdigest() == record["sha256"], "file bytes/SHA")
    return parse_json_bytes(raw)


def load_batch(directory):
    """Check historical bindings, then reconstruct ordered logical case records.

Only recorded files and their internal hashes are inspected here. In particular
this function never opens the current source_files paths or asserts they equal
the recorded historical SHA values.
"""
    directory = Path(directory).resolve()
    manifest = read_json(directory / "manifest.json")
    require(manifest["schema"] == "eab2.case-batch.v1" and manifest["schema_revision"] == "tia2d-2", "batch version")
    source = _bound_file(directory, manifest["source_manifest"])
    require(source["schema"] == "eab2.source-manifest.v1" and source["schema_revision"] == "tia2d-2", "source manifest version")
    for item in (manifest, source):
        require(item["schema_approval"] == "CLAUDE-APPROVED-TIA2D-2" and item["approval_date"] == "2026-10-19", "schema approval")
    require((source["git_commit"] is None and source["git_commit_reason"] == "no_git_checkout") or
            (isinstance(source["git_commit"], str) and re.fullmatch(r"[0-9a-f]{40}", source["git_commit"])
             and source["git_commit_reason"] == "working_tree_source_manifest_authoritative"), "Git provenance anchor")
    require(source["source_files_sha256"] == _digest(source["source_files"]), "historical source list digest")
    require(source["command"] and source["tool_version"] and source["python"] and source["platform"], "command/tool/runtime provenance")
    require(source["source_manifest_basis"] == "actual_root_src_tests_tools_bytes_v1", "source manifest basis")
    require(source["design_sha256"] == "6d174ecc4f1326d5bac21c56c8d333485fb50bbaef3a12150e94eaff14cb4dac", "source design SHA")
    require(bool(source["source_files"]), "empty historical source files")
    require(len({v["path"] for v in source["source_files"]}) == len(source["source_files"]), "duplicate source path")
    for entry in source["source_files"]:
        path = Path(entry["path"])
        require(not path.is_absolute() and ".." not in path.parts and path.parts[0] in ("src", "tests", "tools")
                and path.as_posix() == entry["path"] and re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]),
                "historical source record")
    inputs = {v["case_id"]: v["input_sha256"] for v in source["inputs"]}
    require(len(inputs) == len(source["inputs"]) == len(manifest["cases"]), "input count")
    cases, used_paths = [], {manifest["source_manifest"]["path"]}
    for case_record in manifest["cases"]:
        parts = case_record["parts"]
        require(bool(parts), "empty case fragments")
        reconstructed, header, all_queries = None, None, {}
        for index, part_record in enumerate(parts):
            require(part_record["path"] not in used_paths, "duplicate artifact path")
            used_paths.add(part_record["path"])
            part = _bound_file(directory, part_record)
            require(part["case_id"] == case_record["case_id"], "case ID binding")
            require(part["provenance"] == dict(source_manifest_sha256=manifest["source_manifest"]["sha256"]),
                    "single source manifest reference")
            fragment = part.get("fragment")
            if fragment is not None:
                require(fragment == dict(index=index, count=len(parts), query_indices=part_record["query_indices"]),
                        "fragment ordering")
            else:
                require(len(parts) == 1, "missing split fragment descriptor")
            current_header = {k: v for k, v in part.items() if k not in ("queries", "fragment")}
            require(header is None or header == current_header, "fragment headers")
            header = current_header
            require(len(part["queries"]) == len(part_record["query_indices"]), "fragment query count")
            for key, query in zip(part_record["query_indices"], part["queries"]):
                require(isinstance(key, int) and key not in all_queries, "duplicate query index")
                all_queries[key] = query
        require(set(all_queries) == set(range(case_record["query_count"])), "complete query index coverage")
        reconstructed = dict(header, queries=[all_queries[i] for i in range(case_record["query_count"])])
        digest = _digest(reconstructed["assembly"])
        require(digest == case_record["input_sha256"] == inputs[case_record["case_id"]], "batch input SHA binding")
        cases.append(reconstructed)
    require(len({c["case_id"] for c in cases}) == len(cases), "case IDs unique")
    primary = {}
    for case in cases:
        digest = _digest(case["assembly"])
        if digest in primary:
            require(case["alias_of"] == primary[digest] and case["role"] == "alias", "duplicate input alias")
        else:
            require(case["alias_of"] is None and case["role"] == "primary", "primary input alias")
            primary[digest] = case["case_id"]
    return cases


def verify_python_only(record):
    """Replay private rational diagnostics without ever rounding an input."""
    require(record["diagnostic_format"] == "tia2d.python-only-diagnostic.v1"
            and record["case_v1_export"] is False and record["cpp_input"] is False, "Python-only domain")
    raw = record["assembly"]
    bodies = []
    def point(values):
        return tuple(read_fraction(v) if isinstance(v, str) else Q(v) for v in values)
    for body in raw["bodies"]:
        vertices = tuple(point(p) for p in body["original_vertices"] or body["vertices"])
        value = Body2.from_vertices(body["body_id"], vertices, reference_point=point(body["reference_point"]),
            dof_anchor=point(body["dof_anchor"]), boundary_type=body["boundary_type"],
            dof_mask=tuple(body["dof_mask"]), dead=point(body["dead"]), live=point(body["live"]))
        compare_result(body, value, "python_only.body")
        bodies.append(value)
    pairs = None if raw["pairs"] is None else tuple(tuple(p) for p in raw["pairs"])
    assembly = Assembly2(tuple(bodies), pairs, raw["completeness"], raw["profile"], read_fraction(raw["mu"]))
    require(any(Q(float(v)) != v for body in bodies for p in body.vertices for v in p), "non-binary64 input expected")
    contacts = assemble_contact_set2(assembly)
    limit = limit_load_ideal_exact_2d(assembly, contacts)
    first = first_order_free_twists(assembly, contacts)
    search = record["critical_search"]
    critical = critical_parameter(assembly, contact_set=contacts, max_steps=search["max_steps"],
                                  mu_max=float(read_fraction(search["mu_max"])))
    stats = dict(case_id=record["case_id"], status="PASS", cpp_input=False,
                 fields_compared=0, lp_certificates=0, queries=4 + len(record["lock"]))
    for field, expected in (("contact_set", contacts), ("limit", limit), ("limit_problem", limit.problem),
                             ("first_order", first), ("critical", critical)):
        compare_result(record[field], expected, "python_only." + field, stats)
    verify_lp(record["limit"], record["limit_problem"], stats)
    verify_cones("assembly", record["contact_set"], stats)
    verify_cones("first_order", record["first_order"], stats)
    ids = [body.body_id for body in bodies]
    for entry in record["lock"]:
        index = ids.index(entry["body_id"])
        result = translation_lock_certificate(bodies[index].vertices,
                                              tuple(b.vertices for i, b in enumerate(bodies) if i != index))
        compare_result(entry["result"], result, "python_only.lock", stats)
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    require(output.is_relative_to(ROOT) and not output.exists(), "new output inside worktree required")
    output.parent.mkdir(parents=True, exist_ok=True)
    progress = output.with_suffix(".progress.jsonl")
    require(not progress.exists(), "new progress file required")
    records, python_only = [], []
    started = time.perf_counter()
    def save(status, reason=None):
        output.write_text(json.dumps(dict(status=status, valid=status == "PASS", reason=reason,
            source_batch=str(args.directory), reader="independent_struct_fraction_and_production_replay_v1",
            current_source_hash_equality_required=False, wall_seconds=time.perf_counter() - started,
            cases=records, python_only=python_only), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    save("RUNNING")
    try:
        for case in load_batch(args.directory):
            result = verify_case(case)
            records.append(result)
            with progress.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(result, ensure_ascii=False) + "\n")
            print(case["case_id"], "PASS", result["fields_compared"], flush=True)
        require(bool(records), "no cases")
        folder = args.directory.parent / "python_only"
        if folder.exists():
            for item in read_json(folder / "manifest.json"):
                result = verify_python_only(_bound_file(folder, item))
                python_only.append(result)
                with progress.open("a", encoding="utf-8", newline="\n") as stream:
                    stream.write(json.dumps(result, ensure_ascii=False) + "\n")
                print(result["case_id"], "PASS", result["fields_compared"], flush=True)
        save("PASS")
    except BaseException as error:
        save("FAILED_OR_INTERRUPTED", str(error))
        raise
    print("independent readback: " + str(len(records)) + " cases PASS")


if __name__ == "__main__":
    main()
