"""Targeted integration: new gates, R9/R10 static, all R10, M4a, docs and fixtures."""
from pathlib import Path
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
(HERE / "tmp").mkdir(parents=True, exist_ok=True)
selected = sorted({p.relative_to(ROOT).as_posix()
                   for pattern in ("test_r11*.py", "test_r10*.py", "test_m4*.py",
                                   "test_r9fix_construction_static.py", "test_doc_pointers.py",
                                   "test_fixture_provenance.py", "test_provenance_inputs.py",
                                   "test_filtered_predicates.py")
                   for p in (ROOT / "tests").glob(pattern)})
command = [sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-p", "no:cacheprovider",
           *selected, "--basetemp=reports/codex/R11FIX_evidence/tmp/integration"]
start = time.perf_counter()
result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"})
output = result.stdout + result.stderr
(HERE / "integration.log").write_text(output, encoding="utf-8")
report = {"command": command, "exit_code": result.returncode, "seconds": time.perf_counter()-start,
          "last_line": output.rstrip().splitlines()[-1]}
(HERE / "integration.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
raise SystemExit(result.returncode)
