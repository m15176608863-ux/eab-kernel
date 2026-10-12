"""WO-PERF: retain source JUnit rankings and measured representative cProfile."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import pstats
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "reports/codex/PERF_evidence/profile"
OUT.mkdir(exist_ok=True)


def write_json(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def junit_rankings():
    source = ROOT / "reports/codex/E5b_evidence/final.xml"
    tree = ET.parse(source)
    by_file = defaultdict(lambda: {"seconds": 0.0, "nodes": 0})
    nodes = []
    for case in tree.iter("testcase"):
        seconds = float(case.get("time", "0"))
        file = case.get("classname", "").replace(".", "/") + ".py"
        by_file[file]["seconds"] += seconds
        by_file[file]["nodes"] += 1
        nodes.append({"node": file + "::" + case.get("name", ""), "seconds": seconds})
    files = sorted(({"file": k, **v} for k, v in by_file.items()), key=lambda x: -x["seconds"])
    nodes.sort(key=lambda x: -x["seconds"])
    write_json("baseline_top20.json", {
        "source": str(source.relative_to(ROOT)),
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "file_top20": files[:20], "node_top20": nodes[:20],
        "all_files": files,
        "testcase_count": len(nodes),
        "testcase_seconds_sum": sum(x["seconds"] for x in nodes),
    })
    lines = ["# E5b 最终 JUnit：基线前 20", "", "来源：`reports/codex/E5b_evidence/final.xml`。文件耗时为节点 `time` 汇总，不含额外进程开销。", "", "## 测试文件", "", "|文件|秒|格数|", "|---|---:|---:|"]
    lines += [f"|{x['file']}|{x['seconds']:.3f}|{x['nodes']}|" for x in files[:20]]
    lines += ["", "## 测试节点", "", "|节点|秒|", "|---|---:|"]
    lines += [f"|`{x['node']}`|{x['seconds']:.3f}|" for x in nodes[:20]]
    (OUT / "baseline_top20.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def measure():
    # Explicit sample spans generic/degenerate, rotation, unit scales and 1e6 coordinates.
    suffixes = [
        "test_identity_cell_matches_closed_form[generic]",
        "test_body_distance_scales_and_keeps_its_label[generic-R11-t1000-s1000]",
        "test_body_distance_scales_and_keeps_its_label[yaw_1e-3-R7-t1000-s1000]",
        "test_margin_layer_is_invariant[generic-R7-t1e+06-s1]",
        "test_margin_layer_is_invariant[box_box_face-R7-t0-s0.001]",
        "test_margin_layer_is_invariant[ridge_needle-R11-t1e+06-s0.001]",
        "test_cover_labels_and_strictness_are_invariant[stack_touch-R7-t100000-s1]",
        "test_support_gaps_scale_and_membership_is_invariant[generic-R0-t1e+06-s1]",
        "test_g0_three_votes_are_invariant[generic-R7-t0-s0.001]",
    ]
    nodes = ["tests/test_invariance_geom.py::" + x for x in suffixes]
    cmd = [sys.executable, "-X", "utf8", "-m", "cProfile", "-o", str(OUT / "geom_representative.pstats"), "-m", "pytest", "-q", "-p", "no:cacheprovider", "--basetemp", str(ROOT / "reports/codex/PERF_evidence/tmp/profile_geom"), *nodes]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / "src/eab").rglob("*.py")}
    start = time.perf_counter()
    result = subprocess.run(cmd, cwd=ROOT, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    elapsed = time.perf_counter() - start
    (OUT / "geom_representative.log").write_text(result.stdout, encoding="utf-8")
    stats = pstats.Stats(str(OUT / "geom_representative.pstats"))
    functions = []
    for (file, line, func), (primitive, calls, self_s, cumulative_s, callers) in stats.stats.items():
        if "/src/eab/" not in file.replace("\\", "/"):
            continue
        path = Path(file)
        try:
            file = str(path.relative_to(ROOT)).replace("\\", "/")
        except ValueError:
            pass
        functions.append({"file": file, "line": line, "function": func, "primitive_calls": primitive, "calls": calls, "self_seconds": self_s, "cumulative_seconds": cumulative_s})
    functions.sort(key=lambda x: -x["cumulative_seconds"])
    write_json("geom_representative.json", {"command": cmd, "nodes": nodes, "exit_code": result.returncode, "wall_seconds": elapsed, "source_sha256_before": hashes, "production_top20_cumulative": functions[:20], "production_top20_self": sorted(functions, key=lambda x: -x["self_seconds"])[:20], "all_production_functions": functions})
    lines = ["# 代表格 cProfile 实测", "", f"9 格，退出码 {result.returncode}，带 profiler 墙钟 {elapsed:.3f} s。此耗时不可代替未插桩全套验收。", "", "|生产函数|调用|自身秒|累计秒|", "|---|---:|---:|---:|"]
    lines += [f"|`{x['file']}:{x['line']}::{x['function']}`|{x['calls']}|{x['self_seconds']:.6f}|{x['cumulative_seconds']:.6f}|" for x in functions[:20]]
    lines += ["", "节点与全部生产函数见 JSON，原始 profile 见 `.pstats`。"]
    (OUT / "geom_representative.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(result.stdout)
    print(json.dumps(functions[:20], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    junit_rankings()
    measure()
