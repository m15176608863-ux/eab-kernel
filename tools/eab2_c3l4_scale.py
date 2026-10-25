"""Informational cold-process sensitivity timing; never a performance gate.

Primal and multi-channel derivative calls are timed separately. The C++ times
include the C ABI and JSON transport; Python has no equivalent transport cost.
Each backend/case runs in a new process with no concurrent H1 run requested.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools")]


def worker(args):
    from eab2_c3l4_diff import formal_cases, target_kind
    case, = formal_cases({args.case})
    target = "critical" if args.case.startswith("g1_") else "limit"
    queries = [query for _, query in case["queries"] if target_kind(query) == target]
    model, query = case["model"], case["bases"][target]
    started = time.perf_counter()
    if args.backend == "cpp":
        from eab2_c3l4_abi import C3L4Dll
        dll = C3L4Dll(args.dll)
        try:
            assembly = dll.assembly(model)
            contacts = dll.contacts(assembly)
            geometry_seconds = time.perf_counter() - started
            start = time.perf_counter()
            token, result = dll.base_query(contacts, model, query)
            primal_seconds = time.perf_counter() - start
            start = time.perf_counter()
            derivatives = [channel["result"] for channel in dll.sensitivity(token, queries)["channels"]]
            derivative_seconds = time.perf_counter() - start
            problem = result["problem"] if target == "limit" else result["threshold_certificate"]["problem"]
            value = result["exact_value"] if target == "limit" else result["exact_threshold"]
            state = result["mathematical_status"]
        finally:
            dll.close()
    else:
        from dataclasses import asdict
        from eab.kernel2d.contacts import assemble_contact_set2
        from eab.kernel2d.statics import critical_parameter, limit_load_ideal_exact_2d
        from eab.kernel2d.sensitivity import evaluate_sensitivity2, build_limit_seed2
        from tia2d_seed import propagate_geometry_seed
        from tia2d_readback import read_double
        contacts = assemble_contact_set2(model)
        geometry_seconds = time.perf_counter() - started
        start = time.perf_counter()
        result = (limit_load_ideal_exact_2d(model, contacts) if target == "limit" else
                  critical_parameter(model, contact_set=contacts, mu_max=read_double(query["mu_max_bits"]),
                                     max_steps=query.get("max_steps", 64)))
        primal_seconds = time.perf_counter() - start
        p = result.problem if target == "limit" else result.threshold_certificate.problem
        start = time.perf_counter()
        derivatives = []
        for q in queries:
            seed = propagate_geometry_seed(p, q["geometry_seed"])
            mu_seed = build_limit_seed2(p, mu_seed=1) if target == "critical" else None
            derivatives.append(asdict(evaluate_sensitivity2(result, seed,
                parameter=q["result"]["parameter"], threshold_mu_seed=mu_seed,
                positive_direction_valid=q["direction_domain"]["positive"],
                negative_direction_valid=q["direction_domain"]["negative"],
                validity_conditions=tuple(q["declared_validity_conditions"]))))
        derivative_seconds = time.perf_counter() - start
        problem = dict(b=p.b, c=p.c)
        value = result.exact_value if target == "limit" else result.exact_threshold
        state = result.status
    from fractions import Fraction
    def number(v):
        if v is None:
            return None
        q = Fraction(v)
        return f"{q.numerator}/{q.denominator}"
    return dict(backend=args.backend, case_id=args.case, target=target,
        bodies=len(model.bodies), rows=len(problem["b"]), columns=len(problem["c"]),
        channels=len(queries), geometry_seconds=geometry_seconds,
        primal_seconds=primal_seconds, derivative_seconds=derivative_seconds,
        state=state, exact_value=number(value), derivatives=[dict(
            parameter=d["parameter"], differentiability=d["differentiability"],
            right=number(d["right_derivative"]), left=number(d["left_derivative"])) for d in derivatives])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dll", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--backend", choices=("cpp", "python"))
    parser.add_argument("--case", default="g5_n3_mu1")
    args = parser.parse_args()
    if args.backend:
        print(json.dumps(worker(args), ensure_ascii=False))
        return
    if not args.output:
        parser.error("--output required")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    environment = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    for case in ("g1_slender", "g5_n3_mu1", "g5_n3_mu2"):
        pair = []
        for backend in ("cpp", "python"):
            command = [sys.executable, "-X", "utf8", str(Path(__file__).resolve()),
                       "--backend", backend, "--case", case, "--dll", str(args.dll.resolve())]
            start = time.perf_counter()
            run = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True,
                                 text=True, encoding="utf-8", errors="replace", check=True)
            row = json.loads(run.stdout)
            row["cold_process_seconds"] = time.perf_counter() - start
            row["command"] = command
            rows.append(row); pair.append(row)
            args.output.with_suffix(".progress.json").write_text(json.dumps(dict(
                complete=False, cases=len(rows), latest=row), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for key in ("state", "exact_value", "derivatives", "rows", "columns", "channels"):
            if pair[0][key] != pair[1][key]:
                raise AssertionError(f"timed results disagree: {case}/{key}")
    result = dict(schema="eab2.c3l4.cold-timing.v1", complete=True, samples_per_backend_case=1,
        performance_gate=False, source_commit="b34c966+uncommitted C3L4",
        dll_sha256=hashlib.sha256(args.dll.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        caveats=["one cold-process sample per case/backend", "C++ includes ABI+JSON; Python does not",
                 "primal excludes contact construction; derivative includes exact seed propagation",
                 "small representative queries, not a large-assembly throughput benchmark"],
        rows=rows, last_line="C3L4_TIMING_REPORTED pairs=3 cold_processes=6")
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output.with_suffix(".progress.json").write_text(json.dumps(dict(complete=True, cases=len(rows))) + "\n", encoding="utf-8")
    print(result["last_line"])


if __name__ == "__main__":
    main()
