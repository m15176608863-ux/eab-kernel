"""Public-DLL exact geometry/seed metamorphic gates for C3-L4.

Expected slopes come only from frozen formal results and dimensional changes.
Every transformed input is exact binary64; rational jets stay exact. The
independent differential checker reconstructs matrices and certifies returned
jets from original vertices, never from a C++ propagation helper.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass, replace
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import random
import sys
import time

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src/eab").is_dir())
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "src")]
from eab.kernel2d.assembly import Body2
from eab2_c3l1_diff import geometry_constraint_rows, require
from eab2_c3l3_diff import bits, exact_wire, rational, verify_critical, verify_limit
from eab2_c3l4_abi import C3L4Dll
from eab2_c3l4_diff import (formal_cases, label_set, target_kind, verify_batch,
                          verify_sensitivity)

CASES = ("g5_n3_mu1", "g5_n3_mu2", "g1_slender", "g1_unreversed_t1",
         "g5_rotation_free_mid", "g5_y_free", "regression_f_convex_in_notch")


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


@dataclass(frozen=True)
class Transform:
    name: str
    cosine: Q = Q(1)
    sine: Q = Q(0)
    length_unit: Q = Q(1)
    force_unit: Q = Q(1)
    translation: tuple = (Q(0), Q(0))
    reference_offset: tuple = (Q(0), Q(0))
    anchor_offset: tuple = (Q(0), Q(0))
    orientation: int = 1

    def rotate(self, value):
        x, y = map(Q, value[:2])
        require(self.orientation in (-1, 1), "orthogonal transform orientation")
        y *= self.orientation
        return self.cosine * x - self.sine * y, self.sine * x + self.cosine * y

    def point(self, value):
        return tuple(self.length_unit * v + t for v, t in zip(self.rotate(value), self.translation))

    def vector(self, value):
        return tuple(self.length_unit * v for v in self.rotate(value))

    def wrench(self, value):
        fx, fy = (self.force_unit * v for v in self.rotate(value))
        return fx, fy, self.orientation * self.force_unit * self.length_unit * Q(value[2]) - cross(self.reference_offset, (fx, fy))

    def parameter_unit(self, parameter):
        return self.length_unit if parameter in ("h", "amplitude", "wavelength", "length") else self.force_unit if parameter == "P" else Q(1)


def transforms(case_id):
    yield Transform("identity")
    yield Transform("reflect_x", cosine=Q(-1), orientation=-1)
    yield Transform("reflect_y", orientation=-1)
    yield Transform("swap_xy", cosine=Q(0), sine=Q(1), orientation=-1)
    schedules = ((Q(0), Q(1)), (Q(1000), Q(8)), (Q(100000), Q(1, 1024)))
    if case_id.startswith("g5_"):
        # Axis masks cannot encode a general oblique translation constraint.
        # Quarter turns exactly permute x/y masks; general rotations use G1.
        rotations = ((Q(0), Q(1), 1), (Q(-1), Q(0), 1), (Q(0), Q(-1), 1))
    else:
        generator = random.Random(304617)
        rotations = []
        for _ in range(3):
            m = generator.randint(3, 11)
            n = generator.randint(1, m - 1)
            denominator = m * m + n * n
            rotations.append((Q(m * m - n * n, denominator), Q(2 * m * n, denominator), denominator))
    for index, ((cosine, sine, denominator), (distance, unit)) in enumerate(zip(rotations, schedules)):
        require(cosine * cosine + sine * sine == 1, "exact rigid rotation")
        offset = (Q(3, 5) * distance, Q(4, 5) * distance)
        require(sum(v * v for v in offset) == distance * distance, "translation norm schedule")
        # Both coordinates and wrenches must be binary64: cancel odd factors
        # before the ABI, instead of rounding a rational rotation into doubles.
        yield Transform(f"rigid_units_{index}", cosine, sine, denominator * unit,
                        Q(denominator), offset)
    yield Transform("reference_only", reference_offset=(Q(17, 8), Q(-29, 16)))
    yield Transform("anchor_only", anchor_offset=(Q(131072), Q(-1024)))


def transformed_model(model, transform):
    bodies = []
    for body in model.bodies:
        mask = body.dof_mask
        if mask[0] != mask[1]:
            require(transform.cosine == 0 or transform.sine == 0, "oblique axis-mask transform is unsupported")
            if transform.cosine == 0:
                mask = (mask[1], mask[0], mask[2])
        if transform.anchor_offset != (0, 0):
            require(not mask[2] or mask[:2] == (1, 1), "anchor-only change would alter a partially constrained rotation")
        body = Body2.from_vertices(body.body_id,
            tuple(transform.point(p) for p in body.original_vertices or body.vertices),
            reference_point=tuple(v + d for v, d in zip(transform.point(body.reference_point), transform.reference_offset)),
            dof_anchor=tuple(v + d for v, d in zip(transform.point(body.dof_anchor), transform.anchor_offset)),
            boundary_type=body.boundary_type, dof_mask=mask,
            dead=transform.wrench(body.dead), live=transform.wrench(body.live))
        # Lossy transport is a failed input-domain gate, not a tolerance.
        for group in (body.original_vertices, (body.reference_point, body.dof_anchor), (body.dead, body.live)):
            for value in group:
                for scalar in value:
                    bits(scalar)
        bodies.append(body)
    return replace(model, bodies=tuple(bodies))


def transformed_contacts(contacts, transform):
    result = copy.deepcopy(contacts)
    for contact in result["constraints"]:
        contact["point"] = exact_wire(transform.point(tuple(map(rational, contact["point"]))))
        contact["tangent"] = exact_wire(tuple(transform.orientation * value for value in
                                               transform.vector(tuple(map(rational, contact["tangent"])))))
        contact["label"][2] = copy.deepcopy(contact["point"])
        if transform.orientation == -1:
            contact["label"][4].reverse()
    return result


def transformed_label(label, transform):
    value = copy.deepcopy(label)
    if isinstance(value, list) and len(value) == 2 and isinstance(value[0], list) and len(value[0]) == 5:
        value[0][2] = exact_wire(transform.point(tuple(map(rational, value[0][2]))))
        if transform.orientation == -1:
            value[0][4].reverse()
            value[1] = -value[1]
    return value


def transformed_query(query, transform):
    result = copy.deepcopy(query)
    jet = result["geometry_seed"]
    parameter = jet["parameters"][0]
    unit = transform.parameter_unit(parameter)
    for name in ("vertices", "dof_anchor"):
        jet[name] = [[exact_wire(tuple(v / unit for v in transform.vector(tuple(map(rational, row)))))
                      for row in jet[name][0]]]
    for name in ("dead", "live"):
        jet[name] = [[exact_wire(tuple(v / unit for v in transform.wrench(tuple(map(rational, row)))))
                      for row in jet[name][0]]]
    jet["mu"] = [exact_wire(rational(jet["mu"][0]) / unit)]
    for name in ("directional_derivative", "right_derivative", "left_derivative"):
        if result["result"][name] is not None:
            result["result"][name] = exact_wire(rational(result["result"][name]) / unit)
    for name in ("tied_labels", "near_labels"):
        result["result"][name] = [transformed_label(value, transform) for value in result["result"][name]]
    # These fields are derived expectations of the ORIGINAL model. The public
    # gate rebuilds transformed derivatives independently; do not reuse them.
    result["seed"] = None
    result.pop("threshold_mu_seed", None)
    result["expected_derivative_unit"] = exact_wire(unit)
    return result


def anchor_direction(query):
    result = copy.deepcopy(query)
    jet = result["geometry_seed"]
    jet["parameters"] = ["anchor_frame"]
    jet["vertices"] = [[["0/1", "0/1"] for _ in jet["vertex_ids"]]]
    jet["dead"] = [[["0/1"] * 3 for _ in jet["body_ids"]]]
    jet["live"] = [[["0/1"] * 3 for _ in jet["body_ids"]]]
    jet["dof_anchor"] = [[[exact_wire(Q(i + 1, 8)), exact_wire(Q(-2 * i - 1, 16))]
                           for i in range(len(jet["body_ids"]))]]
    jet["mu"] = ["0/1"]
    result["result"]["parameter"] = "anchor_frame"
    result["result"]["differentiability"] = "smooth"
    result["result"]["reason"] = None
    for name in ("directional_derivative", "right_derivative", "left_derivative"):
        result["result"][name] = "0/1"
    result["direction_domain"] = dict(positive=True, negative=True)
    result["seed"] = None
    result.pop("threshold_mu_seed", None)
    return result


def shared_edge_direction(query, model):
    """An affine shared-interface jet; no fabricated certified slope."""
    result = copy.deepcopy(query)
    jet = result["geometry_seed"]
    jet["parameters"] = ["shared_edge_affine"]
    lookup = {body.body_id: body.original_vertices or body.vertices for body in model.bodies}
    values = []
    for name, index in jet["vertex_ids"]:
        x, y = map(Q, lookup[name][index])
        values.append(exact_wire((Q(1, 8) + x / 8 + y / 16, Q(-3, 16) + x / 16 - y / 8)))
    jet["vertices"] = [values]
    jet["mu"] = ["0/1"]
    for name, width in (("dead", 3), ("live", 3), ("dof_anchor", 2)):
        jet[name] = [[["0/1"] * width for _ in jet["body_ids"]]]
    result["result"]["parameter"] = "shared_edge_affine"
    require(result["result"]["differentiability"] == "unresolved" and
            all(result["result"][name] is None for name in ("right_derivative", "left_derivative", "directional_derivative")),
            "shared-edge propagation-only source must not claim a derivative")
    result["seed"] = None
    return result


def g1_tilt_from_original_edges(model, contacts):
    """Read t=|dx/dy| from original interface edge IDs, not a theta label."""
    bodies = {body.body_id: body for body in model.bodies}
    slopes = set()
    for contact in contacts["constraints"]:
        name, (first, last) = contact["label"][-2:]
        raw = bodies[name].original_vertices or bodies[name].vertices
        dx, dy = (Q(raw[last][k]) - Q(raw[first][k]) for k in (0, 1))
        require(dy != 0, "G1 theta chart requires a nonhorizontal shared interface")
        slopes.add(abs(dx / dy))
    require(len(slopes) == 1, "G1 theta chart requires a single shared tilt magnitude")
    return slopes.pop()


def theta_direction(query, tilt):
    """Exact local chain rule d/dtheta=(1+t*t)d/dt; no trig rounding."""
    require(query["geometry_seed"]["parameters"] == ["t"], "theta direction must bind the original t seed")
    result = copy.deepcopy(query)
    factor = Q(1) + Q(tilt) * Q(tilt)
    jet = result["geometry_seed"]
    jet["parameters"] = ["theta"]
    for name in ("vertices", "dead", "live", "dof_anchor"):
        jet[name] = [[[exact_wire(factor * rational(value)) for value in row]
                      for row in channel] for channel in jet[name]]
    jet["mu"] = [exact_wire(factor * rational(value)) for value in jet["mu"]]
    result["result"]["parameter"] = "theta"
    for name in ("directional_derivative", "right_derivative", "left_derivative"):
        if result["result"][name] is not None:
            result["result"][name] = exact_wire(factor * rational(result["result"][name]))
    condition = "theta chain: t=tan(theta), dt/dtheta=1+t^2"
    result["declared_validity_conditions"] = list(result["declared_validity_conditions"]) + [condition]
    result["result"]["validity_conditions"] = list(result["result"]["validity_conditions"]) + [condition]
    result["seed"] = None
    result.pop("threshold_mu_seed", None)
    return result


def cases(selection=None):
    for source in formal_cases(set(CASES)):
        target = "critical" if source["case_id"].startswith("g1_") else "limit"
        queries = [copy.deepcopy(query) for _, query in source["queries"] if target_kind(query) == target]
        require(queries, "metamorphic source requires frozen queries")
        # The frozen oracle predates this additive output field. Normalize its
        # shape only; never replace its slopes/categories with a fresh solve.
        for query in queries:
            query["result"].setdefault("branch_certificate", None)
        propagation_only = source["case_id"] == "regression_f_convex_in_notch"
        if propagation_only:
            queries = [shared_edge_direction(queries[0], source["model"])]
        else:
            require(all(q["result"]["right_derivative"] is not None for q in queries), "metamorphic source requires certified frozen slope")
        anchor_invariant = all(not b.dof_mask[2] or b.dof_mask[:2] == (1, 1) for b in source["model"].bodies)
        for transform in transforms(source["case_id"]):
            if transform.anchor_offset != (0, 0) and not anchor_invariant:
                continue
            name = source["case_id"] + "/" + transform.name
            if selection is not None and name not in selection:
                continue
            model = transformed_model(source["model"], transform)
            contacts = transformed_contacts(source["contacts"], transform)
            geometry_constraint_rows(model, contacts["constraints"])
            changed = [transformed_query(q, transform) for q in queries]
            # Moving an anchor is a coordinate change for these masks. Its
            # exact nonzero A/load derivatives must cancel in the output.
            if anchor_invariant and not propagation_only:
                changed.append(anchor_direction(changed[0]))
            yield dict(case_id=name, source_case=source["case_id"], target=target,
                model=model, contacts=contacts, queries=changed,
                base_query=source["bases"][target], transform=transform, propagation_only=propagation_only)
        if target == "critical":
            name = source["case_id"] + "/theta_chain"
            if selection is not None and name not in selection:
                continue
            query = next(q for q in queries if q["result"]["parameter"] == "t")
            tilt = g1_tilt_from_original_edges(source["model"], source["contacts"])
            yield dict(case_id=name, source_case=source["case_id"], target=target,
                model=source["model"], contacts=source["contacts"],
                queries=[theta_direction(query, tilt)], base_query=source["bases"][target],
                transform=Transform("theta_chain"), parameterization=dict(base_parameter="t", parameter="theta",
                    definition="t=tan(theta)", t=exact_wire(tilt), chain_factor=exact_wire(1 + tilt * tilt)))


def contact_signature(contacts):
    return sorted(json.dumps({key: item[key] for key in ("a", "b", "point", "tangent", "label")},
        ensure_ascii=True, sort_keys=True, separators=(",", ":")) for item in contacts["constraints"])


def compare_slopes(expected, actual):
    for field in ("differentiability", "quality", "reason", "parameter", "sensitivity_model",
                  "directional_derivative", "left_derivative", "right_derivative"):
        require(expected[field] == actual[field], "metamorphic output: " + field + " expected=" + str(expected[field]) + " actual=" + str(actual[field]))
    for field in ("tied_labels", "near_labels"):
        if field == "tied_labels" and actual.get("branch_certificate") is not None:
            # verify_sensitivity independently verifies this selected basis;
            # cross-basis labels are recorded, not treated as invariant.
            continue
        require(label_set(expected[field]) == label_set(actual[field]), "metamorphic stable-ID label permutation: " + field)


def transform_record(transform):
    return {key: value if isinstance(value, str) else exact_wire(value) for key, value in vars(transform).items()}


def run(dll, output, selection=None):
    inputs = [Path(__file__), ROOT / "tools/eab2_c3l4_abi.py", ROOT / "tools/eab2_c3l4_diff.py",
              ROOT / "eab2/src/sensitivity.cpp", ROOT / "eab2/src/geometry_seed.cpp"]
    hashes = {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}
    started = time.perf_counter()
    records, failures, seen = [], [], set()
    progress = output.with_name(output.stem + "_progress.json")
    for case in cases(selection):
        seen.add(case["case_id"])
        assembly = contacts = base_token = None
        before = time.perf_counter()
        try:
            model = case["model"]
            assembly = dll.assembly(model)
            contacts = dll.contacts(assembly)
            # C++ export already uses assembly indices; the frozen reader alone
            # needs its historical body-ID to index conversion.
            actual_contacts = dll.exact(dll.contact_set2_export_exact, contacts)
            require(contact_signature(actual_contacts) == contact_signature(case["contacts"]), "transformed L1 original-ID contact skeleton")
            base_token, base = dll.base_query(contacts, model, case["base_query"])
            expected_base = case["base_query"]["result"]
            if case["target"] == "limit":
                verify_limit(model, case["contacts"], rational(base["problem"]["mu"]), base)
                require(base["exact_value"] == expected_base["exact_value"], "live multiplier invariant under joint force-unit transform")
            else:
                verify_critical(model, case["contacts"], base)
                require(base["exact_threshold"] == expected_base["exact_threshold"] and base["attained"] == expected_base["attained"], "exact threshold and openness invariant")
            primal_seconds = time.perf_counter() - before
            derivative_start = time.perf_counter()
            batch = dll.sensitivity(base_token, case["queries"])
            verify_batch(batch, case["queries"])
            for query, channel in zip(case["queries"], batch["channels"]):
                verify_sensitivity(model, case["contacts"], base, query, channel, mu_max_binary64=case["base_query"].get("mu_max_bits"))
                compare_slopes(query["result"], channel["result"])
            records.append(dict(case_id=case["case_id"], source_case=case["source_case"], target=case["target"],
                transform=transform_record(case["transform"]), channel_count=len(case["queries"]),
                parameterization=case.get("parameterization"),
                propagation_only=case.get("propagation_only", False),
                tied_label_dispositions=[dict(parameter=query["result"]["parameter"], expected=query["result"]["tied_labels"], actual=channel["result"]["tied_labels"])
                    for query, channel in zip(case["queries"], batch["channels"])
                    if label_set(query["result"]["tied_labels"]) != label_set(channel["result"]["tied_labels"])],
                matrix_and_seed_rebuilt=True, independent_certificates_verified=True,
                derivatives=[{key: channel["result"][key] for key in ("parameter", "differentiability", "right_derivative", "left_derivative")}
                             for channel in batch["channels"]],
                primal_seconds=primal_seconds, derivative_seconds=time.perf_counter() - derivative_start))
        except Exception as error:
            failures.append(dict(case_id=case["case_id"], error=type(error).__name__ + ": " + str(error)))
        finally:
            if base_token is not None:
                dll.check(dll.result_destroy(dll.context, base_token), "destroy base")
            if contacts is not None:
                dll.check(dll.contact_set2_destroy(dll.context, contacts), "destroy contacts")
            if assembly is not None:
                dll.check(dll.assembly2_destroy(dll.context, assembly), "destroy assembly")
        progress.write_text(json.dumps(dict(complete=False, completed=len(records), failed=len(failures),
            last_case=case["case_id"], seconds=time.perf_counter() - started), indent=2) + "\n", encoding="utf-8")
        print("META", case["case_id"], "PASS" if records and records[-1]["case_id"] == case["case_id"] else "FAIL", flush=True)
    if selection is not None and seen != selection:
        failures.append(dict(error="selection not fully executed", expected=sorted(selection), actual=sorted(seen)))
    unchanged = all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha for name, sha in hashes.items())
    if not unchanged:
        failures.append(dict(error="source changed during run; evidence invalid"))
    require(seen, "metamorphic run requires at least one case")
    last = f"C3L4_META cases={len(seen)} channels={sum(r['channel_count'] for r in records)} mismatch={len(failures)}"
    summary = dict(format="eab2.c3l4.public_abi_metamorphic.v1", complete=True, dll_sha256=dll.sha256,
        source_sha256=hashes, source_pre_post_equal=unchanged, cases=records, failures=failures,
        general_rotation_domain="G1 full translational DOFs; G5 partial axis mask uses exact quarter turns only",
        expected_source="frozen formal slopes transformed by dimensional chain rule; no fresh Python slope solve",
        seconds=time.perf_counter() - started, last_line=last)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    progress.write_text(json.dumps(dict(complete=True, cases=len(seen), failed=len(failures), last_line=last), indent=2) + "\n", encoding="utf-8")
    print(last, flush=True)
    return int(bool(failures))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dll", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", action="append")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    dll = C3L4Dll(args.dll)
    try:
        return run(dll, args.output, set(args.case) if args.case else None)
    finally:
        dll.close()


if __name__ == "__main__":
    raise SystemExit(main())
