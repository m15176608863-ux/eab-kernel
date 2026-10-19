"""Small G2/G3/G4 polygon scans, explicitly not eab2.case.v1 exports.

Every output is a diagnostic with source provenance, query scope and exact
status/value records. Condensed lock records intentionally omit the full cell
certificate; they must not be used as C++ certificate fixtures. Interrupted
runs are invalid and require a new output directory and complete rerun.
"""
import argparse
from collections import Counter
from dataclasses import replace
from fractions import Fraction as Q
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eab.adapters.tia2d import morphology_geometry, morphology_seed
from eab.kernel2d.contacts import assemble_contact_set2
from eab.kernel2d.lock import translation_lock_certificate
from eab.kernel2d.mobility import first_order_free_twists
from eab.kernel2d.sensitivity import evaluate_sensitivity2
from eab.kernel2d.statics import critical_parameter
from tia2d_cases import input_record, input_audit, rational, wire, _stable_body_references
from tia2d_provenance import git_provenance


FAMILIES = ("TIA-G2", "TIA-G3", "TIA-G4")
AMPLITUDES = (Q(0), Q(1, 16), Q(1, 8), Q(1, 4))
WAVELENGTHS = (Q(1, 2), Q(1), Q(2))


def _measure(clocks, name, function, *args, **kwargs):
    start = time.perf_counter()
    result = function(*args, **kwargs)
    clocks[name] = dict(seconds=time.perf_counter() - start, clock="perf_counter",
                        scope=name, repetitions=1, cache_state="not_controlled")
    return result


def _single(assembly, index):
    bodies = tuple(body if i == index else replace(body, boundary_type="FIXED_BODY",
                   dof_mask=(0, 0, 0)) for i, body in enumerate(assembly.bodies))
    return replace(assembly, bodies=bodies)


def _lock_summary(result):
    return dict(call_status=result.call_status, mathematical_status=result.mathematical_status,
                display_status=result.display_status, status=result.status, refinement=result.refinement,
                reason=result.reason, radius=wire(result.radius), separation_ray=wire(result.separation_ray),
                seam_ray=wire(result.seam_ray), local_cell_count=len(result.local_cells),
                arc_count=len(result.arcs), radius_bound_count=len(result.radius_bounds),
                complete_certificate_included=False)


def diagnose(family, amplitude, wavelength, *, mu_max=1.0, max_steps=8):
    """Measure one explicit polygon; no threshold or derivative is guessed."""
    clocks = {}
    geometry = _measure(clocks, "geometry", morphology_geometry, family,
                        amplitude=amplitude, wavelength=wavelength)
    assembly = geometry.assembly
    inputs = _measure(clocks, "input_record", input_record, assembly)
    audit = _measure(clocks, "input_audit", input_audit, assembly, inputs)
    contacts = _measure(clocks, "contact_assembly", assemble_contact_set2, assembly)
    multi = _measure(clocks, "first_order_multi_prebuilt_contacts", first_order_free_twists,
                     assembly, contacts)
    critical = _measure(clocks, "critical_prebuilt_contacts", critical_parameter, assembly,
                        contact_set=contacts, mu_max=mu_max, max_steps=max_steps)
    locks, singles = [], []
    for i in (1, 2, 3):
        neighbors = tuple(body.vertices for j, body in enumerate(assembly.bodies) if j != i)
        lock = _measure(clocks, "lock_block_" + str(i + 1), translation_lock_certificate,
                        assembly.bodies[i].vertices, neighbors)
        locks.append(dict(body_id=assembly.bodies[i].body_id,
                          fixed_neighbors=[b.body_id for j, b in enumerate(assembly.bodies) if j != i],
                          result=_lock_summary(lock)))
        single = _single(assembly, i)
        result = _measure(clocks, "first_order_single_block_" + str(i + 1), first_order_free_twists, single)
        singles.append(dict(body_id=assembly.bodies[i].body_id, result=wire(result)))
    if critical.threshold_certificate is not None:
        seed = morphology_seed(critical.threshold_certificate.problem, geometry, "amplitude")
    else:
        seed = None
    sensitivity = _measure(clocks, "amplitude_threshold_sensitivity", evaluate_sensitivity2,
        critical, seed, parameter="amplitude",
        validity_conditions=("L1接触骨架不变",),
        positive_direction_valid=geometry.amplitude > 0, negative_direction_valid=geometry.amplitude > 0)
    critical_record = wire(critical)
    for key in ("lower_certificate", "upper_certificate", "threshold_certificate"):
        value = getattr(critical, key)
        if value is not None:
            critical_record[key]["problem"] = wire(value.problem)
    record = dict(diagnostic_format="tia2d.morphology.diagnostic.v1", case_v1_export=False,
        family=family, amplitude=rational(geometry.amplitude), wavelength=rational(geometry.wavelength),
        period_count=1, full_height_equals_wavelength=True, declared_segment_count=len(geometry.table) - 1,
        interface_orientation="all_same_phase_and_orientation", local_table=wire(geometry.table),
        local_to_global_frame=wire(geometry.frame), conclusions_apply_to="fixed_table_polygon_only",
        assembly=inputs, input_audit=audit, contact_status=contacts.status, contact_points=wire(contacts.points),
        constraint_count=len(contacts.constraints), maximal_segment_count=len(contacts.segments),
        fp_type_counts=dict(Counter(p.fp_type for p in contacts.points)),
        first_order_multi=wire(multi), first_order_single=singles, lock=locks,
        critical=critical_record, amplitude_threshold_sensitivity=wire(sensitivity),
        vertex_seeds=dict(amplitude=wire(geometry.vertex_seeds_amplitude),
                          wavelength=wire(geometry.vertex_seeds_wavelength),
                          ordering="body array; original vertex ID; xy"),
        python_wallclock=clocks)
    return _stable_body_references(record, [b.body_id for b in assembly.bodies])


def summary_row(case):
    critical, sensitivity = case["critical"], case["amplitude_threshold_sensitivity"]
    return dict(family=case["family"], amplitude=case["amplitude"], wavelength=case["wavelength"],
        declared_segment_count=case["declared_segment_count"], constraint_count=case["constraint_count"],
        maximal_segment_count=case["maximal_segment_count"], contact_status=case["contact_status"],
        first_order_multi=case["first_order_multi"]["mathematical_status"],
        first_order_single=[x["result"]["mathematical_status"] for x in case["first_order_single"]],
        lock_refinements=[x["result"]["refinement"] for x in case["lock"]],
        exact_threshold=critical["exact_threshold"], attained=critical["attained"],
        mu_lo=critical["mu_lo"], mu_hi=critical["mu_hi"], critical_reason=critical["reason"],
        derivative_status=sensitivity["differentiability"], derivative_reason=sensitivity["reason"],
        derivative=sensitivity["directional_derivative"], fp_type_counts=case["fp_type_counts"],
        wall_seconds=sum(x["seconds"] for x in case["python_wallclock"].values()))


def _json(path, value):
    data = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
    if len(data) >= 1_000_000:
        raise ValueError("diagnostic artifact must stay below 1 MB")
    path.write_bytes(data)


def _source_hashes():
    paths = [Path(__file__).resolve(), ROOT / "tools/tia2d_cases.py", ROOT / "src/eab/adapters/tia2d.py"]
    paths.extend((ROOT / "src/eab/kernel2d").glob("*.py"))
    paths.extend(ROOT / ("src/eab/" + name + ".py") for name in ("lp", "construction"))
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def run_scan(directory):
    target = Path(directory).resolve()
    if not target.is_relative_to(ROOT / "reports/codex/T1a_evidence") or target.exists():
        raise ValueError("use a new T1a_evidence output directory; interrupted runs cannot resume")
    target.mkdir(parents=True)
    sources = _source_hashes()
    provenance = dict(**git_provenance(ROOT), source_sha256=sources, command=list(sys.argv),
                      profile="profile1", schema_approval="not_requested_diagnostic_only")
    _json(target / "run_status.json", dict(state="running", valid=False, provenance=provenance))
    rows, manifest = [], []
    start = time.perf_counter()
    try:
        for family in FAMILIES:
            for ia, amplitude in enumerate(AMPLITUDES):
                for iw, wavelength in enumerate(WAVELENGTHS):
                    case_id = family + "-A" + str(ia) + "-W" + str(iw)
                    case = diagnose(family, amplitude, wavelength)
                    case["case_id"] = case_id
                    path = target / (case_id + ".json")
                    _json(path, case)
                    row = dict(case_id=case_id, **summary_row(case))
                    rows.append(row)
                    manifest.append(dict(path=path.name, bytes=path.stat().st_size,
                        sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
                    with (target / "progress.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
                        stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
                    print(case_id, row["first_order_multi"], row["exact_threshold"],
                          row["derivative_status"], round(row["wall_seconds"], 4), flush=True)
        if sources != _source_hashes():
            raise RuntimeError("query source changed during run; invalidate and rerun")
        _json(target / "summary.json", rows)
        _json(target / "manifest.json", manifest)
        _json(target / "run_status.json", dict(state="complete", valid=True, cases=len(rows),
            wall_seconds=time.perf_counter() - start, provenance=provenance))
    except BaseException as error:
        _json(target / "run_status.json", dict(state="failed_or_interrupted", valid=False,
            completed=len(rows), reason=str(error), provenance=provenance))
        raise
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    temporary = ROOT / "reports/codex/T1a_evidence/tmp"
    temporary.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(temporary)
    rows = run_scan(args.output)
    print("morphology diagnostics:", len(rows), "complete cases; no eab2.case.v1 export", flush=True)


if __name__ == "__main__":
    main()
