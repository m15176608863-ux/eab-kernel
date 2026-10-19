"""Run six real source-copy mutations against exact semantic acceptance gates.

Only the private evidence copy is edited. The production tree is read-only to
this runner. A killed mutant must exit with pytest's assertion-failure status,
and its output must contain the named semantic assertion, not a hash mismatch,
collection error or incidental exception. Every run starts a fresh directory.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
TEST = "tests/test_tia2d_critical_acceptance.py::"
MUTATIONS = (
    ("C1", "statics.py",
     'closed = at.status == "UNBOUNDED" and (candidate == 0 or below is not None)',
     'closed = at.status == "UNBOUNDED"',
     "test_endpoint_states_do_not_replace_opposite_side_continuation",
     "upper state alone is not a closed threshold"),
    ("C2", "statics.py",
     'opened = (at.status == "OPTIMAL" and not any(zero.b) and above is not None\n                  and candidate < hi)',
     'opened = (at.status == "OPTIMAL" and not any(zero.b)\n                  and candidate < hi)',
     "test_low_budget_threshold_never_certifies_a_false_root",
     "exact root requires both relevant continuation proofs"),
    ("C11", "critical.py",
     "        if _root_count(reduced, lower, upper):\n            return None\n        value = p_eval(poly, sample) / denominator",
     "        value = p_eval(poly, sample) / denominator",
     "test_branch_signs_rejects_interior_numerator_roots_even_when_midpoint_positive",
     "interior numerator roots must not be skipped"),
    ("C10", "critical.py",
     '    if any(value < 0 for value in values):\n        return None\n    return CriticalBasis2("mechanism"',
     '    return CriticalBasis2("mechanism"',
     "test_mechanism_basis_rejects_negative_reduced_costs",
     "negative dual slack is not a mechanism basis"),
    ("S7", "sensitivity.py",
     "    if dual is None:\n        rows = []", "    if False:\n        rows = []",
     "test_dual_recession_requires_the_lp_witness_not_only_lineality",
     "dual half-line recession must suppress a slope"),
    ("C9", "statics.py",
     'reason = "input_resolution_limit" if _binary_midpoint(lo, hi) is None else "iteration_limit"',
     'reason = "iteration_limit"',
     "test_last_allowed_bisection_step_retains_resolution_reason_and_proof_reason",
     "loop-end resolution reason must survive"),
)


def _write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(output):
    output = Path(output).resolve()
    allowed = (ROOT / "reports/codex/T1a_evidence").resolve()
    if not output.is_relative_to(allowed) or output.exists():
        raise ValueError("fresh output under T1a_evidence required")
    output.mkdir(parents=True)
    temporary = (allowed / "tmp" / output.name).resolve()
    if temporary.exists():
        raise ValueError("fresh private copy required")
    temporary.mkdir(parents=True)
    copy = temporary / "source"
    copy.mkdir()
    shutil.copytree(ROOT / "src", copy / "src", ignore=shutil.ignore_patterns("__pycache__"))
    (copy / "tests").mkdir()
    for filename in ("test_tia2d_critical_acceptance.py", "test_tia2d_statics.py", "test_tia2d_sensitivity.py"):
        shutil.copy2(ROOT / "tests" / filename, copy / "tests" / filename)
    shutil.copy2(ROOT / "pyproject.toml", copy / "pyproject.toml")
    environment = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1",
                       TEMP=str(allowed / "tmp"), TMP=str(allowed / "tmp"))
    summary = dict(status="running", method="edited_source_copy_semantic_pytest_assertions", mutations=[])
    _write(output / "summary.json", summary)
    baseline_command = [sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                        "--basetemp", str(temporary / "baseline_pytest"), "tests"]
    baseline = subprocess.run(baseline_command, cwd=copy, env=environment, capture_output=True)
    baseline_log = baseline.stdout + baseline.stderr
    (output / "baseline.log").write_bytes(baseline_log)
    summary["baseline"] = dict(returncode=baseline.returncode, command=baseline_command,
                               last_line=baseline_log.decode("utf-8", "replace").strip().splitlines()[-1])
    _write(output / "summary.json", summary)
    if baseline.returncode:
        raise AssertionError("clean copied source must pass before mutation")
    for name, filename, old, new, gate, assertion in MUTATIONS:
        source = copy / "src/eab/kernel2d" / filename
        original = source.read_bytes()
        text = original.decode("utf-8")
        if text.count(old) != 1:
            raise AssertionError((name, "mutation target count", text.count(old)))
        changed = text.replace(old, new).encode("utf-8")
        command = [sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                   "--basetemp", str(temporary / (name + "_pytest")), TEST + gate]
        before = time.perf_counter()
        source.write_bytes(changed)
        try:
            result = subprocess.run(command, cwd=copy, env=environment, capture_output=True)
        finally:
            source.write_bytes(original)
        log = result.stdout + result.stderr
        (output / (name + ".log")).write_bytes(log)
        decoded = log.decode("utf-8", "replace")
        killed = result.returncode == 1 and assertion in decoded and "AssertionError" in decoded
        record = dict(mutation=name, source="src/eab/kernel2d/" + filename, gate=TEST + gate,
                      before_sha256=hashlib.sha256(original).hexdigest(),
                      mutant_sha256=hashlib.sha256(changed).hexdigest(),
                      killed_by_semantic_assertion=killed, returncode=result.returncode,
                      assertion=assertion, seconds=time.perf_counter() - before,
                      last_line=decoded.strip().splitlines()[-1], command=command)
        summary["mutations"].append(record)
        _write(output / "summary.json", summary)
        print(name, record["last_line"], "semantic_kill=" + str(killed), flush=True)
    summary["status"] = "PASS" if all(item["killed_by_semantic_assertion"] for item in summary["mutations"]) else "FAIL"
    _write(output / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if run(args.output)["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
