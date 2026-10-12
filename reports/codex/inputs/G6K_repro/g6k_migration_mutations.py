"""Replay old and new mathematical gates on isolated source mutations.

Copies are read-only snapshots created by `git archive b6126cf/HEAD src tests
tools fixtures pyproject.toml`, extracted only below review/copies/gates.
No original tracked source is ever changed. Each copied mutation is restored
byte-for-byte and its SHA-256 checked after pytest completes.
"""
from pathlib import Path
import ast
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "review/copies/gates"
OUT = ROOT / "review/logs/gates_migrations"
OUT.mkdir(parents=True, exist_ok=True)
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")

CASES = {
    "boundary_swallowed": "tests/test_kernel2d_g0.py::test_degenerate_parallel_edges_membership_still_exact",
    "nearest_vv_dropped": "tests/test_kernel2d_g0.py::test_distance_completeness_boundary_cases",
    "exit_cover_set_dropped": "tests/test_kernel2d_g0.py::test_exit_completeness_boundary_cases",
    "projection_scaled_099": "tests/test_margin.py::test_config_space_distance_equals_body_distance",
}


def source_function(source, name):
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    lines = source.splitlines(keepends=True)
    start = sum(len(line) for line in lines[:node.lineno-1])
    end = sum(len(line) for line in lines[:node.end_lineno])
    return node, start, end, "".join(lines[node.lineno-1:node.end_lineno])


def mutation(root, label, case):
    new = label.startswith("current")
    if case == "boundary_swallowed":
        rel = "src/eab/kernel2d/exact.py" if new else "src/eab/kernel2d/covers.py"
        name = "membership_exact" if new else "membership_convex"
    elif case in ("nearest_vv_dropped", "exit_cover_set_dropped"):
        rel, name = "src/eab/kernel2d/covers.py", ("vv_cover" if case == "nearest_vv_dropped" else "enumerate_covers")
    else:
        rel, name = "src/eab/margin.py", "nearest_point_on_convex_entrance"
    path = root / rel
    original = path.read_bytes()
    source = original.decode("utf-8-sig")
    node, start, end, function = source_function(source, name)
    if case == "boundary_swallowed":
        anchor = "return worst" if new else "return 0"
        assert function.count(anchor) == 1, (case, label, function)
        changed = function.replace(anchor, "return max(worst, 1)" if new else "return 1")
    elif case in ("nearest_vv_dropped", "exit_cover_set_dropped"):
        first_body = node.body[0].lineno-node.lineno
        changed = "".join(function.splitlines(keepends=True)[:first_body]) + (
            "    return None\n" if case == "nearest_vv_dropped" else "    return []\n")
    else:
        parsed = ast.parse(function)
        class ScaleReturn(ast.NodeTransformer):
            def visit_Return(self, return_node):
                if return_node.value is None:
                    return return_node
                return ast.copy_location(ast.Return(value=ast.Call(
                    func=ast.Name(id="tuple", ctx=ast.Load()), args=[ast.GeneratorExp(
                        elt=ast.BinOp(left=ast.Constant(value=.99), op=ast.Mult(),
                                      right=ast.Name(id="_g6k_c", ctx=ast.Load())),
                        generators=[ast.comprehension(target=ast.Name(id="_g6k_c", ctx=ast.Store()),
                                                     iter=return_node.value, ifs=[], is_async=0)])], keywords=[])), return_node)
        changed = ast.unparse(ast.fix_missing_locations(ScaleReturn().visit(parsed))) + "\n"
    assert changed != function
    path.write_bytes((source[:start]+changed+source[end:]).encode("utf-8"))
    return path, original


def run(root, label, case, stage):
    target = CASES[case]
    temp = root / "review_tmp" / (case+"_"+stage)
    temp.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-p", "no:cacheprovider",
               target, "--basetemp="+str(temp)]
    start = time.perf_counter()
    result = subprocess.run(command, cwd=root, env=ENV, text=True, encoding="utf-8", errors="replace",
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log = OUT / f"{label}_{case}_{stage}.log"
    log.write_text(result.stdout, encoding="utf-8")
    return {"label": label, "case": case, "stage": stage, "command": command,
            "exit_code": result.returncode, "wall_seconds": time.perf_counter()-start,
            "summary": result.stdout.strip().splitlines()[-1], "log": str(log), "output": result.stdout}


records = []
for label in ("old_b6126cf", "current_5591702"):
    root = BASE / label
    assert (root / "pyproject.toml").is_file(), "Create git-archive review snapshots first"
    for case in CASES:
        baseline = run(root, label, case, "baseline")
        records.append(baseline)
        assert baseline["exit_code"] == 0, baseline
        path, original = mutation(root, label, case)
        digest = hashlib.sha256(original).hexdigest()
        try:
            tested = run(root, label, case, "mutant")
            records.append(tested)
        finally:
            path.write_bytes(original)
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
        print(label, case, baseline["summary"], "=>", tested["summary"], flush=True)
        if case != "boundary_swallowed" or label.startswith("current"):
            assert tested["exit_code"] == 1, tested
        else:
            assert tested["exit_code"] == 0, tested
(OUT / "results.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
print("MIGRATION_MUTATIONS_CONFIRMED (all copied source SHA-256 restored)")
