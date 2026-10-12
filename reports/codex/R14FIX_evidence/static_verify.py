"""Run original full AST checker against a byte-frozen source/test/policy set."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
paths = sorted([p for folder in ("src", "tests") for p in (ROOT/folder).rglob("*.py")])
paths += [ROOT/"tools/exact_construction_policy.json", ROOT/"tools/check_exact_construction.py",
          ROOT/"tools/exact_construction_subset.py", ROOT/"tools/exact_construction_flow.py"]


def hashes():
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


before = hashes()
started = time.perf_counter()
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
result = subprocess.run([sys.executable, "-X", "utf8", "tools/check_exact_construction.py"],
                        cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8")
elapsed = time.perf_counter()-started
after = hashes()
(HERE/"static_final.log").write_text(result.stdout+result.stderr, encoding="utf-8")
data = dict(command="PYTHONDONTWRITEBYTECODE=1 python -X utf8 tools/check_exact_construction.py",
            exitcode=result.returncode, seconds=elapsed, final_line=result.stdout.rstrip().splitlines()[-1],
            source_policy_bytes_unchanged=before==after, sha256=after)
(HERE/"static_final_status.json").write_text(json.dumps(data, indent=2)+"\n", encoding="utf-8")
print(json.dumps({k:v for k,v in data.items() if k!="sha256"}, indent=2))
assert before==after, "source/policy changed during verification"
raise SystemExit(result.returncode)
