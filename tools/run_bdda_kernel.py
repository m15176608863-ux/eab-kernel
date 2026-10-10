"""在 scratchpad 沙箱里运行 b-DDA 插桩内核（df_rebuilt.exe，BDDA_KERNEL_MODE），把 dump 收进 fixtures。

纪律（AGENTS §1.2）：exe 与算例输入**复制**到沙箱运行，绝不在 D:\\b-DDA 下运行任何东西。
协议（来自 D:\\b-DDA\\tools\\bdda\\audit_refkernel_nstep.py::run_nstep，2026-09-18 核对）：
  工作目录放 bb、db 两个文件 + ff.c（两行："bb\\r\\ndb\\r\\n"），
  env: BDDA_KERNEL_MODE=1, BDDA_DF17_DEBUG=1, BDDA_DUMP_STEPS=N；内核在 cwd 运行、自行退出，
  产物 bdda_debug_*.csv 落在 cwd。

用法：python tools/run_bdda_kernel.py bbF038 dbF038 --steps 20 [--from bench]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures" / "bdda_df"
sys.path.insert(0, str(ROOT / "tools"))
from ingest_fixtures import upsert_provenance  # noqa: E402
BDDA = Path(r"D:\b-DDA")
KERNEL = BDDA / "build" / "kernel" / "df_rebuilt.exe"
SANDBOX = Path(os.environ.get("CLAUDE_SCRATCHPAD",
                              r"C:\Users\m1517\AppData\Local\Temp\claude\C--Agent--claude\659f270b-c2f6-43a9-9717-6dc28c605be4\scratchpad")) / "bdda_sandbox"

KEEP = ("bdda_debug_contacts.csv", "bdda_debug_verts.csv", "bdda_debug_df18.csv", "bdda_debug_df22.csv",
        "bdda_debug_df18s2.csv", "bdda_debug_df22s2.csv", "bdda_debug_m0s2.csv", "bdda_debug_m01s2.csv",
        "bdda_debug_detparams.csv", "bdda_debug_cand.csv", "bdda_debug_zsto.csv", "bdda_debug_zsto2.csv",
        "bdda_debug_k2.csv", "bdda_debug_k2step.csv", "bdda_progress.csv", "bdda_resid.csv")


NONREPRO = ["bdda_debug_contacts.csv / df18 / m0s2 首步 o3、o4（未初始化残值）", "bdda_progress.csv wall_clock"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(bb: str, db: str, steps: int, source: str, timeout: int = 600) -> Path:
    src_dir = BDDA / "df" / ("bench" if source == "bench" else "")
    for name in (bb, db):
        if not (src_dir / name).exists():
            raise FileNotFoundError(src_dir / name)
    if not KERNEL.exists():
        raise FileNotFoundError(KERNEL)
    tag = f"{bb}_N{steps}"
    work = SANDBOX / tag
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    shutil.copy2(KERNEL, work / KERNEL.name)
    shutil.copy2(src_dir / bb, work / bb)
    shutil.copy2(src_dir / db, work / db)
    (work / "ff.c").write_bytes(f"{bb}\r\n{db}\r\n".encode("ascii"))
    env = dict(os.environ, BDDA_KERNEL_MODE="1", BDDA_DF17_DEBUG="1", BDDA_DUMP_STEPS=str(steps))
    proc = subprocess.run([str(work / KERNEL.name)], cwd=str(work), env=env, timeout=timeout,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if proc.returncode != 0:
        raise RuntimeError(f"kernel rc={proc.returncode} in {work}")
    dest = FIX / tag
    dest.mkdir(parents=True, exist_ok=True)
    entries = []
    copied = 0
    for name in KEEP:
        s = work / name
        if not s.exists():
            continue
        d = dest / name
        shutil.copyfile(s, d)
        rel = f"bdda_df/{tag}/{name}"
        entries.append({"dest": rel, "source": f"generated: {KERNEL} on df/{'bench/' if source == 'bench' else ''}{bb}+{db} "
                                            f"BDDA_KERNEL_MODE=1 BDDA_DF17_DEBUG=1 BDDA_DUMP_STEPS={steps} (sandbox {work})",
                     "ingested": str(date.today()), "status": "ok", "bytes": d.stat().st_size, "sha256": sha256(d),
                     "kernel_sha256": sha256(KERNEL),
                     # G6 第四轮 provenance 镜头：只记内核哈希分不出"内核变了"与"残值变了"——输入也记哈希；首步 o3/o4 与
                     # wall_clock 是不可复现列（未初始化残值 / 时间戳），同一 exe、同一输入重跑 16 份里 **4 份**逐字节不同
                     # （contacts、df18、m0s2 三张表的首步 o3/o4 + progress 的 wall_clock；G6 第五轮沙箱实测三例皆然）
                     "input_sha256": {bb: sha256(src_dir / bb), db: sha256(src_dir / db)},
                     "nonreproducible": NONREPRO})
        copied += 1
    upsert_provenance(entries, FIX.parent / "PROVENANCE.json")      # 与 ingest_fixtures 同一写法（显式 CRLF，按 dest 排序）
    print(f"OK {tag}: {copied} files -> {dest}")
    return dest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("bb")
    ap.add_argument("db")
    ap.add_argument("--steps", type=int, default=10)
    ap.add_argument("--from", dest="source", choices=("golden", "bench"), default="golden")
    a = ap.parse_args()
    run(a.bb, a.db, a.steps, a.source)
    return 0


if __name__ == "__main__":
    sys.exit(main())
