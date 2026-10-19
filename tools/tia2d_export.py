"""Approved-case registry and one-shot export orchestration for WO-T1a.

The binary64 registry includes the original P0 grid, all named regressions,
and the fixed-polygon P2 grid. Pure-rational examples are explicitly separate
private diagnostics: they are never passed to the public case encoder.
"""
import argparse
from dataclasses import replace
from fractions import Fraction as Q
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eab.adapters.tia2d import (g1, g5, g5_seed, g5_reference_from_vertices, morphology_geometry,
                              morphology_seed)
from eab.kernel2d.assembly import Assembly2, Body2
from eab.kernel2d.contacts import assemble_contact_set2
from eab.kernel2d.lock import translation_lock_certificate
from eab.kernel2d.mobility import first_order_free_twists
from eab.kernel2d.sensitivity import build_limit_seed2, evaluate_sensitivity2
from eab.kernel2d.statics import critical_parameter, limit_load_ideal_exact_2d
from tia2d_cases import build_case, export_cases, input_record, wire
from tia2d_seed import geometry_seed, propagate_geometry_seed
from tia2d_dataset import case_specs


APPROVAL = "CLAUDE-APPROVED-TIA2D-2"


def registered_specs():
    """Original 91 roles plus the approved contract-coverage cases."""
    specs = [dict(spec, registry_kind="beam") for spec in case_specs()]
    for name in ("a_saw", "b_bare_vv", "c_redundant_vv", "d_flush_mu0",
                 "d_flush_mu025", "e_mixed_vv_edge", "f_convex_in_notch"):
        specs.append(dict(case_id="regression_" + name, family="named_regression",
                          registry_kind="regression", regression=name))
    for family in ("TIA-G2", "TIA-G3", "TIA-G4"):
        for ia, amplitude in enumerate((Q(0), Q(1, 16), Q(1, 8), Q(1, 4))):
            for iw, wavelength in enumerate((Q(1, 2), Q(1), Q(2))):
                specs.append(dict(case_id=family + "-A" + str(ia) + "-W" + str(iw), family=family,
                    registry_kind="morphology", amplitude=amplitude, wavelength=wavelength))
    for name in ("farkas_free_dead", "separated", "overlap", "completeness_unknown",
                 "unsupported_h", "resolution_bracket", "signed_zero_cw_frames", "redundant_vv_mu2"):
        specs.append(dict(case_id="coverage_" + name, family="contract_coverage",
                          registry_kind="coverage", coverage=name))
    for family in ("TIA-G1", "TIA-G5", "TIA-G2", "TIA-G3", "TIA-G4"):
        for body_index in (1, 2, 3):
            specs.append(dict(case_id="single_" + family + "_body" + str(body_index),
                family=family, registry_kind="single_body", body_index=body_index))
    assert len(specs) == len({spec["case_id"] for spec in specs}) == 114
    return tuple(specs)


def python_only_specs():
    return (dict(case_id="python_only_g1_tenth", family="TIA-G1", registry_kind="beam",
                 kwargs=dict(t=Q(1, 10), height=Q(1), mu=Q(0))),
            dict(case_id="python_only_g1_third_slender", family="TIA-G1", registry_kind="beam",
                 kwargs=dict(t=Q(1, 3), height=Q(1, 4), mu=Q(0))))


def _body(name, vertices, fixed=False):
    return Body2.from_vertices(name, vertices, reference_point=(0, 0), dof_anchor=(0, 0),
        boundary_type="FIXED_BODY" if fixed else None, dof_mask=(0, 0, 0) if fixed else (1, 1, 1),
        live=(0, 0, 0) if fixed else (0, -1, 0))


def _square(name, x=0, y=0, fixed=False):
    return _body(name, ((x, y), (x + 1, y), (x + 1, y + 1), (x, y + 1)), fixed)


def _complete(bodies):
    return Assembly2(tuple(bodies), tuple((i, j) for i in range(len(bodies))
                     for j in range(i + 1, len(bodies))), "complete", "profile1", Q(0))


def _regression(name):
    if name == "a_saw":
        return _complete((_body("A", ((-2, 0), (0, 0), (1, 1), (0, 2), (-2, 2))),
                          _body("B", ((0, 0), (2, 0), (2, 2), (0, 2), (1, 1)), True)))
    if name == "b_bare_vv":
        return _complete((_square("A"), _square("B", 1, 1, True)))
    if name == "c_redundant_vv":
        return _complete((_square("A"), _square("B", 1, 1, True), _square("C", 1, 0, True)))
    if name in ("d_flush_mu0", "d_flush_mu025"):
        return g5(n=3, height=1, pressure=1, mu=Q(0) if name == "d_flush_mu0" else Q(1, 4))
    if name == "e_mixed_vv_edge":
        return _complete((_square("A"), _body("B", ((0, 0), (0, Q(1, 2)), (-Q(1, 2), Q(1, 2)),
            (-1, Q(5, 4)), (0, 1), (-Q(1, 4), 2), (-2, 2), (-2, 0)), True)))
    if name == "f_convex_in_notch":
        return _complete((_body("A", ((0, 0), (2, 1), (1, 2))),
            _body("B", ((-2, -2), (2, -2), (2, 0), (0, 0), (0, 2), (-2, 2)), True)))
    raise ValueError("unknown named regression")


def materialize(spec):
    """Return an exact assembly plus optional fixed-table seed metadata."""
    if spec["registry_kind"] == "regression":
        return _regression(spec["regression"]), None
    if spec["registry_kind"] == "morphology":
        geometry = morphology_geometry(spec["family"], amplitude=spec["amplitude"], wavelength=spec["wavelength"])
        return geometry.assembly, geometry
    if spec["registry_kind"] == "beam":
        return (g1 if spec["family"] == "TIA-G1" else g5)(**spec["kwargs"]), None
    if spec["registry_kind"] == "single_body":
        model = (g1(t=Q(1, 4)) if spec["family"] == "TIA-G1" else
                 g5(n=3) if spec["family"] == "TIA-G5" else
                 morphology_geometry(spec["family"], amplitude=Q(1, 8), wavelength=1).assembly)
        index = spec["body_index"]
        return replace(model, bodies=tuple(body if i == index else
            replace(body, boundary_type="FIXED_BODY", dof_mask=(0, 0, 0), dead=(Q(0),) * 3,
                    live=(Q(0),) * 3) for i, body in enumerate(model.bodies))), None
    if spec["registry_kind"] == "coverage":
        name = spec["coverage"]
        if name == "farkas_free_dead":
            return _complete((replace(_square("A"), dead=(Q(1), Q(0), Q(0))),)), None
        if name in ("separated", "overlap"):
            return _complete((_square("A"), _square("B", 2 if name == "separated" else Q(1, 2), 0, True))), None
        if name == "completeness_unknown":
            return replace(g5(n=3), pairs=None, completeness="completeness_unknown"), None
        if name == "unsupported_h":
            return g5(n=3, mu=Q(1, 4)), None
        if name == "resolution_bracket":
            return g1(t=Q(1, 4), height=Q(1, 4)), None
        if name == "redundant_vv_mu2":
            return _regression("c_redundant_vv"), None
        if name == "signed_zero_cw_frames":
            a = Body2.from_vertices("A", ((-0.0, 0.0), (0, 1), (1, 1), (1, 0)),
                reference_point=(13, -5), dof_anchor=(Q(1, 4), Q(1, 2)), live=(0, -1, Q(25, 2)))
            b = Body2.from_vertices("B", ((2, 1), (1, 1), (1, 0), (2, 0)),
                reference_point=(-3, 7), dof_anchor=(1, Q(1, 2)),
                boundary_type="FIXED_BODY", dof_mask=(0, 0, 0))
            return _complete((a, b)), None
    raise ValueError("unknown registry kind")


def family_parameters(spec, model):
    """Actual numeric family inputs, with no display-rounded angle surrogate."""
    values = spec.get("kwargs", {})
    result = dict(family=spec["family"], mu=Q(model.mu))
    if spec["registry_kind"] in ("beam", "single_body") and spec["family"] == "TIA-G1":
        result.update(t=Q(values.get("t", Q(1, 4))), h=Q(values.get("height", 1)),
                      orientation=values.get("orientation", "koureas"))
    elif spec["family"] == "TIA-G5" or spec.get("regression", "").startswith("d_flush"):
        result.update(N=Q(len(model.bodies) - 2),
                      h=max(p[1] for p in model.bodies[1].vertices) - min(p[1] for p in model.bodies[1].vertices),
                      P=-model.bodies[-1].dead[0],
                      widths=tuple(max(p[0] for p in body.vertices) - min(p[0] for p in body.vertices)
                                   for body in model.bodies[1:-1]))
    elif spec["registry_kind"] == "morphology":
        result.update(A=Q(spec["amplitude"]), wavelength=Q(spec["wavelength"]))
    elif spec["registry_kind"] == "single_body":
        result.update(A=Q(1, 8), wavelength=Q(1))
    return result


def _geometry_jet(spec, model, geometry, parameter):
    vertices, dead, live, anchors = {}, {}, {}, {}
    if parameter == "mu":
        return geometry_seed(model, parameter, mu=1)
    if spec["family"] == "TIA-G1":
        values = spec["kwargs"]
        t, height = Q(values.get("t", Q(1, 4))), Q(values.get("height", 1))
        signs = {"koureas": (-1, -1, 1, 1), "unreversed": (1, -1, 1, -1),
                 "reverse_i1": (-1, -1, 1, -1)}[values.get("orientation", "koureas")]
        for i, body in enumerate(model.bodies):
            for vertex_id, (x, y) in enumerate(body.original_vertices):
                face = (i, i + 1, i + 1, i)[vertex_id]
                sign = signs[face - 1] if 1 <= face <= 4 else 0
                vertices[(body.body_id, vertex_id)] = ((sign * (Q(y) - height / 2), Q(0)) if parameter == "t" else
                    (sign * t * (Q(y) / height - Q(1, 2)), Q(y) / height))
    elif geometry is not None:
        jets = geometry.vertex_seeds_amplitude if parameter == "amplitude" else geometry.vertex_seeds_wavelength
        for body, values in zip(model.bodies, jets):
            vertices.update({(body.body_id, i): value for i, value in enumerate(values)})
    else:
        plate = model.bodies[-1]
        height = max(p[1] for p in plate.vertices) - min(p[1] for p in plate.vertices)
        low = min(p[1] for p in plate.vertices)
        if parameter == "h":
            for body in model.bodies:
                vertices.update({(body.body_id, i): (Q(0), (Q(p[1]) - low) / height)
                                 for i, p in enumerate(body.original_vertices)})
            dead[plate.body_id] = (Q(0), Q(0), -plate.dead[0] / 2)
            anchors[plate.body_id] = (Q(0), Q(1, 2))
        elif parameter == "P":
            dead[plate.body_id] = (Q(-1), Q(0), low + height / 2 - plate.reference_point[1])
        else:
            raise ValueError("unsupported geometry jet")
    return geometry_seed(model, parameter, vertices=vertices, dead=dead, live=live, anchors=anchors)


def _g1_seed(problem, spec, parameter):
    values = spec["kwargs"]
    t, height = Q(values.get("t", Q(1, 4))), Q(values.get("height", 1))
    orientation = values.get("orientation", "koureas")
    signs = {"koureas": (-1, -1, 1, 1), "unreversed": (1, -1, 1, -1), "reverse_i1": (-1, -1, 1, -1)}[orientation]
    seeds = {}
    for contact in problem.contact_set.constraints:
        assert contact.b == contact.a + 1
        sign = signs[contact.a]
        if parameter == "t":
            point = (sign * (contact.point[1] - height / 2), Q(0))
            tangent = (sign * height, Q(0))
        else:
            point = (sign * t * (contact.point[1] / height - Q(1, 2)), contact.point[1] / height)
            tangent = (sign * t, Q(1))
        seeds[contact.label] = (point, tangent)
    return build_limit_seed2(problem, contact_seeds=seeds, parameter=parameter)


def _sensitivity_factory(spec, model, geometry):
    def checked(requests):
        for request in requests:
            if propagate_geometry_seed(request["problem"], request["geometry_seed"]) != request["seed"]:
                raise ArithmeticError("geometry seed propagation differs from the production LP seed")
        return requests
    def requests(limit_result, critical_result):
        extras = []
        is_g5 = spec["family"] == "TIA-G5" or spec.get("regression", "").startswith("d_flush")
        if is_g5 and model.bodies[-1].dof_mask == (1, 0, 0) and limit_result.problem is not None:
            note = (dict(source="closed_form_adapter_not_certified", labels=["sliding", "hinging"])
                    if g5_reference_from_vertices(model)["mode"] == "tie" else None)
            for parameter in ("P", "h"):
                extras.append(dict(seed=g5_seed(limit_result.problem, parameter), problem=limit_result.problem,
                    target="limit", parameter=parameter,
                    negative_direction_valid=parameter != "P" or model.bodies[-1].dead[0] != 0,
                    geometry_seed=_geometry_jet(spec, model, geometry, parameter), display_note=note,
                    validity_conditions=("L1接触骨架不变", "axial_only_plate", "frozen_reference_points")))
        if critical_result is None or critical_result.threshold_certificate is None:
            return checked(extras)
        problem = critical_result.threshold_certificate.problem
        if spec["family"] == "TIA-G1" and spec["registry_kind"] == "beam":
            for parameter in ("t", "h"):
                extras.append(dict(seed=_g1_seed(problem, spec, parameter), problem=problem, target="critical",
                    parameter=parameter, negative_direction_valid=parameter != "t" or spec["kwargs"].get("t", Q(1, 4)) > 0,
                    geometry_seed=_geometry_jet(spec, model, geometry, parameter),
                    validity_conditions=("L1接触骨架不变", "shared_interface_parameter", "nonnegative_t", "positive_h")))
        if geometry is not None:
            for parameter in ("amplitude", "wavelength"):
                valid = parameter != "amplitude" or geometry.amplitude > 0
                extras.append(dict(seed=morphology_seed(problem, geometry, parameter), problem=problem, target="critical",
                    parameter=parameter, positive_direction_valid=valid, negative_direction_valid=valid,
                    geometry_seed=_geometry_jet(spec, model, geometry, parameter),
                    validity_conditions=("L1接触骨架不变", "fixed_polygon_table", "positive_amplitude", "positive_wavelength")))
        return checked(extras)
    return requests


def build_registered_case(spec):
    model, geometry = materialize(spec)
    moving = tuple(i for i, body in enumerate(model.bodies) if any(body.dof_mask))
    is_g5 = spec["family"] == "TIA-G5" or spec.get("regression", "").startswith("d_flush")
    paired = ()
    if spec["case_id"] == "g1_koureas_h0_t3":
        paired = tuple((i, (j,)) for i in (1, 3) for j in (i - 1, i + 1))
    elif spec["case_id"] == "g5_n3_mu0":
        paired = ((2, (1,)), (2, (3,)))
    expected = (tuple((model.bodies[i].body_id, model.bodies[i + 1].body_id)
                      for i in range(len(model.bodies) - 1))
                if spec["registry_kind"] in ("beam", "morphology", "single_body") else None)
    mode = spec.get("coverage")
    case = build_case(model, spec["case_id"], lock_bodies=moving, include_critical=True,
        mu_max=2.0 if mode == "redundant_vv_mu2" else 4.0 if spec["family"] == "TIA-G5" else 1.0,
        include_sensitivity=True, _family_parameters=family_parameters(spec, model),
        _expected_contacts=expected, _lock_pairs=paired,
        _critical_param="h" if mode == "unsupported_h" else "mu",
        _sensitivity_factory=_sensitivity_factory(spec, model, geometry)
            if spec["registry_kind"] not in ("coverage", "single_body") else None)
    if is_g5 and spec["registry_kind"] != "single_body" and model.bodies[-1].dof_mask == (1, 0, 0):
        if g5_reference_from_vertices(model)["mode"] == "tie":
            for query in case["queries"]:
                if query["kind"] == "sensitivity":
                    query["display_note"] = dict(source="closed_form_adapter_not_certified", labels=["sliding", "hinging"])
    return case


def _json(path, value):
    data = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
    if len(data) >= 1_000_000:
        raise ValueError("private diagnostic exceeds 1 MB; do not omit certificates")
    path.write_bytes(data)
    return dict(path=path.name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def _python_only(spec, critical_steps):
    model, geometry = materialize(spec)
    try:
        input_record(model)
    except (ValueError, OverflowError):
        pass
    else:
        raise AssertionError("Python-only registry entry unexpectedly has binary64 inputs")
    started = time.perf_counter()
    contacts = assemble_contact_set2(model)
    limit = limit_load_ideal_exact_2d(model, contacts)
    critical = critical_parameter(model, contact_set=contacts, max_steps=critical_steps)
    first = first_order_free_twists(model, contacts)
    locks = [dict(body_id=body.body_id, result=wire(translation_lock_certificate(body.vertices,
            tuple(other.vertices for j, other in enumerate(model.bodies) if j != i))))
            for i, body in enumerate(model.bodies) if any(body.dof_mask)]
    return dict(diagnostic_format="tia2d.python-only-diagnostic.v1", case_v1_export=False, cpp_input=False,
        reason="non_binary64_exact_input_preserved_without_rounding", case_id=spec["case_id"], parameters=wire(spec),
        critical_search=dict(max_steps=critical_steps, mu_max="1/1"),
        assembly=dict(profile=model.profile, completeness=model.completeness, mu=wire(model.mu),
                      bodies=wire(model.bodies), pairs=wire(model.pairs)),
        contact_set=wire(contacts), limit=wire(limit), limit_problem=wire(limit.problem),
        critical=wire(critical), first_order=wire(first), lock=locks,
        wall_seconds=time.perf_counter() - started, wallclock_scope="python_only_not_cpp_target")


def run_export(directory, *, selected_ids=None, include_python_only=True, _output_root=None):
    """A new root per batch. Any exception invalidates it; never resume in place."""
    target = Path(directory).resolve()
    allowed = (ROOT / "reports/codex/T1a_evidence" if _output_root is None else Path(_output_root)).resolve()
    if not target.is_relative_to(allowed) or target.exists():
        raise ValueError("use a NEW T1a_evidence directory; interrupted batches cannot resume")
    specs = registered_specs()
    if selected_ids is not None:
        wanted = set(selected_ids)
        if not wanted or wanted - {spec["case_id"] for spec in specs}:
            raise ValueError("unknown or empty selected registry IDs")
        specs = tuple(spec for spec in specs if spec["case_id"] in wanted)
    target.mkdir(parents=True)
    started, completed, private = time.perf_counter(), [], []
    _json(target / "registry.json", dict(format="tia2d.export-registry.v1", approval=APPROVAL,
        schema_directory="binary64", formal_specs=wire(specs), python_only_specs=wire(python_only_specs()) if include_python_only else [],
        expected_formal_cases=len(specs), critical_search="production_default_max_steps",
        performance_protocol="fresh_process_per_query_excluding_startup"))
    def generated():
        for spec in specs:
            _json(target / "progress.json", dict(state="RUNNING", valid=False, completed=len(completed),
                total=len(specs), next_case=spec["case_id"], elapsed_seconds=time.perf_counter() - started))
            case = build_registered_case(spec)
            from tia2d_cold_query import cold_case
            def query_progress(timing):
                _json(target / "progress.json", dict(state="RUNNING", valid=False, completed=len(completed),
                    total=len(specs), current_case=spec["case_id"], stage="cold_query_measurement",
                    query_index=timing["query_index"], query_verified=timing["verified"],
                    elapsed_seconds=time.perf_counter() - started))
            warm = cold_case(case, progress=query_progress)
            with (target / "warm_diagnostic_clocks.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(dict(case_id=spec["case_id"], excluded_from_cpp_target=True,
                    warm_diagnostic_queries=warm), ensure_ascii=False, allow_nan=False) + "\n")
            assert all(query["python_wallclock"]["cache_state"] == "cold" for query in case["queries"])
            completed.append(spec["case_id"])
            with (target / "progress.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(dict(case_id=spec["case_id"], query_count=len(case["queries"]),
                    elapsed_seconds=time.perf_counter() - started), ensure_ascii=False, allow_nan=False) + "\n")
            yield case
        # Keep Python-only generation inside the codec's single batch source
        # guard. A source change here invalidates the formal batch as well.
        if include_python_only:
            folder = target / "python_only"
            folder.mkdir()
            for spec in python_only_specs():
                private.append(_json(folder / (spec["case_id"] + ".json"), _python_only(spec, 10)))
            (folder / "README.md").write_text("# Python-only exact-rational diagnostics\n\nThese files are NOT eab2.case.v1 and must NOT be passed to C++. No binary64 input is fabricated.\n", encoding="utf-8", newline="\n")
            _json(folder / "manifest.json", private)
    try:
        manifest = export_cases(generated(), target / "binary64", schema_approval=APPROVAL, _output_root=allowed)
        _json(target / "progress.json", dict(state="COMPLETE", valid=True, completed=len(completed), total=len(specs),
            elapsed_seconds=time.perf_counter() - started, binary64_manifest="binary64/manifest.json", python_only_cases=len(private)))
        return manifest
    except BaseException as error:
        _json(target / "progress.json", dict(state="INVALIDATED", valid=False, completed=len(completed), total=len(specs),
            reason=str(error), instruction="discard this entire batch and rerun into a new directory"))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--case-id", action="append", help="small explicit subset; default is the complete approved registry")
    parser.add_argument("--without-python-only", action="store_true")
    args = parser.parse_args()
    temporary = ROOT / "reports/codex/T1a_evidence/tmp"
    temporary.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(temporary)
    run_export(args.output, selected_ids=args.case_id, include_python_only=not args.without_python_only)
    print("formal TIA2D-2 export complete; see binary64/manifest.json; Python-only inputs excluded from C++")


if __name__ == "__main__":
    main()
