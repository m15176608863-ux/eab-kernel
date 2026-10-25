"""Deterministic asymmetric raw-primitive channels and exact red-flag probes.

The repaired Python referee and C++ are compared by the L4 harness. Finite
differences are only an independent warning: Richardson envelopes are NOT K
certificates or rigorous derivative bounds. Every probe must retain the actual
labelled L1 skeleton and every threshold/bracket is independently certified.
"""
from __future__ import annotations
import argparse
import copy
from dataclasses import replace
from fractions import Fraction as Q
import hashlib
import itertools
import json
from pathlib import Path
import random
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "src")]
from eab.kernel2d.assembly import Body2
from eab.kernel2d.contacts import assemble_contact_set2
from eab.kernel2d.statics import critical_parameter, limit_load_ideal_exact_2d
from eab2_c3l3_diff import bits, exact_wire, rational, verify_critical
from eab2_c3l4_diff import formal_cases, geometry_jet, t1b_cases

CHANNELS = ("single_face", "single_vertex", "random_rational_0", "random_rational_1", "random_rational_2", "dead_live")
DEFAULT_EXPONENTS = (18, 22, 26)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def raw_points(model):
    return sorted({tuple(map(Q, point)) for body in model.bodies for point in body.original_vertices or body.vertices})


def seed_channels(source):
    """All shared coordinates get one velocity; seeds never use a slope oracle."""
    model, contacts = source["model"], source["contacts"]
    points = raw_points(model)
    constraints = contacts["constraints"]
    require(points and constraints, "exact-threshold asymmetric source needs contact primitives")
    edge_body, (i, j) = constraints[0]["label"][-2:]
    body = next(body for body in model.bodies if body.body_id == edge_body)
    vertices = body.original_vertices or body.vertices
    first, last = tuple(map(Q, vertices[i])), tuple(map(Q, vertices[j]))
    edge = tuple(b-a for a, b in zip(first, last))
    width = sum(v*v for v in edge)
    normal = (-edge[1], edge[0])
    magnitude = max(map(abs, normal))
    require(width > 0 and magnitude > 0, "nonzero source face")
    scale = Q(2)**max(0, magnitude.numerator.bit_length()-magnitude.denominator.bit_length()+1)
    axis = 0 if abs(edge[0]) >= abs(edge[1]) else 1
    chosen = tuple(map(Q, constraints[0]["point"]))
    require(chosen in points, "single-vertex channel needs original shared vertex")
    for channel in CHANNELS:
        velocities = {point: (Q(0), Q(0)) for point in points}
        if channel == "single_face":
            for point in points:
                offset = tuple(p-a for p, a in zip(point, first))
                fraction = sum(x*y for x, y in zip(offset, edge)) / width
                if offset[0]*edge[1] == offset[1]*edge[0] and 0 <= fraction <= 1:
                    # A dyadic affine tilt, including collinear intermediate
                    # vertices; do not divide by an arbitrary edge length.
                    offset_along = point[axis]-(first[axis]+last[axis])/2
                    velocities[point] = tuple(offset_along*v/scale/8 for v in normal)
        elif channel == "single_vertex":
            velocities[chosen] = (Q(1, 16), Q(-1, 32))
        elif channel.startswith("random_"):
            digest = hashlib.sha256((source["case_id"] + "/" + channel).encode()).digest()
            generator = random.Random(int.from_bytes(digest, "big"))
            velocities = {point: tuple(Q(generator.randint(-3, 3), 64) for _ in range(2)) for point in points}
        parameter = "asym_" + channel
        jet = geometry_jet(model, parameter, [[velocities[tuple(map(Q, p))] for p in body.original_vertices or body.vertices]
                                            for body in model.bodies])
        if channel in ("random_rational_2", "dead_live"):
            by_id = {body.body_id: body for body in model.bodies}
            # Collinear amplitude jets activate both load arrays without
            # replacing a zero-dead beam by an arbitrary infeasible load case.
            jet["dead"] = [[exact_wire(tuple(Q(v)/8 for v in by_id[name].live)) for name in jet["body_ids"]]]
            jet["live"] = [[exact_wire(tuple(Q(v)/16 for v in by_id[name].live)) for name in jet["body_ids"]]]
        yield channel, jet


def perturb(model, jet, epsilon):
    velocities = dict(zip(map(tuple, jet["vertex_ids"]), jet["vertices"][0]))
    table = {kind: dict(zip(jet["body_ids"], jet[kind][0])) for kind in ("dead", "live", "dof_anchor")}
    bodies = []
    for body in model.bodies:
        name = body.body_id
        vertices = tuple(tuple(Q(v)+epsilon*Q(d) for v, d in zip(point, velocities[name, i]))
                         for i, point in enumerate(body.original_vertices or body.vertices))
        values = {kind: tuple(Q(v)+epsilon*Q(d) for v, d in zip(getattr(body, kind), table[kind][name]))
                  for kind in table}
        for row in (*vertices, body.reference_point, *values.values()):
            for scalar in row:
                bits(scalar)
        bodies.append(Body2.from_vertices(name, vertices, reference_point=body.reference_point,
            dof_anchor=values["dof_anchor"], dead=values["dead"], live=values["live"],
            boundary_type=body.boundary_type, dof_mask=body.dof_mask))
    return replace(model, bodies=tuple(bodies))


def skeleton(model, contacts):
    """Feature identities, not changing coordinates or tangent vector values."""
    identities = {}
    for body in model.bodies:
        for index, point in enumerate(body.original_vertices or body.vertices):
            identities.setdefault(tuple(map(Q, point)), []).append([body.body_id, index])
    def owners(item):
        return sorted(identities.get(tuple(map(Q, item["point"])), []))
    constraints = [dict(a=item["a"], b=item["b"], owners=owners(item),
                        source=item["label"][-2:]) for item in contacts["constraints"]]
    points = [dict(a=item["a"], b=item["b"], owners=owners(item), fp_type=item["fp_type"],
                   retained=item["retained"], sources=item["sources"]) for item in contacts["points"]]
    return json.dumps(dict(constraints=sorted(constraints, key=lambda x: json.dumps(x, sort_keys=True)),
        points=sorted(points, key=lambda x: json.dumps(x, sort_keys=True)),
        mathematical_status=contacts["mathematical_status"], pair_states=contacts["pair_states"]),
        sort_keys=True, separators=(",", ":"))


def skeleton_checks(source, jet, exponents=DEFAULT_EXPONENTS):
    original = skeleton(source["model"], source["contacts"])
    result = {}
    for name, sign in (("positive", 1), ("negative", -1)):
        rows = []
        for exponent in exponents:
            epsilon = Q(sign, 2**exponent)
            try:
                moved = perturb(source["model"], jet, epsilon)
                contacts = exact_wire(assemble_contact_set2(moved))
                observed = skeleton(moved, contacts)
                rows.append(dict(epsilon=exact_wire(epsilon), same_skeleton=observed == original,
                                 skeleton_sha256=hashlib.sha256(observed.encode()).hexdigest()))
            except (ValueError, AssertionError) as error:
                rows.append(dict(epsilon=exact_wire(epsilon), same_skeleton=False,
                                 reason=type(error).__name__ + ": " + str(error)))
        result[name] = dict(valid=all(row["same_skeleton"] for row in rows), probes=rows)
    return result


def asymmetric_cases(sources=None, selection=None, exponents=DEFAULT_EXPONENTS):
    """Prepare only; root L4 run performs exactly one fresh referee refresh."""
    if sources is None:
        source_selection = None if selection is None else {name.removeprefix("asymmetric/") for name in selection}
        sources = itertools.chain(formal_cases(source_selection), t1b_cases(source_selection, prepare_only=True),
                                  t1b_cases(source_selection, thickness=True, prepare_only=True))
    for source in sources:
        base = source["bases"].get("critical")
        limit_base = source["bases"].get("limit")
        threshold = bool(base and base["result"]["exact_threshold"] is not None)
        finite = bool(limit_base and limit_base["result"].get("mathematical_status") == "OPTIMAL"
                      and limit_base["result"].get("exact_value") is not None
                      and raw_points(source["model"]) and source["contacts"]["constraints"])
        if not (threshold or finite):
            continue
        name = "asymmetric/" + source["case_id"]
        if selection is not None and name not in selection:
            continue
        queries, bases = [], {}
        if threshold:
            bases["critical"] = copy.deepcopy(base)
        for index, (kind, jet) in enumerate(seed_channels(source) if threshold else ()):
            checks = skeleton_checks(source, jet, exponents)
            condition = "asymmetric shared-original-vertex affine path; L1 skeleton checked at three exact probes per side"
            query = dict(kind="sensitivity", threshold_query_ref="critical", generated_channel=True,
                geometry_seed=jet, direction_domain={key: row["valid"] for key, row in checks.items()},
                declared_validity_conditions=[condition], declared_tied_labels=[], seed=None,
                result=dict(parameter=jet["parameters"][0], differentiability="unresolved", quality="approximate",
                            right_derivative=None, left_derivative=None, directional_derivative=None,
                            reason="pending_live_referee", validity_conditions=[condition]),
                asymmetric_probe=dict(source_case=source["case_id"], channel_kind=kind, exponents=list(exponents),
                                      skeleton=checks), expectation_source="generated raw primitive seed; not frozen expected slope")
            queries.append((index, query))
            print("ASYM_PREPARE", name, kind, "positive=" + str(checks["positive"]["valid"]),
                  "negative=" + str(checks["negative"]["valid"]), flush=True)
        if finite:
            # Finite-capacity target with nonzero dead and live load jets: the
            # Mills/Freund live-load column derivative was otherwise never
            # exercised by any differential (acceptance 2026-10-23).
            jet = dict(next(j for k, j in seed_channels(source) if k == "dead_live"), parameters=["asym_limit_dead_live"])
            checks = skeleton_checks(source, jet, exponents)
            condition = "asymmetric load-jet affine path on the limit target; L1 skeleton checked at three exact probes per side"
            queries.append((len(queries), dict(kind="sensitivity", limit_query_ref="limit", generated_channel=True,
                geometry_seed=jet, direction_domain={key: row["valid"] for key, row in checks.items()},
                declared_validity_conditions=[condition], declared_tied_labels=[], seed=None,
                result=dict(parameter="asym_limit_dead_live", differentiability="unresolved", quality="approximate",
                            right_derivative=None, left_derivative=None, directional_derivative=None,
                            reason="pending_live_referee", validity_conditions=[condition]),
                asymmetric_probe=dict(source_case=source["case_id"], channel_kind="limit_dead_live", target="limit",
                                      exponents=list(exponents), skeleton=checks),
                expectation_source="generated raw primitive load jet on the limit target; not frozen expected slope")))
            bases["limit"] = copy.deepcopy(limit_base)
            print("ASYM_PREPARE", name, "limit_dead_live", "positive=" + str(checks["positive"]["valid"]),
                  "negative=" + str(checks["negative"]["valid"]), flush=True)
        yield dict(source, case_id=name, source_case=source["case_id"], family="asymmetric/" + source["family"],
                   queries=queries, bases=bases)


def richardson_envelope(intervals, epsilons):
    """Conservative diagnostic envelope, NOT an analytic error bound.

    Two linear Richardson estimates plus 4x last quotient change / estimate
    drift and exact threshold-bracket half-widths. This admits same-side
    convergence (the face example approaches 1/2 strictly from below).
    """
    require(len(intervals) == len(epsilons) == 3 and all(a > b > 0 for a, b in zip(epsilons, epsilons[1:])), "three shrinking exact probes required")
    require(all(lo <= hi for lo, hi in intervals), "threshold interval order")
    estimates = []
    for (lo0, hi0), (lo1, hi1), e0, e1 in zip(intervals, intervals[1:], epsilons, epsilons[1:]):
        ratio = e0/e1
        estimates.append(((ratio*lo1-hi0)/(ratio-1), (ratio*hi1-lo0)/(ratio-1)))
    centers = [(lo+hi)/2 for lo, hi in intervals]
    extrapolated = [(lo+hi)/2 for lo, hi in estimates]
    radius = 4*max(abs(centers[-1]-centers[-2]), abs(extrapolated[-1]-extrapolated[-2]))
    radius += 4*sum((hi-lo)/2 for lo, hi in intervals) + (estimates[-1][1]-estimates[-1][0])/2
    return min(intervals[-1][0], estimates[-1][0])-radius, max(intervals[-1][1], estimates[-1][1])+radius


def red_flag_check(case, query, result):
    """Check every certified side against exact L3 probes, never prove a jet."""
    metadata = query["asymmetric_probe"]
    limit_target = metadata.get("target") == "limit"
    base = case["bases"]["limit" if limit_target else "critical"]
    if limit_target:
        value0, mu = Q(base["result"]["exact_value"]), Q(base.get("mu", case["model"].mu))
    else:
        threshold = Q(base["result"]["exact_threshold"])
        maximum = struct.unpack(">d", bytes.fromhex(base.get("mu_max_bits", "3ff0000000000000")))[0]
    records = []
    for side, sign, field in (("positive", 1, "right_derivative"), ("negative", -1, "left_derivative")):
        if result[field] is None:
            records.append(dict(direction=side, status="no_certified_value", skeleton_valid=metadata["skeleton"][side]["valid"]))
            continue
        require(metadata["skeleton"][side]["valid"] and query["direction_domain"][side], "certified derivative outside checked L1 skeleton")
        steps, intervals, epsilons = [], [], []
        for exponent in metadata["exponents"]:
            epsilon = Q(1, 2**exponent)
            print("ASYM_RED_FLAG_PROBE", case["case_id"], query["result"]["parameter"], side,
                  "epsilon=" + exact_wire(sign*epsilon), flush=True)
            moved = perturb(case["model"], query["geometry_seed"], sign*epsilon)
            contacts = assemble_contact_set2(moved)
            contact_wire = exact_wire(contacts)
            require(skeleton(moved, contact_wire) == skeleton(case["model"], case["contacts"]), "red-flag probe changed labelled L1 skeleton")
            if limit_target:
                # Exact finite capacity of the perturbed loads: the quotient
                # carries no bracket error. Diagnostic only, like the probes
                # below; the referee's LP certificate is exact by construction.
                limit = limit_load_ideal_exact_2d(moved, contacts, mu=mu)
                require(limit.mathematical_status == "OPTIMAL" and limit.exact_value is not None,
                        "certified limit direction lacks a finite probe capacity")
                lower = upper = Q(limit.exact_value) - value0
            else:
                critical = critical_parameter(moved, contact_set=contacts, mu_max=maximum, max_steps=64)
                exported = exact_wire(critical)
                for key in ("lower_certificate", "upper_certificate", "threshold_certificate"):
                    value = getattr(critical, key)
                    if value is not None:
                        exported[key]["problem"] = exact_wire(value.problem)
                verify_critical(moved, contact_wire, exported)
                if critical.exact_threshold is not None:
                    lower = upper = Q(critical.exact_threshold) - threshold
                else:
                    require(critical.mu_lo is not None and critical.mu_hi is not None and
                            critical.upper_certificate is not None and critical.upper_certificate.status == "UNBOUNDED",
                            "certified direction lacks a finite probe threshold bracket")
                    lower, upper = Q(critical.mu_lo) - threshold, Q(critical.mu_hi) - threshold
            interval = (lower/epsilon, upper/epsilon)
            intervals.append(interval)
            epsilons.append(epsilon)
            steps.append(dict(epsilon=exact_wire(sign*epsilon), offset_interval=exact_wire((lower, upper)),
                              quotient_interval=exact_wire(interval), independent_critical_verified=not limit_target))
        envelope = richardson_envelope(intervals, epsilons)
        derivative = sign*Q(result[field])
        require(envelope[0] <= derivative <= envelope[1], "certified slope outside exact Richardson red-flag envelope")
        records.append(dict(direction=side, status="PASS", signed_seed_slope=exact_wire(derivative),
                            envelope=exact_wire(envelope), steps=steps,
                            contract="diagnostic Richardson envelope with exact bracket errors; not a derivative proof"))
        print("ASYM_RED_FLAG_PASS", case["case_id"], query["result"]["parameter"], side, flush=True)
    return records


def main():
    from eab2_c3l4_abi import C3L4Dll
    from eab2_c3l4_diff import run
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dll", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", action="append")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    selection = set(args.case) if args.case else None
    dll = C3L4Dll(args.dll)
    try:
        return run(dll, asymmetric_cases(selection=selection), args.output, selection)
    finally:
        dll.close()


if __name__ == "__main__":
    raise SystemExit(main())
