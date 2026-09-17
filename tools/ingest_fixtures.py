"""从姊妹仓库的既有导出复制夹具（只读复制，不运行任何 exe），并写溯源 fixtures/PROVENANCE.json。

来源路径是 2026-09-18 探查实测；缺失则跳过并在溯源里记 missing。
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures"
MAX_BYTES = 20 * 1024 * 1024

SOURCES = [
    # b-DDA 插桩内核 dump（studio 运行，2026-07-12）
    (r"D:\b-DDA\runs\studio_20260712T154254\p1_l5y4hzxj\bdda_debug_contacts.csv", "bdda_df/studio_20260712/bdda_debug_contacts.csv"),
    (r"D:\b-DDA\runs\studio_20260712T154254\p1_l5y4hzxj\bdda_debug_df18.csv", "bdda_df/studio_20260712/bdda_debug_df18.csv"),
    (r"D:\b-DDA\runs\studio_20260712T154254\p1_l5y4hzxj\bdda_debug_df22.csv", "bdda_df/studio_20260712/bdda_debug_df22.csv"),
    (r"D:\b-DDA\runs\studio_20260712T154254\p1_l5y4hzxj\bdda_debug_verts.csv", "bdda_df/studio_20260712/bdda_debug_verts.csv"),
    (r"D:\b-DDA\runs\sensor_20260624T120811\p1_v1l5vve1\bdda_debug_contacts.csv", "bdda_df/sensor_20260624/bdda_debug_contacts.csv"),
    (r"D:\b-DDA\runs\sensor_20260624T120811\p1_v1l5vve1\bdda_debug_df18.csv", "bdda_df/sensor_20260624/bdda_debug_df18.csv"),
    (r"D:\b-DDA\runs\sensor_20260624T120811\p1_v1l5vve1\bdda_debug_df22.csv", "bdda_df/sensor_20260624/bdda_debug_df22.csv"),
    # 3DDA tf.cpp 探针（HeavyProbe 既有输出）
    (r"C:\3DDA\3d-DDA-work\reports\gpu_regression_smoke\smoke_cpu\runs\20260722_224658\contact_pair_stage.tsv", "tf/smoke_cpu_20260722/contact_pair_stage.tsv"),
    (r"C:\3DDA\3d-DDA-work\projects\calibration\sandstone_phi50_h100_n8_study\final_cases\fine_seed_20260712\runs\20260712_223421\retry_contact_pair_probe.tsv", "tf/sandstone_fine_20260712/retry_contact_pair_probe.tsv"),
    (r"C:\3DDA\3d-DDA-work\projects\calibration\sandstone_phi50_h100_n8_study\final_cases\medium_seed_20260712\runs\20260712_222041\retry_contact_pair_probe.tsv", "tf/sandstone_medium_20260712/retry_contact_pair_probe.tsv"),
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    prov_path = FIX / "PROVENANCE.json"
    prov = json.loads(prov_path.read_text(encoding="utf-8")) if prov_path.exists() else {"entries": []}
    seen = {e["dest"]: e for e in prov["entries"]}
    for src, dest in SOURCES:
        s = Path(src)
        d = FIX / dest
        entry = {"dest": dest, "source": src, "ingested": str(date.today())}
        if not s.exists():
            entry["status"] = "missing"
            print(f"MISSING  {src}")
        elif s.stat().st_size > MAX_BYTES:
            entry["status"] = "skipped_too_large"
            entry["bytes"] = s.stat().st_size
            print(f"TOO LARGE {src} ({s.stat().st_size} B)")
        else:
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(s, d)   # 逐字节复制，不改换行符
            entry["status"] = "ok"
            entry["bytes"] = d.stat().st_size
            entry["sha256"] = sha256(d)
            assert sha256(s) == entry["sha256"]
            print(f"OK       {dest} ({entry['bytes']} B)")
        seen[dest] = entry
    prov["entries"] = [seen[k] for k in sorted(seen)]
    FIX.mkdir(exist_ok=True)
    prov_path.write_text(json.dumps(prov, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
