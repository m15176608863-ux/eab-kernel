"""在 3-b-dda 自己的环境里（子进程，cwd=D:\\3-b-dda，PYTHONPATH=src）把算例的入口 dict 与顶点导出为 JSON。

本仓库不 import bdda3d；只有 JSON 跨越边界。对 3-b-dda 一律只读（不写它的目录）。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIBLING = Path(r"D:\3-b-dda")
OUT = ROOT / "fixtures" / "bdda3d"

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
    for name in ("cb2_locked", "cb2_sliding", "cb_bond"):
        proc = subprocess.run([sys.executable, "-c", CHILD, name], cwd=str(SIBLING), env=env,
                              capture_output=True, text=True, encoding="utf-8")
        if proc.returncode != 0:
            print(f"FAIL {name}: {proc.stderr[-800:]}")
            continue
        data = json.loads(proc.stdout)
        (OUT / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True),
                                          encoding="utf-8", newline="\n")
        print(f"OK   {name}: {len(data['entrances'])} entrances")
    return 0


if __name__ == "__main__":
    sys.exit(main())
