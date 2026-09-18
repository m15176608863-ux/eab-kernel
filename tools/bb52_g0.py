"""bb52 真几何上的二维盖枚举：G1 集合对照（对 legacy 接触表）+ G0 近接触自证。

几何来自夹具 bdda_debug_verts.csv（步 1，vidx 为全局顶点号，每块按多边形序连续，尾部带两个
回绕重复点——df 存储 d[i2+1]=d[i1]、d[i2+2]=d[i1+1] 的 dump 外露；legacy 用重复索引引用首边）。
legacy 接触来自 bdda_debug_contacts.csv（mtype 0 = v-e：p1 顶点、p3->p2 边；mtype 1 = v-v）。
检测参数来自 b-DDA 的 detparams：d0 = 0.196875（搜索距离），h5 = 0.3，h1 = 3°（角度容差）。

`analyze()` 返回数字供 tests/test_bb52_g1.py 钉门；`main()` 打印明细。
"""

from __future__ import annotations

import csv
import json
import random
import sys
from collections import defaultdict
from math import radians, sin
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eab.kernel2d.covers import enumerate_covers  # noqa: E402
from eab.kernel2d.geom import ensure_ccw, is_convex, polygons_overlap, reflex_vertices, translate  # noqa: E402

FIX = ROOT / "fixtures" / "bdda_df" / "studio_20260712"
D0, H5, H1, TOL = 0.19687500000000002, 0.3, 3.0, 1e-9
CONE_TOL = sin(radians(H1))     # legacy 兼容：法锥判据的角容差（sin 单位）
SEG_TOL = 1e-9


def load_blocks(step: int = 1) -> tuple[dict, dict[int, int]]:
    """从 verts.csv 重建多边形；剥离尾部回绕重复点并返回 alias（重复 vidx -> 真实 vidx）。"""
    rows = [r for r in csv.DictReader((FIX / "bdda_debug_verts.csv").open(newline="")) if int(r["step"]) == step]
    by: dict[int, list[tuple[int, tuple[float, float]]]] = defaultdict(list)
    for r in rows:
        by[int(r["block"])].append((int(r["vidx"]), (float(r["x"]), float(r["y"]))))
    blocks = {}
    alias: dict[int, int] = {}
    for b, lst in by.items():
        lst.sort()
        vids = [v for v, _ in lst]
        poly = [p for _, p in lst]
        while len(poly) > 3:
            k = len(poly) - 1
            dup = None
            for h, p in enumerate(poly[:2]):
                if abs(p[0] - poly[k][0]) <= 1e-12 and abs(p[1] - poly[k][1]) <= 1e-12:
                    dup = h
                    break
            if dup is None:
                break
            alias[vids[k]] = vids[dup]
            poly.pop()
            vids.pop()
        ccw, flipped = ensure_ccw(poly)
        gmap = list(reversed(vids)) if flipped else vids
        blocks[b] = {"poly": ccw, "vidx": gmap, "flipped": flipped}
    return blocks, alias


def legacy_contacts(step: int = 1):
    out = []
    for r in csv.DictReader((FIX / "bdda_debug_contacts.csv").open(newline="")):
        if int(r["step"]) != step:
            continue
        out.append((int(r["mtype"]), int(r["p1"]), int(r["p2"]), int(r["p3"]), int(r["m0_2"]), float(r["o2"])))
    return out


def analyze(*, samples_per_pair: int = 60, seed: int = 0, cone_tol: float = CONE_TOL) -> dict:
    blocks, alias = load_blocks(1)
    canon = lambda v: alias.get(v, v)  # noqa: E731
    v2b = {v: b for b, d in blocks.items() for v in d["vidx"]}
    pos = {v: d["poly"][i] for b, d in blocks.items() for i, v in enumerate(d["vidx"])}
    ids = sorted(blocks)

    eab_ve: dict = {}
    eab_vv: dict = {}
    for i, bi in enumerate(ids):
        for bj in ids[i + 1:]:
            A, B = blocks[bi], blocks[bj]
            for c in enumerate_covers(A["poly"], B["poly"], window=D0, tol=TOL, cone_tol=cone_tol, seg_tol=SEG_TOL):
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

    leg = legacy_contacts(1)
    leg_ve = {(canon(p1), frozenset((canon(p2), canon(p3)))): (m0, o2) for mt, p1, p2, p3, m0, o2 in leg if mt == 0}
    leg_vv = {frozenset((canon(p1), canon(p2))): (m0, o2) for mt, p1, p2, p3, m0, o2 in leg if mt == 1}

    common = set(leg_ve) & set(eab_ve)
    legacy_only = sorted(set(leg_ve) - set(eab_ve))
    eab_only = sorted(set(eab_ve) - set(leg_ve), key=lambda k: eab_ve[k].gap)

    def at_endpoint(c) -> bool:
        return c.param is not None and (abs(c.param) < 1e-6 or abs(c.param - 1.0) < 1e-6)

    eab_only_endpoint = [k for k in eab_only if at_endpoint(eab_ve[k])]
    eab_only_mid = [k for k in eab_only if not at_endpoint(eab_ve[k])]

    leg_vb = {(v, next(iter({v2b[x] for x in e}))) for v, e in leg_ve}
    eab_vb = {(v, next(iter({v2b[x] for x in e}))) for v, e in eab_ve}
    extra_vb = sorted(eab_vb - leg_vb)
    mirror = 0
    non_mirror = []
    for v, blk in extra_vb:
        hit = any(v2b[vp] == blk and b2 == v2b[v]
                  and abs(pos[vp][0] - pos[v][0]) < 1e-6 and abs(pos[vp][1] - pos[v][1]) < 1e-6
                  for (vp, b2) in leg_vb)
        mirror += hit
        if not hit:
            non_mirror.append((v, blk))

    # G0 近接触自证（一般多边形，严格法锥模式）
    rng = random.Random(seed)
    total = agree = 0
    disagree = []
    pairs = {tuple(sorted((v2b[v], next(iter({v2b[x] for x in e}))))) for v, e in eab_ve}
    for bi, bj in sorted(pairs):
        A, B = blocks[bi]["poly"], blocks[bj]["poly"]
        for _ in range(samples_per_pair):
            x = (rng.uniform(-D0, D0), rng.uniform(-D0, D0))
            At = translate(A, x)
            brute = polygons_overlap(At, B, 1e-12)
            covs = enumerate_covers(At, B, window=D0, tol=TOL)
            pen = min((c.gap for c in covs if c.kind != "VV"), default=None)
            if pen is None or abs(pen) <= 1e-9 or brute == 0:
                continue
            total += 1
            if (1 if pen < 0 else -1) == brute:
                agree += 1
            else:
                disagree.append((bi, bj, x, brute, pen))

    return {
        "blocks": len(blocks), "stripped_duplicates": len(alias),
        "convex_blocks": sum(is_convex(d["poly"], 1e-12) for d in blocks.values()),
        "reflex_total": sum(len(reflex_vertices(d["poly"], 1e-12)) for d in blocks.values()),
        "ve_legacy": len(leg_ve), "ve_eab": len(eab_ve), "ve_common": len(common),
        "ve_legacy_only": [(v, sorted(e)) for v, e in legacy_only],
        "ve_eab_only_endpoint": len(eab_only_endpoint), "ve_eab_only_mid": [(v, sorted(e), round(eab_ve[(v, e)].gap, 9), round(eab_ve[(v, e)].param, 4)) for v, e in eab_only_mid],
        "matched_gap_max_abs": max((abs(eab_ve[k].gap) for k in common), default=0.0),
        "vb_legacy": len(leg_vb), "vb_eab": len(eab_vb), "vb_common": len(leg_vb & eab_vb),
        "vb_legacy_only": sorted(leg_vb - eab_vb), "vb_eab_only": len(extra_vb), "vb_eab_only_mirror": mirror,
        "vb_eab_only_non_mirror": non_mirror,
        "vv_legacy": [sorted(k) for k in leg_vv], "vv_eab_active": len(eab_vv),
        "g0_samples": total, "g0_agree": agree, "g0_disagree": disagree[:10],
    }


def main() -> int:
    out = analyze()
    for k, v in out.items():
        print(f"{k}: {v}")
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "bb52_g1_g0.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
