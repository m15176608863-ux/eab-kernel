"""Run a command with UTF-8/bytecode discipline and persist its raw evidence."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[3]
prefix = Path(sys.argv[1])
prefix.parent.mkdir(parents=True, exist_ok=True)
command = sys.argv[2:]
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
start = time.perf_counter()
with prefix.with_suffix(".log").open("wb") as output:
    result = subprocess.run(command, cwd=root, env=env, stdout=output,
                            stderr=subprocess.STDOUT)
metadata = dict(command=command, cwd=str(root), exit_code=result.returncode,
                wall_seconds=time.perf_counter()-start)
prefix.with_suffix(".json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
print(json.dumps(metadata))
print(prefix.with_suffix(".log").read_text(encoding="utf-8", errors="replace")[-5000:])
sys.exit(result.returncode)
