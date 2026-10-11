"""WO-E5b rerunnable, source-bound test runner and test-inventory audit."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).resolve().parent


def hashes():
    return {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for directory in ("src", "tests", "tools")
        for p in sorted((ROOT / directory).rglob("*.py"))
    }


def save(name, value):
    (EVIDENCE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(name, args):
    if args and args[0] == "--":
        args = args[1:]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
    temp = EVIDENCE / "tmp" / (name + "_runtime")
    temp.mkdir(parents=True, exist_ok=True)
    env.update(TEMP=str(temp), TMP=str(temp))
    command = [sys.executable, "-X", "utf8", *args]
    record = {"command": command, "cwd": str(ROOT), "environment": {
        key: env[key] for key in ("PYTHONDONTWRITEBYTECODE", "PYTHONIOENCODING", "PYTHONUNBUFFERED", "TEMP", "TMP")},
        "source_before": hashes(), "start_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    save(name + ".running.json", record)
    started = time.perf_counter()
    with (EVIDENCE / (name + ".log")).open("w", encoding="utf-8", newline="") as log:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    record.update(exit_code=result.returncode, wall_seconds=time.perf_counter() - started,
                  source_after=hashes(), end_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    record["sources_unchanged_during_run"] = record["source_before"] == record["source_after"]
    lines = (EVIDENCE / (name + ".log")).read_text(encoding="utf-8").splitlines()
    record["last_nonempty_line"] = next((line for line in reversed(lines) if line.strip()), "")
    record["log_sha256"] = hashlib.sha256((EVIDENCE / (name + ".log")).read_bytes()).hexdigest()
    save(name + ".json", record)
    print(json.dumps({key: record[key] for key in ("exit_code", "wall_seconds", "sources_unchanged_during_run", "last_nonempty_line")}, ensure_ascii=False))
    return result.returncode


def functions(tree):
    result = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            result[node.name] = {"decorators": [ast.dump(d) for d in node.decorator_list],
                                 "body": ast.dump(node), "line": node.lineno}
    return result


def inventory():
    baseline = EVIDENCE / "baseline" / "tests"
    deleted, changed, decorators, new_skip = [], [], [], []
    old_count = new_count = 0
    for old in sorted(baseline.rglob("test_*.py")):
        relative = old.relative_to(baseline)
        current = ROOT / "tests" / relative
        before = functions(ast.parse(old.read_text(encoding="utf-8-sig")))
        after = functions(ast.parse(current.read_text(encoding="utf-8-sig"))) if current.exists() else {}
        old_count += len(before)
        for name, value in before.items():
            label = relative.as_posix() + "::" + name
            if name not in after:
                deleted.append(label)
            elif value["body"] != after[name]["body"]:
                changed.append(label)
            if name in after and value["decorators"] != after[name]["decorators"]:
                decorators.append(label)
        old_marks = [ast.dump(n) for n in ast.walk(ast.parse(old.read_text(encoding="utf-8-sig")))
                     if isinstance(n, ast.Attribute) and n.attr in ("skip", "skipif", "xfail")]
        if current.exists():
            new_marks = [ast.dump(n) for n in ast.walk(ast.parse(current.read_text(encoding="utf-8-sig")))
                         if isinstance(n, ast.Attribute) and n.attr in ("skip", "skipif", "xfail")]
            if len(new_marks) > len(old_marks):
                new_skip.append(relative.as_posix())
    for current in (ROOT / "tests").rglob("test_*.py"):
        new_count += len(functions(ast.parse(current.read_text(encoding="utf-8-sig"))))
        if not (baseline / current.relative_to(ROOT / "tests")).exists():
            for node in ast.walk(ast.parse(current.read_text(encoding="utf-8-sig"))):
                if isinstance(node, ast.Attribute) and node.attr in ("skip", "skipif", "xfail"):
                    new_skip.append(current.relative_to(ROOT).as_posix())
    record = dict(old_test_functions=old_count, current_test_functions=new_count,
                  removed_test_functions=deleted, modified_old_test_functions=changed,
                  modified_old_decorators=decorators, increased_skip_xfail_references=new_skip,
                  warning="AST inventory is not a substitute for per-assertion strength review or collected-node comparison.")
    save("test_inventory_audit.json", record)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return int(bool(deleted or new_skip))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("run", "inventory"))
    parser.add_argument("name", nargs="?")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    options = parser.parse_args()
    raise SystemExit(inventory() if options.action == "inventory" else run(options.name, options.args))
