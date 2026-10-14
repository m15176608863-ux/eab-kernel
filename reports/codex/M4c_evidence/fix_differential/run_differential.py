"""Rerun WO-M4c-fix #4 tests and preserve compact exact differential evidence."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
TEMP = ROOT / "reports/codex/M4c_evidence/tmp/fix_differential"


def write(name, data):
    (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def main():
    os.chdir(ROOT)
    (TEMP / "env").mkdir(parents=True, exist_ok=True)
    os.environ.update(TEMP=str(TEMP / "env"), TMP=str(TEMP / "env"),
                      PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    sys.dont_write_bytecode = True
    command = [sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-p", "no:cacheprovider",
               "--basetemp", str(TEMP / "pytest_evidence"),
               "--junitxml", str(HERE / "pytest.xml"), "tests/test_m4c_fix_differential.py"]
    start = perf_counter()
    process = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    pytest_wall = perf_counter()-start
    (HERE / "pytest.txt").write_text(process.stdout+process.stderr, encoding="utf-8")
    if process.returncode:
        raise SystemExit(process.returncode)
    sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "src"), str(ROOT / "tools")]
    from test_m4c_fix_differential import CASES
    from m4c_independent_oracle import entrance
    from eab.kernel2d.motion import motion_first_entrance
    from check_exact_construction import scan_text
    cases = []
    statuses = Counter()
    initial_states = Counter()
    body_states = Counter()
    algebraic_contact_count = tied_contact_count = concave_count = 0
    start = perf_counter()
    for name, data in CASES:
        expected = entrance(*data)
        actual = motion_first_entrance(*data)
        cert = None if actual.exact_time is None else actual.exact_time.certificate
        observed = (actual.initial_state, actual.status, cert, actual.incidences, actual.features)
        assert observed == expected[:5], name
        statuses[actual.status] += 1
        initial_states[str(actual.initial_state)] += 1
        body_states.update(str(state) for _, state in expected[5])
        algebraic_contact_count += cert is not None and cert["rational"] is None
        tied_contact_count += len(actual.features) > 1
        concave_count += any(len(poly) == 6 for poly in data)
        cases.append({"case": name, "data": [[[str(x), str(y)] for x, y in p] for p in data],
                      "initial_state": actual.initial_state, "status": actual.status,
                      "time_certificate": cert, "incidences": actual.incidences,
                      "features": actual.features,
                      "rational_intervals": [[str(t), state] for t, state in expected[5]]})
    differential_wall = perf_counter()-start
    write("cases.json", cases)
    paths = ("tests/m4c_independent_oracle.py", "tests/test_m4c_fix_differential.py")
    static = {relative: scan_text((ROOT / relative).read_text(encoding="utf-8"), relative,
                                 repository_root=ROOT) for relative in paths}
    assert not any(static.values())
    junit = ET.parse(HERE / "pytest.xml")
    testcases = junit.findall(".//testcase")
    # JUnit reports setup + call + teardown and rounds per-node to milliseconds.
    pytest_case_seconds = sum(float(node.get("time", "0")) for node in testcases)
    summary = {"status": "GREEN", "timestamp_utc": datetime.now(timezone.utc).isoformat(),
               "command": command, "exit_code": process.returncode,
               "last_line": process.stdout.strip().splitlines()[-1],
               "case_count": len(CASES), "random_nontranslation_cases": 108,
               "structured_cases": 15, "concave_input_cases": concave_count,
               "status_counts": dict(statuses), "initial_state_counts": dict(initial_states),
               "irrational_first_contacts": algebraic_contact_count,
               "multiple_cover_contacts": tied_contact_count,
               "g0_interval_state_counts": dict(body_states),
               "g0_samples_per_interval": 2, "mismatches": 0,
               "pytest_tests": len(testcases), "skip_count": len(junit.findall(".//skipped")),
               "pytest_wall_seconds": pytest_wall, "pytest_case_seconds_junit_rounded": pytest_case_seconds,
               "differential_evidence_wall_seconds": differential_wall,
               "historical_full_suite_call_seconds": 3523.370647,
               "historical_full_suite_wall_seconds": 1700.583613,
               "pytest_case_to_historical_suite_call_percent": 100*pytest_case_seconds/3523.370647,
               "performance_caveat": "Historical denominator is not a same-run benchmark; final-suite timing is authoritative.",
               "oracle_direct_imports": ["dataclasses.dataclass", "fractions.Fraction", "math.isqrt", "math.lcm",
                                         "eab.kernel2d.g0_oracle.overlap"],
               "static_issues_for_new_files": static, "added_waivers": 0,
               "source_sha256": {relative: hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()
                                  for relative in paths}}
    write("summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
