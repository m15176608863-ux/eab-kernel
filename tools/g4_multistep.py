"""G4 砖一·多步实验：几何先验 vs 转移态先验，各自对"收敛活动集"的命中率，逐步统计。

数据：一个 bdda_df 夹具目录（多步 dump）。对步 k：
  - 步初几何：verts.csv 步 k → 多边形 → 盖枚举（legacy 兼容容差）→ 每条 legacy 接触的 gap_k
  - 转移态先验 P1：contacts.csv 步 k 的 m0_2（携带进本步的状态 = df22 该步第一轮的 m0_prev，三份夹具逐条相等）
  - 几何先验 P2：gap_k ≤ g_tol → 预测闭合，否则张开
  - 运动学先验 P3：gap_k + (gap_k − gap_{k−1}) ≤ g_tol
  - **收敛真值（2026-09-24 改，G6 gap 1）**：df22 该步**最后一轮**开闭迭代的 m0_new（legacy 开闭迭代在本步的终判；
    与 readers.bdda_df.load_records 的 mode 同一条规则 `last_oc_judgments`）。
    旧口径（步 k+1 携带进来的 m0_2，键在 k+1 消失即判张开）混进了转移/移除假象，保留为对照列 *_old_truth。
  - 后验几何一致性：gap_{k+1}（步 k+1 几何 = 步 k 的结果几何）≤ g_tol 与真值闭合的一致率
输出每步与总计的命中率表（两种真值并列）。这是数据点收集器，不下结论。
"""

from __future__ import annotations

import csv
import json
import sys
from math import radians, sin
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eab.kernel2d.covers import enumerate_covers  # noqa: E402
from eab.readers.bdda_df import last_oc_judgments, read_df22_csv  # noqa: E402
from eab.readers.bdda_geom import load_step_geometries  # noqa: E402

TRUTH = "df22_last_oc_iter_m0_new"


def read_detparams(d: Path) -> dict[str, float]:
    p = d / "bdda_debug_detparams.csv"
    if not p.exists():
        return {"d0": 0.19687500000000002, "h5": 0.3, "h1": 3.0, "w0": 3.15}
    rows = list(csv.DictReader(p.open(newline="")))
    r = rows[0]
    return {"d0": float(r["d0"]), "h5": float(r["h5"]), "h1": float(r["h1"]), "w0": float(r["w0"])}


def read_contacts(d: Path) -> dict[int, list[dict]]:
    out: dict[int, list[dict]] = {}
    for r in csv.DictReader((d / "bdda_debug_contacts.csv").open(newline="")):
        out.setdefault(int(r["step"]), []).append({k: (int(v) if k in ("contact", "mtype", "p1", "p2", "p3", "m4", "m5", "m6", "m0_0", "m0_2") else float(v))
                                                   for k, v in r.items() if k != "step"})
    return out


def cover_gaps(sg, cone_tol: float, window: float) -> dict[tuple[int, frozenset], float]:
    """legacy 键 (vertex vidx, {edge vidx pair}) -> gap（步初几何，兼容容差）。"""
    gaps: dict[tuple[int, frozenset], float] = {}
    ids = sorted(sg.blocks)
    for i, bi in enumerate(ids):
        for bj in ids[i + 1:]:
            A, B = sg.blocks[bi], sg.blocks[bj]
            for c in enumerate_covers(A.poly, B.poly, window=window, tol=1e-9, cone_tol=cone_tol, seg_tol=1e-9,
                                      require_in_segment=False):
                if c.kind == "VE":
                    key = (A.vidx[c.a_index], frozenset((B.vidx[c.b_index], B.vidx[(c.b_index + 1) % len(B.poly)])))
                elif c.kind == "EV":
                    key = (B.vidx[c.b_index], frozenset((A.vidx[c.a_index], A.vidx[(c.a_index + 1) % len(A.poly)])))
                else:
                    continue
                if key not in gaps or abs(c.gap) < abs(gaps[key]):
                    gaps[key] = c.gap
    return gaps


_COUNT_KEYS = ("n", "p1", "p2", "p3", "post", "closed_true", "removed", "no_gap",
               "flips", "flip_p2", "flip_p3", "flip_post",
               "closed_old_truth", "p1_old_truth", "p2_old_truth", "p3_old_truth", "post_old_truth",
               "flips_old_truth", "flips_old_truth_removed", "flip_p2_old_truth", "flip_p3_old_truth", "flip_post_old_truth",
               "flips_both", "flips_only_old_truth", "flips_only_old_truth_removed", "flips_only_new_truth")


def analyze(fixture_dir: Path, *, g_tol_factor: float = 1e-6) -> dict:
    d = Path(fixture_dir)
    dp = read_detparams(d)
    cone_tol = sin(radians(dp["h1"]))
    window = 5.0 * dp["d0"]           # 宽窗口：只为取 gap，不筛
    g_tol = g_tol_factor * dp["w0"]
    geoms = load_step_geometries(d / "bdda_debug_verts.csv")
    contacts = read_contacts(d)
    final = last_oc_judgments(read_df22_csv(d / "bdda_debug_df22.csv"))
    steps = sorted(s for s in contacts if s + 1 in contacts and s in geoms and s + 1 in geoms)
    per_step = []
    samples = []
    tot = {k: 0 for k in _COUNT_KEYS}
    gap_cache: dict[int, dict] = {}
    for k in steps:
        sg, sg1 = geoms[k], geoms[k + 1]
        gk = gap_cache.get(k) or cover_gaps(sg, cone_tol, window)
        gk1 = cover_gaps(sg1, cone_tol, window)
        gap_cache[k], gap_cache[k + 1] = gk, gk1
        gkm = gap_cache.get(k - 1) if k - 1 in geoms else None
        if gkm is None and k - 1 in geoms:
            gkm = cover_gaps(geoms[k - 1], cone_tol, window)
            gap_cache[k - 1] = gkm
        nxt = {}
        for c in contacts[k + 1]:
            if c["mtype"] != 0:
                continue
            nxt[(sg1.canon(c["p1"]), frozenset((sg1.canon(c["p2"]), sg1.canon(c["p3"]))))] = c["m0_2"]
        row = {"step": k, **{kk: 0 for kk in _COUNT_KEYS}}
        for c in contacts[k]:
            if c["mtype"] != 0:
                continue
            key = (sg.canon(c["p1"]), frozenset((sg.canon(c["p2"]), sg.canon(c["p3"]))))
            truth_closed = final[(k, c["contact"])].m0_new > 0          # df22 本步末轮开闭判定
            old_truth_closed = nxt.get(key, 0) > 0                       # 旧口径：步 k+1 携带进来的 m0_2
            removed = key not in nxt
            p1_closed = c["m0_2"] > 0
            if key not in gk:
                row["no_gap"] += 1
                continue
            p2_closed = gk[key] <= g_tol
            # P3 运动学先验：用上一步到本步的 gap 变化外推一步
            if gkm is not None and key in gkm:
                p3_closed = (gk[key] + (gk[key] - gkm[key])) <= g_tol
            else:
                p3_closed = p2_closed
            post_closed = (gk1.get(key, float("inf")) <= g_tol)
            row["n"] += 1
            row["removed"] += removed
            row["closed_true"] += truth_closed
            row["closed_old_truth"] += old_truth_closed
            row["p1"] += (p1_closed == truth_closed)
            row["p2"] += (p2_closed == truth_closed)
            row["p3"] += (p3_closed == truth_closed)
            row["post"] += (post_closed == truth_closed)
            row["p1_old_truth"] += (p1_closed == old_truth_closed)
            row["p2_old_truth"] += (p2_closed == old_truth_closed)
            row["p3_old_truth"] += (p3_closed == old_truth_closed)
            row["post_old_truth"] += (post_closed == old_truth_closed)
            flip, flip_old = p1_closed != truth_closed, p1_closed != old_truth_closed
            if flip:                               # 翻转事件：转移态 != 本步开闭迭代终判
                row["flips"] += 1
                row["flip_p2"] += (p2_closed == truth_closed)
                row["flip_p3"] += (p3_closed == truth_closed)
                row["flip_post"] += (post_closed == truth_closed)
            if flip_old:                           # 旧口径的"翻转"（对照列）
                row["flips_old_truth"] += 1
                row["flips_old_truth_removed"] += removed
                row["flip_p2_old_truth"] += (p2_closed == old_truth_closed)
                row["flip_p3_old_truth"] += (p3_closed == old_truth_closed)
                row["flip_post_old_truth"] += (post_closed == old_truth_closed)
            row["flips_both"] += flip and flip_old
            row["flips_only_old_truth"] += flip_old and not flip
            row["flips_only_old_truth_removed"] += flip_old and not flip and removed
            row["flips_only_new_truth"] += flip and not flip_old
            samples.append({"step": k, "contact": c["contact"], "p1_closed": p1_closed, "truth_closed": truth_closed,
                            "old_truth_closed": old_truth_closed, "removed_next": removed, "p2_closed": p2_closed,
                            "p3_closed": p3_closed, "post_closed": post_closed})
        per_step.append(row)
        for kk in _COUNT_KEYS:
            tot[kk] += row[kk]
    return {"fixture": str(d), "truth": TRUTH, "old_truth": "next_step_carried_m0_2_missing_key_open",
            "detparams": dp, "g_tol": g_tol, "steps": per_step, "total": tot, "samples": samples}


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: g4_multistep.py <fixture_dir> [more...]")
        return 2
    for arg in sys.argv[1:]:
        res = analyze(Path(arg))
        t = res["total"]
        print(f"\n== {Path(arg).name}  truth={res['truth']}  steps={len(res['steps'])}  "
              f"contacts(v-e, step-pairs)={t['n']}  closed_true={t['closed_true']}  removed_next={t['removed']}")
        print(f"   P1 transferred-state prior hit: {t['p1']}/{t['n']}  ({t['p1'] / max(t['n'], 1):.3f})")
        print(f"   P2 geometric prior (gap<=tol)  : {t['p2']}/{t['n']}  ({t['p2'] / max(t['n'], 1):.3f})")
        print(f"   P3 gap-extrapolation prior     : {t['p3']}/{t['n']}  ({t['p3'] / max(t['n'], 1):.3f})")
        print(f"   posterior geometry consistency : {t['post']}/{t['n']}  ({t['post'] / max(t['n'], 1):.3f})")
        print(f"   FLIP events (transferred != df22 final): {t['flips']}   caught by P2: {t['flip_p2']}  "
              f"by P3: {t['flip_p3']}  by posterior geometry: {t['flip_post']}")
        print(f"   [old truth = next-step m0_2] flips: {t['flips_old_truth']}   caught by P2: {t['flip_p2_old_truth']}  "
              f"by P3: {t['flip_p3_old_truth']}  by posterior: {t['flip_post_old_truth']}")
        print(f"   flips in both: {t['flips_both']}  only old truth (transfer/removal artefacts): "
              f"{t['flips_only_old_truth']} (of which key removed at k+1: {t['flips_only_old_truth_removed']})  "
              f"only new truth: {t['flips_only_new_truth']}")
        for r in res["steps"]:
            print(f"   step {r['step']:3d}: n={r['n']:3d} closed={r['closed_true']:3d} P1={r['p1']:3d} P2={r['p2']:3d} P3={r['p3']:3d} post={r['post']:3d} flips={r['flips']} (P2 {r['flip_p2']}, P3 {r['flip_p3']}, post {r['flip_post']}) old-truth flips={r['flips_old_truth']} removed={r['removed']}")
        out = {k: v for k, v in res.items() if k != "samples"}
        out["fixture"] = Path(arg).as_posix()
        (ROOT / "reports").mkdir(exist_ok=True)
        (ROOT / "reports" / f"g4_{Path(arg).name}.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
