"""WO-M4b: fresh byte-copy export, exhaustive four-shard pytest and AST gate.

No Git state changes. The exported tree has no .git and is not a fresh clone;
the owner prohibited worktree/checkout operations. Preserve each run for audit.
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


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run(command, cwd, env, log):
    start = time.perf_counter()
    with log.open("wb") as stream:
        result = subprocess.run(command, cwd=cwd, env=env, stdout=stream,
                                stderr=subprocess.STDOUT)
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    return {"command": command, "cwd": str(cwd), "exit_code": result.returncode,
            "seconds": time.perf_counter() - start, "log": str(log),
            "last_line": lines[-1] if lines else ""}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--export", type=Path, required=True)
    args = ap.parse_args()
    out, export = args.out.resolve(), args.export.resolve()
    if not out.is_relative_to(ROOT) or not export.is_relative_to(ROOT / "build"):
        ap.error("evidence must be in this workspace; fresh export must be under build/")
    if export.exists():
        ap.error("export must be new; this tool never overwrites an earlier run")
    out.mkdir(parents=True, exist_ok=True)
    export.mkdir(parents=True)
    names = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT).decode("utf-8").split("\0")
    manifest = []
    for name in sorted(set(filter(None, names))):
        src = ROOT / name
        if src.is_relative_to(out) or src.is_relative_to(ROOT / "build"):
            continue
        if not src.is_file():
            continue
        dst = export / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        data = dst.read_bytes()
        assert data == src.read_bytes(), name
        manifest.append({"path": name, "bytes": len(data),
                         "sha256": hashlib.sha256(data).hexdigest()})
    write_json(out / "export_manifest.json", manifest)
    # pytest creates basetemp itself, but not its missing parent directory.
    (export / "build").mkdir(exist_ok=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8",
               PYTHONPATH=str(export / "src"))
    for name in ("BDDA_DETECT", "BDDA_DETECT_SHADOW", "BDDA_SHADOW_PATH"):
        env.pop(name, None)
    python = [sys.executable, "-X", "utf8"]
    collected = run(python + ["-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
                    export, env, out / "collection.txt")
    assert collected["exit_code"] == 0, collected
    nodes = [s for s in (out / "collection.txt").read_text(encoding="utf-8").splitlines()
             if s.startswith("tests/") and "::" in s]
    assert nodes and len(nodes) == len(set(nodes)), "empty or duplicate collection"
    shards = [nodes[i::4] for i in range(4)]
    assert sorted(n for shard in shards for n in shard) == sorted(nodes)
    write_json(out / "node_coverage.json", {"collected": len(nodes), "shards": shards})

    def shard_run(i):
        response = out / f"shard_{i + 1}_nodes.txt"
        response.write_text("\n".join(shards[i]) + "\n", encoding="utf-8")
        command = python + ["-m", "pytest", "-q", "-p", "no:cacheprovider",
                            "@" + str(response), "--basetemp", str(export / f"build/tmp_{i + 1}")]
        result = run(command, export, env, out / f"shard_{i + 1}.txt")
        result["collected_nodes"] = len(shards[i])
        write_json(out / f"shard_{i + 1}.json", result)
        print(f"shard {i + 1}: {result['last_line']}", flush=True)
        return result

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(shard_run, range(4)))
    static = run(python + ["tools/check_exact_construction.py"], export, env,
                 out / "exact_construction.txt")
    passed = all(r["exit_code"] == 0 for r in results + [static])
    write_json(out / "summary.json", {"audit": "GREEN" if passed else "RED",
               "export": str(export), "collected": len(nodes), "shards": results,
               "static": static, "fresh_git_checkout": False})
    print(static["last_line"], flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
