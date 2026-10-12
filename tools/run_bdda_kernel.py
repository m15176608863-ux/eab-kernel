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


NONREPRO = ["bdda_debug_contacts.csv / df18 / m0s2 首步 o3、o4（未初始化残值）", "bdda_progress.csv wall_clock",
            "bdda_debug_df22.csv 首步 o4：mtype=1 或 m0_new=0 时 df.c:3994 跳过 :4030 更新；M4 两次同输入实测不同，检测对账不消费该状态列"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(bb: str, db: str, steps: int, source: str, timeout: int = 600, *,
        sandbox: Path | None = None, tag: str | None = None,
        keep: tuple[str, ...] = KEEP, include_inputs: bool = False,
        ingest: bool = True) -> Path:
    """复制后运行；已有沙箱拒绝复用，避免旧输出混入或递归删除未知文件。

    M4 可显式选择本树沙箱、不同 db 的独立 tag、保留表与输入快照；
    ingest=False 只生成复跑证据，不改 fixtures / PROVENANCE。
    """
    if steps < 1 or source not in ("golden", "bench"):
        raise ValueError("positive steps and golden/bench source required")
    for name in (bb, db, *keep):
        if Path(name).name != name or name in (".", ".."):
            raise ValueError(f"not a plain file name: {name}")
    src_dir = BDDA / "df" / ("bench" if source == "bench" else "")
    for name in (bb, db):
        if not (src_dir / name).exists():
            raise FileNotFoundError(src_dir / name)
    if not KERNEL.exists():
        raise FileNotFoundError(KERNEL)
    tag = tag or f"{bb}_N{steps}"
    if Path(tag).name != tag or tag in (".", ".."):
        raise ValueError(f"not a plain fixture tag: {tag}")
    sandbox = Path(sandbox or SANDBOX).resolve()
    work = (sandbox / tag).resolve()
    if work.parent != sandbox or work.is_relative_to(BDDA.resolve()):
        raise ValueError(f"sandbox must be outside the sibling repository: {work}")
    # No recursive deletion: a repeat must use a new sandbox root.
    work.mkdir(parents=True, exist_ok=False)
    shutil.copy2(KERNEL, work / KERNEL.name)
    shutil.copy2(src_dir / bb, work / bb)
    shutil.copy2(src_dir / db, work / db)
    (work / "ff.c").write_bytes(f"{bb}\r\n{db}\r\n".encode("ascii"))
    env = dict(os.environ, BDDA_KERNEL_MODE="1", BDDA_DF17_DEBUG="1", BDDA_DUMP_STEPS=str(steps))
    proc = subprocess.run([str(work / KERNEL.name)], cwd=str(work), env=env, timeout=timeout,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if proc.returncode != 0:
        raise RuntimeError(f"kernel rc={proc.returncode} in {work}")
    if not ingest:
        return work
    dest = FIX / tag
    dest.mkdir(parents=True, exist_ok=True)
    entries = []
    copied = 0
    for name in (*keep, *((bb, db) if include_inputs else ())):
        s = work / name
        if not s.exists():
            continue
        d = dest / name
        shutil.copyfile(s, d)
        rel = f"bdda_df/{tag}/{name}"
        entries.append({"dest": rel, "source": f"generated: {KERNEL} on df/{'bench/' if source == 'bench' else ''}{bb}+{db} "
                                            f"BDDA_KERNEL_MODE=1 BDDA_DF17_DEBUG=1 BDDA_DUMP_STEPS={steps} (sandbox {work})",
                     "ingested": str(date.today()), "status": "ok", "bytes": d.stat().st_size, "sha256": sha256(d),
                     "kernel_sha256": sha256(work / KERNEL.name),
                     # G6 第四轮 provenance 镜头：只记内核哈希分不出"内核变了"与"残值变了"——输入也记哈希；首步 o3/o4 与
                     # wall_clock 是不可复现列（未初始化残值 / 时间戳），同一 exe、同一输入重跑 16 份里 **4 份**逐字节不同
                     # （contacts、df18、m0s2 三张表的首步 o3/o4 + progress 的 wall_clock；G6 第五轮沙箱实测三例皆然）
                     "input_sha256": {bb: sha256(work / bb), db: sha256(work / db)},
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
    ap.add_argument("--sandbox", type=Path, help="new sandbox root; exe and inputs are copied here")
    ap.add_argument("--tag", help="fixture tag, e.g. bbv01_dbv01a_N3")
    a = ap.parse_args()
    run(a.bb, a.db, a.steps, a.source, sandbox=a.sandbox, tag=a.tag)
    return 0


if __name__ == "__main__":
    sys.exit(main())
