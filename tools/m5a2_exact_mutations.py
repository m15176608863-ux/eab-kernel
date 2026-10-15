"""M5a2 exact-boundary source-body mutations, no source hash tripwire.

Each fresh worker first disables the replay's source/file hash callbacks, then
executes either the unchanged guard or a real function-body mutant compiled
in memory. No tracked source is overwritten. A mutant passes this evidence
only when it fails the named semantic assertion (never import/hash failure).
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
EVIDENCE = ROOT / "reports/codex/M5a2_evidence"


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def worker(kind, mutated):
    sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests"), str(ROOT / "tools")]
    import test_m5a2_exact as guard
    # Both source and fixture file hashing are disabled BEFORE control and
    # mutant execution. Numerical expectations still come only from tests.
    guard.replay.code_hashes = lambda: {}
    guard.replay.file_hash = lambda _: "HASH_TRIPWIRE_DISABLED"
    print("source_hash_tripwire=DISABLED", flush=True)
    if mutated:
        with guard.exact_mutation(kind):
            guard.exact_mutation_guard(kind)
    else:
        guard.exact_mutation_guard(kind)
    print("EXACT_SEMANTIC_GUARD_PASS", flush=True)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="exact_mutations_r1")
    parser.add_argument("--worker")
    parser.add_argument("--mutant", action="store_true")
    args = parser.parse_args()
    if args.worker:
        return worker(args.worker, args.mutant)
    if Path(args.name).name != args.name or args.name in (".", ".."):
        parser.error("name must be one fresh evidence directory")
    out = EVIDENCE / args.name
    if out.exists():
        parser.error("new directory required; interrupted evidence is invalid, never resumed")
    out.mkdir(parents=True)
    temporary = EVIDENCE / "tmp"
    temporary.mkdir(parents=True, exist_ok=True)
    os.environ.update(TEMP=str(temporary), TMP=str(temporary), PYTHONDONTWRITEBYTECODE="1")
    sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests"), str(ROOT / "tools")]
    from test_m5a2_exact import EXACT_MUTATIONS
    rows = []
    started = time.perf_counter()
    dump(out / "progress.json", {"complete": False, "interruption_invalidates": True, "rows": rows})
    for kind, expected in EXACT_MUTATIONS:
        record = {"kind": kind, "expected_semantic_assertion": expected}
        for stage in ("control", "mutant"):
            command = [sys.executable, "-X", "utf8", str(Path(__file__).resolve()), "--worker", kind]
            if stage == "mutant":
                command.append("--mutant")
            env = dict(os.environ, PYTHONIOENCODING="utf-8")
            try:
                result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True,
                                        encoding="utf-8", errors="replace", timeout=60)
                output, code = result.stdout+result.stderr, result.returncode
            except subprocess.TimeoutExpired:
                output, code = "WORKER_TIMEOUT: nonterminating guard is RED", 124
            (out / (kind+"_"+stage+".log")).write_text(output, encoding="utf-8")
            record[stage] = {"exit_code": code, "last_line": output.strip().splitlines()[-1],
                             "hash_tripwire_disabled": "source_hash_tripwire=DISABLED" in output,
                             "semantic_assertion_seen": expected in output}
        record["semantic_kill"] = (record["control"]["exit_code"] == 0 and
            record["mutant"]["exit_code"] == 1 and record["mutant"]["semantic_assertion_seen"] and
            record["control"]["hash_tripwire_disabled"] and record["mutant"]["hash_tripwire_disabled"])
        rows.append(record)
        dump(out / "progress.json", {"complete": False, "interruption_invalidates": True, "rows": rows})
        print(kind, record["semantic_kill"], flush=True)
    summary = {"complete": True, "audit": "GREEN" if all(r["semantic_kill"] for r in rows) else "RED",
               "mutation_kind": "actual internal function body compiled in memory; no fake post-output data",
               "hash_tripwire": "disabled before all controls and mutants", "rows": rows,
               "seconds": time.perf_counter()-started,
               "sources_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in (
                   "src/eab/kernel2d/algebraic.py", "src/eab/kernel2d/se2.py",
                   "tests/m5a_independent_oracle.py", "tests/test_m5a2_exact.py",
                   "tools/m5a2_exact_mutations.py")}}
    dump(out / "summary.json", summary)
    dump(out / "progress.json", summary)
    return 0 if summary["audit"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
