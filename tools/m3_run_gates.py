"""WO-M3 exhaustive four-shard runner; no Git writes, immutable byte snapshots.

The owner forbids worktrees. A fresh file export is not a committed checkout.
Record *actual* collected and executed node IDs, not only the dispatch list.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/codex/M3_evidence"


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(command, cwd, env, path):
    start = time.perf_counter()
    with path.open("wb") as log:
        result = subprocess.run(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return {"command": command, "exit_code": result.returncode,
            "seconds": time.perf_counter()-start, "last_line": lines[-1] if lines else "",
            "log": str(path)}


PLUGIN = '''import json, os
from pathlib import Path
collected = []
reports = []
def pytest_collection_finish(session):
    collected.extend(item.nodeid for item in session.items)
def pytest_runtest_logreport(report):
    reports.append(dict(nodeid=report.nodeid, when=report.when, outcome=report.outcome))
def pytest_sessionfinish(session, exitstatus):
    Path(os.environ["M3_EXECUTION_RECORD"]).write_text(json.dumps(dict(
        collected=collected, reports=reports, exitstatus=int(exitstatus)), indent=2), encoding="utf-8")
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--source", type=Path, help="Use an already frozen source, otherwise make a byte export")
    args = parser.parse_args()
    out = EVIDENCE / args.name
    if out.exists():
        parser.error("output must be new")
    out.mkdir(parents=True)
    source = args.source.resolve() if args.source else EVIDENCE / "tmp" / (args.name + "_export")
    if not source.is_relative_to(EVIDENCE / "tmp"):
        parser.error("frozen source must stay in this workspace evidence tmp")
    if args.source is None:
        source.mkdir()
        names = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT).decode("utf-8").split("\0")
        for name in sorted(set(filter(None, names))):
            src = ROOT / name
            if (src.is_relative_to(EVIDENCE / "tmp") or src.is_relative_to(out)
                    or src.is_relative_to(ROOT / "build") or not src.is_file()):
                continue
            dst = source / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            assert src.read_bytes() == dst.read_bytes(), name
    manifest = [{"path": p.relative_to(source).as_posix(), "bytes": p.stat().st_size,
                 "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                for p in source.rglob("*") if p.is_file()]
    write_json(out / "export_manifest.json", manifest)
    (out / "m3_execution_plugin.py").write_text(PLUGIN, encoding="utf-8")
    temp = EVIDENCE / "tmp" / (args.name + "_temp")
    temp.mkdir()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8",
               PYTHONPATH=os.pathsep.join((str(source/"src"), str(out))), TEMP=str(temp), TMP=str(temp))
    for key in ("BDDA_DETECT", "BDDA_DETECT_SHADOW", "BDDA_SHADOW_PATH"):
        env.pop(key, None)
    python = [sys.executable, "-X", "utf8"]
    start = time.perf_counter()
    collection = run(python + ["-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"], source, env, out/"collection.txt")
    assert collection["exit_code"] == 0, collection
    nodes = [s for s in (out/"collection.txt").read_text(encoding="utf-8").splitlines()
             if s.startswith("tests/") and "::" in s]
    assert nodes and len(nodes) == len(set(nodes))
    shards = [nodes[i::4] for i in range(4)]

    def shard(i):
        response = out / f"shard_{i+1}_nodes.txt"
        response.write_text("\n".join(shards[i])+"\n", encoding="utf-8")
        record = out / f"shard_{i+1}_execution.json"
        local_env = dict(env, M3_EXECUTION_RECORD=str(record))
        result = run(python + ["-m", "pytest", "-q", "-p", "no:cacheprovider", "-p", "m3_execution_plugin",
                               "@"+str(response), "--basetemp", str(temp/f"pytest_{i+1}")],
                     source, local_env, out/f"shard_{i+1}.txt")
        data = json.loads(record.read_text(encoding="utf-8")) if record.exists() else {"collected": [], "reports": []}
        executed = [r["nodeid"] for r in data["reports"] if r["when"] == "call"]
        skipped = [r for r in data["reports"] if r["outcome"] == "skipped"]
        result.update(dispatched=len(shards[i]), collected=len(data["collected"]), executed=len(executed),
                      skip_count=len(skipped), node_sets_equal=(sorted(shards[i]) == sorted(data["collected"]) == sorted(executed)))
        write_json(out/f"shard_{i+1}.json", result)
        print(f"shard {i+1}: {result['last_line']}", flush=True)
        return result

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(shard, range(4)))
    static = run(python+["tools/check_exact_construction.py"], source, env, out/"exact_construction.txt")
    good = all(r["exit_code"] == 0 and r["node_sets_equal"] and r["skip_count"] == 0 for r in results) and static["exit_code"] == 0
    write_json(out/"summary.json", dict(audit="GREEN" if good else "RED", collected=len(nodes), shards=results,
                                       static=static, elapsed_seconds=time.perf_counter()-start,
                                       source=str(source), fresh_git_checkout=False))
    print(static["last_line"], flush=True)
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
