"""Approved case codec and measured queries with per-batch source provenance.

The codec preserves the approved schema without implying batch acceptance. Certificates are exact
rationals, input bits are binary64, and timings are neither certificates nor
estimates of a C++ implementation. Geometry generators live in adapters/tia2d.
"""
from dataclasses import fields, is_dataclass, replace
from fractions import Fraction as Q
import hashlib
import json
import math
from pathlib import Path
import platform
import struct
import subprocess
import sys
import time
from tia2d_provenance import git_provenance

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eab.kernel2d.contacts import assemble_contact_set2
from eab.kernel2d.exact import polygons_overlap_exact
from eab.kernel2d.lock import translation_lock_certificate
from eab.kernel2d.mobility import first_order_free_twists
from eab.kernel2d.sensitivity import LimitSeed2, build_limit_seed2, evaluate_sensitivity2
from eab.kernel2d.statics import critical_parameter, limit_load_ideal_exact_2d
from tia2d_seed import geometry_seed

SCHEMA_REVISION = "tia2d-2"
SCHEMA_APPROVAL = "CLAUDE-APPROVED-TIA2D-2"
APPROVAL_DATE = "2026-10-19"
TOOL_VERSION = "tia2d-cases-3"
MAX_BYTES = 1_000_000
VALIDITY_CONDITIONS = frozenset(("L1接触骨架不变", "axial_only_plate", "frozen_reference_points",
    "shared_interface_parameter", "nonnegative_t", "positive_h", "fixed_polygon_table",
    "positive_amplitude", "positive_wavelength", "临界证书基非奇异", "所列越零分量及方向保持有效",
    "true_vv_excluded_from_statics"))


class _CaseDraft(dict):
    """A JSON dictionary with an in-memory-only source guard, never serialized."""

    def __init__(self, record, source_stamp):
        super().__init__(record)
        self._source_stamp = source_stamp


def rational(value):
    value = Q(value)
    return str(value.numerator) + "/" + str(value.denominator)


def binary64(value):
    """Lossless input encoder, preserving the original float negative zero."""
    if isinstance(value, bool):
        raise ValueError("boolean is not a numeric input")
    rounded = float(value)
    if not math.isfinite(rounded):
        raise ValueError("NaN/Inf input is not allowed")
    if Q(rounded) != Q(value):
        raise ValueError("non-binary64 input belongs to Python-only cases")
    return struct.pack(">d", rounded).hex()


def decode_bits(bits):
    if (not isinstance(bits, str) or len(bits) != 16
            or any(c not in "0123456789abcdef" for c in bits)):
        raise ValueError("bits must be sixteen lowercase hexadecimal digits")
    value = struct.unpack(">d", bytes.fromhex(bits))[0]
    if not math.isfinite(value):
        raise ValueError("NaN/Inf input is not allowed")
    return value


def _current_input(raw, exact):
    return raw if raw and tuple(Q(v) for v in raw) == tuple(exact) else exact


_EXACT_FIELDS = frozenset("point start end sample vertices active_edges squared_distance radius separation_ray seam_ray tangent normal boundaries forbidden matrix rhs objective exact_x exact_y rays lineality generators multipliers twist A b c reference_points dof_anchors mu exact_value feasible_point improving_ray farkas exact_threshold dA db dc directional_derivative left_derivative right_derivative primal_recession_ray dual_recession_ray normalized_value forward_certificate reverse_certificate".split())


def _exact_wire(value):
    if value is None:
        return None
    if isinstance(value, (int, Q)) and not isinstance(value, bool):
        return rational(value)
    if isinstance(value, (tuple, list)):
        return [_exact_wire(item) for item in value]
    return wire(value)


def wire(value):
    """Private, exact JSON projection; object links are emitted separately."""
    if isinstance(value, Q):
        return rational(value)
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return {"bits": binary64(value), "exact": rational(value)}
    if is_dataclass(value):
        return {field.name: (_exact_wire(getattr(value, field.name)) if field.name in _EXACT_FIELDS
                            and not (field.name == "b" and isinstance(getattr(value, field.name), int))
                            else wire(getattr(value, field.name))) for field in fields(value)
                if field.name not in ("assembly", "contact_set", "problem") and not field.name.startswith("_")}
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("wire mappings require explicit string keys")
        return {key: wire(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [wire(item) for item in value]
    raise TypeError("unsupported certificate field: " + type(value).__name__)


def input_record(assembly):
    """Encode actual vertices, then independently recheck the decoded input.

    Uses only struct decoding, exact rational cross products and ear/SAT
    polygons_overlap_exact; does not consult the production contact skeleton.
    No rounding is accepted in the exported subset. Thus every turn and edge
    cross product must be unchanged, including exact parallelism/collinearity.
    """
    bodies, decoded = [], []
    for body in assembly.bodies:
        raw = body.original_vertices or body.vertices
        original_bits = [[binary64(v) for v in p] for p in raw]
        ids = body.vertex_ids or tuple(range(len(body.vertices)))
        ccw_bits = [original_bits[i] for i in ids]
        ring = tuple(tuple(Q(decode_bits(v)) for v in p) for p in ccw_bits)
        if ring != body.vertices:
            raise ValueError("original IDs and current geometry do not match")
        decoded.append(ring)
        bodies.append(dict(body_id=body.body_id, vertices_xy_bits=original_bits,
            vertex_ids=list(range(len(raw))), ccw_vertex_ids=list(ids), geometry_version="input-1",
            reference_point=[rational(v) for v in body.reference_point],
            reference_point_bits=[binary64(v) for v in _current_input(body._reference_input, body.reference_point)],
            dof_anchor=[rational(v) for v in body.dof_anchor],
            dof_anchor_bits=[binary64(v) for v in _current_input(body._anchor_input, body.dof_anchor)],
            boundary_type=body.boundary_type, dof_mask=list(body.dof_mask),
            dead=[rational(v) for v in body.dead], live=[rational(v) for v in body.live],
            load_source=dict(kind="explicit_wrench_about_reference",
                dead_bits=[binary64(v) for v in _current_input(body._dead_input, body.dead)],
                live_bits=[binary64(v) for v in _current_input(body._live_input, body.live)])))
    return dict(bodies=bodies, mu_bits=binary64(assembly.mu), profile=assembly.profile,
        completeness=assembly.completeness,
        adjacency=None if assembly.pairs is None else [[assembly.bodies[i].body_id,
            assembly.bodies[j].body_id] for i, j in assembly.pairs])


def input_audit(assembly, inputs=None, expected_contacts=None):
    """Tool-only audit outside the hashed Assembly; every predicate is evaluated."""
    inputs = input_record(assembly) if inputs is None else inputs
    rings = [tuple(tuple(Q(decode_bits(v)) for v in item["vertices_xy_bits"][i])
                   for i in item["ccw_vertex_ids"]) for item in inputs["bodies"]]
    pairs, expected, before, after, parallel = [], [], [], [], []
    for i, j in assembly.pairs if assembly.pairs is not None else (
            (i, j) for i in range(len(rings)) for j in range(i + 1, len(rings))):
        state = polygons_overlap_exact(rings[i], rings[j])
        old = polygons_overlap_exact(assembly.bodies[i].vertices, assembly.bodies[j].vertices)
        pair = [assembly.bodies[i].body_id, assembly.bodies[j].body_id]
        pairs.append(dict(a=pair[0], b=pair[1], state={-1: "OUTSIDE", 0: "CONTACT", 1: "OVERLAP"}[state]))
        if old == 0:
            expected.append(pair)
    def concave(ring):
        return [k for k in range(len(ring)) if
            (ring[k][0] - ring[k - 1][0]) * (ring[(k + 1) % len(ring)][1] - ring[k][1])
            - (ring[k][1] - ring[k - 1][1]) * (ring[(k + 1) % len(ring)][0] - ring[k][0]) < 0]
    edges = []
    for body, ring in zip(assembly.bodies, rings):
        before.append(dict(body_id=body.body_id, ccw_indices=concave(body.vertices)))
        after.append(dict(body_id=body.body_id, ccw_indices=concave(ring)))
        edges.extend((body.body_id, k, (ring[(k + 1) % len(ring)][0] - p[0],
                       ring[(k + 1) % len(ring)][1] - p[1])) for k, p in enumerate(ring))
    for index, (a, i, u) in enumerate(edges):
        for b, j, v in edges[index + 1:]:
            if u[0] * v[1] - u[1] * v[0] == 0:
                parallel.append([a, i, b, j])
    expected = expected if expected_contacts is None else [list(pair) for pair in expected_contacts]
    actual = [[row["a"], row["b"]] for row in pairs if row["state"] == "CONTACT"]
    matches = sorted(sorted(pair) for pair in expected) == sorted(sorted(pair) for pair in actual)
    if not matches:
        raise ArithmeticError("RN geometry differs from the expected CONTACT skeleton")
    return dict(lossless_binary64=all(ring == body.vertices for body, ring in zip(assembly.bodies, rings)),
        exact_pair_states=pairs, exact_parallel_edge_pairs=parallel,
        concave_vertices_before=before, concave_vertices_after=after,
        no_new_concave_vertices=before == after, expected_contact_pairs=expected,
        contact_skeleton_matches=matches)


def _clocked(function, *args, scope, **kwargs):
    start = time.perf_counter()
    result = function(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return result, dict(seconds=elapsed, clock="perf_counter", repeat_index=0,
                        cache_state="warm", scope=scope)


def _query(kind, result, clock, observable):
    payload = wire(result)
    has_display = {"assembly": result.mathematical_status not in (None, "UNPROVED"),
        "first_order": getattr(result, "cone_is_zero", None) is not None,
        "limit": getattr(result, "exact_value", None) is not None,
        "lock": getattr(result, "status", None) is not None,
        "critical": getattr(result, "mu_lo", None) is not None and getattr(result, "mu_hi", None) is not None,
        "sensitivity": any(getattr(result, key, None) is not None for key in
            ("directional_derivative", "left_derivative", "right_derivative"))}[kind]
    display = "EXACT" if has_display else "NOT_APPLICABLE"
    if "display_status" in payload:
        payload["display_status"] = display
    return dict(kind=kind, source="python_referee", observable=observable,
        call_status=result.call_status, mathematical_status=result.mathematical_status,
        display_status=display,
        result=payload, python_wallclock=clock)


def comparison_contract(kind):
    """Path rules override the exact default; ** matches any descendant.

    Certificate vectors/bases are not unique mathematical answers. C++ must
    verify their defining identities and inequalities, not copy Python's pivot
    choices. Informational fields never decide mathematical agreement.
    """
    rules = {"python_wallclock.**": "informational", "display_note.**": "informational",
        "result.**.basis": "verify_certificate", "result.**.exact_x": "verify_certificate",
        "result.**.exact_y": "verify_certificate", "result.**.feasible_point": "verify_certificate",
        "result.**.improving_ray": "verify_certificate", "result.**.farkas": "verify_certificate",
        "result.**.multipliers": "verify_certificate", "result.**.cell_index": "informational",
        "result.**.labels": "set", "result.**.sources": "set",
        "result.validity_conditions": "set"}
    if kind == "assembly":
        rules.update({"result." + field: "set" for field in
            ("constraints", "points", "raw_sources", "segments", "unresolved", "pair_states")})
        rules["result.redundancy_certificates"] = "verify_certificate"
        rules["result.reachable_witnesses"] = "verify_certificate"
    elif kind == "first_order":
        rules.update({"result." + field: "verify_certificate" for field in
            ("rays", "lineality", "generators", "zero_certificates")})
    elif kind == "lock":
        rules.update({"result." + field: "verify_certificate" for field in
            ("local_cells", "radius_bounds", "radius", "separation_ray", "seam_ray", "arcs")})
        rules["result.contact_sources"] = "set"
    elif kind == "critical":
        rules["result.threshold_proof.**"] = "verify_certificate"
        rules["result.critical_polynomials"] = "verify_certificate"
        rules["result.queries"] = "informational"
    elif kind == "sensitivity":
        rules.update({"result." + field: "verify_certificate" for field in
            ("forward_certificate", "reverse_certificate", "primal_recession_ray", "dual_recession_ray",
             "implicit_components", "selected_piece", "piece_jacobians", "branch_certificate")})
        rules["result.tied_labels"] = rules["result.near_labels"] = "set"
    return dict(default="exact", rules=rules)


def _stable_body_references(value, body_ids):
    """Convert private array indices to explicit IDs in exported certificates."""
    if isinstance(value, dict):
        result = {key: _stable_body_references(item, body_ids) for key, item in value.items()}
        if "a" in result and "b" in result and isinstance(result["a"], int) and isinstance(result["b"], int):
            result["a"], result["b"] = body_ids[result["a"]], body_ids[result["b"]]
        if "dofs" in result:
            result["dofs"] = [[body_ids[i], k] for i, k in result["dofs"]]
        if "pair_states" in result:
            states = result["pair_states"]
            names = {-1: "OUTSIDE", 0: "CONTACT", 1: "OVERLAP"}
            result["pair_states"] = ([[body_ids[i], body_ids[j], names[state]] for i, j, state in states]
                                      if states and isinstance(states[0], list) else
                                      [names[state] for state in states])
        return result
    if isinstance(value, list):
        return [_stable_body_references(item, body_ids) for item in value]
    return value


def _source_stamp():
    """Hash actual source-root bytes, including ignored execution snapshots.

The historical uncommitted_source_* keys are retained in this draft codec,
but their explicitly tagged basis is the complete src/tests/tools manifest,
not Git's dirty-path view. Git HEAD is only the provenance anchor.
"""
    git = git_provenance(ROOT)
    records = []
    for folder in ("src", "tests", "tools"):
        for path in sorted((ROOT / folder).rglob("*")):
            if path.is_file() and "__pycache__" not in path.relative_to(ROOT).parts:
                records.append(dict(path=path.relative_to(ROOT).as_posix(),
                                    sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    digest = hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()
    return dict(**git, uncommitted_source_files=records, uncommitted_source_sha256=digest,
                source_manifest_basis="actual_root_src_tests_tools_bytes_v1", command=list(sys.argv),
                tool_version=TOOL_VERSION,
                design_sha256=hashlib.sha256((ROOT / "docs/eab2_design.md").read_bytes()).hexdigest())


def _source_key(stamp):
    return (stamp["git_commit"], stamp["uncommitted_source_sha256"],
            json.dumps(stamp["uncommitted_source_files"], sort_keys=True),
            stamp["source_manifest_basis"], stamp["tool_version"], stamp["design_sha256"])


def _input_hash(case):
    return hashlib.sha256(json.dumps(case["assembly"], sort_keys=True, allow_nan=False).encode()).hexdigest()


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode("utf-8")


def _source_manifest(cases, stamp):
    return dict(schema="eab2.source-manifest.v1", schema_revision=SCHEMA_REVISION,
        schema_approval=SCHEMA_APPROVAL, approval_date=APPROVAL_DATE,
        git_commit=stamp["git_commit"], git_commit_reason=stamp["git_commit_reason"],
        source_manifest_basis=stamp["source_manifest_basis"],
        source_files=stamp["uncommitted_source_files"],
        source_files_sha256=stamp["uncommitted_source_sha256"], tool_version=stamp["tool_version"],
        command=stamp["command"], python=platform.python_version(), platform=platform.platform(),
        design_sha256=stamp["design_sha256"],
        inputs=[dict(case_id=case["case_id"], input_sha256=_input_hash(case)) for case in cases])


def _lock_sources(query, moving, fixed):
    a_ids = moving.vertex_ids or tuple(range(len(moving.vertices)))
    for source in query["result"]["contact_sources"]:
        neighbor = fixed[source["neighbor_index"]]
        b_ids = neighbor.vertex_ids or tuple(range(len(neighbor.vertices)))
        kind, i, j = source["label"]
        source["neighbor_body_id"] = neighbor.body_id
        source["label"] = ([kind, moving.body_id, a_ids[i], neighbor.body_id,
                             [b_ids[j], b_ids[(j + 1) % len(b_ids)]]] if kind == "VE" else
                            [kind, moving.body_id, [a_ids[i], a_ids[(i + 1) % len(a_ids)]],
                             neighbor.body_id, b_ids[j]])
    # Local cell indices are addresses within an explicitly ID-bound neighbor.
    for key in ("local_cells", "radius_bounds"):
        for item in query["result"][key]:
            item["neighbor_body_id"] = fixed[item["neighbor_index"]].body_id


def _sensitivity_query(result, seed, *, target="limit", parameter="mu", mu_seed=None,
                       positive_direction_valid=True, negative_direction_valid=True,
                       validity_conditions=("L1接触骨架不变",), tied_labels=()):
    """Keep all derivative inputs and explicit links to their original problem."""
    sensitivity, elapsed = _clocked(evaluate_sensitivity2, result, seed,
        parameter=parameter, threshold_mu_seed=mu_seed,
        positive_direction_valid=positive_direction_valid,
        negative_direction_valid=negative_direction_valid,
        validity_conditions=validity_conditions, tied_labels=tied_labels,
        scope="critical_basis_implicit_derivative" if target == "critical" else
              "optimal_face_tests_and_directional_LPs")
    observable = ("d_mu_crit_d_" if target == "critical" else "d_live_load_multiplier_d_") + parameter
    query = _query("sensitivity", sensitivity, elapsed, observable)
    query["seed"] = wire(seed)
    query["direction_domain"] = dict(positive=positive_direction_valid, negative=negative_direction_valid)
    query["declared_validity_conditions"] = wire(tuple(validity_conditions))
    right, left = sensitivity.right_derivative, sensitivity.left_derivative
    query["directional_values"] = dict(D_plus=None if right is None else rational(right),
                                        D_minus=None if left is None else rational(-left))
    if target == "critical":
        query["threshold_mu_seed"] = wire(mu_seed)
        query["threshold_query_ref"] = "critical"
        query["threshold_certificate_ref"] = dict(query="critical", field="result.threshold_certificate")
    else:
        query["limit_query_ref"] = "limit"
    return query


def _extra_sensitivity_query(spec, limit_result, critical_result):
    """Private request: exact seed plus the exact problem it was built against.

No family-specific derivative is constructed here. The caller supplies a
production LimitSeed2, its LimitProblem2, target, and valid directions.
"""
    allowed = {"seed", "problem", "target", "parameter", "threshold_mu_seed",
               "positive_direction_valid", "negative_direction_valid", "validity_conditions", "tied_labels",
               "geometry_seed", "display_note"}
    if not isinstance(spec, dict) or set(spec) - allowed:
        raise ValueError("unknown sensitivity query input")
    seed = spec.get("seed")
    if not isinstance(seed, LimitSeed2):
        raise ValueError("sensitivity query requires an exact LimitSeed2")
    # Preserve the original affine primitives retained by the production
    # builder; recreating only dA/db/dc would discard higher-order K data.
    seed = replace(seed, dA=tuple(tuple(Q(v) for v in row) for row in seed.dA),
                   db=tuple(Q(v) for v in seed.db), dc=tuple(Q(v) for v in seed.dc))
    target = spec.get("target", "limit")
    if target not in ("limit", "critical"):
        raise ValueError("sensitivity target must be limit or critical")
    result = limit_result if target == "limit" else critical_result
    if result is None or (target == "critical" and result.threshold_certificate is None):
        raise ValueError("threshold query and exact endpoint certificate are required")
    problem = result.problem if target == "limit" else result.threshold_certificate.problem
    if problem is None or spec.get("problem") != problem:
        raise ValueError("sensitivity seed problem does not match the referenced query")
    positive, negative = spec.get("positive_direction_valid", True), spec.get("negative_direction_valid", True)
    if not isinstance(positive, bool) or not isinstance(negative, bool):
        raise ValueError("sensitivity direction validity must be boolean")
    mu_seed = spec.get("threshold_mu_seed")
    if target == "critical" and mu_seed is None:
        mu_seed = build_limit_seed2(problem, mu_seed=1)
    if mu_seed is not None and (target != "critical" or not isinstance(mu_seed, LimitSeed2)):
        raise ValueError("threshold_mu_seed requires a critical query and LimitSeed2")
    if mu_seed is not None:
        mu_seed = replace(mu_seed, dA=tuple(tuple(Q(v) for v in row) for row in mu_seed.dA),
                          db=tuple(Q(v) for v in mu_seed.db), dc=tuple(Q(v) for v in mu_seed.dc))
    parameter = spec.get("parameter", seed.parameter)
    if not isinstance(parameter, str) or not parameter:
        raise ValueError("sensitivity parameter must be a nonempty name")
    query = _sensitivity_query(result, seed, target=target, parameter=parameter, mu_seed=mu_seed,
        positive_direction_valid=positive, negative_direction_valid=negative,
        validity_conditions=tuple(spec.get("validity_conditions", ("L1接触骨架不变",))),
        tied_labels=tuple(spec.get("tied_labels", ())))
    query["geometry_seed"] = spec.get("geometry_seed")
    if spec.get("display_note"):
        query["display_note"] = spec["display_note"]
    return query


def build_case(assembly, case_id, *, lock_bodies=(), include_critical=False, mu_max=1.0,
               include_sensitivity=False, critical_max_steps=64, _sensitivity_queries=(),
               _sensitivity_factory=None, _sensitivity_labels=(), _family_parameters=None,
               _expected_contacts=None, _lock_pairs=(), _critical_param="mu"):
    """Build one approved-format case in memory, not a completed batch export.

    Contact assembly is measured once; first_order and limit use that very
    ContactSet2. Their clocks explicitly exclude geometry assembly. Locks
    specify every other body as a fixed neighbor, irrespective of its multi-
    body boundary; this difference is explicit in each lock query's inputs.
    Additional private sensitivity requests provide production exact seeds and
    matching original problems; the codec never hardcodes a geometry family.
    """
    if type(critical_max_steps) is not int or critical_max_steps != 64:
        raise ValueError("approved schema requires critical max_steps=64 for replay")
    def check_numeric(value):
        if isinstance(value, (int, float, Q)) and not isinstance(value, bool):
            binary64(value)
        elif isinstance(value, dict):
            for item in value.values():
                check_numeric(item)
        elif isinstance(value, (tuple, list)):
            for item in value:
                check_numeric(item)
    check_numeric(_family_parameters)
    provenance = _source_stamp()
    inputs = input_record(assembly)
    audit = input_audit(assembly, inputs, _expected_contacts)
    contacts, elapsed = _clocked(assemble_contact_set2, assembly, scope="contact_assembly")
    queries = [_query("assembly", contacts, elapsed, "zero_window_contact_set")]
    mobility, elapsed = _clocked(first_order_free_twists, assembly, contacts,
                                scope="normal_cone_with_prebuilt_contact_set")
    queries.append(_query("first_order", mobility, elapsed, "first_order_normal_cone"))
    result, elapsed = _clocked(limit_load_ideal_exact_2d, assembly, contacts,
                              scope="LP_and_exact_certificates_with_prebuilt_contact_set")
    query = _query("limit", result, elapsed, "live_load_multiplier")
    query["problem"] = wire(result.problem)
    queries.append(query)
    limit_result, critical_result = result, None
    if include_sensitivity:
        seed = build_limit_seed2(result.problem, mu_seed=1) if result.problem is not None else None
        queries.append(_sensitivity_query(result, seed, negative_direction_valid=assembly.mu > 0,
                                          tied_labels=tuple(_sensitivity_labels)))
        queries[-1]["geometry_seed"] = geometry_seed(assembly, "mu", mu=1)
    for i, neighbors_override in tuple((i, None) for i in lock_bodies) + tuple(_lock_pairs):
        if not 0 <= i < len(assembly.bodies):
            raise ValueError("unknown moving body")
        fixed = (tuple(j for j in range(len(assembly.bodies)) if j != i)
                 if neighbors_override is None else tuple(neighbors_override))
        neighbors = tuple(assembly.bodies[j].vertices for j in fixed)
        result, elapsed = _clocked(translation_lock_certificate, assembly.bodies[i].vertices,
                                  neighbors, scope="local_cells_angular_cover_and_radius")
        query = _query("lock", result, elapsed, "local_translation_separation")
        query["moving_body"] = assembly.bodies[i].body_id
        query["fixed_neighbors"] = [assembly.bodies[j].body_id for j in fixed]
        _lock_sources(query, assembly.bodies[i], tuple(assembly.bodies[j] for j in fixed))
        queries.append(query)
    if include_critical:
        result, elapsed = _clocked(critical_parameter, assembly, param=_critical_param, mu_max=mu_max,
                                  max_steps=critical_max_steps, contact_set=contacts,
                                  scope="threshold_LPs_and_certificates")
        critical_result = result
        query = _query("critical", result, elapsed, "friction_unboundedness_threshold")
        for key in ("mu_lo", "mu_hi"):
            value = getattr(result, key)
            query["result"].pop(key, None)
            query["result"][key + "_bits"] = None if value is None else binary64(value)
        query["mu_max_bits"] = binary64(mu_max)
        query["param"] = _critical_param
        query["midpoint_rule"] = "exact_mean_else_floor_to_binary64_then_strict_interior_v1"
        # Endpoint result objects need their LP data, not only x/y/r vectors.
        for key in ("lower_certificate", "upper_certificate", "threshold_certificate"):
            value = getattr(result, key, None)
            if value is not None:
                query["result"][key]["problem"] = wire(value.problem)
        queries.append(query)
    extra = tuple(_sensitivity_queries)
    if _sensitivity_factory is not None:
        extra += tuple(_sensitivity_factory(limit_result, critical_result))
    queries.extend(_extra_sensitivity_query(spec, limit_result, critical_result) for spec in extra)
    body_ids = [body.body_id for body in assembly.bodies]
    queries = [_stable_body_references(query, body_ids) for query in queries]
    input_hash = hashlib.sha256(json.dumps(inputs, sort_keys=True, allow_nan=False).encode()).hexdigest()
    contact_hash = hashlib.sha256(json.dumps(queries[0]["result"], sort_keys=True, allow_nan=False).encode()).hexdigest()
    for query in queries:
        query.setdefault("geometry_seed", geometry_seed(assembly))
        query["comparison_contract"] = comparison_contract(query["kind"])
        if query["kind"] == "sensitivity" and "threshold_query_ref" in query:
            query["comparison_contract"]["rules"]["result.tied_labels"] = "verify_certificate"
        query["assembly_ref"] = dict(id=input_hash, version="input-1")
        if query["kind"] != "lock":
            query["contact_set_ref"] = dict(id=contact_hash, version="contact-1")
    if _source_key(_source_stamp()) != _source_key(provenance):
        raise RuntimeError("source changed during query generation; discard and rerun")
    record = dict(schema="eab2.case.v1", schema_revision=SCHEMA_REVISION, case_id=case_id,
        input_version="tia2d-input-1", design_sha256=hashlib.sha256((ROOT / "docs/eab2_design.md").read_bytes()).hexdigest(),
        profile="profile1", assembly=inputs, input_audit=audit, queries=queries,
        family_parameters=wire(_family_parameters or {}), alias_of=None, role="primary",
        provenance={},
        python_wallclock=dict(clock="perf_counter", scope="per_query_above", includes_process_start=False))
    manifest = _source_manifest((record,), provenance)
    record["provenance"] = dict(source_manifest_sha256=hashlib.sha256(_json_bytes(manifest)).hexdigest())
    return _CaseDraft(record, provenance)


def encode_case(case):
    """Strict deterministic JSON; direct single-file encoding has a hard cap."""
    data = _json_bytes(case)
    if len(data) > MAX_BYTES:
        raise ValueError("case exceeds 1 MB; export_cases splits queries without discarding certificates")
    return data


def _split_case(case, max_bytes=MAX_BYTES):
    """Partition ordered whole queries, never truncating any exact certificate."""
    if not 1 <= max_bytes <= MAX_BYTES:
        raise ValueError("invalid part size limit")
    queries = case["queries"]
    groups, current = [], []
    # Pessimistic fragment numbers bound the final metadata length.
    bound = max(1, len(queries))
    def part(indices, index, count):
        return dict(case, queries=[queries[i] for i in indices],
                    fragment=dict(index=index, count=count, query_indices=list(indices)))
    for i in range(len(queries)):
        candidate = current + [i]
        if len(_json_bytes(part(candidate, bound, bound))) > max_bytes:
            if not current:
                raise ValueError("single query exceeds 1 MB; certificate subdivision is not supported")
            groups.append(current)
            current = [i]
            if len(_json_bytes(part(current, bound, bound))) > max_bytes:
                raise ValueError("single query exceeds 1 MB; certificate subdivision is not supported")
        else:
            current = candidate
    if current or not groups:
        groups.append(current)
    results = []
    for index, indices in enumerate(groups):
        data = _json_bytes(part(indices, index, len(groups)))
        if len(data) > max_bytes:
            raise ValueError("case envelope exceeds the part size limit")
        results.append((indices, data))
    return results


def export_cases(cases, directory, *, schema_approval=None, _output_root=None):
    """Write one approved batch, guarding actual source bytes before and after.

The private output-root injection is only an isolated test I/O boundary;
production defaults to ROOT and source provenance always reads ROOT.
"""
    if schema_approval != SCHEMA_APPROVAL:
        raise PermissionError("Claude schema confirmation CLAUDE-APPROVED-TIA2D-2 required")
    before = _source_stamp()
    materialized = []
    for case in cases:
        stamp = getattr(case, "_source_stamp", None)
        if stamp is None:
            raise ValueError("case lacks its in-memory source guard; rebuild from current inputs")
        if _source_key(stamp) != _source_key(before):
            raise ValueError("batch cases have different source stamps")
        name = case["case_id"]
        if not name or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in name):
            raise ValueError("unsafe case_id")
        if case["schema_revision"] != SCHEMA_REVISION or case["design_sha256"] != before["design_sha256"]:
            raise ValueError("case schema or design differs from approved batch")
        if any(query["kind"] == "sensitivity" and query.get("seed") is not None
               and query.get("geometry_seed") is None for query in case["queries"]):
            raise ValueError("formal sensitivity requires geometry_seed; LP-only probes are private")
        for query in case["queries"]:
            declared = query.get("declared_validity_conditions", ())
            result_conditions = query["result"].get("validity_conditions", ())
            if (set(declared) | set(result_conditions)) - VALIDITY_CONDITIONS:
                raise ValueError("formal validity_conditions must use the approved enum codes")
        materialized.append(case)
    if len({case["case_id"] for case in materialized}) != len(materialized):
        raise ValueError("duplicate case_id")
    aliases = {}
    for case in materialized:
        digest = _input_hash(case)
        case["alias_of"] = aliases.get(digest)
        case["role"] = "alias" if digest in aliases else "primary"
        aliases.setdefault(digest, case["case_id"])
    if _source_key(_source_stamp()) != _source_key(before):
        raise RuntimeError("source changed during batch generation; discard and rerun")
    source = _source_manifest(materialized, before)
    source_data = _json_bytes(source)
    if len(source_data) > MAX_BYTES:
        raise ValueError("source manifest exceeds 1 MB")
    source_sha = hashlib.sha256(source_data).hexdigest()
    files = [("source_manifest.json", source_data)]
    records = []
    for case in materialized:
        stamped = dict(case, provenance=dict(source_manifest_sha256=source_sha))
        parts = []
        for index, (indices, data) in enumerate(_split_case(stamped)):
            path = case["case_id"] + ".part" + str(index + 1).zfill(3) + ".json"
            files.append((path, data))
            parts.append(dict(path=path, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                              query_indices=list(indices)))
        records.append(dict(case_id=case["case_id"], input_sha256=_input_hash(case),
                            query_count=len(case["queries"]), parts=parts))
    manifest = dict(schema="eab2.case-batch.v1", schema_revision=SCHEMA_REVISION,
        schema_approval=SCHEMA_APPROVAL, approval_date=APPROVAL_DATE,
        source_manifest=dict(path="source_manifest.json", bytes=len(source_data), sha256=source_sha), cases=records)
    manifest_data = _json_bytes(manifest)
    if len(manifest_data) > MAX_BYTES:
        raise ValueError("batch manifest exceeds 1 MB")
    target = Path(directory).resolve()
    output_root = ROOT if _output_root is None else Path(_output_root).resolve()
    if not target.is_relative_to(output_root) or target.exists():
        raise ValueError("choose a new output directory inside the worktree")
    target.mkdir(parents=True)
    try:
        for name, data in files:
            (target / name).write_bytes(data)
        if _source_key(_source_stamp()) != _source_key(before):
            raise RuntimeError("source changed during batch writing; discard and rerun")
        (target / "manifest.json").write_bytes(manifest_data)
    except BaseException:
        (target / "INVALIDATED.json").write_bytes(_json_bytes(dict(status="INVALIDATED", reason="failed_or_changed_batch_do_not_resume")))
        raise
    return manifest
