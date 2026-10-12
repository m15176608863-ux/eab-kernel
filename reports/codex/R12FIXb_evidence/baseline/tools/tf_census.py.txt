"""tf.cpp 三维接触的类型普查（能从现有夹具里榨出来的唯一东西）。

`retry_contact_pair_probe.tsv` 与 `contact_pair_stage.tsv` **都不带块体顶点坐标**，
所以无法重跑盖枚举做 G2 对账。能做的只有类型分布统计。
"""

from __future__ import annotations

import collections
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KINDS = ("nn_count", "ne_count", "np_count", "ee_count")
PROBE_TYPE = {0: "n-n", 1: "n-e", 2: "n-p", 3: "e-e"}


def census() -> dict:
    out: dict[str, dict] = {}
    for p in sorted((ROOT / "fixtures" / "tf").glob("*/contact_pair_stage.tsv")):
        rows = list(csv.DictReader(p.open(newline=""), delimiter="\t"))
        c = collections.Counter()
        for r in rows:
            for k in KINDS:
                c[k] += int(r[k])
        out[p.parent.name + "/stage"] = {
            "pairs": len(rows), "contacts": sum(c.values()),
            "by_kind": dict(c),
            "steps": len({int(r["step"]) for r in rows}),
        }
    for p in sorted((ROOT / "fixtures" / "tf").glob("*/retry_contact_pair_probe.tsv")):
        rows = list(csv.DictReader(p.open(newline=""), delimiter="\t"))
        c = collections.Counter(PROBE_TYPE.get(int(r["contact_type"]), "?") for r in rows)
        out[p.parent.name + "/probe"] = {
            "rows": len(rows), "by_kind": dict(c),
            "steps": len({int(r["step"]) for r in rows}),
            "note": "探针是抽样非全量（只在重试事件、且只写涉及触发块/顶压板的接触）",
        }
    return out


def main() -> int:
    res = census()
    total = collections.Counter()
    for name, r in res.items():
        n = r.get("contacts", r.get("rows"))
        print(f"{name}: {n} 条")
        for k, v in sorted(r["by_kind"].items()):
            print(f"    {k:10s} {v:6d}  ({100.0 * v / max(n, 1):6.2f}%)")
            total[k.replace('_count', '').replace('nn', 'n-n').replace('ne', 'n-e')
                  .replace('np', 'n-p').replace('ee', 'e-e')] += v
    print("\n合计（两种口径并列，仅看有无）：", dict(total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
