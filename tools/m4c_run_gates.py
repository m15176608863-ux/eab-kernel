"""WO-M4c exhaustive four-shard runner; no Git writes, immutable byte snapshots.

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
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/codex/M4c_evidence"


def write_json(path, value):
    temporary = path.with_name(path.name + ".writing")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Windows readers may briefly deny delete-sharing on the old target.
    # Keep the write atomic; retry only that transient permission failure.
    for attempt in range(12):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt == 11:
                raise
            time.sleep(min(0.01 * (attempt + 1), 0.1))


def run(command, cwd, env, path):
    start = time.perf_counter()
    progress = path.with_suffix(".progress.json")
    with path.open("wb") as log:
        result = subprocess.Popen(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
        while result.poll() is None:
            write_json(progress, dict(status="RUNNING", complete=False, pid=result.pid,
                                     command=command, elapsed_seconds=time.perf_counter()-start,
                                     output_bytes=path.stat().st_size))
            time.sleep(5)
    write_json(progress, dict(status="FINISHED", complete=True, exit_code=result.returncode,
                             elapsed_seconds=time.perf_counter()-start))
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return {"command": command, "exit_code": result.returncode,
            "seconds": time.perf_counter()-start, "last_line": lines[-1] if lines else "",
            "log": str(path)}


PLUGIN = '''import json, os, time
from pathlib import Path
collected = []
reports = []
started = time.monotonic()
def progress(complete=False):
    target = Path(os.environ["M4C_NODE_PROGRESS"])
    temporary = target.with_suffix(".writing")
    temporary.write_text(json.dumps(dict(complete=complete, collected=len(collected),
        calls=sum(r["when"] == "call" for r in reports),
        failed=sum(r["outcome"] == "failed" for r in reports),
        skipped=sum(r["outcome"] == "skipped" for r in reports),
        last=reports[-1] if reports else None, elapsed_seconds=time.monotonic()-started)), encoding="utf-8")
    for attempt in range(12):
        try:
            temporary.replace(target)
            return
        except PermissionError:
            if attempt == 11:
                raise
            time.sleep(min(0.01 * (attempt + 1), 0.1))
def pytest_collection_finish(session):
    collected.extend(item.nodeid for item in session.items)
    progress()
def pytest_runtest_logreport(report):
    row = dict(nodeid=report.nodeid, when=report.when, outcome=report.outcome, duration=report.duration)
    reports.append(row)
    with Path(os.environ["M4C_NODE_JOURNAL"]).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row)+"\\n")
    if report.when == "teardown":
        progress()
def pytest_sessionfinish(session, exitstatus):
    Path(os.environ["M4C_EXECUTION_RECORD"]).write_text(json.dumps(dict(
        complete=True, collected=collected, reports=reports, exitstatus=int(exitstatus)), indent=2), encoding="utf-8")
    progress(complete=True)
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--source", type=Path, help="Use an already frozen source, otherwise make a byte export")
    parser.add_argument("--baseline-head", action="store_true", help="Read-only git archive HEAD, not edited files")
    args = parser.parse_args()
    if Path(args.name).name != args.name or args.name in (".", ".."):
        parser.error("name must be a single new directory name")
    if args.source and args.baseline_head:
        parser.error("source and baseline-head are mutually exclusive")
    out = EVIDENCE / args.name
    if out.exists():
        parser.error("output must be new")
    out.mkdir(parents=True)
    (EVIDENCE / "tmp").mkdir(parents=True, exist_ok=True)
    write_json(out / "run_state.json", dict(status="EXPORTING", complete=False,
               results_reused=False, baseline_head=args.baseline_head, started_unix=time.time()))
    source = args.source.resolve() if args.source else EVIDENCE / "tmp" / (args.name + "_export")
    if not source.is_relative_to(EVIDENCE / "tmp"):
        parser.error("frozen source must stay in this workspace evidence tmp")
    if args.baseline_head:
        source.mkdir()
        archive = EVIDENCE / "tmp" / (args.name + "_head.zip")
        with archive.open("wb") as stream:
            subprocess.run(["git", "archive", "--format=zip", "HEAD"], cwd=ROOT, stdout=stream, check=True)
        with zipfile.ZipFile(archive) as bundle:
            for name in bundle.namelist():
                if not (source / name).resolve().is_relative_to(source):
                    raise ValueError("archive path escapes source")
            bundle.extractall(source)
    elif args.source is None:
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
    (out / "m4c_execution_plugin.py").write_text(PLUGIN, encoding="utf-8")
    temp = EVIDENCE / "tmp" / (args.name + "_temp")
    temp.mkdir()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8",
               PYTHONUNBUFFERED="1", PYTHONPATH=os.pathsep.join((str(source/"src"), str(out))), TEMP=str(temp), TMP=str(temp))
    for key in ("BDDA_DETECT", "BDDA_DETECT_SHADOW", "BDDA_SHADOW_PATH"):
        env.pop(key, None)
    python = [sys.executable, "-X", "utf8"]
    start = time.perf_counter()
    write_json(out / "run_state.json", dict(status="COLLECTING", complete=False, source=str(source)))
    collection = run(python + ["-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"], source, env, out/"collection.txt")
    assert collection["exit_code"] == 0, collection
    nodes = [s for s in (out/"collection.txt").read_text(encoding="utf-8").splitlines()
             if s.startswith("tests/") and "::" in s]
    assert nodes and len(nodes) == len(set(nodes))
    shards = [nodes[i::4] for i in range(4)]
    write_json(out / "run_state.json", dict(status="TESTING", complete=False, source=str(source),
               collected=len(nodes), shards=[len(s) for s in shards]))

    def shard(i):
        response = out / f"shard_{i+1}_nodes.txt"
        response.write_text("\n".join(shards[i])+"\n", encoding="utf-8")
        record = out / f"shard_{i+1}_execution.json"
        local_env = dict(env, M4C_EXECUTION_RECORD=str(record),
                         M4C_NODE_PROGRESS=str(out / f"shard_{i+1}_node_progress.json"),
                         M4C_NODE_JOURNAL=str(temp / f"shard_{i+1}_execution.jsonl"))
        result = run(python + ["-m", "pytest", "-q", "-p", "no:cacheprovider", "-p", "m4c_execution_plugin",
                               "@"+str(response), "--basetemp", str(temp/f"pytest_{i+1}")],
                     source, local_env, out/f"shard_{i+1}.txt")
        data = json.loads(record.read_text(encoding="utf-8")) if record.exists() else {"collected": [], "reports": []}
        executed = [r["nodeid"] for r in data["reports"] if r["when"] == "call"]
        skipped = [r for r in data["reports"] if r["outcome"] == "skipped"]
        result.update(dispatched=len(shards[i]), collected=len(data["collected"]), executed=len(executed),
                      skip_count=len(skipped), execution_complete=data.get("complete", False),
                      node_sets_equal=(sorted(shards[i]) == sorted(data["collected"]) == sorted(executed)))
        write_json(out/f"shard_{i+1}.json", result)
        print(f"shard {i+1}: {result['last_line']}", flush=True)
        return result

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(shard, range(4)))
    write_json(out / "run_state.json", dict(status="STATIC_GATE", complete=False, source=str(source)))
    static = run(python+["tools/check_exact_construction.py"], source, env, out/"exact_construction.txt")
    good = all(r["exit_code"] == 0 and r["execution_complete"] and r["node_sets_equal"] and r["skip_count"] == 0 for r in results) and static["exit_code"] == 0
    write_json(out/"summary.json", dict(audit="GREEN" if good else "RED", complete=True, collected=len(nodes), shards=results,
                                       static=static, elapsed_seconds=time.perf_counter()-start,
                                       source=str(source), fresh_git_checkout=False))
    write_json(out / "run_state.json", dict(status="GREEN" if good else "RED", complete=True,
               elapsed_seconds=time.perf_counter()-start, source=str(source)))
    print(static["last_line"], flush=True)
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
