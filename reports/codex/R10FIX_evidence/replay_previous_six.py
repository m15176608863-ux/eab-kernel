"""Read-only replay of G6J's six positive R9 checks; only adapt root discovery."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
INPUT = ROOT / "reports/codex/inputs/G6J_repro"
EVIDENCE = Path(__file__).resolve().parent

if len(sys.argv) > 1:
    path = INPUT / sys.argv[1]
    source = path.read_text(encoding="utf-8")
    source = source.replace("Path(__file__).resolve().parents[2]", f"Path({str(ROOT)!r})")
    exec(compile(source, str(path), "exec"), {"__name__": "__main__", "__file__": str(path)})
else:
    rows = []
    for path in sorted(INPUT.glob("r9_positive*.py")):
        start = time.perf_counter()
        result = subprocess.run([sys.executable, "-X", "utf8", __file__, path.name],
                                cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                                errors="replace", env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        log = EVIDENCE / (path.stem + ".log")
        log.write_text(result.stdout + result.stderr, encoding="utf-8")
        rows.append({"script": path.name, "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                     "exit_code": result.returncode, "seconds": time.perf_counter()-start,
                     "log": log.name})
    (EVIDENCE / "previous_six_replay.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps(rows, indent=2))
    sys.exit(any(row["exit_code"] for row in rows))
