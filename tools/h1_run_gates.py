"""H1 fast/full runner. New output only, recorded execution, no Git writes.

Fast: python tools/h1_run_gates.py --name fast
Full: python tools/h1_run_gates.py --name final --runslow
The final source is a byte export, not a fresh Git worktree.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import threading

from h1_module_coverage import audit_module_coverage

PROCESSES = set()
PROCESS_LOCK = threading.Lock()
CANCELLED = threading.Event()

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/codex/H1_evidence"
VERSION = "h1-gates-1"


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".writing")
    for attempt in range(12):
        try:
            temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
            temporary.replace(path)
            return
        except PermissionError:
            if attempt == 11:
                raise
            time.sleep(0.02 * (attempt + 1))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def terminate(process):
    """Terminate only this runner's own process subtree, never unrelated jobs."""
    if process.poll() is None:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        else:
            process.kill()
        process.wait(timeout=20)


def terminate_all():
    CANCELLED.set()
    with PROCESS_LOCK:
        current = tuple(PROCESSES)
    for process in current:
        terminate(process)


def run(command, source, env, logfile, timeout=10800):
    started = time.monotonic()
    process = None
    try:
        with logfile.open("wb") as stream:
            if CANCELLED.is_set():
                raise RuntimeError("run invalidated by another interrupted shard")
            process = subprocess.Popen(command, cwd=source, env=env, stdout=stream, stderr=subprocess.STDOUT)
            with PROCESS_LOCK:
                PROCESSES.add(process)
            while process.poll() is None:
                elapsed = time.monotonic()-started
                write(logfile.with_suffix(".progress.json"), dict(complete=False, pid=process.pid, seconds=elapsed))
                stalled = False
                progress = Path(env["H1_PROGRESS"]) if env.get("H1_PROGRESS") else None
                if progress is not None and progress.exists():
                    try:
                        journal = json.loads(progress.read_text("utf-8"))
                        last = journal.get("last_event_epoch")
                        stalled = last is not None and time.time()-last > 900
                    except (OSError, json.JSONDecodeError):
                        pass  # A transient reader lock cannot invalidate numerical results.
                if CANCELLED.is_set() or elapsed > timeout or stalled:
                    raise RuntimeError("incomplete run invalidated: interrupted/timeout/stalled; use a NEW run name")
                time.sleep(2)
        lines = logfile.read_text("utf-8", errors="replace").splitlines()
        result = dict(command=command, exit_code=process.returncode, seconds=time.monotonic()-started,
                      last_line=lines[-1] if lines else "", log=str(logfile))
        write(logfile.with_suffix(".progress.json"), dict(complete=True, **result))
        return result
    finally:
        if process is not None:
            terminate(process)
            with PROCESS_LOCK:
                PROCESSES.discard(process)


def source_names():
    names = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT).decode("utf-8").split("\0")
    return sorted({name for name in names if name and not name.startswith("reports/codex/H1_evidence/")
                   and (ROOT / name).is_file()})


def snapshot(destination):
    destination.mkdir()
    names = source_names()
    rows = []
    for name in sorted(set(filter(None, names))):
        src = ROOT / name
        if name.startswith("reports/codex/H1_evidence/") or not src.is_file():
            continue
        dst = destination / name
        if not dst.resolve().is_relative_to(destination.resolve()):
            raise ValueError("snapshot path escaped root")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        assert digest(src) == digest(dst), name
        rows.append(dict(path=name, sha256=digest(dst), bytes=dst.stat().st_size))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--runslow", action="store_true")
    args = parser.parse_args()
    if not hasattr(sys, "monitoring"):
        parser.error("execution coverage requires Python 3.12+; no unverified GREEN is emitted")
    if Path(args.name).name != args.name or args.name in (".", ".."):
        parser.error("name must be a new single directory name")
    out = EVIDENCE / args.name
    temp = EVIDENCE / "tmp" / args.name
    if out.exists() or temp.exists():
        parser.error("incomplete and complete runs are immutable; choose a new name")
    out.mkdir(parents=True)
    temp.mkdir(parents=True)
    source = temp / "source"
    write(out / "state.json", dict(complete=False, status="EXPORTING", started=time.time(), version=VERSION))
    manifest = snapshot(source)
    write(temp / "source_manifest.json", manifest)
    env = dict(os.environ, TEMP=str(temp), TMP=str(temp), PYTHONDONTWRITEBYTECODE="1",
               PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1",
               PYTHONPATH=os.pathsep.join((str(source / "src"), str(source / "tools"))))
    for key in ("BDDA_DETECT", "BDDA_DETECT_SHADOW", "BDDA_SHADOW_PATH"):
        env.pop(key, None)
    python = [sys.executable, "-X", "utf8"]
    full = ["--runslow"] if args.runslow else []
    started = time.monotonic()
    collection = run(python + ["-m", "pytest", "-q", "--collect-only", "-p", "no:cacheprovider",
                              "--basetemp", str(temp / "collection_tmp"), *full], source, env, temp / "collection.txt")
    if collection["exit_code"]:
        write(out / "summary.json", dict(audit="RED", complete=False, collection=collection))
        return 1
    nodes = [line for line in (temp / "collection.txt").read_text("utf-8").splitlines()
             if line.startswith("tests/") and "::" in line]
    assert nodes and len(nodes) == len(set(nodes))
    count = 4 if args.runslow else 1
    shards = [nodes[i::count] for i in range(count)]
    write(out / "state.json", dict(complete=False, status="TESTING", collected=len(nodes), source=str(source)))

    def shard(i):
        response = temp / f"shard_{i+1}_nodes.txt"
        response.write_text("\n".join(shards[i])+"\n", encoding="utf-8")
        record = temp / f"shard_{i+1}_execution.json"
        local = dict(env, H1_EXECUTION=str(record), H1_PROGRESS=str(out / f"shard_{i+1}_progress.json"))
        result = run(python + ["-m", "pytest", "-q", "-p", "no:cacheprovider", "-p", "h1_execution_plugin",
                    "@"+str(response), "--basetemp", str(temp / f"pytest_{i+1}"), "--durations=0", *full],
                    source, local, temp / f"shard_{i+1}.txt", timeout=10800 if args.runslow else 900)
        data = json.loads(record.read_text("utf-8")) if record.exists() else {}
        calls = [r["nodeid"] for r in data.get("reports", ()) if r["when"] == "call"]
        result.update(dispatched=len(shards[i]), collected=len(data.get("collected", ())), executed=len(calls),
            complete=data.get("complete", False), node_sets_equal=Counter(shards[i]) == Counter(data.get("collected", ())) == Counter(calls),
            skip_count=sum(r["outcome"] == "skipped" for r in data.get("reports", ())),
            failed_count=sum(r["outcome"] == "failed" for r in data.get("reports", ())))
        write(out / f"shard_{i+1}.json", result)
        print(f"shard {i+1}: {result['last_line']}", flush=True)
        return result

    pool = ThreadPoolExecutor(max_workers=count)
    try:
        futures = {pool.submit(shard, i): i for i in range(count)}
        results = [None] * count
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    except BaseException as error:
        terminate_all()
        write(out / "state.json", dict(complete=False, status="INVALIDATED", reason=repr(error)))
        raise
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
    records = [json.loads((temp / f"shard_{i+1}_execution.json").read_text("utf-8"))
               for i in range(count)]
    coverage = audit_module_coverage(source, records)
    write(out / "module_coverage.json", coverage)
    static = None
    if args.runslow:
        static = run(python + ["tools/check_exact_construction.py"], source, env, temp / "exact_construction.txt")
        print(static["last_line"], flush=True)
    changed = [r["path"] for r in manifest if not (source / r["path"]).is_file() or digest(source / r["path"]) != r["sha256"]]
    expected_names = {r["path"] for r in manifest}
    actual_names = {p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()}
    changed = sorted(set(changed) | (actual_names ^ expected_names))
    live_names = set(source_names())
    live_changed = sorted((live_names ^ expected_names) | {r["path"] for r in manifest
        if not (ROOT / r["path"]).is_file() or digest(ROOT / r["path"]) != r["sha256"]})
    good = all(r["exit_code"] == 0 and r["complete"] and r["node_sets_equal"] and not r["skip_count"] and not r["failed_count"] for r in results)
    good = good and coverage["complete"] and not changed and not live_changed and (static is None or static["exit_code"] == 0)
    write(out / "summary.json", dict(audit="GREEN" if good else "RED", complete=True, collected=len(nodes), shards=results,
        static=static, module_coverage_complete=coverage["complete"], elapsed_seconds=time.monotonic()-started, source=str(source), temp=str(temp),
        export_changed=changed, live_tree_changed=live_changed, fresh_git_checkout=False, version=VERSION))
    write(out / "state.json", dict(complete=True, status="GREEN" if good else "RED"))
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
