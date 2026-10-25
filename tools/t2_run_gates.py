"""T2 H1 wrapper: approved external evidence, immutable snapshots, four shards.

Reuses the unchanged H1 execution/progress and module-coverage implementation.
No Git writes; byte snapshots are explicitly not fresh Git checkouts.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile

import h1_run_gates as h1

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = Path("D:/eab-evidence/reports/codex/T2a_evidence")


def source_names():
    names = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT).decode("utf-8").split("\0")
    # T2 run products are external. The small in-tree admission ledger is
    # required test input and must be present in the byte export as well.
    return sorted({n for n in names if n and (ROOT / n).is_file()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--runslow", action="store_true")
    parser.add_argument("--baseline", action="store_true")
    args = parser.parse_args()
    if not hasattr(sys, "monitoring"):
        parser.error("H1 execution coverage requires Python 3.12+")
    if Path(args.name).name != args.name or args.name in (".", ".."):
        parser.error("use a new single-component run name")
    out, temp = EVIDENCE / args.name, EVIDENCE / "tmp" / args.name
    out.mkdir(parents=True, exist_ok=False)
    temp.mkdir(parents=True, exist_ok=False)
    source = temp / "source"
    source.mkdir()
    h1.write(out / "state.json", dict(status="EXPORTING", complete=False))
    if args.baseline:
        with zipfile.ZipFile(EVIDENCE / "baseline_anchor/source.zip") as bundle:
            for member in bundle.infolist():
                target = (source / member.filename).resolve()
                if not target.is_relative_to(source.resolve()):
                    raise ValueError("snapshot member escaped approved destination")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(bundle.read(member))
        names = sorted(p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file())
    else:
        names = source_names()
        for name in names:
            target = source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
    manifest = [dict(path=n, bytes=(source / n).stat().st_size,
                     sha256=h1.digest(source / n)) for n in names]
    h1.write(out / "source_manifest.json", manifest)
    env = dict(os.environ, TEMP=str(temp), TMP=str(temp), PYTHONDONTWRITEBYTECODE="1",
               PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1",
               PYTHONPATH=os.pathsep.join((str(source / "src"), str(source / "tools"))))
    python = [sys.executable, "-X", "utf8"]
    full = ["--runslow"] if args.runslow else []
    start = time.perf_counter()
    collection = h1.run(python + ["-m", "pytest", "-q", "--collect-only", "-p", "no:cacheprovider",
                       "--basetemp", str(temp / "collection_tmp"), *full], source, env, out / "collection.txt")
    if collection["exit_code"]:
        h1.write(out / "summary.json", dict(audit="RED", complete=False, collection=collection))
        return 1
    nodes = [s for s in (out / "collection.txt").read_text("utf-8").splitlines()
             if s.startswith("tests/") and "::" in s]
    assert nodes and len(nodes) == len(set(nodes))
    count = 4 if args.runslow else 1
    shards = [nodes[i::count] for i in range(count)]
    h1.write(out / "state.json", dict(status="TESTING", complete=False, collected=len(nodes)))

    def shard(i):
        response = out / f"shard_{i+1}_nodes.txt"
        response.write_text("\n".join(shards[i])+"\n", encoding="utf-8")
        record = out / f"shard_{i+1}_execution.json"
        local = dict(env, H1_EXECUTION=str(record), H1_PROGRESS=str(out / f"shard_{i+1}_progress.json"))
        result = h1.run(python + ["-m", "pytest", "-q", "-p", "no:cacheprovider", "-p", "h1_execution_plugin",
                        "@"+str(response), "--basetemp", str(temp / f"pytest_{i+1}"), "--durations=0", *full],
                        source, local, out / f"shard_{i+1}.txt", timeout=10800 if args.runslow else 1800)
        data = json.loads(record.read_text("utf-8")) if record.exists() else {}
        calls = [r["nodeid"] for r in data.get("reports", ()) if r["when"] == "call"]
        result.update(dispatched=len(shards[i]), executed=len(calls), complete=data.get("complete", False),
                      node_sets_equal=Counter(shards[i]) == Counter(data.get("collected", ())) == Counter(calls),
                      skip_count=sum(r["outcome"] == "skipped" for r in data.get("reports", ())),
                      failed_count=sum(r["outcome"] == "failed" for r in data.get("reports", ())))
        h1.write(out / f"shard_{i+1}.json", result)
        print(f"shard {i+1}: {result['last_line']}", flush=True)
        return result

    pool = ThreadPoolExecutor(max_workers=count)
    try:
        futures = {pool.submit(shard, i): i for i in range(count)}
        results = [None] * count
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    except BaseException as error:
        h1.terminate_all()
        h1.write(out / "state.json", dict(status="INVALIDATED", complete=False, reason=repr(error)))
        raise
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
    records = [json.loads((out / f"shard_{i+1}_execution.json").read_text("utf-8")) for i in range(count)]
    coverage = h1.audit_module_coverage(source, records)
    h1.write(out / "module_coverage.json", coverage)
    static = h1.run(python + ["tools/check_exact_construction.py"], source, env,
                    out / "exact_construction.txt") if args.runslow else None
    expected = set(names)
    actual = {p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()}
    changed = sorted((actual ^ expected) | {r["path"] for r in manifest
                     if not (source / r["path"]).is_file() or h1.digest(source / r["path"]) != r["sha256"]})
    live_changed = [] if args.baseline else sorted((set(source_names()) ^ expected) | {
        r["path"] for r in manifest if not (ROOT / r["path"]).is_file() or h1.digest(ROOT / r["path"]) != r["sha256"]})
    good = all(r["exit_code"] == 0 and r["complete"] and r["node_sets_equal"]
               and not r["skip_count"] and not r["failed_count"] for r in results)
    good = good and coverage["complete"] and not changed and not live_changed and (static is None or static["exit_code"] == 0)
    h1.write(out / "summary.json", dict(audit="GREEN" if good else "RED", complete=True, collected=len(nodes),
        shards=results, static=static, module_coverage_complete=coverage["complete"],
        elapsed_seconds=time.perf_counter()-start, source=str(source), temp=str(temp),
        export_changed=changed, live_tree_changed=live_changed, baseline=args.baseline,
        fresh_git_checkout=False, version="t2-h1-external-3"))
    h1.write(out / "state.json", dict(complete=True, status="GREEN" if good else "RED"))
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
