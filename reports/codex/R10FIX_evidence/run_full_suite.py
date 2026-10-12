"""Serial whole-repository run with retained output, wall time and exit status."""
from pathlib import Path
import datetime
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
# pytest creates its basetemp leaf but not missing ancestors.
(HERE / "tmp").mkdir(parents=True, exist_ok=True)
command = [sys.executable, "-X", "utf8", "-m", "pytest", "-q", "--durations=20",
           "--basetemp=reports/codex/R10FIX_evidence/tmp/full_suite"]
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
start = time.perf_counter()
with (HERE / "full_suite.log").open("w", encoding="utf-8", newline="") as log:
    result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"})
lines = (HERE / "full_suite.log").read_text(encoding="utf-8").splitlines()
report = {"command": command, "cwd": str(ROOT), "started_utc": started,
          "wall_seconds": time.perf_counter()-start, "exit_code": result.returncode,
          "last_line": next((line for line in reversed(lines) if line.strip()), "")}
(HERE / "full_suite.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2), flush=True)
sys.exit(result.returncode)
