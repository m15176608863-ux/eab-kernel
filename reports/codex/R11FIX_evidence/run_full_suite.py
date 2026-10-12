"""Run the unchanged full suite serially and retain exact output and code hashes."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def snapshot():
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ("src", "tests", "tools")
            for p in sorted((ROOT / folder).rglob("*.py"))}


if __name__ == "__main__":
    (HERE / "tmp").mkdir(parents=True, exist_ok=True)
    before = snapshot()
    (HERE / "final_run_code_snapshot.json").write_text(json.dumps(before, indent=2), encoding="utf-8")
    command = [sys.executable, "-X", "utf8", "-m", "pytest", "-q", "--durations=20",
               "-p", "no:cacheprovider", "--basetemp=reports/codex/R11FIX_evidence/tmp/full_suite"]
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    start = time.perf_counter()
    with (HERE / "full_suite.log").open("w", encoding="utf-8", newline="") as log:
        result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"})
    wall_seconds = time.perf_counter() - start
    after = snapshot()
    drift = sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))
    lines = (HERE / "full_suite.log").read_text(encoding="utf-8").splitlines()
    report = {"command": command, "cwd": str(ROOT), "started_utc": started,
              "finished_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "wall_seconds": wall_seconds, "exit_code": result.returncode,
              "last_line": next((line for line in reversed(lines) if line.strip()), ""),
              "code_files_checked": len(before), "code_drift": drift,
              "within_900_seconds": wall_seconds <= 900}
    (HERE / "full_suite.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    sys.exit(result.returncode or bool(drift))
