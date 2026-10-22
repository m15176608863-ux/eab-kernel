"""WO-T1b exact tolerance cases; persistent rational certificates, no Git use.

Run: python tools/tia2d_t1b_tolerance.py
The large result goes outside the checkout; the compact summary stays inside.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eab.adapters.tia2d import g1, g5, tolerance_dovetail, tolerance_knob
from eab.kernel2d.erosion import erode_polygon_exact, square_element, octagon_element
from eab.kernel2d.translation_space import (
    TranslationComponent2, translation_component, critical_tolerance,
)


VERSION = "tia2d-t1b-tolerance-1"
BASELINE_COMMIT = "7f9510502ba265e53b5be8de4be22308dfe65f9a"


def dovetail_threshold(head_width, neck_width, height, element="square", erode_boundaries=True):
    """Throat-opening event, subject to no earlier lower-seam escape.

Let m=(wk-wn)/(2h), hK=support_K(1,m), c=m+hK. The eroded
moving bottom width is wk-2*c*delta, and the fixed-ring upper throat
width is wn+2*c*delta*e. Equality gives (wk-wn)/(2*c*(1+e)).
The scans also independently certify both sides and equality; this helper
alone is not a theorem about arbitrary finite wall thickness or height.
"""
    wk, wn, h = Q(head_width), Q(neck_width), Q(height)
    if not 0 < wn < wk or h <= 0:
        raise ValueError("require 0 < neck < head and positive height")
    kernel = square_element() if element == "square" else octagon_element() if element == "octagon" else None
    if kernel is None:
        raise ValueError("unknown element")
    m = (wk-wn)/(2*h)
    c = m+max(x+m*y for x, y in kernel)
    return (wk-wn)/(2*c*(1+bool(erode_boundaries)))


def evaluate(moving, obstacles, delta, element, erode_boundaries, boundary_flags=None):
    """All ordinary blocks erode; only explicit boundary bodies are optional."""
    delta = Q(delta)
    if boundary_flags is None:
        boundary_flags = (True,)*len(obstacles)
    a = erode_polygon_exact(moving, delta, element)
    bs = tuple(erode_polygon_exact(p, delta if (erode_boundaries or not fixed) else 0, element)
               for p, fixed in zip(obstacles, boundary_flags))
    rejected = [r.reason for r in (a,)+bs if r.status != "ACCEPTED"]
    if rejected:
        result = TranslationComponent2("UNPROVED", "erosion_rejected:"+";".join(rejected))
    else:
        result = translation_component(a.polygon, tuple(b.polygon for b in bs))
    return dict(delta=delta, moving=a.polygon, obstacles=tuple(b.polygon for b in bs),
                erosion_rejections=rejected, result=result)


def dovetail_row(wk, wn, element, erode_boundaries, iterations=10):
    h = Q(2)
    geometry = tolerance_dovetail(head_width=wk, neck_width=wn, height=h, wall=Q(2))
    star = dovetail_threshold(wk, wn, h, element, erode_boundaries)
    epsilon = min(Q(1, 1024), star/4)
    samples = tuple(evaluate(geometry["moving"], geometry["obstacles"], d,
                             element, erode_boundaries)
                    for d in (Q(0), star-epsilon, star, star+epsilon))
    high = Q((star*1024).__ceil__()+1, 1024)
    bracket = critical_tolerance(geometry["moving"], geometry["obstacles"], 0, high,
                                 iterations=iterations, element=element,
                                 erode_obstacles=erode_boundaries)
    ends = tuple(evaluate(geometry["moving"], geometry["obstacles"], bracket[key],
                         element, erode_boundaries) for key in ("low", "high"))
    statuses = tuple(x["result"].status for x in samples)
    success = statuses == ("TRAPPED_TRANSLATION", "TRAPPED_TRANSLATION",
                           "ESCAPABLE_TRANSLATION", "ESCAPABLE_TRANSLATION")
    success = success and bracket["status"] == "CERTIFIED_BRACKET" and bracket["low"] < star <= bracket["high"]
    return dict(family="dovetail", head_width=Q(wk), neck_width=Q(wn), height=h,
                element=element, erode_boundaries=erode_boundaries, geometry=geometry,
                exact_threshold=star, attained=False, samples=samples,
                dyadic_bracket=bracket, bracket_inputs=ends, closed_form_verified=success)


def assembly_rows(family, element, erode_boundaries, n=3):
    assembly = g1(t=Q(3, 32)) if family == "TIA-G1" else g5(n=n)
    rows = []
    for i, body in enumerate(assembly.bodies):
        if body.boundary_type is not None:
            continue
        others = tuple(b for j, b in enumerate(assembly.bodies) if j != i)
        obstacles = tuple(b.vertices for b in others)
        flags = tuple(b.boundary_type is not None for b in others)
        samples = tuple(evaluate(body.vertices, obstacles, d, element, erode_boundaries, flags)
                        for d in (Q(0), Q(1, 64)))
        rows.append(dict(family=family, inner_count=3 if family == "TIA-G1" else n,
                         g1_tilt=Q(3, 32) if family == "TIA-G1" else None,
                         body_id=body.body_id, element=element,
                         erode_boundaries=erode_boundaries, samples=samples,
                         critical_tolerance=None,
                         threshold_reason="empty_trapped_set_already_escapable_at_zero"
                         if samples[0]["result"].status == "ESCAPABLE_TRANSLATION"
                         else "requires_further_search"))
    return rows


def knob_row(element, erode_boundaries, iterations=10):
    geometry = tolerance_knob(segments=4)
    bracket = critical_tolerance(geometry["moving"], geometry["obstacles"], 0, Q(7, 16),
                                 iterations=iterations, element=element,
                                 erode_obstacles=erode_boundaries)
    kernel = square_element() if element == "square" else octagon_element()
    support = max(x+y/2 for x, y in kernel)
    star = 1/(4*support+1) if erode_boundaries else 1/(2*support)
    samples = tuple(evaluate(geometry["moving"], geometry["obstacles"], d,
                             element, erode_boundaries)
                    for d in (Q(0), Q(1, 8), bracket["low"], bracket["high"],
                              star-Q(1, 16384), star, star+Q(1, 16384)))
    return dict(family="polygon_knob", element=element, erode_boundaries=erode_boundaries,
                geometry=geometry, dyadic_bracket=bracket, samples=samples,
                exact_threshold=star, attained=False,
                closed_form_verified=tuple(s["result"].status for s in samples[-3:]) ==
                    ("TRAPPED_TRANSLATION", "ESCAPABLE_TRANSLATION", "ESCAPABLE_TRANSLATION"),
                scope="eight_rational_chords_on_two_semicircle_samples_not_a_smooth_circle")


def standard_rows():
    rows = []
    for label, wk, wn, h, delta in (
            ("small_positive_tolerance_sensitive", Q(1025, 1024), Q(1), Q(2), Q(1, 1024)),
            ("large_tolerance_still_trapped", Q(5), Q(1), Q(4), Q(3, 8))):
        geometry = tolerance_dovetail(head_width=wk, neck_width=wn, height=h, wall=Q(3))
        for element in ("square", "octagon"):
            for policy in (False, True):
                samples = tuple(evaluate(geometry["moving"], geometry["obstacles"], d, element, policy)
                                for d in (Q(0), delta))
                rows.append(dict(name=label, element=element, erode_boundaries=policy,
                                 geometry=geometry, samples=samples,
                                 throat_event=dovetail_threshold(wk, wn, h, element, policy)))
    return rows


def _json(value):
    if is_dataclass(value):
        return _json(asdict(value))
    if isinstance(value, Q):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _json(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json(v) for v in value]
    return value


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_json(value), ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def _summary(data):
    def sample(row):
        result = row["result"]
        return dict(delta=row["delta"], status=result.status, reason=result.reason,
                    area_bounds=result.area_bounds, diameter_squared_bounds=result.diameter_squared_bounds,
                    verified=bool(result.verification and result.verification.valid))
    answer = {"version": VERSION, "status": data["status"], "elapsed_seconds": data.get("elapsed_seconds"),
              "counts": {k: len(data[k]) for k in ("dovetail", "knob", "assemblies", "standards")}}
    for category in ("dovetail", "knob", "assemblies", "standards"):
        answer[category] = []
        for row in data[category]:
            compact = {k: v for k, v in row.items() if k not in
                       ("geometry", "samples", "dyadic_bracket", "bracket_inputs")}
            compact["samples"] = [sample(s) for s in row["samples"]]
            if "dyadic_bracket" in row:
                compact["dyadic_bracket"] = {k: v for k, v in row["dyadic_bracket"].items()
                                             if k not in ("low_result", "high_result")}
            answer[category].append(compact)
    return answer


def run(output, summary, iterations=10, source_commit=BASELINE_COMMIT):
    started = time.perf_counter()
    output, summary = Path(output), Path(summary)
    progress_path = output.with_suffix(output.suffix+".progress.json")
    for path in (output, summary, progress_path):
        if path.exists():
            raise FileExistsError("refusing to replace an existing artifact: "+str(path))
    def source_manifest():
        files = sorted((ROOT/"src/eab").rglob("*.py"))+[Path(__file__).resolve()]
        return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    before = source_manifest()
    data = dict(version=VERSION, status="RUNNING", source_commit=source_commit,
                source_commit_role="rollback_baseline_only_current_files_are_uncommitted_working_bytes",
                source_sha256_before=before,
                dovetail=[], knob=[], assemblies=[], standards=[])
    def progress():
        data["elapsed_seconds"] = round(time.perf_counter()-started, 3)
        _write(progress_path, data)
        print({"status": data["status"], **{k: len(data[k]) for k in ("dovetail", "knob", "assemblies", "standards")}}, flush=True)
    progress()
    for element in ("square", "octagon"):
        for policy in (False, True):
            for wk in (Q(5, 2), Q(3), Q(7, 2)):
                for wn in (Q(1), Q(3, 2), Q(2)):
                    data["dovetail"].append(dovetail_row(wk, wn, element, policy, iterations))
                    progress()
            data["knob"].append(knob_row(element, policy, iterations))
            data["assemblies"].extend(assembly_rows("TIA-G1", element, policy))
            for n in (3, 5, 7):
                data["assemblies"].extend(assembly_rows("TIA-G5", element, policy, n))
            progress()
    data["standards"] = standard_rows()
    data["status"] = "PASS" if all(row["closed_form_verified"] for row in data["dovetail"]+data["knob"]) and all(
        row["dyadic_bracket"]["status"] == "CERTIFIED_BRACKET" for row in data["knob"]) and all(
        sample["result"].status != "UNPROVED" for category in ("dovetail", "knob", "assemblies", "standards")
        for row in data[category] for sample in row["samples"]) else "PARTIAL"
    data["source_sha256_after"] = source_manifest()
    data["source_unchanged_during_run"] = data["source_sha256_after"] == before
    if not data["source_unchanged_during_run"]:
        data["status"] = "INVALID_SOURCE_CHANGED_DURING_RUN"
    progress()
    if not data["source_unchanged_during_run"]:
        raise RuntimeError("source changed during run; only invalid progress evidence was retained")
    _write(output, data)
    _write(summary, _summary(data))
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("D:/eab-evidence/reports/codex/T1b_evidence/p0_tolerance.json"))
    parser.add_argument("--summary", type=Path, default=ROOT/"reports/codex/T1b_evidence/p0_summary.json")
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--source-commit", default=BASELINE_COMMIT,
                        help="full rollback-baseline commit, not a claim that dirty source equals HEAD")
    args = parser.parse_args()
    result = run(args.output, args.summary, args.iterations, args.source_commit)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
