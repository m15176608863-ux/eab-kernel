"""bb52 真几何上的二维盖枚举：G1 集合对照（对 legacy 接触表）+ G0 近接触自证（距离完备性 + 出口完备性）。

几何来自夹具 bdda_debug_verts.csv（步 1，vidx 为全局顶点号，每块按多边形序连续，尾部带两个
回绕重复点——df 存储 d[i2+1]=d[i1]、d[i2+2]=d[i1+1] 的 dump 外露；legacy 用重复索引引用首边）。
legacy 接触来自 bdda_debug_contacts.csv（mtype 0 = v-e：p1 顶点、p3->p2 边；mtype 1 = v-v）。
检测参数来自 b-DDA 的 detparams：d0 = 0.196875（搜索距离），h5 = 0.3，h1 = 3°（角度容差）。

`analyze()` 返回数字供 tests/test_bb52_g1.py 钉门；`main()` 打印明细。

G0 口径（2026-09-24 改）：真值一律暴力 `polygons_overlap`；盖侧被检验的是定理"∂E ⊆ ∪ 有效盖线段"
的两面——分离样本上的**距离完备性**（有效盖见证距离的最小值 == 暴力特征距离，与三维
`g0_distance_completeness3` 同构），相交样本上的**出口完备性**（沿随机方向首次离开 E 的 ∂E 点处必有有效盖
作见证，`g0_exit_completeness`）。两者都不是凹块成员谓词（M3）。
2026-09-18 版把 sign(min gap) 当凹块成员谓词——这条规则两个方向都是假的：分离判成相交（审查的
"细臂 L 块 + 凹槽内悬浮方块"）、相交判成分离（"槽角楔块"：楔尖压进槽角，楔尖的负间隙盖投影全部出界、
被边内筛除，窗口里只剩槽顶的正间隙盖）。两条反例都钉在 tests/test_bb52_g1.py；那版的 "1186/1186" 撤回。
"""

from __future__ import annotations

import csv
import json
import random
import sys
from collections import defaultdict
from math import cos, pi, radians, sin
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import eab.kernel2d.covers as cv  # noqa: E402  （归因走模块属性：被替换的盖函数也要被如实归因）
from eab.kernel2d.covers import enumerate_covers  # noqa: E402
from eab.kernel2d.g0 import g0_distance_completeness, g0_exit_completeness  # noqa: E402
from eab.kernel2d.geom import edge, ensure_ccw, is_convex, norm, reflex_vertices, sub, translate  # noqa: E402
from eab.readers.bdda_geom import strip_duplicate_vertices  # noqa: E402

FIX = ROOT / "fixtures" / "bdda_df" / "studio_20260712"
D0, H5, H1, TOL = 0.19687500000000002, 0.3, 3.0, 1e-9
CONE_TOL = sin(radians(H1))     # legacy 兼容：法锥判据的角容差（sin 单位）
SEG_TOL = 1e-9


def load_blocks(step: int = 1) -> tuple[dict, dict[int, int]]:
    """从 verts.csv 重建多边形；剥离尾部回绕重复点与**任何**循环连续重复点（零长边，审查 C19），
    返回 alias（被剥 vidx -> 保留 vidx）。剥点规则与 readers.bdda_geom 共用同一个函数。"""
    with (FIX / "bdda_debug_verts.csv").open(newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if int(r["step"]) == step]
    by: dict[int, list[tuple[int, tuple[float, float]]]] = defaultdict(list)
    for r in rows:
        by[int(r["block"])].append((int(r["vidx"]), (float(r["x"]), float(r["y"]))))
    blocks = {}
    alias: dict[int, int] = {}
    for b, lst in by.items():
        lst.sort()
        vids, poly, al = strip_duplicate_vertices([v for v, _ in lst], [p for _, p in lst], 1e-12, block=b)
        alias.update(al)
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


def classify_completeness_failure(At, B, arg) -> str:
    """距离完备性失配的归因：暴力实现特征对在盖枚举里遭遇了什么。

    端点处实现（t ∈ {0,1}）= 顶点-顶点，应由活跃 VV 盖（或相邻边在端点处的 VE/EV 盖）接住；
    边内部实现 = 顶点-边，应由 VE/EV 盖接住。归因分三类：盖漏枚举（法锥判据拒绝）/ 边内筛除 / 其他。
    """
    tag, i, j, t = arg
    a_side = tag == "A-vertex/B-edge"
    P_edge = B if a_side else At
    if t <= 0.0 or t >= 1.0:
        k = j if t <= 0.0 else (j + 1) % len(P_edge)
        ia, jb = (i, k) if a_side else (k, i)
        c = cv.vv_cover(At, ia, B, jb, TOL)
        what = f"A 顶点 {ia} × B 顶点 {jb}（顶点-顶点实现）"
        if c is None:
            return f"盖漏枚举：{what} 无 VV 盖（法锥相对内部交为空），相邻边端点处的 VE/EV 盖也未接住"
        if not c.strict:
            return f"盖漏枚举：{what} 的 VV 盖不活跃（分离方向落在交锥外）"
        return f"其他：{what} 有活跃 VV 盖（gap {c.gap:.6g}），见证距离却不等于暴力距离"
    if a_side:
        c = cv.ve_cover(At, i, B, j, TOL)
        what = f"A 顶点 {i} × B 边 {j} (t={t:.4g})"
    else:
        c = cv.ev_cover(At, j, B, i, TOL)
        what = f"B 顶点 {i} × A 边 {j} (t={t:.4g})"
    if c is None:
        return f"盖漏枚举：{what} 被法锥判据拒绝"
    p, q = edge(P_edge, j)
    le = norm(sub(q, p))
    if not (-SEG_TOL / le <= c.param <= 1.0 + SEG_TOL / le):
        return f"边内筛除：{what} 盖存在但投影参数 {c.param:.6g} 在边外"
    return f"其他：{what} 盖存在且在边内（gap {c.gap:.6g}），见证距离却不等于暴力距离"


def g0_draws(pairs: list[tuple[int, int]], samples_per_pair: int, seed: int):
    """G0 的平移序列：同一 rng、按块对序、每对 samples_per_pair 个 x ∈ [−D0, D0]²。

    与 2026-09-18 版逐位相同，所以 samples_per_pair=60, seed=0 重跑的就是当初报 "1186/1186"
    的那批平移（tests/test_bb52_g1.py 用这个函数重放旧投票、复现 1186 这个数来看着这句话）。
    """
    rng = random.Random(seed)
    return [(bi, bj, [(rng.uniform(-D0, D0), rng.uniform(-D0, D0)) for _ in range(samples_per_pair)])
            for bi, bj in pairs]


def g0_exit_directions(pairs: list[tuple[int, int]], samples_per_pair: int, seed: int) -> list[list[tuple[float, float]]]:
    """出口完备性的射线方向：每次平移配一个单位方向（极角均匀）。独立的 rng（字符串种子），
    不动 `g0_draws` 的随机序列——"同一批平移"那句话仍然成立。"""
    rng = random.Random(f"bb52-g0-exit/{seed}")
    out = []
    for _ in pairs:
        angs = [rng.uniform(0.0, 2.0 * pi) for _ in range(samples_per_pair)]
        out.append([(cos(a), sin(a)) for a in angs])
    return out


def analyze(*, samples_per_pair: int = 60, seed: int = 0, cone_tol: float = CONE_TOL, exit_probes: bool = True) -> dict:
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

    # G0 近接触自证（一般多边形，严格法锥模式）：真值一律暴力。分离样本检验距离完备性，
    # 相交样本检验出口完备性（同一条定理 ∂E ⊆ ∪ 有效盖线段 的两面）。
    g0 = {"draws": 0, "overlap": 0, "touch": 0, "separated": 0, "agree": 0, "worst": 0.0,
          "exit_samples": 0, "exit_agree": 0, "exit_worst": 0.0}
    disagree = []
    exit_disagree = []
    pairs = sorted({tuple(sorted((v2b[v], next(iter({v2b[x] for x in e}))))) for v, e in eab_ve})
    dirs = g0_exit_directions(pairs, samples_per_pair, seed)
    for (bi, bj, xs), us in zip(g0_draws(pairs, samples_per_pair, seed), dirs):
        A, B = blocks[bi]["poly"], blocks[bj]["poly"]
        rep = g0_distance_completeness(A, B, xs, tol=TOL, atol=1e-9)
        g0["draws"] += rep.draws
        g0["overlap"] += rep.overlapping
        g0["touch"] += rep.touching
        g0["separated"] += rep.samples
        g0["agree"] += rep.samples - len(rep.failures)
        g0["worst"] = max(g0["worst"], rep.worst_abs_error)
        for x, got, truth, arg in rep.failures:
            disagree.append((bi, bj, x, got, truth, arg, classify_completeness_failure(translate(A, x), B, arg)))
        if not exit_probes:
            continue
        ex = g0_exit_completeness(A, B, xs, us, tol=TOL, atol=1e-9)
        g0["exit_samples"] += ex.samples
        g0["exit_agree"] += ex.samples - len(ex.failures)
        g0["exit_worst"] = max(g0["exit_worst"], ex.worst_witness)
        for x, u, t, got, arg in ex.failures:
            Az = translate(A, (x[0] + t * u[0], x[1] + t * u[1]))
            exit_disagree.append((bi, bj, x, u, t, got, arg, classify_completeness_failure(Az, B, arg)))

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
        # G0：命题 = 距离完备性（分离样本上 min 见证距离 == 暴力特征距离）；真值 = polygons_overlap。
        "g0_proposition": "distance_completeness", "g0_pairs": pairs,
        "g0_draws": g0["draws"], "g0_brute_overlap": g0["overlap"], "g0_brute_touch": g0["touch"],
        "g0_samples": g0["separated"], "g0_agree": g0["agree"], "g0_worst_abs_error": g0["worst"],
        "g0_disagree": disagree[:10],
        # 相交样本：命题 = 出口完备性（沿随机方向首个 ∂E 点处有效盖最小见证距离 == 0）。不是成员谓词（M3）；
        # 仅接触样本只计数。exit_probes=False 时这四项为 0 / []。
        "g0_exit_proposition": "exit_completeness" if exit_probes else None,
        "g0_exit_samples": g0["exit_samples"], "g0_exit_agree": g0["exit_agree"],
        "g0_exit_worst_witness": g0["exit_worst"], "g0_exit_disagree": exit_disagree[:10],
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
