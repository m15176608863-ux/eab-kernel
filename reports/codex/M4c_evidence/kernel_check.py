"""Rerun the small M4c motion component gates without modifying source files."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    sys.dont_write_bytecode = True
    here = Path(__file__).resolve().parent
    root = here.parents[2]
    temporary = here / "tmp"
    temporary.mkdir(exist_ok=True)
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", TEMP=str(temporary), TMP=str(temporary))
    command = [sys.executable, "-X", "utf8", "-m", "pytest", "-q", "tests/test_m4c_motion.py", "--durations=5"]
    start = time.perf_counter()
    run = subprocess.run(command, cwd=root, env=environment, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, encoding="utf-8")
    elapsed = time.perf_counter()-start
    (here / "kernel_pytest.txt").write_text(run.stdout, encoding="utf-8", newline="")
    spec = importlib.util.spec_from_file_location("m4c_component_static_gate", root / "tools/check_exact_construction.py")
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    files = {}
    for name in ("src/eab/kernel2d/motion.py", "tests/test_m4c_motion.py"):
        source = (root/name).read_bytes()
        files[name] = {"sha256": hashlib.sha256(source).hexdigest(), "utf8_bom": source.startswith(b"\xef\xbb\xbf"),
                       "static_issues": gate.scan_text(source.decode("utf-8"), name)}
    passed = run.returncode == 0 and all(not item["static_issues"] and not item["utf8_bom"] for item in files.values())
    report = {"scope": "component only; not the full-suite or G6 exit gate", "passed": passed,
              "command": command, "test_returncode": run.returncode, "test_wall_seconds": elapsed,
              "pytest_final_line": run.stdout.strip().splitlines()[-1], "files": files,
              "sample_counts": {"m3_translation": 18, "m2_convex_translation": 9,
                                "independent_signs": 324, "independent_root_orderings": 132,
                                "single_cover_transformations": 24, "multi_cover_transformations": 54,
                                "internal_mutations": 4},
              "oracle_imports": ["fractions.Fraction", "math.nextafter", "math.inf",
                                 "eab.kernel2d.g0_oracle", "eab.oracle_construction"],
              "mutation_expected_assertions": {"wrong_quadratic_branch": "earliest quadratic branch",
                                               "open_endpoint": "closed endpoint event lost",
                                               "lost_tie": "complete simultaneous cover set",
                                               "translation_bypass": "general event path translation consistency"},
              "mutation_gate": "test_internal_mutations_fail_the_intended_guard; pytest.raises matches the expected assertion"}
    (here / "kernel_component_gate.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="")
    print(report["pytest_final_line"])
    print("component static issues:", sum(len(item["static_issues"]) for item in files.values()))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
