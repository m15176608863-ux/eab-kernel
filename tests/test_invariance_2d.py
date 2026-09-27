"""纪律 F（M0.2）· 二维内核的刚体运动与单位不变性元门。

G6（2026-09-24）的 6 条 critical 里 5 条同根：绝对容差遍布内核，而测试从不平移、从不旋转、从不放到工程坐标。
这里对 kernel2d 的每个几何 API 施加同一族变换

    T(p) = s·R(θ)·p + t，  θ 为固定种子的非轴对齐角，|t| ∈ {0, 1e3, 1e5}，s ∈ {1e-3, 1, 1e3}，

并要求结果按应有的方式变换：
  · 盖枚举：标签 (kind, a_index, b_index, strict) 集合不变（顶点/边编号不因刚体运动改变），间隙 ×s；
  · polygons_overlap：判定（1 / 0 / −1）不变——**含恰好接触的位形**（工程上块体就是贴着的）；
  · interior_point：严格在内（独立 oracle：Fraction 精确射线奇偶，另写一份，不调 geom）；
  · 距离完备性 / 出口完备性：通过，且分离/接触/相交样本计数不变；brute_ray_exit 的出口 ×s；
  · 凸块 G0：通过，facet 标签集合不变；
  · 凸性 / 反射顶点（带平直 T 形顶点的合成块、bb52 真几何）不变；
  · 读取器边界的重复点剥除（readers.bdda_geom）：近重复点照样被剥，工程坐标上只差一个 ulp 的重复点也认得出。
调用方给的长度容差随单位一起缩放（tol → s·tol）——这是换单位的本义；角度容差是无量纲的，不缩放。
**库内部不许再有绝对阈值**：参考结果取恒等变换下的库输出，变换后的输出必须与它一致。
唯一的例外有数有据：bb52 真几何里相邻块沿同一节理的边近乎平行（sin 夹角 1.7e-8 … 3e-6，Fraction 精确算），
低于 s=1e-3 且搬到 1e3/1e5 处时的角度舍入下限——那 19 个格子只断言夹逼（见 test_cover_enumeration_is_invariant）。

先在 b6468f3 上跑出红（见 M0.2 返回值 red_before），再修（相对容差 tol_eff = max(tol, c·eps·C)，
角度侧 c·eps·C/ℓ；库函数自己稳健，不在测试里把输入挪回原点）。
"""

from __future__ import annotations

import math
import random
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from eab.kernel2d.covers import convex_entrance_block, enumerate_covers
from eab.kernel2d.g0 import (brute_ray_exit, g0_convex, g0_distance_completeness, g0_exit_completeness,
                             random_convex_polygon)
from eab.kernel2d.geom import interior_point, is_convex, polygons_overlap, reflex_vertices, translate

ROOT = Path(__file__).resolve().parents[1]

# 舍入下限 c·eps·C 的常数，测试自带一份（不从被测库导入）：只用于界定不可约的表示误差，
# 也就是测试容许的最小误差带——库若用更小的下限，只会更严，不会让这里放水。
EPS = sys.float_info.epsilon
ROUND_C = 64.0

# ---------------------------------------------------------------- 变换族

_RNG = random.Random(20260924)
THETA = _RNG.uniform(0.2, 1.3)            # 非轴对齐（≈0.217 rad ≈ 12.4°）
PHI = _RNG.uniform(0.0, 2 * math.pi)      # 平移方向


MOTIONS = [(f"rot_s{s:g}_t{tm:g}", THETA, s, tm) for s in (1e-3, 1.0, 1e3) for tm in (0.0, 1e3, 1e5)]
MOTION_IDS = [m[0] for m in MOTIONS]


def _T(theta, s, tm):
    c, sn = math.cos(theta), math.sin(theta)
    tx, ty = tm * math.cos(PHI), tm * math.sin(PHI)

    def pt(p):
        return (s * (c * p[0] - sn * p[1]) + tx, s * (sn * p[0] + c * p[1]) + ty)

    def vec(v):                       # 平移量/方向：只转、只缩，不平移
        return (s * (c * v[0] - sn * v[1]), s * (sn * v[0] + c * v[1]))

    def poly(P):
        return [pt(p) for p in P]
    return pt, vec, poly


# ---------------------------------------------------------------- 几何

SQ = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
DIAMOND = [(0.0, -0.5), (0.5, 0.0), (0.0, 0.5), (-0.5, 0.0)]
BRICK = [(0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)]
ROW = [(0.0, 0.0), (2.0, 0.0), (4.0, 0.0), (4.0, 1.0), (2.0, 1.0), (0.0, 1.0)]   # 带两个平直 T 形顶点（DDA 常见）
CHANNEL = [(0.0, 0.0), (3.0, 0.0), (3.0, 1.0), (1.0, 1.0), (1.0, 1.8), (3.0, 1.8), (3.0, 2.8), (0.0, 2.8)]
WEDGE = [(0.0, 0.0), (0.6, 0.2), (0.2, 0.75)]
THIN_L = [(0.0, 0.0), (3.0, 0.0), (3.0, 0.1), (0.1, 0.1), (0.1, 3.0), (0.0, 3.0)]
C3 = [(0.0, 0.0), (3.0, 0.0), (3.0, 1.0), (1.0, 1.0), (1.0, 2.0), (3.0, 2.0), (3.0, 3.0), (0.0, 3.0)]


def _star(rng, n, scale=1.0):
    angs = sorted(rng.uniform(0.0, 2 * math.pi) for _ in range(n))
    return [(scale * r * math.cos(a), scale * r * math.sin(a)) for a, r in ((a, rng.uniform(0.35, 1.0)) for a in angs)]


def _bb52_blocks():
    sys.path.insert(0, str(ROOT / "tools"))
    import bb52_g0
    if not (bb52_g0.FIX / "bdda_debug_verts.csv").exists():
        return None
    blocks, _ = bb52_g0.load_blocks(1)
    return {b: d["poly"] for b, d in blocks.items()}


_BB = _bb52_blocks()

# 盖枚举的位形：(名字, A, B, x, 长度容差 τ, cone_tol（无量纲；None=库默认）, 窗口)
_rs = random.Random(5)
_SA, _SB = _star(_rs, 9), _star(_rs, 8)
COVER_CASES = [
    ("FF_edge_touch", SQ, SQ, (1.0, 0.3), 1e-9, None, 0.5),
    ("vertex_on_edge", DIAMOND, SQ, (0.4, 1.5), 1e-9, None, 0.5),
    ("corner_corner", SQ, SQ, (1.0, 1.0), 1e-9, None, 0.5),
    ("brick_on_row_flat_vertices", BRICK, ROW, (1.0, 1.0), 1e-9, None, 0.5),
    ("brick_on_row_legacy_cone", BRICK, ROW, (1.0, 1.0), 1e-9, math.sin(math.radians(3.0)), 0.196875),
    ("wedge_in_channel", WEDGE, CHANNEL, (0.97, 0.95), 1e-9, None, 0.3),
    ("star_pair_generic", _SA, _SB, (1.1, 0.4), 1e-9, None, 5.0),
]
# bb52 步 1 真几何：21 个有盖的块对全部上（贴合位形、平直顶点、窄缝——工程输入本来的样子）
BB52_PAIRS = [(1, 2), (1, 3), (1, 4), (1, 9), (1, 10), (1, 11), (2, 3), (2, 6), (2, 7), (2, 8), (2, 11), (3, 8), (3, 9),
              (4, 5), (4, 9), (4, 10), (5, 10), (6, 7), (6, 11), (7, 8), (10, 11)]
if _BB is not None:
    for bi, bj in BB52_PAIRS:
        COVER_CASES.append((f"bb52_{bi}_{bj}_legacy", _BB[bi], _BB[bj], (0.0, 0.0), 1e-9,
                            math.sin(math.radians(3.0)), 0.196875))
        COVER_CASES.append((f"bb52_{bi}_{bj}_strict", _BB[bi], _BB[bj], (0.0, 0.0), 1e-9, None, 0.196875))


def _covers(A, B, x, tau, cone_tol, window):
    covs = enumerate_covers(translate(A, x), B, window=window, tol=tau, cone_tol=cone_tol, seg_tol=tau)
    labels = sorted((c.kind, c.a_index, c.b_index, c.strict) for c in covs)
    gaps = {(c.kind, c.a_index, c.b_index): c.gap for c in covs}
    return labels, gaps


def _floor_in_reference_units(A, B, motion):
    """变换后位形的长度舍入下限 c·eps·C_t，折回恒等变换的单位（÷s）。"""
    _, theta, s, tm = motion
    pt, vec, poly = _T(theta, s, tm)
    C = max(abs(v) for P in (A, B) for p in poly(P) for v in p)
    return ROUND_C * EPS * C / s


@pytest.mark.parametrize("motion", MOTIONS, ids=MOTION_IDS)
@pytest.mark.parametrize("case", COVER_CASES, ids=[c[0] for c in COVER_CASES])
def test_cover_enumeration_is_invariant(case, motion):
    """盖标签 (kind, a, b, strict) 不变、间隙 ×s。

    **可分辨性**：变换后的坐标带 ~eps·C_t 的表示误差，角度判据分辨不了比 c·eps·C_t/ℓ 更小的偏差。合成位形
    （贴合、平行边、平直顶点、一般位置）的判据余量要么精确为 0（由容差吸收），要么 ≫ 舍入下限——全格必须逐项相等
    （下面断言合成位形没有一个格子落在不可分辨带里）。bb52 真几何不同：相邻块沿同一节理的边**近乎**平行，
    sin 夹角实测 1.7e-8（块 7–8）… 3e-6（Fraction 精确计算），低于 s=1e-3、|t|=1e3/1e5 时的角度舍入下限
    （~2e-7 / ~2e-5）。判定方式（不依赖被测变换）：恒等变换下把长度容差抬到 4× 该格子的舍入下限（折回原单位）
    再枚举一次——若盖集不变，余量都在带外，该格必须逐项相等；若变了，该格落在不可分辨带里，只断言**夹逼**：
    每个标签的去留与严格性都取两份恒等参考之一（两份都有的必须有、两份都没有的不许有）——即库在带内的判定
    只能是"精确判定"或"容差吸收"之一，不能是第三种（丢盖、凭空多盖、翻成外部）。
    """
    name, A, B, x, tau, cone_tol, window = case
    _, theta, s, tm = motion
    ref_labels, ref_gaps = _covers(A, B, x, tau, cone_tol, window)
    assert ref_labels, name
    pt, vec, poly = _T(theta, s, tm)
    labels, gaps = _covers(poly(A), poly(B), vec(x), s * tau, cone_tol, s * window)
    infl = max(tau, 4.0 * _floor_in_reference_units(A, B, motion))
    wide_labels, _ = _covers(A, B, x, infl, cone_tol, window)
    if wide_labels != ref_labels:
        assert name.startswith("bb52_"), (name, "synthetic case fell into the unresolvable band")
        both, either = set(ref_labels) & set(wide_labels), set(ref_labels) | set(wide_labels)
        assert both <= set(labels) <= either, (name, sorted(set(labels) - either), sorted(both - set(labels)))
        return
    assert labels == ref_labels, (name, sorted(set(labels) ^ set(ref_labels)))
    C = max(abs(v) for P in (A, B) for p in poly(P) for v in p)
    for k, g in ref_gaps.items():
        assert abs(gaps[k] - s * g) <= s * tau + 1e-12 * s + 1e-13 * C, (name, k, gaps[k], s * g)


def _seg_dist(a, b, c, d):
    """闭线段间距离（不相交时在某条的端点处实现；内联算术，只作邻近筛选）。"""
    def pd(p, u, v):
        ex, ey = v[0] - u[0], v[1] - u[1]
        t = max(0.0, min(1.0, ((p[0] - u[0]) * ex + (p[1] - u[1]) * ey) / (ex * ex + ey * ey)))
        return math.hypot(p[0] - u[0] - t * ex, p[1] - u[1] - t * ey)
    return min(pd(a, c, d), pd(b, c, d), pd(c, a, b), pd(d, a, b))


def _min_near_parallel_sin(P, Q, reach=0.3):
    """两块里相距 < reach 的边对之间 |sin 夹角| 的最小**非零**值（Fraction 精确叉积；不调 geom）。"""
    out = 1.0
    for i in range(len(P)):
        e0, e1 = P[i], P[(i + 1) % len(P)]
        for j in range(len(Q)):
            f0, f1 = Q[j], Q[(j + 1) % len(Q)]
            if _seg_dist(e0, e1, f0, f1) >= reach:
                continue
            ex, ey = Fraction(e1[0]) - Fraction(e0[0]), Fraction(e1[1]) - Fraction(e0[1])
            fx, fy = Fraction(f1[0]) - Fraction(f0[0]), Fraction(f1[1]) - Fraction(f0[1])
            c = ex * fy - ey * fx
            if c != 0:
                out = min(out, abs(float(c)) / (math.hypot(float(ex), float(ey)) * math.hypot(float(fx), float(fy))))
    return out


def _min_edge(P):
    return min(math.dist(P[i], P[(i + 1) % len(P)]) for i in range(len(P)))


def test_cover_invariance_unresolvable_cells_are_explained_by_measured_near_parallel_edges():
    """把"不可分辨带"钉成数：只允许出现在 bb52 真几何上，且每个这样的格子都由 Fraction 精确算出的近平行边对解释——
    该块对相距 < 0.3 的边对里最小非零 sin 夹角，小于该格子抬高后的角度舍入下限 4·c·eps·C_t/(s·ℓ_min)。
    2026-09-24 实测：19 个格子（全在 21 块对 × 2 模式 × 9 变换 = 378 格里），sin 夹角 1.7e-8（块 7–8）… 3e-6（块 6–11）。"""
    bad = []
    for case in COVER_CASES:
        name, A, B, x, tau, cone_tol, window = case
        ref, _ = _covers(A, B, x, tau, cone_tol, window)
        for motion in MOTIONS:
            fl = _floor_in_reference_units(A, B, motion)
            wide, _ = _covers(A, B, x, max(tau, 4.0 * fl), cone_tol, window)
            if wide != ref:
                bad.append((name, motion, fl))
    assert all(n.startswith("bb52_") for n, _, _ in bad), [n for n, _, _ in bad]
    for n, motion, fl in bad:
        bi, bj = (int(v) for v in n.split("_")[1:3])
        margin = _min_near_parallel_sin(_BB[bi], _BB[bj])
        ang_floor = 4.0 * fl / min(_min_edge(_BB[bi]), _min_edge(_BB[bj]))
        assert margin < ang_floor, (n, motion[0], margin, ang_floor)
    assert len(bad) == 19, len(bad)


# ---------------------------------------------------------------- polygons_overlap：判定不变（含恰好接触）

OVERLAP_CASES = [
    ("edge_touch", SQ, SQ, (1.0, 0.3), 0),
    ("corner_touch", SQ, SQ, (1.0, 1.0), 0),
    ("vertex_on_edge", DIAMOND, SQ, (0.4, 1.5), 0),
    ("brick_on_row", BRICK, ROW, (1.0, 1.0), 0),
    ("brick_in_row_flush", BRICK, ROW, (2.0, 0.0), 1),     # 贴合重叠：边全共线，只有面积说明相交
    ("identical", C3, C3, (0.0, 0.0), 1),
    ("separated_thin", SQ, SQ, (1.001, 0.2), -1),
    ("overlap_shallow", SQ, SQ, (0.999, 0.2), 1),
    ("wedge_in_channel", WEDGE, CHANNEL, (0.97, 0.95), 1),
    ("box_in_notch", [(0.0, 0.0), (1.0, 0.0), (1.0, 0.5), (0.0, 0.5)], C3, (1.5, 1.25), -1),
    ("thin_arm_overlap", [(0.0, 0.0), (0.5, 0.0), (0.5, 0.05), (0.0, 0.05)], THIN_L, (0.3, 0.02), 1),
]


@pytest.mark.parametrize("motion", MOTIONS, ids=MOTION_IDS)
@pytest.mark.parametrize("case", OVERLAP_CASES, ids=[c[0] for c in OVERLAP_CASES])
def test_polygons_overlap_is_invariant(case, motion):
    name, A, B, x, want = case
    _, theta, s, tm = motion
    tau = 1e-12
    assert polygons_overlap(translate(A, x), B, tau) == want, name           # 恒等变换下先对
    pt, vec, poly = _T(theta, s, tm)
    At, Bt = translate(poly(A), vec(x)), poly(B)
    assert polygons_overlap(At, Bt, s * tau) == want, name
    assert polygons_overlap(Bt, At, s * tau) == want, name


# ---------------------------------------------------------------- interior_point：严格在内（独立精确 oracle）

def _exact_inside(pt, poly) -> int:
    """Fraction 精确射线奇偶：1 严格在内 / 0 在边界 / −1 在外。不调 geom 的任何原语。"""
    px, py = Fraction(pt[0]), Fraction(pt[1])
    P = [(Fraction(a), Fraction(b)) for a, b in poly]
    n = len(P)
    inside = False
    for i in range(n):
        (ax, ay), (bx, by) = P[i], P[(i + 1) % n]
        cr = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
        if cr == 0 and min(ax, bx) <= px <= max(ax, bx) and min(ay, by) <= py <= max(ay, by):
            return 0
        if (ay > py) != (by > py):
            xint = ax + (py - ay) * (bx - ax) / (by - ay)
            if px < xint:
                inside = not inside
    return 1 if inside else -1


_ri = random.Random(11)
IP_POLYS = [("square", SQ), ("channel", CHANNEL), ("thin_L", THIN_L), ("C3", C3), ("row_flat", ROW),
            ("star_a", _star(_ri, 11)), ("star_b", _star(_ri, 7))]
if _BB is not None:
    IP_POLYS += [(f"bb52_{b}", _BB[b]) for b in sorted(_BB)]


@pytest.mark.parametrize("motion", MOTIONS, ids=MOTION_IDS)
@pytest.mark.parametrize("item", IP_POLYS, ids=[p[0] for p in IP_POLYS])
def test_interior_point_is_strictly_inside_under_motion(item, motion):
    name, P = item
    _, theta, s, tm = motion
    pt, vec, poly = _T(theta, s, tm)
    Pt = poly(P)
    assert _exact_inside(interior_point(Pt), Pt) == 1, name


# ---------------------------------------------------------------- 距离完备性 / 出口完备性

def _ring(rng, n, r):
    return [(r * math.cos(t), r * math.sin(t)) for t in (rng.uniform(0, 2 * math.pi) for _ in range(n))]


_rd = random.Random(31)
_DA, _DB = _star(_rd, 8), _star(_rd, 9)
DIST_CASES = [
    ("stars", _DA, _DB, _ring(_rd, 30, 1.6)),
    ("squares_with_contacts", SQ, SQ, [(1.3, 0.0), (1.3, 1.3), (1.0, 0.3), (1.0, 1.0), (0.4, 1.25), (-1.0, 0.5)]),
    ("box_near_thin_L", [(0.0, 0.0), (0.5, 0.0), (0.5, 0.05), (0.0, 0.05)], THIN_L,
     [(ox, oy) for ox in (0.15, 0.3, 1.7) for oy in (0.105, 0.12, 0.9)]),
]


@pytest.mark.parametrize("motion", MOTIONS, ids=MOTION_IDS)
@pytest.mark.parametrize("case", DIST_CASES, ids=[c[0] for c in DIST_CASES])
def test_distance_completeness_is_invariant(case, motion):
    name, A, B, xs = case
    _, theta, s, tm = motion
    ref = g0_distance_completeness(A, B, xs, tol=1e-9, atol=1e-9)
    assert ref.passed and ref.samples > 0, name
    pt, vec, poly = _T(theta, s, tm)
    rep = g0_distance_completeness(poly(A), poly(B), [vec(x) for x in xs], tol=1e-9 * s, atol=1e-9)
    assert (rep.samples, rep.overlapping, rep.touching) == (ref.samples, ref.overlapping, ref.touching), name
    assert rep.passed, (name, rep.failures[:2])


_re = random.Random(41)
_EA, _EB = _star(_re, 8), _star(_re, 9)
EXIT_CASES = [
    ("stars", _EA, _EB, _ring(_re, 20, 0.4), [(math.cos(t), math.sin(t)) for t in (_re.uniform(0, 6.28) for _ in range(20))]),
    ("squares", SQ, SQ, [(0.3, 0.2), (0.3, 0.2), (0.3, 0.3), (0.3, 0.2)], [(1.0, 0.0), (0.6, 0.8), (1.0, 1.0), (0.5, 0.0)]),
    ("small_in_channel", [(0.0, 0.0), (0.2, 0.0), (0.2, 0.2), (0.0, 0.2)], CHANNEL, [(1.5, 0.3)], [(0.0, 1.0)]),
]


@pytest.mark.parametrize("motion", MOTIONS, ids=MOTION_IDS)
@pytest.mark.parametrize("case", EXIT_CASES, ids=[c[0] for c in EXIT_CASES])
def test_exit_completeness_and_ray_exit_are_invariant(case, motion):
    name, A, B, xs, us = case
    _, theta, s, tm = motion
    ref = g0_exit_completeness(A, B, xs, us, tol=1e-9, atol=1e-9)
    assert ref.passed and ref.samples > 0, name
    pt, vec, poly = _T(theta, s, tm)
    At, Bt = poly(A), poly(B)
    rus = [(vec(u)[0] / s, vec(u)[1] / s) for u in us]            # 方向只转不缩：t 以 |u| 计，出口 ×s
    rep = g0_exit_completeness(At, Bt, [vec(x) for x in xs], rus, tol=1e-9 * s, atol=1e-9)
    assert (rep.samples, rep.separated, rep.touching) == (ref.samples, ref.separated, ref.touching), name
    assert rep.passed, (name, rep.failures[:2])
    for x, u, ru in zip(xs, us, rus):
        if polygons_overlap(translate(A, x), B, 1e-12) != 1:
            continue
        t0 = brute_ray_exit(translate(A, x), B, u)
        t1 = brute_ray_exit(translate(At, vec(x)), Bt, ru)
        # 不可约的下限：变换后的坐标本身带 ~eps·C 的表示误差，出口位置分辨不到比它更细（÷|u|：t 以 |u| 计）
        C = max(abs(v) for p in (*At, *Bt) for v in p)
        assert abs(t1 - s * t0) <= 1e-9 * s * max(1.0, t0) + ROUND_C * EPS * C / math.hypot(*ru), (name, x, u, t1, s * t0)


# ---------------------------------------------------------------- 凸块 G0

_rc = random.Random(51)
CONVEX_CASES = [("squares", SQ, SQ), ("square_diamond", SQ, DIAMOND), ("brick_square", BRICK, SQ),
                ("random", random_convex_polygon(_rc, 8), random_convex_polygon(_rc, 7))]


def _facet_set(A, B):
    return sorted(convex_entrance_block(A, B, (0.0, 0.0), 0.0).facets)     # tol 是长度：只用舍入下限


@pytest.mark.parametrize("motion", MOTIONS, ids=MOTION_IDS)
@pytest.mark.parametrize("case", CONVEX_CASES, ids=[c[0] for c in CONVEX_CASES])
def test_convex_g0_is_invariant(case, motion):
    name, A, B = case
    _, theta, s, tm = motion
    ref = g0_convex(A, B, samples=300, seed=3)
    assert ref.passed, name
    pt, vec, poly = _T(theta, s, tm)
    At, Bt = poly(A), poly(B)
    assert _facet_set(At, Bt) == _facet_set(A, B), name
    rep = g0_convex(At, Bt, samples=300, seed=3)
    assert rep.passed, (name, rep.mismatches[:2], rep.facet_symmetric_diff, rep.hull_vertex_mismatch)
    assert (rep.facet_local, rep.facet_global) == (ref.facet_local, ref.facet_global), name


# ---------------------------------------------------------------- 凸性 / 反射顶点（bb52 真几何）

FLAT = [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0), (3.0, 1.0), (1.5, 1.0), (0.0, 1.0)]   # 3 个平直顶点


@pytest.mark.parametrize("motion", MOTIONS, ids=MOTION_IDS)
@pytest.mark.parametrize("item", [("row", ROW), ("flat3", FLAT), ("channel", CHANNEL), ("C3", C3)],
                         ids=["row", "flat3", "channel", "C3"])
def test_convexity_with_flat_vertices_is_invariant(item, motion):
    """平直顶点（DDA 块边上别块角点留下的 T 形顶点，理想转角恰为 0）：刚体运动后转角成 ±eps·C/ℓ，
    角容差 1e-12 分辨不了——不许因此判成反射顶点、把凸块判成凹块。"""
    name, P = item
    _, theta, s, tm = motion
    pt, vec, poly = _T(theta, s, tm)
    assert (is_convex(poly(P), 1e-12), reflex_vertices(poly(P), 1e-12)) == (is_convex(P, 1e-12), reflex_vertices(P, 1e-12)), name


@pytest.mark.skipif(_BB is None, reason="bb52 fixture missing")
@pytest.mark.parametrize("motion", MOTIONS, ids=MOTION_IDS)
def test_convexity_census_of_bb52_is_invariant(motion):
    _, theta, s, tm = motion
    pt, vec, poly = _T(theta, s, tm)
    ref = {b: (is_convex(P, 1e-12), tuple(reflex_vertices(P, 1e-12))) for b, P in _BB.items()}
    got = {b: (is_convex(poly(P), 1e-12), tuple(reflex_vertices(poly(P), 1e-12))) for b, P in _BB.items()}
    assert got == ref


# ---------------------------------------------------------------- 读取器边界：重复点剥除（readers.bdda_geom）

@pytest.mark.parametrize("motion", MOTIONS, ids=MOTION_IDS)
def test_duplicate_vertex_stripping_is_invariant(motion):
    """df 的 dump 把块环写成带回绕尾巴与内部重复点的点列；读取器按 |Δ| ≤ dup_tol 判"同一点"剥除并登记 alias。
    近重复点（相差 1e-13，恒等下 ≤ dup_tol=1e-12 被剥）经刚体运动 + 换单位后只差舍入级——必须照样被剥：
    否则内核拿到一条 ~ulp 长的边，法向是噪声。dup_tol 随单位缩放（s·1e-12），库内抬到舍入下限。"""
    from eab.readers.bdda_geom import strip_duplicate_vertices
    ring = [(0.0, 0.0), (1.0, 0.0), (1.0 + 1e-13, 1e-13), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0), (1.0, 0.0)]
    vids = list(range(100, 100 + len(ring)))
    ref = strip_duplicate_vertices(vids, ring, 1e-12, block=1)
    assert ref[0] == [100, 101, 103, 104] and ref[2] == {102: 101, 105: 100, 106: 101}
    _, theta, s, tm = motion
    pt, vec, poly = _T(theta, s, tm)
    got = strip_duplicate_vertices(vids, poly(ring), 1e-12 * s, block=1)
    assert (got[0], got[2]) == (ref[0], ref[2])


@pytest.mark.parametrize("C", [1.0, 1e3, 1e5, 1e7], ids=["C1", "C1e3", "C1e5", "C1e7"])
def test_one_ulp_duplicate_is_stripped_at_any_coordinate_magnitude(C):
    """确定性的工程坐标版：块环搬到坐标量级 C，内部重复点与原点只差**一个 ulp**（dump 走另一条代码路径算出同一点
    的典型样子）。绝对 dup_tol=1e-12 在 C=1e5 时比一个 ulp（1.46e-11）还小，永远认不出它——库内抬到舍入下限。"""
    from eab.readers.bdda_geom import strip_duplicate_vertices
    base = [(C, C), (C + 1.0, C), (C + 1.0, C + 1.0), (C, C + 1.0)]
    dup = (math.nextafter(base[1][0], math.inf), base[1][1])
    ring = [base[0], base[1], dup, base[2], base[3]]
    vids, poly, alias = strip_duplicate_vertices([10, 11, 12, 13, 14], ring, 1e-12, block=3)
    assert vids == [10, 11, 13, 14] and alias == {12: 11}, (vids, alias)
