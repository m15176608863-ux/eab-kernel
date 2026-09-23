"""在 3-b-dda 自己的环境里（子进程，cwd=D:\\3-b-dda，PYTHONPATH=src）把算例的入口 dict 与顶点导出为 JSON。

本仓库不 import bdda3d；只有 JSON 跨越边界。对 3-b-dda 一律只读（不写它的目录）。
每写一个 JSON 同时在 fixtures/PROVENANCE.json 登记 sha256/字节数/来源（审查盲区 3：此前三个 JSON
零条目，G2 的 legacy 侧没有被哈希看护）。姊妹仓库的版本（git 提交）不记——AGENTS.md §1.2 不许对
姊妹仓库做任何 git 操作——来源说明里如实写"版本未记录"。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIBLING = Path(r"D:\3-b-dda")
OUT = ROOT / "fixtures" / "bdda3d"
sys.path.insert(0, str(ROOT / "tools"))
from ingest_fixtures import provenance_entry, upsert_provenance  # noqa: E402

BUILDERS = {"cb2_locked": "cases.build_cb2(None, bx=0.0)",
            "cb2_sliding": "cases.build_cb2(None, bx=2.0)",
            "cb_bond": "cases.build_cb_bond(None)"}


def source_note(name: str) -> str:
    """PROVENANCE 的来源说明：写清楚知道什么、不知道什么。"""
    return (f"tools/ingest_bdda3d.py 导出：在 {SIBLING} 自己的环境里（子进程，PYTHONPATH=src）运行 "
            f"bdda3d.{BUILDERS[name]}，取 ss.blocks 顶点与入口 dict 列表写 JSON。姊妹仓库版本未记录；"
            f"入口是 detect.py 的枚举产出还是算例预置列表，未核实。")

# 在子进程里执行的脚本：只读 bdda3d，把 (ss, C) 转成纯 JSON。
CHILD = r'''
import json, sys
from bdda3d import cases
name = sys.argv[1]
builders = {"cb2_locked": lambda: cases.build_cb2(None, bx=0.0),
            "cb2_sliding": lambda: cases.build_cb2(None, bx=2.0),
            "cb_bond": lambda: cases.build_cb_bond(None)}
ss, C = builders[name]()
verts = {str(b): [list(map(float, v)) for v in blk["vertices"]] for b, blk in ss.blocks.items()}
def enc(c):
    out = {}
    for k, v in c.items():
        if isinstance(v, (list, tuple)):
            out[k] = [list(x) if isinstance(x, (list, tuple)) else x for x in v]
        else:
            out[k] = v
    return out
print(json.dumps({"case": name, "step": 0, "verts": verts, "entrances": [enc(c) for c in C]},
                 ensure_ascii=False, sort_keys=True))
'''


def main() -> int:
    if not (SIBLING / "src" / "bdda3d").exists():
        print(f"MISSING sibling package at {SIBLING}")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SIBLING / "src")
    for name in BUILDERS:
        proc = subprocess.run([sys.executable, "-c", CHILD, name], cwd=str(SIBLING), env=env,
                              capture_output=True, text=True, encoding="utf-8")
        if proc.returncode != 0:
            print(f"FAIL {name}: {proc.stderr[-800:]}")
            continue
        data = json.loads(proc.stdout)
        (OUT / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True),
                                          encoding="utf-8", newline="\n")
        upsert_provenance([provenance_entry(f"bdda3d/{name}.json", source_note(name), str(date.today()))])
        print(f"OK   {name}: {len(data['entrances'])} entrances")
    return 0


if __name__ == "__main__":
    sys.exit(main())
