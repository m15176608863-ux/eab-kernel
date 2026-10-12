"""UTF-8 capture of final gate, regression, M4a and documentation checks."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
(HERE / "tmp").mkdir(parents=True, exist_ok=True)
env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
commands = {
    "static_gate": ["tools/check_exact_construction.py"],
    "targeted_regression": ["-m", "pytest", "-q", "-p", "no:cacheprovider", "--durations=10",
        "tests/test_r9fix_construction_static.py", "tests/test_r10_static_construction.py",
        "tests/test_r11fix_static_flow.py", "tests/test_r12fix_static_closed.py",
        "--basetemp=reports/codex/R12FIX_evidence/tmp/final_targeted"],
    "m4_and_documents": ["-m", "pytest", "-q", "-p", "no:cacheprovider",
        "tests/test_m4_bdda_adapter.py", "tests/test_m4_bdda_shadow.py", "tests/test_m4_bdda_vv_reader.py",
        "tests/test_doc_pointers.py", "tests/test_r7fix_docs.py",
        "--basetemp=reports/codex/R12FIX_evidence/tmp/final_m4_docs"],
    "canon_pointers": ["tools/fix_canon_ptrs.py", "--apply"],
    "mutation_teeth": ["reports/codex/R12FIX_evidence/record_mutation_teeth.py"],
}
rows = []
for name, args in commands.items():
    start = time.perf_counter()
    command = [sys.executable, "-X", "utf8", *args]
    with (HERE / (name + ".log")).open("w", encoding="utf-8", newline="") as log:
        proc = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    lines = (HERE / (name + ".log")).read_text(encoding="utf-8").splitlines()
    row = {"name": name, "command": command, "exit_code": proc.returncode,
           "wall_seconds": time.perf_counter() - start,
           "last_line": next((line for line in reversed(lines) if line.strip()), "")}
    rows.append(row)
    (HERE / "targeted_verification.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps(row), flush=True)
    if proc.returncode:
        sys.exit(proc.returncode)
print("R12_TARGETED_VERIFICATION_PASS", flush=True)
