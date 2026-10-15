"""Control/red evidence for the callback site rule and timeout protocol."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/codex/M5a2_evidence"


def main():
    out = EVIDENCE / "static_mutations_r1"
    out.mkdir(exist_ok=False)
    temp = EVIDENCE / "tmp/static_mutations_r1"
    temp.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, TEMP=str(temp), TMP=str(temp), PYTHONIOENCODING="utf-8",
               PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=os.pathsep.join((str(ROOT / "src"), str(ROOT / "tools"), str(ROOT / "tests"))))
    common = ["-q", "-p", "no:cacheprovider", "--basetemp", str(temp / "pytest"),
              "tests/test_m5a2_static_runner.py::test_arbitrary_algebraic_comparator_requires_individual_site_admission"]
    child = '''import inspect, sys, pytest
import check_exact_construction as gate
if sys.argv[1] == "mutant":
    source = inspect.getsource(gate.scan_text)
    old = 'if "scalar_algebraic" in names:'
    assert source.count(old) == 1
    namespace = dict(vars(gate))
    exec(compile(source.replace(old, "if False:"), "<M5a2 comparator gate internal mutant>", "exec"), namespace)
    gate.scan_text = namespace["scan_text"]
raise SystemExit(pytest.main(sys.argv[2:]))
'''
    results = {}
    for phase in ("control", "mutant"):
        result = subprocess.run([sys.executable, "-X", "utf8", "-c", child, phase, *common],
                                cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", timeout=60)
        output = result.stdout + result.stderr
        (out / (phase + ".txt")).write_text(output, encoding="utf-8")
        results[phase] = dict(exit_code=result.returncode, last_line=output.strip().splitlines()[-1])
        if phase == "mutant":
            assert "arbitrary comparator must not inherit exactness" in output
    assert results["control"]["exit_code"] == 0 and results["mutant"]["exit_code"] == 1
    command = [sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-p", "no:cacheprovider",
               "--basetemp", str(temp / "timeouts"),
               "tests/test_m5a2_static_runner.py::test_per_test_watchdog_terminates_real_internal_nontermination",
               "tests/test_m5a2_static_runner.py::test_gate_step_deadline_also_covers_collection_and_static_nontermination"]
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", timeout=60)
    output = result.stdout + result.stderr
    (out / "timeouts.txt").write_text(output, encoding="utf-8")
    assert result.returncode == 0
    results["timeouts"] = dict(exit_code=0, last_line=output.strip().splitlines()[-1],
                               internal_defect="RealAlgebraic.refine infinite loop", expected_child_exit=124)
    results.update(complete=True, audit="GREEN", hash_tripwire="not invoked; no source/fixture hash is an oracle",
                   defect="disable comparator-specific condition inside scan_text", witness="named semantic assertion")
    (out / "summary.json").write_text(json.dumps(results, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("M5A2_STATIC_MUTATIONS_GREEN")


if __name__ == "__main__":
    main()
