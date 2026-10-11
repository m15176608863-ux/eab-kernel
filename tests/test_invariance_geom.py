"""纪律 F（M0.2）· 刚体运动与单位不变性元门：几何核与裕度层。

G6（`reports/g6_20260924.md`）的 6 条 critical 里 5 条同根：**绝对容差遍布内核，而测试从不平移、
从不旋转、从不放到工程坐标上**。本文件是这一根因的统一复现与看护：对每个几何 API，把同一对物体
施加相似变换

    p ↦ t + s·R·p        R：固定种子的非轴对齐旋转（外加恒等旋转作纯平移格）
                         |t| ∈ {0, 1e3, 1e5, 1e6}（方向固定、非轴对齐），s ∈ {1e-3, 1, 1e3}

结果必须按应有的方式变换：
  · 距离 ×s（body_distance、margin_contacts 的见证距离、distance_to_convex_entrance、support_gaps3）；
  · 稳定区判定不变，边界逐格对给定舍入数据作精确检查；
  · E5a 的盖标签/strict 和凸包结构可因输入舍入而改变，必须逐格等于独立精确 oracle，不能按噪声略过；
  · G0 三票照样通过且所有精确极点/标签计数一致；E 的体积 ×s³、流形干净（entrance_block_convex）。

**oracle（纪律 A）**：每一格的对照是**同一 API 在恒等变换下的结果**（蜕变关系），而恒等格本身再对
闭式真值（本文件逐对写明：解析距离、解析贯入证人、E 的解析体积）。E5a 的边界标签和结构另对
独立 Fraction 支撑集/Gram/极射线 oracle（不调用被测几何原语），所有旧参数格保留，零噪声豁免。
容差：距离比较用 1e-9·s·L 加上坐标舍入的噪声预算 1e3·eps·(|t| + s·L)（L 为物体尺度），
不许为了过门把输入先挪回原点——库函数自己必须稳健。

margin 层（body_distance / margin_contacts / inflated_membership / entrance_block_convex）
本组只调用、不改：它的失败若只因本组文件（geom3 / covers3 / g03），就是本组的缺陷。
"""

from __future__ import annotations

import math
import random
from functools import lru_cache
from fractions import Fraction

import pytest
from e5a_cover_oracle import cover_labels as independent_cover_labels

from eab.kernel3d.covers3 import (enumerate_covers3, local_facets3, membership_convex3,
                                  support_gaps3)
from eab.kernel3d.g03 import g0_convex3
from eab.kernel3d import g03_exact as exact_oracle
from eab.kernel3d.geom3 import (Polyhedron, box, brute_feature_distance, convex_hull_3d, merge_coplanar,
                                polyhedra_overlap, tetra, exact_convex_view)
from eab.margin import (INSIDE, OUTSIDE, PENETRATING, body_distance, distance_to_convex_entrance,
                        entrance_block_convex, inflated_membership, margin_contacts)

EPS = 2.220446049250313e-16
T_DIR = (0.6, -0.48, 0.64)                   # 单位向量，非轴对齐
ROTS = (0, 7, 11)                            # 0 = 恒等旋转（纯平移 / 纯缩放格）
TRANS = (0.0, 1e3, 1e5, 1e6)                # 1e6：G6 第二轮点名的盲区（两条 critical 都在 |t| ≥ 1e5 的角落）
SCALES = (1e-3, 1.0, 1e3)
CELLS = [(r, t, s) for r in ROTS for t in TRANS for s in SCALES if (r, t, s) != (0, 0.0, 1.0)]
CELL_IDS = [f"R{r}-t{t:g}-s{s:g}" for r, t, s in CELLS]
# G0 三票很贵：只在一个一般旋转的全部 (t, s) 格上跑
G0_CELLS = [c for c in CELLS if c[0] == 7]
G0_IDS = [f"R{r}-t{t:g}-s{s:g}" for r, t, s in G0_CELLS]


# ================================================================ 相似变换（纯算术）

def _rotation(seed: int):
    if seed == 0:
        return ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    rng = random.Random(9100 + seed)
    q = [rng.gauss(0.0, 1.0) for _ in range(4)]
    n = math.sqrt(sum(c * c for c in q))
    w, x, y, z = (c / n for c in q)
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


class Motion:
    def __init__(self, rot: int, tmag: float, s: float):
        self.R = _rotation(rot)
        self.t = tuple(tmag * c for c in T_DIR)
        self.tmag, self.s = tmag, s

    def vec(self, v):
        R, s = self.R, self.s
        return tuple(s * (R[i][0] * v[0] + R[i][1] * v[1] + R[i][2] * v[2]) for i in range(3))

    def point(self, p):
        v = self.vec(p)
        return tuple(self.t[i] + v[i] for i in range(3))

    def poly(self, P: Polyhedron) -> Polyhedron:
        return Polyhedron([self.point(p) for p in P.verts], list(P.faces))

    def dist_tol(self, L: float) -> float:
        """距离比较的容差：相对 1e-9 加坐标舍入噪声预算（1e3 ulp 量级）。"""
        return 1e-9 * self.s * L + 1e3 * EPS * (self.tmag + self.s * L)


# ================================================================ 物体对（局部坐标里构造，真值闭式）

def _slab(theta: float, c, half) -> Polyhedron:
    ct, st = math.cos(theta), math.sin(theta)
    P = box(half=half)
    return Polyhedron([(c[0] + ct * x - st * y, c[1] + st * x + ct * y, c[2] + z) for x, y, z in P.verts],
                      list(P.faces))


def _pair_tetra_box_vv():
    """C5 退化对（平行面）+ 唯一最近对 VV3：四面体顶点 3 悬在方块顶点 (1,1,−1) 外 0.1·unit(1,1,−1)。
    解析：−n 严格在四面体顶点锥内、n 严格在方块顶点锥内 ⇒ 距离 0.1，标签 VV3(3, 2)（G6 critical 26）。"""
    T0 = tetra((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    B = box(half=(1.0, 1.0, 1.0))
    r3 = 1.0 / math.sqrt(3.0)
    apex = (1.0 + 0.1 * r3, 1.0 + 0.1 * r3, -1.0 - 0.1 * r3)
    A = T0.translated(tuple(apex[i] - T0.verts[3][i] for i in range(3)))
    return A, B


def _pair_box_box_face():
    """两个方块面对面、竖向间隙 0.05、平面内部分重叠（全是 FF/FE/EEP 退化，最近对大量并列）。"""
    B = box(half=(1.0, 0.8, 0.5))
    A = box(center=(0.4, 0.3, 0.5 + 0.05 + 0.35), half=(0.7, 0.6, 0.35))
    return A, B


def _pair_generic():
    """一般位置的两个随机凸包，分离。"""
    rng = random.Random(5)
    A = convex_hull_3d([(rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)) for _ in range(8)])
    B = convex_hull_3d([(rng.uniform(-1, 1) + 2.6, rng.uniform(-1, 1) + 0.3, rng.uniform(-1, 1) - 0.2)
                        for _ in range(8)])
    return A, B


VE3_GAP = 1e-4


def _pair_ve3_wedge():
    """G6 critical 6 的几何：B 是屋脊沿 x 的楔，A 是尖朝下的细棱锥，尖端悬在屋脊正上方 g。
    解析距离 = g（尖端投影落在屋脊段内；两坡面 45°，尖端到坡面平面的投影落在坡面之外）。"""
    B = merge_coplanar(convex_hull_3d([(x, y, z) for x in (-2.0, 2.0)
                                       for (y, z) in ((0.0, 0.0), (-1.0, -1.0), (1.0, -1.0))]))
    c, s = math.cos(0.5), math.sin(0.5)
    A = convex_hull_3d([(0.3, 0.0, VE3_GAP)] + [(0.3 + c * x - s * y, s * x + c * y, VE3_GAP + 1.0)
                                                for x, y in ((0.2, 0.0), (-0.1, 0.17), (-0.1, -0.17))])
    return A, B


def _pair_x_cross():
    """G6 critical 5/10：两块等高板 X 形交叉（真实贯入 0.1 深），无顶点在对方体内、棱交点全在共面上。
    解析证人：两中线交点 z=0.2 处，离两板侧面 0.1、离顶底面 0.3。"""
    A = _slab(0.7123231161619232, (-0.08666247398702509, -0.28261190955518073, 0.0), (1.0, 0.1, 0.5))
    B = _slab(2.3208944052154075, (0.0, 0.0, 0.0), (1.0, 0.1, 0.5))
    return A, B


def _pair_stack_touch():
    """G6 minor 7：方块面对面静置（接触、零重叠体积）。"""
    return box((0.1, -0.2, 0.5), (1.0, 1.0, 0.5)), box((0.0, 0.0, -0.5), (2.0, 2.0, 0.5))


def _pair_sliver():
    """共面同向面的二维重叠（票 b 类）：两块共享顶底平面，x 向咬合 0.02 的薄片——真实贯入。"""
    return box((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)), box((1.49, 0.5, 0.5), (0.51, 0.3, 0.5))


def _pair_yaw(theta: float):
    """近平行棱对（G6 第三轮 major：EE 候选法向噪声未除 sinθ、票二候选噪声同病）：1 m 方块绕 z 偏航 θ 搁在 2 m 板上方 0.1。
    解析距离 0.1（四个 VF 并列）；恒等格里 EE 候选恰是面法向、判边界，一经旋转叉积被舍入倾斜 ~1e-11 rad。"""
    B = box(half=(1.0, 1.0, 0.5))
    A = _slab(theta, (0.0, 0.0, 1.1), (0.5, 0.5, 0.5))
    return A, B


def _pair_ridge_needle():
    """展示算例脊 + 针的**可分辨**版本（G6 第三轮 major：G0 三票对脊高 1e-6、针底 1e-3 的原版在 |t| ≥ 200 起不具平移不变性）：
    脊高 1e-3 的屋脊（两坡面夹 2e-3 rad），底半径 0.3 的尖锥，尖端在脊线正上方 0.05。解析距离 0.05：VE3(尖, 脊)；
    尖端在两坡面上的投影落在坡面之外 5e-5，所以两个 VF 不在程。原版在 ×1e-3、|t| ≥ 1e5 的格上脊高 1e-9 m 低于坐标舍入
    1.4e-9——那是诚实的"分辨不了"，由 tests/test_margin_resolution.py 的脊对三票门按三态看护，不属于本元门的等式口径。"""
    h = 1e-3
    sec = [(-1.0, -1.0), (1.0, -1.0), (1.0, 0.0), (0.0, h), (-1.0, 0.0)]
    B = Polyhedron([(-2.0, y, z) for y, z in sec] + [(2.0, y, z) for y, z in sec],
                   [(4, 3, 2, 1, 0), (5, 6, 7, 8, 9)] + [(i, (i + 1) % 5, 5 + (i + 1) % 5, 5 + i) for i in range(5)])
    A = convex_hull_3d([(0.3, 0.0, h + 0.05)] + [(0.3 + 0.3 * math.cos(t), 0.3 * math.sin(t), h + 1.05)
                                                 for t in (0.1, 2.1943951, 4.2887902)])
    return A, B


def _pair_size_ratio():
    """两体尺寸比 100（G6 第三轮 major：point_in_polyhedron 的面内边界带随**大**体的对角线）：小方块的底面与大方块的顶面共面、
    在面内落在大方块之外 1e-3。解析距离 1e-3（两条平行棱）。"""
    B = box(half=(50.0, 50.0, 50.0))
    A = box(center=(50.0 + 0.5 + 1e-3, 0.0, 50.5), half=(0.5, 0.5, 0.5))
    return A, B


# name → (构造器, 真 overlap, 解析距离（贯入为 None）, 裕度 δ, 是否凸对（跑成员/G0/E）, 尺度 L)
PAIRS = {
    "tetra_box_vv": (_pair_tetra_box_vv, -1, 0.1, 0.2, True, 3.0),
    "box_box_face": (_pair_box_box_face, -1, 0.05, 0.1, True, 3.0),
    "generic": (_pair_generic, -1, None, 0.5, True, 5.0),
    "ve3_wedge": (_pair_ve3_wedge, -1, VE3_GAP, 10 * VE3_GAP, True, 4.0),
    "x_cross": (_pair_x_cross, 1, None, 0.05, True, 3.0),
    "stack_touch": (_pair_stack_touch, 0, 0.0, 0.05, True, 4.0),
    "sliver": (_pair_sliver, 1, None, 0.05, True, 3.0),
    # G6 第三轮（2026-10-10）：八路报出的三维 major 全坐在旧格子外——把它们的几何放进来
    "yaw_1e-5": (lambda: _pair_yaw(1e-5), -1, 0.1, 0.2, True, 4.0),
    "yaw_1e-3": (lambda: _pair_yaw(1e-3), -1, 0.1, 0.2, True, 4.0),
    "ridge_needle": (_pair_ridge_needle, -1, 0.05, 0.1, True, 5.0),
    "size_ratio": (_pair_size_ratio, -1, 1e-3, 2e-3, True, 100.0),
}
PAIR_NAMES = list(PAIRS)


@lru_cache(maxsize=None)
def _base(name: str):
    """恒等格（基准）：同一 API 在原位的结果，并对闭式真值自检。"""
    make, ov, d0, delta, convex, L = PAIRS[name]
    A, B = make()
    d, lab = body_distance(A, B)
    covs = [c for c in enumerate_covers3(A, B, window=float("inf"), tol=1e-9) if c.in_extent]
    labels = frozenset((c.label(), c.strict) for c in covs)
    wit = sorted(math.dist(c.point_a, c.point_b) for c in covs)
    dmin = wit[0] if wit else float("inf")
    ties = frozenset(c.label() for c in covs if math.dist(c.point_a, c.point_b) <= dmin + 1e-12)
    # 真距离：解析值；没有解析值的分离对用 brute_feature_distance（全特征对、零法锥筛选、只用坐标）
    truth = None if ov == 1 else (d0 if d0 is not None else brute_feature_distance(A, B))
    return dict(A=A, B=B, d=truth, lab=lab, labels=labels, ties=ties, dmin=dmin,
                facets=frozenset(local_facets3(A, B, 1e-12)))


@pytest.mark.parametrize("name", PAIR_NAMES)
def test_identity_cell_matches_closed_form(name):
    """基准格自身对闭式真值：overlap 判决、解析距离（最近对唯一时连标签）、贯入哨兵。"""
    make, ov, d0, delta, convex, L = PAIRS[name]
    base = _base(name)
    A, B = base["A"], base["B"]
    assert polyhedra_overlap(A, B, 1e-12) == ov
    d, lab = body_distance(A, B)
    if ov == 1:
        assert (d, lab) == (0.0, (PENETRATING,))
        return
    if d0 is not None:
        assert abs(d - d0) <= 1e-12, (d, d0, lab)
        assert abs(base["dmin"] - d0) <= 1e-12
    assert lab in base["ties"], lab
    if name == "tetra_box_vv":
        assert lab == ("VV3", ("vertex", 3), ("vertex", 2))
    if name == "ve3_wedge":
        assert lab[0] == "VE3" and lab[1] == ("vertex", 0), lab


def _cell(name, rot, tmag, s):
    base = _base(name)
    M = Motion(rot, tmag, s)
    return base, M, M.poly(base["A"]), M.poly(base["B"])


# ================================================================ 判定不变：polyhedra_overlap

@pytest.mark.parametrize("rot,tmag,s", CELLS, ids=CELL_IDS)
@pytest.mark.parametrize("name", PAIR_NAMES)
def test_overlap_verdict_is_invariant(name, rot, tmag, s):
    """默认 tol=0 与按单位缩放的 tol=1e-9·s 都必须给出同一判决（G6 critical 5、minor 7）。"""
    _, M, A, B = _cell(name, rot, tmag, s)
    want = PAIRS[name][1]
    assert polyhedra_overlap(A, B) == want, "default tol"
    assert polyhedra_overlap(A, B, 1e-9 * s) == want, "tol 1e-9*s"
    assert polyhedra_overlap(B, A, 1e-9 * s) == want, "argument order"


# ================================================================ 距离 ×s：body_distance

@pytest.mark.parametrize("rot,tmag,s", CELLS, ids=CELL_IDS)
@pytest.mark.parametrize("name", PAIR_NAMES)
def test_body_distance_scales_and_keeps_its_label(name, rot, tmag, s):
    base, M, A, B = _cell(name, rot, tmag, s)
    d, lab = body_distance(A, B)
    if PAIRS[name][1] == 1:
        assert (d, lab) == (0.0, (PENETRATING,))
        return
    L = PAIRS[name][5]
    assert abs(d - s * base["d"]) <= M.dist_tol(L), (d, s * base["d"], lab)
    assert lab in base["ties"], (lab, sorted(base["ties"]))


# ================================================================ 盖标签不变

@pytest.mark.parametrize("rot,tmag,s", CELLS, ids=CELL_IDS)
@pytest.mark.parametrize("name", PAIR_NAMES)
def test_cover_labels_and_strictness_are_invariant(name, rot, tmag, s):
    base, M, A, B = _cell(name, rot, tmag, s)
    covs = [c for c in enumerate_covers3(A, B, window=float("inf"), tol=1e-9) if c.in_extent]
    got = frozenset((c.label(), c.strict) for c in covs)
    expected_covers=independent_cover_labels(A,B,tol=1e-9)
    assert got==expected_covers, (sorted(got-expected_covers)[:6],sorted(expected_covers-got)[:6])
    facets = frozenset(local_facets3(A, B, 1e-12))
    # Convex models are exact hulls of each rounded input, not the ideal rotated
    # planes. Check every strict label against independent rational support sets.
    ca,cb=exact_convex_view(A),exact_convex_view(B)
    expected,_=exact_oracle.support_labels(tuple(ca.verts),tuple(ca.faces),tuple(cb.verts),tuple(cb.faces))
    assert facets==expected, (sorted(facets-expected),sorted(expected-facets))


# ================================================================ 成员判定与支撑间隙

def _displacements(name):
    """成员判定的采样位移（局部坐标）：固定种子，只取离边界清楚的点（|φ| 由基准格量）。"""
    rng = random.Random(77)
    return [(rng.uniform(-3, 3), rng.uniform(-3, 3), rng.uniform(-3, 3)) for _ in range(24)] + [(0.0, 0.0, 0.0)]


@pytest.mark.parametrize("rot,tmag,s", CELLS, ids=CELL_IDS)
@pytest.mark.parametrize("name", [n for n in PAIR_NAMES if PAIRS[n][4]])
def test_support_gaps_scale_and_membership_is_invariant(name, rot, tmag, s):
    base, M, A, B = _cell(name, rot, tmag, s)
    L = PAIRS[name][5]
    for x in _displacements(name):
        g0 = support_gaps3(base["A"], base["B"], x)
        g1 = support_gaps3(A, B, M.vec(x))
        ca,cb=exact_convex_view(A),exact_convex_view(B)
        # The rounded input may split one source face into several exact facets.
        # Each output plane, not just their maximum, has an independent value.
        expected=_support_gap_oracle(ca,cb,M.vec(x))
        assert len(g1)==len(expected)==len(ca.faces)+len(cb.faces)
        for actual,want_gap in zip(g1,expected):
            assert abs(actual-want_gap)<=32*EPS*max(abs(want_gap),s*L), (x,actual,want_gap)
        assert abs(max(g1)-s*max(g0))<=M.dist_tol(L), (x,g0,g1)
        assert membership_convex3(A,B,M.vec(x),0)==exact_oracle.overlap(tuple(A.verts),tuple(B.verts),M.vec(x))
        phi = max(g0)
        if abs(phi) > 1e-6:  # Boundary inputs above are checked exactly, not skipped.
            want = membership_convex3(base["A"], base["B"], x, 1e-9)
            assert membership_convex3(A, B, M.vec(x), 1e-9 * s) == want, (x, phi)


def _support_gap_oracle(A,B,x):
    """Inline Fraction support arithmetic; no production normal/plane helper."""
    av,bv=tuple(map(exact_oracle.qpoint,A.verts)),tuple(map(exact_oracle.qpoint,B.verts))
    x=exact_oracle.qpoint(x)
    result=[]
    for pts,faces,other,sign in ((bv,B.faces,av,1),(av,A.faces,bv,-1)):
        for face in faces:
            p,q,r=(pts[i] for i in face[:3])
            n=exact_oracle.wedge(exact_oracle.minus(q,p),exact_oracle.minus(r,p))
            if sign==1:
                v=min(exact_oracle.scalar(n,a) for a in other)+exact_oracle.scalar(n,x)-exact_oracle.scalar(n,p)
            else:
                v=min(exact_oracle.scalar(n,b) for b in other)-exact_oracle.scalar(n,x)-exact_oracle.scalar(n,p)
            scale=max(map(abs,n));u=tuple(float(c/scale) for c in n)
            result.append(float(v/scale)/math.sqrt(sum(c*c for c in u)))
    return result


# ================================================================ 裕度层（只调用，不改）

@pytest.mark.parametrize("rot,tmag,s", CELLS, ids=CELL_IDS)
@pytest.mark.parametrize("name", PAIR_NAMES)
def test_margin_layer_is_invariant(name, rot, tmag, s):
    base, M, A, B = _cell(name, rot, tmag, s)
    _, ov, _, delta, _, L = PAIRS[name]
    # 真值：贯入或真距离 < δ ⇒ 裕度违约（INSIDE）；否则 OUTSIDE（本文件的 δ 都离真距离很远）
    want_in = INSIDE if ov == 1 or base["d"] < delta else OUTSIDE
    assert inflated_membership(A, B, delta=s * delta) == want_in
    m1 = margin_contacts(A, B, delta=s * delta)
    if ov == 1:
        assert [m.label for m in m1] == [(PENETRATING,)]
        return
    if want_in == INSIDE:
        assert m1, "间距 < δ 却返回 []（= 裕度安全）：fail-unsafe"
    m0 = margin_contacts(base["A"], base["B"], delta=delta)
    # Rounded boundary features can become exactly strict/non-active. Instead
    # of preserving ideal labels, independently enumerate every local cover,
    # construct its witnesses and apply the existing margin selection contract.
    from e5a_cover_oracle import margin_selection
    expected = margin_selection(A, B, s * delta, touching=(ov == 0))
    expected_base = margin_selection(base["A"], base["B"], delta, touching=(ov == 0))
    current, original = {m.label: m for m in m1}, {m.label: m for m in m0}
    assert len(current) == len(m1) and len(original) == len(m0), "duplicate margin labels"
    assert set(current) == set(expected), (set(current) - set(expected), set(expected) - set(current))
    assert set(original) == set(expected_base)
    for label, contact in current.items():
        assert abs(contact.distance - expected[label]) <= M.dist_tol(L), (label, contact.distance, expected[label])
        assert contact.margin_gap == contact.distance - s * delta
    # Retain rigid-motion/scale distance checks, now matching physical feature
    # identities instead of zipping unrelated entries after labels split.
    for label in set(current) & set(original):
        assert abs(current[label].distance - s * original[label].distance) <= M.dist_tol(L), label


# ================================================================ 凸入口块（定理二的 oracle）与 G0 三票

@pytest.mark.parametrize("rot,tmag,s", CELLS, ids=CELL_IDS)
@pytest.mark.parametrize("name", [n for n in PAIR_NAMES if PAIRS[n][4]])
def test_entrance_block_scales(name, rot, tmag, s):
    base, M, A, B = _cell(name, rot, tmag, s)
    E0 = entrance_block_convex(base["A"], base["B"])
    E1 = entrance_block_convex(A, B)
    assert E1.manifold_issues() == [], E1.manifold_issues()[:3]
    assert E1.volume() == pytest.approx(s ** 3 * E0.volume(), rel=1e-7)
    if PAIRS[name][1] != 1:
        want = base["d"]
        got = distance_to_convex_entrance(E1, (0.0, 0.0, 0.0))
        assert abs(got - s * want) <= M.dist_tol(PAIRS[name][5]) + 1e-7 * s, (got, s * want)


@pytest.mark.parametrize("rot,tmag,s", G0_CELLS, ids=G0_IDS)
@pytest.mark.parametrize("name", ["tetra_box_vv", "box_box_face", "generic", "ve3_wedge"])
def test_g0_three_votes_are_invariant(name, rot, tmag, s):
    base = _base(name)
    rb = g0_convex3(base["A"], base["B"], samples=12, seed=1)
    assert rb.passed, rb
    _, M, A, B = _cell(name, rot, tmag, s)
    r = g0_convex3(A, B, samples=12, seed=1)
    assert r.passed, (r.mismatches[:2], r.facet_symmetric_diff[:4], r.hull_vertices, r.e_vertices)
    assert rb.facet_ambiguous == 0 and rb.e_vertices_ambiguous == 0
    p,f,_=exact_oracle.difference_hull(tuple(A.verts),tuple(B.verts))
    nv=len({i for face in f for i in face})
    ca,cb=exact_convex_view(A),exact_convex_view(B)
    labels,deg=exact_oracle.support_labels(tuple(ca.verts),tuple(ca.faces),tuple(cb.verts),tuple(cb.faces))
    assert r.e_vertices==r.hull_vertices==nv
    assert (r.facet_local,r.facet_global,r.facet_degenerate)==(len(labels),len(labels),deg)
    assert r.facet_ambiguous==r.facet_local_dropped==r.e_vertices_ambiguous==r.band_skipped==0
    assert r.samples==12+r.boundary_probes and r.boundary_checked==r.boundary_probes>0


@pytest.mark.parametrize("rot,tmag,s", CELLS, ids=CELL_IDS)
def test_merge_coplanar_face_count_is_invariant(rot, tmag, s):
    """G6 minor 8：三角化的方块归并回 6 个面，与位置、朝向、单位无关。"""
    M = Motion(rot, tmag, s)
    W = [M.point(p) for p in box(half=(1.0, 0.5, 0.3)).verts]
    H = merge_coplanar(convex_hull_3d(W))
    points,faces,_=exact_oracle.hull(tuple(W))
    expected={frozenset(points[i] for i in f) for f in faces}
    actual={frozenset(tuple(Fraction(c) for c in H.verts[i]) for i in f) for f in H.faces}
    assert actual==expected and H.manifold_issues()==[]
    assert len(merge_coplanar(convex_hull_3d(box(half=(1,.5,.3)).verts)).faces)==6
    assert H.volume() == pytest.approx(1.2 * s ** 3, rel=1e-7)


# ================================================================ G6 第三轮 minor：票二"说不清"带宽的牙

@pytest.mark.parametrize("tmag,amb,dropped,glob", [(1e5, 0, 0, 39), (1e6, 2, 2, 37)])
def test_vote_two_ambiguity_band_is_pinned_on_the_generic_cells(tmag, amb, dropped, glob):
    """保留原两格及历史参数，E5a 不再允许带宽豁免。

    独立精确支撑集在两格都要求39个严格facet；旧1e6格允许丢两个的口径已删除。
    """
    base = _base("generic")
    M = Motion(7, tmag, 1e-3)
    A,B=M.poly(base["A"]),M.poly(base["B"])
    r = g0_convex3(A,B, samples=12, seed=1)
    ca,cb=exact_convex_view(A),exact_convex_view(B)
    expected,deg=exact_oracle.support_labels(tuple(ca.verts),tuple(ca.faces),tuple(cb.verts),tuple(cb.faces))
    assert r.passed and (r.facet_ambiguous,r.facet_local_dropped,r.e_vertices_ambiguous)==(0,0,0),r
    assert r.facet_global==r.facet_local==len(expected)==39
    assert r.facet_degenerate==deg
