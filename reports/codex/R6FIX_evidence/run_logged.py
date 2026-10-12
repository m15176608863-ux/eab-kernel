"""Run a command with UTF-8/no bytecode; preserve stdout, exit status and time."""
from pathlib import Path
import subprocess
import sys
import os
import time
import json

root = Path(__file__).resolve().parents[3]
prefix = root / "reports/codex/R6FIX_evidence" / sys.argv[1]
prefix.parent.mkdir(parents=True, exist_ok=True)
cmd = sys.argv[2:]
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
t = time.perf_counter()
with prefix.with_suffix(".log").open("w", encoding="utf-8", newline="") as stream:
    result = subprocess.run(cmd, cwd=root, env=env, stdout=stream, stderr=subprocess.STDOUT)
elapsed = time.perf_counter()-t
lines = prefix.with_suffix(".log").read_text(encoding="utf-8").splitlines()
summary = dict(command=cmd, cwd=str(root), exit_code=result.returncode, elapsed_seconds=elapsed,
               last_line=next((line for line in reversed(lines) if line.strip()), ""))
prefix.with_suffix(".json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
sys.exit(result.returncode)
