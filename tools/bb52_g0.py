"""在 b-DDA 的 bb52 真几何上跑二维盖枚举与 G0 自证，并与 legacy 接触表做第一次集合对照（报告，不断言）。

几何来自夹具 bdda_debug_verts.csv（步 1，vidx 为全局顶点号，每块按多边形序连续）。
legacy 接触来自 bdda_debug_contacts.csv（mtype 0 = v-e：p1 顶点、p2-p3 边；mtype 1 = v-v）。
检测参数来自 b-DDA 的 detparams：d0 = 0.196875（搜索距离），h5 = 0.3。
"""

from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eab.kernel2d.covers import enumerate_covers  # noqa: E402
from eab.kernel2d.geom import ensure_ccw, is_convex, polygons_overlap, reflex_vertices, translate  # noqa: E402

FIX = ROOT / "fixtures" / "bdda_df" / "studio_20260712"
D0, H5, TOL = 0.19687500000000002, 0.3, 1e-9


ALIAS: dict[int, int] = {}   # 回绕重复顶点 vidx -> 真实顶点 vidx（legacy 用重复索引引用首边）


def load_blocks(step: int = 1):
    """从 verts.csv 重建多边形。

    实测（2026-09-18）：每块顶点表尾部带回绕重复点（block 11：172≡166、173≡167），是 df 存储
    d[i2+1]=d[i1]、d[i2+2]=d[i1+1] 的 dump 外露。剥离后建 ALIAS 表供 legacy 索引换算。
    """
    rows = [r for r in csv.DictReader((FIX / "bdda_debug_verts.csv").open(newline="")) if int(r["step"]) == step]
    by: dict[int, list[tuple[int, tuple[float, float]]]] = defaultdict(list)
    for r in rows:
        by[int(r["block"])].append((int(r["vidx"]), (float(r["x"]), float(r["y"]))))
    blocks = {}
    for b, lst in by.items():
        lst.sort()
        vids = [v for v, _ in lst]
        poly = [p for _, p in lst]
        # 剥离尾部与头部重合的顶点
        while len(poly) > 3:
            k = len(poly) - 1
            head = poly[: k]
            dup = None
            for h, p in enumerate(head[:2]):
                if abs(p[0] - poly[k][0]) <= 1e-12 and abs(p[1] - poly[k][1]) <= 1e-12:
                    dup = h
                    break
            if dup is None:
                break
            ALIAS[vids[k]] = vids[dup]
            poly.pop()
            vids.pop()
        ccw, flipped = ensure_ccw(poly)
        gmap = list(reversed(vids)) if flipped else vids
        blocks[b] = {"poly": ccw, "vidx": gmap, "flipped": flipped}
    return blocks


def canon(v: int) -> int:
    return ALIAS.get(v, v)


def legacy_contacts(step: int = 1):
    out = []
    for r in csv.DictReader((FIX / "bdda_debug_contacts.csv").open(newline="")):
        if int(r["step"]) != step:
            continue
        out.append((int(r["mtype"]), int(r["p1"]), int(r["p2"]), int(r["p3"]), int(r["m0_2"]), float(r["o2"])))
    return out


def main() -> int:
    from math import radians, sin
    blocks = load_blocks(1)
    v2b = {v: b for b, d in blocks.items() for v in d["vidx"]}
    print("blocks:", len(blocks), "stripped duplicates:", len(ALIAS), "flipped:", sum(d["flipped"] for d in blocks.values()),
          "convex:", sum(is_convex(d["poly"], 1e-12) for d in blocks.values()),
          "reflex counts:", {b: len(reflex_vertices(d["poly"], 1e-12)) for b, d in blocks.items() if reflex_vertices(d["poly"], 1e-12)})

    H1 = 3.0                        # legacy 角度容差（度），detparams h1
    CONE_TOL = sin(radians(H1))     # 法锥判据的兼容容差（sin 单位）
    SEG_TOL = 1e-9

    # ---- eab 枚举（legacy 兼容模式）：对所有块对
    eab_ve = {}   # (vertex_vidx, frozenset(edge vidx pair)) -> cover
    eab_vv = {}
    ids = sorted(blocks)
    for i, bi in enumerate(ids):
        for bj in ids[i + 1:]:
            A, B = blocks[bi], blocks[bj]
            for c in enumerate_covers(A["poly"], B["poly"], window=D0, tol=TOL, cone_tol=CONE_TOL, seg_tol=SEG_TOL):
                if c.kind == "VE":
                    v = A["vidx"][c.a_index]
                    e = frozenset((B["vidx"][c.b_index], B["vidx"][(c.b_index + 1) % len(B["poly"])]))
                    eab_ve[(v, e)] = c
                elif c.kind == "EV":
                    v = B["vidx"][c.b_index]
                    e = frozenset((A["vidx"][c.a_index], A["vidx"][(c.a_index + 1) % len(A["poly"])]))
                    eab_ve[(v, e)] = c
                elif c.kind == "VV":
                    eab_vv[frozenset((A["vidx"][c.a_index], B["vidx"][c.b_index]))] = c

    # ---- legacy 集合（索引经 ALIAS 换算）
    leg = legacy_contacts(1)
    leg_ve = {(canon(p1), frozenset((canon(p2), canon(p3)))): (m0, o2) for mt, p1, p2, p3, m0, o2 in leg if mt == 0}
    leg_vv = {frozenset((canon(p1), canon(p2))): (m0, o2) for mt, p1, p2, p3, m0, o2 in leg if mt == 1}

    # ---- 一级：顶点-边精确对照
    common = set(leg_ve) & set(eab_ve)
    print(f"\n[tier 1: vertex-edge]  legacy={len(leg_ve)}  eab={len(eab_ve)}  common={len(common)}  "
          f"legacy-only={len(set(leg_ve) - set(eab_ve))}  eab-only={len(set(eab_ve) - set(leg_ve))}")
    gaps = [eab_ve[k].gap for k in common]
    if gaps:
        print("  gap of matched covers: min %.4g  max %.4g  (>0 separated)" % (min(gaps), max(gaps)))
    for k in sorted(set(leg_ve) - set(eab_ve))[:15]:
        v, e = k
        print("  legacy-only:", v, sorted(e), "blocks", v2b.get(v), {v2b.get(x) for x in e}, "m0_2/o2", leg_ve[k])
    eo = sorted(set(eab_ve) - set(leg_ve), key=lambda k: eab_ve[k].gap)
    n_endpoint = sum(1 for k in eo if eab_ve[k].param is not None and (abs(eab_ve[k].param) < 1e-6 or abs(eab_ve[k].param - 1) < 1e-6))
    print(f"  eab-only at edge endpoints (s≈0/1, i.e. vertex-on-vertex): {n_endpoint} / {len(eo)}")
    for k in [k for k in eo if not (eab_ve[k].param is not None and (abs(eab_ve[k].param) < 1e-6 or abs(eab_ve[k].param - 1) < 1e-6))][:12]:
        v, e = k
        c = eab_ve[k]
        print("  eab-only (mid-edge):", v, sorted(e), "blocks", v2b.get(v), {v2b.get(x) for x in e}, f"gap={c.gap:.4g} s={c.param:.3f} strict={c.strict}")

    # ---- 二级：顶点-块对照（哪些顶点与哪块接触，忽略选哪条边）
    leg_vb = {(v, next(iter({v2b[x] for x in e}))) for v, e in leg_ve}
    eab_vb = {(v, next(iter({v2b[x] for x in e}))) for v, e in eab_ve}
    print(f"[tier 2: vertex-block]  legacy={len(leg_vb)}  eab={len(eab_vb)}  common={len(leg_vb & eab_vb)}  "
          f"legacy-only={sorted(leg_vb - eab_vb)}  eab-only(count)={len(eab_vb - leg_vb)}")
    print(f"\nv-v  legacy={len(leg_vv)}  eab(active)={len(eab_vv)}  common={len(set(leg_vv) & set(eab_vv))}  legacy={[sorted(k) for k in leg_vv]}")

    # ---- G0（一般多边形，近接触域）：对每对相邻块，随机小平移，暴力谓词 vs 盖谓词
    rng = random.Random(0)
    total = agree = 0
    disagree = []
    pairs = {(v2b[k[0]], v2b[next(iter(k[1]))]) for k in eab_ve} | {(v2b[next(iter(k))], v2b[list(k)[1]]) for k in eab_vv}
    for bi, bj in sorted({tuple(sorted(p)) for p in pairs if None not in p}):
        A, B = blocks[bi]["poly"], blocks[bj]["poly"]
        for _ in range(60):
            x = (rng.uniform(-D0, D0), rng.uniform(-D0, D0))
            At = translate(A, x)
            brute = polygons_overlap(At, B, 1e-12)
            covs = enumerate_covers(At, B, window=D0, tol=TOL)
            pen = min((c.gap for c in covs if c.kind != "VV"), default=None)
            if pen is None or abs(pen) <= 1e-9 or brute == 0:
                continue
            cover_says = 1 if pen < 0 else -1
            total += 1
            if cover_says == brute:
                agree += 1
            else:
                disagree.append((bi, bj, x, brute, pen))
    print(f"\nG0 near-contact (general polygons): samples={total} agree={agree} disagree={len(disagree)}")
    for d in disagree[:8]:
        print("  ", d)
    out = {"ve_legacy": len(leg_ve), "ve_eab": len(eab_ve), "ve_common": len(common),
           "vv_legacy": len(leg_vv), "vv_eab": len(eab_vv), "g0_samples": total, "g0_agree": agree}
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "bb52_g0_first_look.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
