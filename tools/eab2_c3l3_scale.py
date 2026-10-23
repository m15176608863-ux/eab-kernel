"""C3-L3 P2 cold process measurement, not an acceptance/performance gate.

No solver-result cache or frozen LP is reused. Each implementation builds the
same disconnected exact polygon assembly in a new process. Timings include
original contact assembly separately from statics/solve/export; no benchmark
claim is made about production assemblies or other hardware.
"""
from __future__ import annotations
import argparse
from fractions import Fraction as Q
import hashlib
from itertools import combinations
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src/eab").is_dir())
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))


def model(count, segments):
    from eab.kernel2d.assembly import Assembly2, Body2
    bodies = []
    for i in range(count):
        x = 16 * i
        edge = tuple((Q(x) + Q(k, 2), Q(k % 2, 8)) for k in range(segments + 1))
        width = Q(segments, 2)
        origin = (Q(x) + Q(3, 8), Q(-5, 8))
        moving = edge + ((Q(x) + width, Q(2)), (Q(x), Q(2)))
        support = ((Q(x), Q(-2)), (Q(x) + width, Q(-2))) + tuple(reversed(edge))
        live = (Q(0), Q(-1), -(Q(x) + width / 2 - origin[0]))
        bodies.append(Body2.from_vertices(f"moving_{i}", moving, reference_point=origin,
            dof_anchor=origin, live=live))
        bodies.append(Body2.from_vertices(f"support_{i}", support, reference_point=origin,
            dof_anchor=origin, boundary_type="FIXED_BODY", dof_mask=(0, 0, 0)))
    return Assembly2(tuple(bodies), tuple(combinations(range(len(bodies)), 2)), "complete", mu=Q(1, 4))


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def worker(args):
    started = time.perf_counter()
    assembly = model(args.bodies, args.segments)
    if args.worker == "cpp":
        from eab2_c3l3_diff import C3L3Dll, verify_limit
        dll = C3L3Dll(args.dll.resolve())
        try:
            handle = dll.assembly(assembly)
            contact_start = time.perf_counter()
            contacts = dll.contacts(handle)
            contact_seconds = time.perf_counter() - contact_start
            exported = dll.exact(dll.contact_set2_export_exact, contacts)
            solve_start = time.perf_counter()
            result = dll.l3_query(contacts, assembly, {"kind": "limit"})
            solve_seconds = time.perf_counter() - solve_start
            verify_limit(assembly, exported, assembly.mu, result)
            problem = result["problem"]
            status = result["mathematical_status"]
            fingerprint = hashlib.sha256(json.dumps({key: problem[key] for key in ("A", "b", "c")},
                sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            answer = dict(implementation="cpp", rows=len(problem["b"]), columns=len(problem["c"]),
                constraints=len(exported["constraints"]), status=status, exact_value=result["exact_value"],
                lp_sha256=fingerprint, dll_sha256=dll.sha256, build_identity=dll.identity,
                independent_certificate_verified=True)
        finally:
            dll.close()
    else:
        from eab.kernel2d.contacts import assemble_contact_set2
        from eab.kernel2d.statics import limit_load_ideal_exact_2d
        from eab2_c3l3_diff import exact_wire, verify_limit
        contact_start = time.perf_counter()
        contacts = assemble_contact_set2(assembly)
        contact_seconds = time.perf_counter() - contact_start
        solve_start = time.perf_counter()
        result = limit_load_ideal_exact_2d(assembly, contacts)
        solve_seconds = time.perf_counter() - solve_start
        wire = exact_wire(result)
        verify_limit(assembly, exact_wire(contacts), assembly.mu, wire)
        problem = result.problem
        assert problem is not None
        fingerprint = hashlib.sha256(json.dumps({key: exact_wire(getattr(problem, key)) for key in ("A", "b", "c")},
                sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        answer = dict(implementation="python", rows=len(problem.b), columns=len(problem.c),
            constraints=len(contacts.constraints), status=result.status, exact_value=exact_wire(result.exact_value),
            lp_sha256=fingerprint, python=sys.version, independent_certificate_verified=True)
    answer.update(bodies=args.bodies, segments=args.segments, cold_contact_seconds=contact_seconds,
        cold_limit_solve_export_seconds=solve_seconds, worker_seconds=time.perf_counter() - started,
        timing_includes_json_export=args.worker == "cpp")
    dump(args.output, answer)
    print(f"C3L3_SCALE_WORKER implementation={args.worker} rows={answer['rows']} columns={answer['columns']} status={status if args.worker == 'cpp' else result.status}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dll", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bodies", type=int, default=20)
    parser.add_argument("--segments", type=int, default=18)
    parser.add_argument("--timeout", type=float, default=900)
    parser.add_argument("--worker", choices=("cpp", "python"))
    args = parser.parse_args()
    if not 1 <= args.bodies <= 20 or not 2 <= args.segments <= 24 or args.segments % 2:
        parser.error("measurement domain: 1..20 movable bodies, even 2..24 segments")
    if args.worker:
        worker(args)
        return 0
    temp = ROOT / "reports/codex/C3L3_evidence/tmp/scale"
    temp.mkdir(parents=True, exist_ok=True)
    observations = []
    for implementation in ("cpp", "python"):
        output = temp / f"{implementation}_{args.bodies}_{args.segments}.json"
        log = output.with_suffix(".log")
        command = [sys.executable, "-X", "utf8", str(Path(__file__).resolve()), "--worker", implementation,
            "--dll", str(args.dll.resolve()), "--output", str(output), "--bodies", str(args.bodies), "--segments", str(args.segments)]
        start = time.perf_counter()
        dump(args.output.with_suffix(".progress.json"), dict(complete=False, current=implementation, command=command, observations=observations))
        env = dict(os.environ, TEMP=str(temp), TMP=str(temp), PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
        with log.open("w", encoding="utf-8") as stream:
            try:
                result = subprocess.run(command, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=args.timeout, check=False)
                item = json.loads(output.read_text("utf-8")) if result.returncode == 0 else dict(implementation=implementation, error="worker_failure", exit_code=result.returncode)
            except subprocess.TimeoutExpired:
                item = dict(implementation=implementation, error="measurement_timeout", timeout_seconds=args.timeout)
        item.update(process_cold_seconds=time.perf_counter()-start, command=command, log=str(log))
        observations.append(item)
        dump(args.output.with_suffix(".progress.json"), dict(complete=False, observations=observations))
    report = dict(work_order="WO-C3L3", performance_gate=False, cold_repeats_per_implementation=1,
        model=f"{args.bodies} independent movable bodies above complementary zigzag fixed supports; all pairs explicit",
        caveat="single-host cold samples; background work may affect timings; no target speedup or production claim",
        observations=observations, complete=all("error" not in r for r in observations))
    if report["complete"]:
        report["same_exact_lp"] = observations[0]["lp_sha256"] == observations[1]["lp_sha256"]
        report["same_status_value"] = all(observations[0][k] == observations[1][k] for k in ("status", "exact_value"))
    dump(args.output, report)
    print(f"C3L3_SCALE_REPORT complete={report['complete']} performance_gate=false observations={len(observations)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
