"""C3-L1 differential reader and independent exact certificate checks.

The expected side reads original IEEE bits and canonical fractions directly;
no C++ helper or case encoder is imported. Certificate matrices are rebuilt
from original polygon edges and actual masked velocity anchors, not trusted
from either export. Nonunique coordinates are verified on those rebuilt rows;
every strict representation difference is retained separately. Contact selection
still has the Python referee as its oracle. A missing selected query fails.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
from dataclasses import fields, is_dataclass
from fractions import Fraction as Q
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import sys
import time

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src/eab").is_dir())
sys.path.insert(0, str(ROOT / "src"))
FORMAL = ROOT / "fixtures/eab2_cases/tia2d-2/formal_20261019_02/binary64"
KINDS = ("assembly", "first_order", "lock")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def rational(value):
    require(isinstance(value, str) and re.fullmatch(r"-?(0|[1-9][0-9]*)/[1-9][0-9]*", value),
            "noncanonical rational: " + repr(value))
    result = Q(value)
    require(value == f"{result.numerator}/{result.denominator}", "unreduced rational")
    return result


def double_bits(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{16}", value), "invalid binary64 bits")
    result = struct.unpack(">d", bytes.fromhex(value))[0]
    require(math.isfinite(result), "nonfinite binary64 input")
    return result


def _object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def _constant(value):
    raise ValueError("nonfinite JSON constant: " + value)


def read_json(data):
    if isinstance(data, Path):
        data = data.read_bytes()
    require(not data.startswith(b"\xef\xbb\xbf"), "UTF-8 BOM")
    return json.loads(data.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)


def wire(value):
    """Serialize Python public dataclasses without importing any case codec."""
    if isinstance(value, Q):
        return f"{value.numerator}/{value.denominator}"
    if is_dataclass(value):
        return {f.name: wire(getattr(value, f.name)) for f in fields(value)
                if not f.name.startswith("_") and f.name not in ("assembly", "contact_set", "problem")}
    if isinstance(value, (list, tuple)):
        return [wire(v) for v in value]
    if isinstance(value, dict):
        return {k: wire(v) for k, v in value.items()}
    return value


def decode_assembly(record):
    from eab.kernel2d.assembly import Assembly2, Body2
    bodies = []
    for item in record["bodies"]:
        ring = tuple(tuple(double_bits(x) for x in p) for p in item["vertices_xy_bits"])
        require(item["vertex_ids"] == list(range(len(ring))), "original vertex IDs")
        kwargs = {}
        for name, bits in (("reference_point", item["reference_point_bits"]),
                           ("dof_anchor", item["dof_anchor_bits"]),
                           ("dead", item["load_source"]["dead_bits"]),
                           ("live", item["load_source"]["live_bits"])):
            kwargs[name] = tuple(double_bits(v) for v in bits)
            require(tuple(Q(v) for v in kwargs[name]) == tuple(rational(v) for v in item[name]),
                    name + " bits/rational mismatch")
        body = Body2.from_vertices(item["body_id"], ring, boundary_type=item["boundary_type"],
                                  dof_mask=tuple(item["dof_mask"]), **kwargs)
        require(list(body.vertex_ids) == item["ccw_vertex_ids"], "CCW vertex IDs mismatch")
        bodies.append(body)
    indices = {body.body_id: i for i, body in enumerate(bodies)}
    require(len(indices) == len(bodies), "duplicate body IDs")
    pairs = record["adjacency"]
    pairs = None if pairs is None else tuple(tuple(indices[v] for v in p) for p in pairs)
    return Assembly2(tuple(bodies), pairs, record["completeness"], record["profile"],
                     Q(double_bits(record["mu_bits"])))


def _private_ids(value, ids):
    if isinstance(value, list):
        return [_private_ids(v, ids) for v in value]
    if not isinstance(value, dict):
        return value
    out = {k: _private_ids(v, ids) for k, v in value.items()}
    if "a" in out and "b" in out and isinstance(out["a"], str):
        out["a"], out["b"] = ids.index(out["a"]), ids.index(out["b"])
    if "dofs" in out:
        out["dofs"] = [[ids.index(i), k] for i, k in out["dofs"]]
    if "pair_states" in out:
        states = {"OUTSIDE": -1, "CONTACT": 0, "OVERLAP": 1}
        out["pair_states"] = [([ids.index(p[0]), ids.index(p[1]), states[p[2]]]
                                if isinstance(p, list) else states[p]) for p in out["pair_states"]]
    return out


def fixture_result(query, assembly):
    """Undo only stable-ID wire references; exact geometry is untouched."""
    out = _private_ids(copy.deepcopy(query["result"]), [b.body_id for b in assembly.bodies])
    if query["kind"] != "lock":
        return out
    moving = next(b for b in assembly.bodies if b.body_id == query["moving_body"])
    neighbors = [next(b for b in assembly.bodies if b.body_id == name) for name in query["fixed_neighbors"]]
    for key in ("local_cells", "radius_bounds", "contact_sources"):
        for row in out[key]:
            other = neighbors[row["neighbor_index"]]
            require(row.pop("neighbor_body_id") == other.body_id, "lock neighbor ID mismatch")
            if key != "contact_sources":
                continue
            kind, a, ai, b, bi = row["label"]
            require(a == moving.body_id and b == other.body_id, "lock source body mismatch")
            av, bv = moving.vertex_ids, other.vertex_ids
            if kind == "VE":
                i, j = av.index(ai), bv.index(bi[0])
                require(bi[1] == bv[(j + 1) % len(bv)], "lock source edge mismatch")
            else:
                require(kind == "EV", "lock source kind mismatch")
                i, j = av.index(ai[0]), bv.index(bi)
                require(ai[1] == av[(i + 1) % len(av)], "lock source edge mismatch")
            row["label"] = [kind, i, j]
    return out


def formal_cases(directory=FORMAL, selection=None):
    manifest = read_json(directory / "manifest.json")
    for entry in manifest["cases"]:
        if selection is not None and entry["case_id"] not in selection:
            continue
        all_queries = {}
        raw_assembly = None
        for part in entry["parts"]:
            raw = gzip.decompress((directory / (part["path"] + ".gz")).read_bytes())
            require(len(raw) == part["bytes"] and hashlib.sha256(raw).hexdigest() == part["sha256"],
                    "fixture integrity: " + part["path"])
            record = read_json(raw)
            require(record["case_id"] == entry["case_id"], "fixture case ID mismatch")
            require(raw_assembly is None or raw_assembly == record["assembly"], "fragment input mismatch")
            raw_assembly = record["assembly"]
            require(len(part["query_indices"]) == len(record["queries"]), "fragment query count")
            for index, query in zip(part["query_indices"], record["queries"]):
                require(index not in all_queries, "duplicate query index")
                all_queries[index] = query
        require(set(all_queries) == set(range(entry["query_count"])), "incomplete query fragments")
        assembly = decode_assembly(raw_assembly)
        queries = [(i, q, fixture_result(q, assembly)) for i, q in sorted(all_queries.items()) if q["kind"] in KINDS]
        yield entry["case_id"], assembly, queries


def vec(raw):
    return tuple(rational(v) for v in raw)


def mat(raw):
    return tuple(vec(row) for row in raw)


def dot(a, b):
    require(len(a) == len(b), "dot dimensions")
    return sum((x * y for x, y in zip(a, b)), Q(0))


def verify_optimum(A, b, c, x, y, objective, maximize=True):
    require(len(A) == len(b) and all(len(row) == len(c) for row in A), "LP dimensions")
    require(len(x) == len(c) and len(y) == len(b), "LP certificate dimensions")
    require(all(v >= 0 for v in x), "LP primal nonnegative")
    require(all(dot(row, x) == target for row, target in zip(A, b)), "LP primal Ax=b")
    for j, cost in enumerate(c):
        dual = sum((A[i][j] * y[i] for i in range(len(b))), Q(0))
        require(dual >= cost if maximize else dual <= cost, "LP dual feasibility")
    require(dot(c, x) == dot(b, y) == objective, "LP primal/dual objective")


def verify_lp(problem, result):
    """Only original A,b,c and Fraction equations; no solver imports."""
    A, b, c = mat(problem["A"]), vec(problem["b"]), vec(problem["c"])
    require(len(A) == len(b) and all(len(row) == len(c) for row in A), "LP input dimensions")
    state = result["status"].lower()
    if state == "optimal":
        verify_optimum(A, b, c, vec(result["x"]), vec(result["y"]), rational(result["objective"]),
                       problem.get("maximize", False))
    elif state == "infeasible":
        y = vec(result["y"])
        require(len(y) == len(b) and dot(b, y) > 0, "Farkas strict positive rhs")
        require(all(sum((A[i][j] * y[i] for i in range(len(b))), Q(0)) <= 0
                    for j in range(len(c))), "Farkas columns")
    elif state == "unbounded":
        x, ray = vec(result["x"]), vec(result["ray"])
        require(len(x) == len(c) and len(ray) == len(c), "unbounded dimensions")
        require(all(v >= 0 for v in x + ray), "unbounded nonnegative")
        require(all(dot(row, x) == target for row, target in zip(A, b)), "unbounded feasible point")
        require(all(dot(row, ray) == 0 for row in A), "unbounded kernel ray")
        require(dot(c, ray) == (1 if problem.get("maximize", False) else -1), "unbounded improvement normalization")
    else:
        raise ValueError("unrecognized LP state")


def rank(rows, width):
    a = [list(row) for row in rows]
    require(all(len(row) == width for row in a), "rank dimensions")
    k = 0
    for j in range(width):
        p = next((i for i in range(k, len(a)) if a[i][j]), None)
        if p is None:
            continue
        a[k], a[p] = a[p], a[k]
        q = a[k][j]
        a[k] = [v / q for v in a[k]]
        for i in range(k + 1, len(a)):
            q = a[i][j]
            a[i] = [u - q * v for u, v in zip(a[i], a[k])]
        k += 1
    return k


def _sub2(a, b):
    return (a[0] - b[0], a[1] - b[1])


def _cross2(a, b):
    return a[0] * b[1] - a[1] * b[0]


def _rot2(v):
    return (-v[1], v[0])


def _on_segment(p, a, b):
    return _cross2(_sub2(p, a), _sub2(b, a)) == 0 and dot(_sub2(p, a), _sub2(p, b)) <= 0


def geometry_dofs(assembly):
    """Use actual masked kinematics, not an exported coordinate declaration."""
    return tuple((i, k) for i, body in enumerate(assembly.bodies)
                 for k in range(3) if body.boundary_type != "FIXED_BODY" and body.dof_mask[k])


def geometry_velocity_row(assembly, a, b, point, normal, dofs):
    row = []
    for body_index, coordinate in dofs:
        if body_index not in (a, b):
            row.append(Q(0))
            continue
        # A load reference is NOT the velocity anchor. Moving it alone cannot
        # change this row; an actual anchor offset changes the rotation column.
        value = (normal[coordinate] if coordinate < 2 else
                 _cross2(_sub2(point, assembly.bodies[body_index].dof_anchor), normal))
        row.append(value if body_index == a else -value)
    return tuple(row)


def geometry_constraint_rows(assembly, constraints):
    """Rebuild every normal from its labelled original CCW edge.

    Contact selection remains checked against the Python referee. Neither an
    exported tangent nor matrix is an input to the reconstructed row, even if
    both sides of a field comparison were corrupted consistently. No contact
    matrix/velocity helper from Python or C++ is called here.
    """
    dofs = geometry_dofs(assembly)
    rows = []
    for item in constraints:
        a, b, point = item["a"], item["b"], vec(item["point"])
        require(0 <= a < b < len(assembly.bodies), "geometry constraint body pair")
        left, right = assembly.bodies[a], assembly.bodies[b]
        la, lb, lp, edge_body, edge_ids = item["label"]
        require((la, lb, vec(lp)) == (left.body_id, right.body_id, point), "geometry constraint label")
        require(edge_body in (left.body_id, right.body_id), "geometry edge body")
        side = 0 if edge_body == left.body_id else 1
        body = (left, right)[side]
        require(len(edge_ids) == 2 and edge_ids[0] in body.vertex_ids, "geometry edge IDs")
        k = body.vertex_ids.index(edge_ids[0])
        end = (k + 1) % len(body.vertices)
        require(body.vertex_ids[end] == edge_ids[1], "geometry edge must be labelled CCW edge")
        require(_on_segment(point, body.vertices[k], body.vertices[end]), "geometry point on labelled edge")
        other = (right, left)[side]
        require(any(_on_segment(point, p, other.vertices[(j + 1) % len(other.vertices)])
                    for j, p in enumerate(other.vertices)), "geometry point on other boundary")
        tangent = _sub2(body.vertices[end], body.vertices[k])
        if side:
            tangent = tuple(-v for v in tangent)
        require(vec(item["tangent"]) == tangent, "geometry tangent must equal labelled edge")
        rows.append(geometry_velocity_row(assembly, a, b, point, _rot2(tangent), dofs))
    return tuple(rows)


def _material_generators(ring, point):
    """Incident material wedges reconstructed only from the input polygon."""
    def halfplane(edge):
        return (edge, tuple(-v for v in edge), _rot2(edge))
    if point in ring:
        k = ring.index(point)
        before = _sub2(point, ring[k - 1])
        after = _sub2(ring[(k + 1) % len(ring)], point)
        turn = _cross2(before, after)
        if turn > 0:
            return ((after, tuple(-v for v in before)),)
        return (halfplane(after),) if turn == 0 else (halfplane(before), halfplane(after))
    for k, p in enumerate(ring):
        q = ring[(k + 1) % len(ring)]
        if _on_segment(point, p, q):
            return (halfplane(_sub2(q, p)),)
    raise ValueError("geometry VV point is not on body boundary")


def geometry_forbidden_normals(assembly, a, b, point):
    """Exact facets of each local difference cone; no exported cone normals."""
    require(0 <= a < b < len(assembly.bodies), "geometry VV body pair")
    cones = []
    for left in _material_generators(assembly.bodies[a].vertices, point):
        for right in _material_generators(assembly.bodies[b].vertices, point):
            generators = right + tuple(tuple(-v for v in g) for g in left)
            facets = {}
            for g in generators:
                for n in (_rot2(g), tuple(-v for v in _rot2(g))):
                    if all(dot(n, h) >= 0 for h in generators):
                        size = sum(map(abs, n))
                        facets.setdefault(tuple(v / size for v in n), n)
            cone = tuple(facets[key] for key in sorted(facets))
            if cone not in cones:
                cones.append(cone)
    return tuple(cones)


def geometry_normalized_lp(G, width):
    count = len(G)
    A = tuple(tuple(row) + tuple(-v for v in row)
              + tuple(Q(-int(i == j)) for j in range(count)) + (Q(0),)
              for i, row in enumerate(G))
    A += ((Q(0),) * (2 * width) + (Q(1),) * (count + 1),)
    b = (Q(0),) * count + (Q(1),)
    c = (Q(0),) * (2 * width) + (Q(1),) * count + (Q(0),)
    return A, b, c


def verify_cone(kind, result, *, assembly, contacts=None):
    dofs = geometry_dofs(assembly)
    if kind == "assembly" or (kind == "first_order" and result["matrix"] is not None):
        if contacts is None:
            from eab.kernel2d.contacts import assemble_contact_set2
            contacts = assemble_contact_set2(assembly)
        require(contacts.assembly == assembly, "geometry contacts assembly mismatch")
        rows = geometry_constraint_rows(assembly, wire(contacts.constraints))
    if kind == "assembly":
        # The public constraint collection is unordered; certificate coordinates
        # retain the referee's construction order, not the export's list order.
        geometry_constraint_rows(assembly, result["constraints"])
        for proof in result["redundancy_certificates"] + result["reachable_witnesses"]:
            point = proof["point"]
            a, b, p = point["a"], point["b"], vec(point["point"])
            cones = geometry_forbidden_normals(assembly, a, b, p)
            require(len(cones) == 1 and cones[0], "geometry VV needs one forbidden cone")
            require(tuple(mat(cone) for cone in point["forbidden"]) == cones, "geometry VV forbidden normals")
            blocked = tuple(geometry_velocity_row(assembly, a, b, p, n, dofs) for n in cones[0])
            H = rows + blocked
            rhs = (Q(0),) * len(rows) + (Q(1),) * len(blocked)
            require(tuple(map(tuple, proof["dofs"])) == dofs, "geometry VV dofs")
            require(mat(proof["matrix"]) == H and vec(proof["rhs"]) == rhs, "geometry VV matrix/rhs")
            width = len(dofs)
            if proof["unreachable"]:
                weights = vec(proof["multipliers"])
                require(len(weights) == len(rhs) and all(w >= 0 for w in weights), "VV Farkas weights")
                require(dot(rhs, weights) == 1, "VV Farkas normalization")
                require(all(sum((H[i][j] * weights[i] for i in range(len(H))), Q(0)) == 0
                            for j in range(width)), "VV Farkas null equation")
            else:
                twist = vec(proof["twist"])
                require(len(twist) == width and all(dot(row, twist) >= b for row, b in zip(H, rhs)),
                        "VV reachable twist")
    if kind == "first_order" and result["matrix"] is not None:
        G = rows
        require(tuple(map(tuple, result["dofs"])) == dofs, "geometry first-order dofs")
        require(mat(result["matrix"]) == G, "geometry first-order matrix")
        width = len(dofs)
        r = rank(G, width)
        require(result["exact_rank"] == r, "exact rank mismatch")
        proof = result["normalization_certificate"]
        require(proof is not None, "missing normalization certificate")
        A, rhs, objective = geometry_normalized_lp(G, width)
        require(mat(proof["matrix"]) == A, "geometry normalized LP matrix")
        require(vec(proof["rhs"]) == rhs, "geometry normalized rhs")
        require(vec(proof["objective"]) == objective, "geometry normalized objective")
        verify_optimum(A, rhs, objective, vec(proof["exact_x"]), vec(proof["exact_y"]),
                       rational(result["normalized_value"]))
        zero = r == width and rational(result["normalized_value"]) == 0
        require(result["cone_is_zero"] is zero, "zero-cone rank/LP criterion")
        require(result["mathematical_status"] == ("ZERO_CONE" if zero else "NONZERO_CONE"), "cone status")
        for generator in result["generators"]:
            v = vec(generator)
            require(len(v) == width and any(v) and all(dot(row, v) >= 0 for row in G), "cone generator")
        lines = mat(result["lineality"])
        require(rank(lines, width) == width - r, "lineality dimension")
        require(all(dot(row, line) == 0 for row in G for line in lines), "lineality kernel")
        signs = set()
        for item in result["zero_certificates"]:
            weights = vec(item["multipliers"])
            require(len(weights) == len(G) and all(v >= 0 for v in weights), "zero-cone weights")
            k, sign = item["coordinate"], item["sign"]
            require(0 <= k < width and sign in (-1, 1), "zero-cone coordinate/sign")
            require(all(sum((G[i][j] * weights[i] for i in range(len(G))), Q(0)) == (sign if j == k else 0)
                        for j in range(width)), "zero-cone combination")
            signs.add((k, sign))
        require(not zero or signs == {(j, s) for j in range(width) for s in (-1, 1)}, "missing zero-cone combinations")


def verify_lock(result):
    if result["mathematical_status"] == "OVERLAP":
        require(result["status"] is None and result["radius"] is None, "overlap must reject lock signing")
        return
    radius = rational(result["radius"])
    require(radius > 0, "positive lock radius")
    for bound in result["radius_bounds"]:
        a, b = vec(bound["start"]), vec(bound["end"])
        e = tuple(y - x for x, y in zip(a, b))
        t = min(Q(1), max(Q(0), -dot(a, e) / dot(e, e)))
        p = tuple(x + t * v for x, v in zip(a, e))
        q = dot(p, p)
        require(q == rational(bound["squared_distance"]) and radius * radius < q, "strict rational radius bound")
    cells = {(x["neighbor_index"], x["cell_index"]): x for x in result["local_cells"]}
    for arc in result["arcs"]:
        v = vec(arc["sample"])
        require(sum(map(abs, v)) == 1, "lock arc L1 normalization")
        blockers, contact = [], False
        for key, cell in cells.items():
            signs = []
            for a, b in cell["active_edges"]:
                a, b = vec(a), vec(b)
                signs.append((b[0] - a[0]) * v[1] - (b[1] - a[1]) * v[0])
            if all(s > 0 for s in signs):
                blockers.append(list(key))
            elif all(s >= 0 for s in signs):
                contact = True
        require(arc["state"] == ("PENETRATING" if blockers else "CONTACT" if contact else "SEPARATING"), "lock arc classification")
        require(sorted(arc["blockers"]) == sorted(blockers), "lock arc blockers")
    for key, state in (("separation_ray", "SEPARATING"), ("seam_ray", "CONTACT")):
        if result[key] is not None:
            require(any(a["sample"] == result[key] and a["state"] == state for a in result["arcs"]), "lock witness arc")


SET_FIELDS = frozenset(("constraints", "points", "raw_sources", "unresolved", "segments", "pair_states",
                        "sources", "labels", "generators", "rays", "lineality"))
NONUNIQUE_FIELDS = frozenset(("exact_x", "exact_y", "multipliers", "twist"))


def _canonical(value, name="", semantic=False):
    if semantic and name in NONUNIQUE_FIELDS:
        return "<independently verified nonunique certificate>" if value is not None else None
    if isinstance(value, dict):
        return {k: _canonical(v, k, semantic) for k, v in sorted(value.items())}
    if isinstance(value, list):
        values = [_canonical(v, "", semantic) for v in value]
        if name in SET_FIELDS:
            values.sort(key=lambda x: json.dumps(x, sort_keys=True, ensure_ascii=True))
        return values
    return value


def differences(expected, actual, path="result"):
    if type(expected) is not type(actual):
        return [dict(path=path, expected=expected, actual=actual)]
    if isinstance(expected, dict):
        out = []
        for key in sorted(set(expected) | set(actual)):
            if key not in expected or key not in actual:
                out.append(dict(path=path + "." + key, expected=expected.get(key, "<missing>"), actual=actual.get(key, "<missing>")))
            else:
                out.extend(differences(expected[key], actual[key], path + "." + key))
        return out
    if isinstance(expected, list):
        if len(expected) != len(actual):
            return [dict(path=path + ".length", expected=len(expected), actual=len(actual))]
        return [d for i, (a, b) in enumerate(zip(expected, actual)) for d in differences(a, b, f"{path}[{i}]")]
    return [] if expected == actual else [dict(path=path, expected=expected, actual=actual)]


def compare(kind, expected, actual, *, assembly, contacts=None):
    verify_cone(kind, actual, assembly=assembly, contacts=contacts)
    if kind == "lock":
        verify_lock(actual)
    strict = differences(_canonical(expected), _canonical(actual))
    semantic = differences(_canonical(expected, semantic=True), _canonical(actual, semantic=True))
    return dict(strict_field_differences=strict, semantic_differences=semantic)


def python_query(assembly, query, contacts=None):
    from eab.kernel2d.contacts import assemble_contact_set2
    from eab.kernel2d.lock import translation_lock_certificate
    from eab.kernel2d.mobility import first_order_free_twists
    kind = query["kind"]
    if kind == "assembly":
        return assemble_contact_set2(assembly)
    if kind == "first_order":
        return first_order_free_twists(assembly, contacts)
    ids = {b.body_id: b for b in assembly.bodies}
    return translation_lock_certificate(ids[query["moving_body"]].vertices,
                                       tuple(ids[name].vertices for name in query["fixed_neighbors"]))


def t1b_cases(directory=None):
    from eab.kernel2d.assembly import Assembly2, Body2
    directory = directory or ROOT / "fixtures/eab2_cases/t1b_l1"
    manifest = read_json(directory / "manifest.json")
    require(manifest["count"] == len(manifest["cases"]), "T1b case count")
    for entry in manifest["cases"]:
        data = (directory / entry["path"]).read_bytes()
        require(hashlib.sha256(data).hexdigest() == entry["sha256"], "T1b projection integrity")
        record = read_json(gzip.decompress(data))
        bodies = []
        for item in record["bodies"]:
            ring = tuple(vec(p) for p in item["original_vertices"])
            require(all(Q(float(x)) == x for p in ring for x in p), "T1b binary64 lossy geometry")
            require(all(Q(float(rational(x))) == rational(x) for name in ("reference_point", "dof_anchor") for x in item[name]), "T1b binary64 lossy frame")
            body = Body2.from_vertices(item["body_id"], ring,
                reference_point=vec(item["reference_point"]), dof_anchor=vec(item["dof_anchor"]),
                boundary_type=item["boundary_type"], dof_mask=tuple(item["dof_mask"]),
                dead=vec(item["dead"]), live=vec(item["live"]))
            require(list(body.vertex_ids) == item["vertex_ids"], "T1b vertex ID mismatch")
            bodies.append(body)
        pairs = tuple((i, j) for i in range(len(bodies)) for j in range(i + 1, len(bodies)))
        assembly = Assembly2(tuple(bodies), pairs, "complete", record["profile"], Q(0))
        yield record["case_id"], assembly, [
            (0, dict(kind="assembly", frozen_contact_status=record["contact_status"],
                     frozen_constraint_count=record["constraint_count"]), None),
            (1, dict(kind="first_order"), record["first_order"])]



def transform_assembly(assembly, matrix, scale, translation):
    from eab.kernel2d.assembly import Assembly2, Body2
    def transform(point):
        return tuple(scale * dot(row, point) + translation[i] for i, row in enumerate(matrix))
    bodies = []
    for b in assembly.bodies:
        mask = tuple(b.dof_mask[next(j for j, v in enumerate(row) if v)] for row in matrix) + (b.dof_mask[2],)
        bodies.append(Body2.from_vertices(b.body_id, tuple(transform(p) for p in b.original_vertices),
            reference_point=transform(b.reference_point), dof_anchor=transform(b.dof_anchor),
            boundary_type=b.boundary_type, dof_mask=mask))
    return Assembly2(tuple(bodies), assembly.pairs, assembly.completeness, assembly.profile, assembly.mu)


def transformed_generators(result, target_dofs, matrix, scale):
    if result["generators"] is None:
        return None
    det = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    output = set()
    for row in result["generators"]:
        indexed = dict(zip(map(tuple, result["dofs"]), vec(row)))
        out = []
        for body, coordinate in target_dofs:
            if coordinate == 2:
                out.append(det * indexed.get((body, 2), Q(0)))
            else:
                out.append(scale * sum((matrix[coordinate][j] * indexed.get((body, j), Q(0)) for j in (0, 1)), Q(0)))
        norm = sum(map(abs, out))
        output.add(tuple(x / norm for x in out))
    return output


def metamorphic_cases():
    names = {"regression_" + n for n in ("a_saw", "b_bare_vv", "c_redundant_vv", "d_flush_mu0", "e_mixed_vv_edge", "f_convex_in_notch")}
    transforms = (
        (((1, 0), (0, 1)), Q(1), (Q(0), Q(0))),
        (((0, -1), (1, 0)), Q(1, 8), (Q(1024), Q(-2048))),
        (((-1, 0), (0, -1)), Q(8), (Q(131072), Q(-65536))),
        (((0, 1), (-1, 0)), Q(2), (Q(17, 2), Q(-9, 4))),
        (((-1, 0), (0, 1)), Q(1, 2), (Q(-1024), Q(2048))),
        (((0, 1), (1, 0)), Q(4), (Q(65536), Q(-131072))))
    for name, assembly, queries in formal_cases(selection=names):
        base = {q["kind"]: r for _, q, r in queries if q["kind"] != "lock"}
        for i, (rotation, scale, translation) in enumerate(transforms):
            transformed = transform_assembly(assembly, rotation, scale, translation)
            output = []
            contacts = None
            for index, query, original in queries:
                fresh_value = python_query(transformed, query, contacts)
                if query["kind"] == "assembly":
                    contacts = fresh_value
                fresh = wire(fresh_value)
                require(fresh["mathematical_status"] == original["mathematical_status"], "transformed classification changed")
                if query["kind"] == "lock":
                    require(fresh["refinement"] == original["refinement"], "transformed lock refinement changed")
                elif query["kind"] == "first_order" and fresh["generators"] is not None:
                    require(transformed_generators(base["first_order"], fresh["dofs"], rotation, scale) == set(mat(fresh["generators"])),
                            "transformed generator set changed")
                output.append((index, query, fresh))
            yield f"meta/{name}/{i}", transformed, output

def run(dll, cases, output, *, fixture_audit_only=False):
    source_paths = ["tools/eab2_c3l1_diff.py", "tools/eab2_c3l1_abi.py",
                    "src/eab/lp.py", "src/eab/kernel2d/assembly.py", "src/eab/kernel2d/contacts.py",
                    "src/eab/kernel2d/lock.py", "src/eab/kernel2d/mobility.py",
                    "src/eab/kernel2d/global_entrance.py", "src/eab/kernel2d/exact.py"]
    source_hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in source_paths}
    counts, strict_counts = Counter(), Counter()
    rows, mismatches = [], []
    started = time.perf_counter()
    for name, assembly, queries in cases:
        ahandle = chandle = None
        contacts = None
        case_rows = []
        try:
            if dll is not None:
                ahandle = dll.assembly(assembly)
            for index, query, expected in queries:
                kind = query["kind"]
                item = dict(case_id=name, query_index=index, kind=kind)
                t = time.perf_counter()
                value = python_query(assembly, query, contacts)
                item["python_kernel_seconds"] = time.perf_counter() - t
                fresh = read_json(json.dumps(wire(value), ensure_ascii=False).encode("utf-8"))
                item["python_seconds"] = time.perf_counter() - t
                if kind == "assembly":
                    contacts = value
                    if "frozen_contact_status" in query:
                        require(value.status == query["frozen_contact_status"], "T1b frozen contact status")
                        require(len(value.constraints) == query["frozen_constraint_count"], "T1b frozen constraint count")
                if expected is not None:
                    check = compare(kind, expected, fresh, assembly=assembly, contacts=contacts)
                    require(not check["semantic_differences"], "fresh Python referee differs from frozen expectation: " + repr(check["semantic_differences"][:2]))
                else:
                    expected = fresh
                if fixture_audit_only:
                    actual = fresh
                    item["cpp_seconds"] = None
                else:
                    t = time.perf_counter()
                    if kind == "assembly" and chandle is None:
                        chandle = dll.contacts(ahandle)
                    actual = dll.query(ahandle, chandle, assembly, query)
                    item["cpp_seconds"] = time.perf_counter() - t
                comparison = compare(kind, expected, actual, assembly=assembly, contacts=contacts)
                item["semantic_mismatch_count"] = len(comparison["semantic_differences"])
                item["strict_field_difference_count"] = len(comparison["strict_field_differences"])
                item["semantic_differences"] = comparison["semantic_differences"]
                item["strict_field_differences"] = comparison["strict_field_differences"]
                item["mathematical_status"] = actual["mathematical_status"]
                counts[kind] += 1
                strict_counts[kind] += item["strict_field_difference_count"]
                if comparison["semantic_differences"]:
                    mismatches.append(dict(case_id=name, query_index=index, kind=kind, reason="semantic fields differ"))
                case_rows.append(item)
        except Exception as error:
            mismatches.append(dict(case_id=name, reason=type(error).__name__ + ": " + str(error)))
        finally:
            if dll is not None and chandle is not None:
                dll.check(dll.contact_set2_destroy(dll.context, chandle), "contact_set2_destroy")
            if dll is not None and ahandle is not None:
                dll.check(dll.assembly2_destroy(dll.context, ahandle), "assembly2_destroy")
        require(len(case_rows) <= len(queries), "internal query count")
        if len(case_rows) != len(queries):
            mismatches.append(dict(case_id=name, reason="not all selected queries executed", expected=len(queries), actual=len(case_rows)))
        rows.extend(case_rows)
        progress = dict(case_id=name, completed_queries=len(rows), mismatch=len(mismatches), seconds=time.perf_counter() - started)
        output.with_suffix(".progress.json").write_text(json.dumps(progress, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(progress), flush=True)
    source_hashes_after = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in source_paths}
    if source_hashes_after != source_hashes:
        mismatches.append(dict(reason="source bytes changed during differential; run invalid"))
    last = ("C3L1_FIXTURE_AUDIT" if fixture_audit_only else "C3L1_DIFF") + " " + " ".join(f"{k}={counts[k]}" for k in KINDS) + f" mismatch={len(mismatches)} strict_fields={sum(strict_counts.values())}"
    result = dict(schema="eab2.c3l1.differential.v1", cpp_executed=not fixture_audit_only,
        build_identity=dll.identity if dll is not None else None,
        dll_path=str(dll.path) if dll is not None else None,
        dll_sha256=dll.sha256 if dll is not None else None,
        source_sha256=source_hashes, source_pre_post_equal=source_hashes_after == source_hashes,
        counts=dict(counts),
        timing_scope="One query per assembly state; excludes process/DLL startup and input decode; first_order uses prebuilt contacts on both sides. python_seconds includes query+dataclass JSON encode/decode; python_kernel_seconds is query only; cpp_seconds includes ABI+ctypes+JSON decode; no performance gate",
        strict_field_difference_counts=dict(strict_counts), mismatches=mismatches,
        queries=rows, seconds=time.perf_counter() - started, last_line=last)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(last, flush=True)
    return 1 if mismatches else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dll", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", action="append")
    parser.add_argument("--dataset", choices=("formal", "t1b", "meta", "all"), default="all")
    parser.add_argument("--fixture-audit-only", action="store_true")
    args = parser.parse_args()
    require(args.fixture_audit_only or args.dll is not None, "--dll is mandatory for C++ differential")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    selection = set(args.case) if args.case else None
    def cases():
        if args.dataset in ("formal", "all"):
            yield from formal_cases(selection=selection)
        if args.dataset in ("t1b", "all"):
            for item in t1b_cases():
                if selection is None or item[0] in selection:
                    yield item
        if args.dataset in ("meta", "all"):
            for item in metamorphic_cases():
                if selection is None or item[0] in selection:
                    yield item
    selected = list(cases())
    require(bool(selected), "no selected cases")
    if selection is not None:
        require({item[0] for item in selected} == selection, "unknown or missing selected case")
    dll = None
    try:
        if not args.fixture_audit_only:
            from eab2_c3l1_abi import Dll
            dll = Dll(args.dll)
        return run(dll, selected, args.output, fixture_audit_only=args.fixture_audit_only)
    finally:
        if dll is not None:
            dll.close()


if __name__ == "__main__":
    raise SystemExit(main())
