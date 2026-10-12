"""Four ordinary pytest processes; exact collected/executed union must equal full suite.

No xdist/install, skip, xfail, -k or grid changes. Audit plugin is read-only with
respect to selection. All source/tool/test bytes and policy stay frozen.
"""
import collections
import concurrent.futures
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RUN_NAME = os.environ.get("R13B_RUN_NAME", "full_suite_final")
assert RUN_NAME and all(c.isalnum() or c in "_-" for c in RUN_NAME)
OUT = HERE / RUN_NAME


def snapshot():
    paths = [p for folder in ("src", "tests", "tools") for p in (ROOT / folder).rglob("*.py")]
    paths += [ROOT / "tools/exact_construction_policy.json", ROOT / "pyproject.toml"]
    paths += [ROOT / "README.md", ROOT / "docs/canon_map.md", ROOT / "docs/r13fix_design_sync.md",
              Path(__file__).resolve(), HERE / "r13_audit_plugin.py"]
    paths += list((ROOT / "docs").glob("*.md"))
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def dump(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def run(name, files=None, collect=False):
    system_temp = HERE / "tmp" / RUN_NAME / (name + "_system_temp")
    system_temp.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-p", "no:cacheprovider",
               "-p", "r13_audit_plugin", "--durations=20",
               "--basetemp=" + str(HERE / "tmp" / RUN_NAME / name)]
    if collect:
        command += ["--collect-only"]
    if files:
        command += files
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8",
           "TEMP": str(system_temp), "TMP": str(system_temp), "TMPDIR": str(system_temp),
           "PYTHONPATH": str(HERE) + os.pathsep + os.environ.get("PYTHONPATH", ""),
           "R13_COLLECTION": str(OUT / (name + "_nodes.json")),
           "R13_RESULTS": str(OUT / (name + "_results.jsonl"))}
    results = OUT / (name + "_results.jsonl")
    assert not results.exists(), "Use a fresh output directory; do not mix audit runs"
    started = time.perf_counter()
    with (OUT / (name + ".log")).open("w", encoding="utf-8", newline="") as log:
        proc = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    elapsed = time.perf_counter() - started
    lines = (OUT / (name + ".log")).read_text(encoding="utf-8").splitlines()
    info = {"name": name, "command": command, "exit_code": proc.returncode,
            "wall_seconds": elapsed, "last_line": next((x for x in reversed(lines) if x.strip()), "")}
    dump(name + "_run.json", info)
    print(json.dumps(info, ensure_ascii=False), flush=True)
    return info


def main():
    OUT.mkdir(exist_ok=False)
    (HERE / "tmp" / RUN_NAME).mkdir(parents=True, exist_ok=True)
    started_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    before = snapshot()
    dump("before_snapshot.json", before)
    collect = run("collection", collect=True)
    assert collect["exit_code"] == 0
    nodes = json.loads((OUT / "collection_nodes.json").read_text(encoding="utf-8"))
    counts = collections.Counter(x.split("::")[0] for x in nodes)
    weights = {f: max(1., n * .06) for f, n in counts.items()}
    # Conservative prior timings; affects scheduling only, not membership.
    for name, weight in {"bb52_g1": 280, "invariance_interlock": 180, "invariance_geom": 130,
                         "interlock_escape": 120, "interlock_walls": 90, "interlocking": 70,
                         "frozen_lowdim": 65, "r9fix_construction_static": 35,
                         "r12fix_static_closed": 45, "lp_certificates": 30}.items():
        weights["tests/test_" + name + ".py"] = weight
    prior = json.loads((HERE / "prior_file_seconds.json").read_text(encoding="utf-8"))
    weights.update({f: seconds for f, seconds in prior.items() if f in counts})
    shards, loads = [[] for _ in range(4)], [0.] * 4
    for f in sorted(counts, key=lambda f: (-weights[f], f)):
        target = min(range(4), key=lambda i: loads[i])
        shards[target].append(f)
        loads[target] += weights[f]
    assert set(sum(shards, [])) == set(counts) and sum(map(len, shards)) == len(counts)
    dump("partition.json", {"files": shards, "weights": loads, "collected_tests": len(nodes)})
    start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(run, f"shard_{i+1}", sorted(files)) for i, files in enumerate(shards)]
        runs = [f.result() for f in futures]
    wall = time.perf_counter() - start
    collected, calls, bad = [], [], []
    for info in runs:
        name = info["name"]
        collected += json.loads((OUT / (name + "_nodes.json")).read_text(encoding="utf-8"))
        for line in (OUT / (name + "_results.jsonl")).read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row["when"] == "call":
                calls.append(row["nodeid"])
            if row["outcome"] != "passed":
                bad.append(row)
    after = snapshot()
    drift = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
    checks = {"collection_union_exact_no_duplicates": collections.Counter(collected) == collections.Counter(nodes),
              "executed_union_exact_no_duplicates": collections.Counter(calls) == collections.Counter(nodes),
              "full_collection_itself_unique": len(nodes) == len(set(nodes)),
              "all_pytest_processes_exit_zero": all(r["exit_code"] == 0 for r in runs),
              "all_setup_call_teardown_pass": not bad, "source_policy_unchanged": not drift,
              "all_original_11723_nodes_preserved": set(json.loads((HERE / "baseline_nodes.json").read_text(encoding="utf-8"))) <= set(nodes)}
    passed = all(checks.values())
    report = {"mode": "four standard pytest processes, complete-file partition, exact node union verified",
              "started_utc": started_utc, "finished_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "tests_collected": len(nodes), "tests_executed": len(calls), "wall_seconds": wall,
              "collection_seconds": collect["wall_seconds"], "elapsed_contract": "Measured wall time, no user-requested runtime acceptance cap; never drop nodes",
              "sum_pytest_process_seconds": sum(r["wall_seconds"] for r in runs),
              "checks": checks, "code_drift": drift, "nonpass_reports": bad, "runs": runs,
              "status": "PASS" if passed else "FAIL"}
    dump("summary.json", report)
    print(json.dumps(report, indent=2), flush=True)
    print(f"R13FIXb_FULL_SUITE {report['status']}: {len(calls)} calls; wall={wall:.3f}s; failures_or_skips={len(bad)}; source_drift={len(drift)}", flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
