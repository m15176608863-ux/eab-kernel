"""凸成员谓词 `membership_convex3` 在**退化（非一般位置）**输入上的门——审查 C2（critical）。

缺陷：成员谓词只对 strict=True 的 facet 取 max。凡 E 的 facet 由平行面（FF）或
棱平行于面（FE）生成，都是非严格的，被整个丢掉：四面体 vs 方块在 +x 侧判"相交"
（t = 1.5/2/3 明明分离），两个轴对齐方块直接对空集取 max 崩溃。

**oracle（纪律 A）**：闭式解析判据，不调用 geom3 / covers3 的任何原语。
  四面体 T_s = {p ≥ 0, Σp ≤ s} 平移 x 后与方块 B = {|p − c| ≤ h}：
      φ(x) = max( max_i (x_i − c_i − h_i),  Σ_i max(0, c_i − h_i − x_i) − s )
  φ < 0 ⟺ 内部相交；φ > 0 ⟺ 分离；φ = 0 ⟺ 仅相触。
  推导：A+x = {p ≥ x, Σ(p − x) ≤ s}；在 B 内能取到的 Σ(p − x) 下确界为
  Σ max(0, c_i − h_i − x_i)，且需 x_i ≤ c_i + h_i 才可行。
  两方块：E 是以 c_B − c_A 为心、半宽 h_A + h_B 的方块，同样闭式。

纪律 B：分界点（t = 1.0 恰相触、t = −2.0 恰相触）、非对称输入（非均匀半宽、偏心方块、
一般位置随机平移）、尺度 ×1e-3 / ×1 / ×1e3。
"""

import math
import random

import pytest

from eab.kernel3d.covers3 import local_facets3, membership_convex3
from eab.kernel3d.g03 import g0_convex3
from eab.kernel3d.geom3 import box, tetra


def _tetra(s: float = 1.0):
    return tetra((0.0, 0.0, 0.0), (s, 0.0, 0.0), (0.0, s, 0.0), (0.0, 0.0, s))


def _phi_tetra_box(x, s, c, h) -> float:
    """解析判据 φ（见模块文档）。只用算术。"""
    upper = max(x[i] - c[i] - h[i] for i in range(3))
    lower = sum(max(0.0, c[i] - h[i] - x[i]) for i in range(3)) - s
    return max(upper, lower)


def _phi_box_box(x, ca, ha, cb, hb) -> float:
    """A+x 与 B（均轴对齐方块）：φ = max_i (|x_i − (cb_i − ca_i)| − (ha_i + hb_i))。"""
    return max(abs(x[i] - (cb[i] - ca[i])) - (ha[i] + hb[i]) for i in range(3))


def _sign(phi: float) -> int:
    return 1 if phi < 0 else (-1 if phi > 0 else 0)


# ---------------------------------------------------------------- 审查原例

@pytest.mark.parametrize("t,want", [
    (-3.0, -1), (-2.5, -1), (-2.0, 0), (-1.5, 1), (-1.0, 1), (0.0, 1), (0.5, 1),
    (0.999, 1), (1.0, 0), (1.001, -1), (1.5, -1), (2.0, -1), (3.0, -1),
])
def test_membership_tetra_vs_box_sweep_along_x(t, want):
    """审查复现：t ≥ 1.0 全判"相交"。t = 1.0 与 t = −2.0 是分界点（恰相触 → 0）。"""
    T, B = _tetra(), box(half=(1.0, 1.0, 1.0))
    x = (t, 0.0, 0.0)
    assert _sign(_phi_tetra_box(x, 1.0, (0.0, 0.0, 0.0), (1.0, 1.0, 1.0))) == want   # oracle 自检
    assert membership_convex3(T, B, x, 1e-9) == want, (t, want)


def test_membership_axis_aligned_boxes_does_not_crash():
    """两个轴对齐方块：严格 facet 集合为空（全部 FF 退化），旧实现对空集取 max 抛 ValueError。"""
    a, b = box(half=(1.0, 1.0, 1.0)), box(half=(2.0, 2.0, 2.0))
    assert local_facets3(a, b, 1e-12) == set()               # 前提：确实全退化
    assert membership_convex3(a, b, (5.0, 0.0, 0.0), 1e-9) == -1
    assert membership_convex3(a, b, (3.0, 0.0, 0.0), 1e-9) == 0
    assert membership_convex3(a, b, (2.9, -2.9, 2.9), 1e-9) == 1


# ---------------------------------------------------------------- 一般位置 + 尺度

@pytest.mark.parametrize("scale", [1e-3, 1.0, 1e3])
@pytest.mark.parametrize("seed", range(2))
def test_membership_tetra_vs_offcenter_box_matches_closed_form(scale, seed):
    """非均匀半宽、偏心方块、四面体边长 ≠ 方块边长；随机平移 vs 解析 φ。"""
    s = 0.8 * scale
    c = (0.3 * scale, -0.2 * scale, 0.1 * scale)
    h = (1.0 * scale, 0.6 * scale, 1.7 * scale)
    T = _tetra(s)
    B = box(center=c, half=h)
    rng = random.Random(seed)
    n_in = n_out = 0
    for _ in range(300):
        x = tuple(rng.uniform(c[i] - h[i] - 1.3 * s, c[i] + h[i] + 0.3 * s) for i in range(3))
        phi = _phi_tetra_box(x, s, c, h)
        if abs(phi) < 1e-7 * scale:
            continue
        want = _sign(phi)
        got = membership_convex3(T, B, x, 1e-10 * scale)
        assert got == want, (x, phi, got)
        n_in += want == 1
        n_out += want == -1
    assert n_in > 30 and n_out > 30, (n_in, n_out)          # 两侧都真被采到


@pytest.mark.parametrize("scale", [1e-3, 1.0, 1e3])
def test_membership_box_vs_box_matches_closed_form(scale):
    ca, ha = (0.1 * scale, 0.0, -0.4 * scale), (0.5 * scale, 1.2 * scale, 0.3 * scale)
    cb, hb = (-0.2 * scale, 0.7 * scale, 0.0), (1.0 * scale, 0.4 * scale, 0.9 * scale)
    A, B = box(center=ca, half=ha), box(center=cb, half=hb)
    rng = random.Random(7)
    seen = set()
    for _ in range(300):
        x = tuple(rng.uniform(-2.5 * scale, 2.5 * scale) for _ in range(3))
        phi = _phi_box_box(x, ca, ha, cb, hb)
        if abs(phi) < 1e-7 * scale:
            continue
        want = _sign(phi)
        assert membership_convex3(A, B, x, 1e-10 * scale) == want, (x, phi)
        seen.add(want)
    assert seen == {1, -1}


# ---------------------------------------------------------------- 支撑半空间本身的性质

def _pairs():
    from eab.kernel3d.geom3 import convex_hull_3d
    rng = random.Random(11)
    out = [(_tetra(), box(half=(1.0, 1.0, 1.0))),
           (box(half=(1.0, 1.0, 1.0)), box(center=(0.3, 0.0, -0.2), half=(2.0, 0.5, 1.0)))]
    for _ in range(3):
        out.append(tuple(convex_hull_3d([tuple(rng.uniform(-1, 1) for _ in range(3)) for _ in range(8)])
                         for _ in range(2)))
    return out


@pytest.mark.parametrize("k", range(5))
def test_support_gaps_are_supporting_half_spaces(k):
    """support_gaps3 的每一条都**含 E 且贴着 E**：E 的每个点 x = b − a（差点，纯坐标构造）
    都满足全部间隙 ≤ 0，且每一条间隙都在某个差点处取到 0。"""
    from eab.kernel3d.covers3 import support_gaps3
    from eab.kernel3d.geom3 import sub
    A, B = _pairs()[k]
    diffs = [sub(b, a) for a in A.verts for b in B.verts]
    G = [support_gaps3(A, B, x) for x in diffs]
    m = len(G[0])
    assert m == len(A.faces) + len(B.faces)
    for j in range(m):
        col = [g[j] for g in G]
        assert max(col) <= 1e-12, (j, max(col))
        assert abs(max(col)) <= 1e-12, (j, max(col))            # 贴着：取到 0


def test_vote1_catches_a_wrong_facet_label(monkeypatch):
    """membership_convex3 的文档声称：facets 里的错标签只会把答案推向"外部"，从而被票一抓住。
    注入一个非支撑的 VF 标签（离支撑顶点最远的那个 A 顶点 × 某 B 面），票一必须报失配。"""
    import eab.kernel3d.g03 as g03
    from eab.kernel3d.geom3 import dot
    A, B = _pairs()[2]
    full = local_facets3(A, B, 1e-12)
    n = B.face_normal(0)
    ia = max(range(len(A.verts)), key=lambda i: dot(n, A.verts[i]))  # 最不该配这个面的顶点
    bogus = ("VF", ("vertex", ia), ("face", 0))
    assert bogus not in full
    monkeypatch.setattr(g03, "local_facets3", lambda a, b, t: set(full) | {bogus})
    rep = g0_convex3(A, B, samples=200, seed=3)
    assert rep.mismatches, rep
    assert all(brute == 1 and cov == -1 for _, brute, cov in rep.mismatches)   # 只会错判成"外部"


# ---------------------------------------------------------------- G0 门在退化几何上

def test_g0_convex3_tetra_vs_box_has_zero_mismatches():
    """审查：g0_convex3(tetra, box) 报 57/200 失配。"""
    rep = g0_convex3(_tetra(), box(half=(1.0, 1.0, 1.0)), samples=200, seed=0)
    assert rep.mismatches == [], rep.mismatches[:3]
    assert rep.samples > 100, rep
    assert rep.passed, rep


def _vertices_of_tetra_box_E():
    """E(T, [−1,1]³) 的顶点，独立地由 φ 的线性不等式组枚举（Fraction 精确，三平面求交 + 可行性）。
    φ ≤ 0 ⟺ x_i ≤ 1、x_i ≥ −2、−x_i − x_j ≤ 3、−Σx ≤ 4（共 10 个 facet）。"""
    from fractions import Fraction as Fr
    from itertools import combinations
    e = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
    cons = [(e[i], 1) for i in range(3)] + [(tuple(-c for c in e[i]), 2) for i in range(3)]
    cons += [(tuple(-(e[i][k] + e[j][k]) for k in range(3)), 3) for i, j in combinations(range(3), 2)]
    cons += [((-1, -1, -1), 4)]

    def det(m):
        return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
                + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))

    pts = set()
    for tri in combinations(cons, 3):
        M = [[Fr(c) for c in a] for a, _ in tri]
        D = det(M)
        if D == 0:
            continue
        x = []
        for k in range(3):
            Mk = [row[:] for row in M]
            for r in range(3):
                Mk[r][k] = Fr(tri[r][1])
            x.append(det(Mk) / D)
        if all(sum(a[k] * x[k] for k in range(3)) <= b for a, b in cons):
            pts.add(tuple(x))
    return pts


def test_g0_vote3_counts_only_extreme_points_on_degenerate_input():
    """退化输入（64 个差点里大量落在 facet 内部/棱上）：凸包的**顶点集**必须恰是 E 的顶点集——
    tetra vs box 的 E 恰有 13 个顶点（上面的精确枚举），box vs box 恰 8 个。旧 Quickhull 把共面/共线点留作三角
    网格顶点、靠一道"极点筛"补救；M0.3 起凸包自己保证（全局最远者优先 + 并列按离质心最远裁决 + 细条面兜底）。"""
    truth = _vertices_of_tetra_box_E()
    assert len(truth) == 13
    from eab.kernel3d.geom3 import convex_hull_3d, sub
    T, B = _tetra(), box(half=(1.0, 1.0, 1.0))
    hull = convex_hull_3d([sub(b, a) for a in T.verts for b in B.verts], tol=1e-12)
    got = {tuple(round(c, 7) + 0.0 for c in v) for v in hull.verts}
    assert got == {tuple(float(c) for c in p) for p in truth}
    rep = g0_convex3(_tetra(), box(half=(1.0, 1.0, 1.0)), samples=0)
    assert rep.hull_vertices == rep.e_vertices == 13 and rep.hull_vertex_mismatch == 0, rep
    rep = g0_convex3(box(half=(1.0, 1.0, 1.0)), box(half=(2.0, 0.5, 1.5)), samples=0)
    assert rep.hull_vertices == rep.e_vertices == 8 and rep.hull_vertex_mismatch == 0, rep


def test_g0_convex3_box_vs_box_runs_and_passes():
    """cb2 同构的堆叠方块几何（phase-2 报告宣称覆盖）：旧实现直接 ValueError。"""
    rep = g0_convex3(box(half=(1.0, 1.0, 1.0)), box(center=(0.2, -0.1, 0.3), half=(2.0, 1.5, 0.7)),
                     samples=200, seed=0)
    assert rep.mismatches == [], rep.mismatches[:3]
    assert rep.samples > 100, rep
    assert rep.passed, rep


# ---------------------------------------------------------------- G6 critical 26：旋转后的平行面退化对
#
# 缺陷（covers3.py:155）：closest_point_of_convex_hull_to_origin 只在 |v0| ≤ 1e-300 时跳过四点单形。
# 平行面/平行棱的退化对一旦不轴对齐，锥生成元"平行到舍入"，四点单形的 v0 ~ 1e-17，重心坐标是噪声，
# 可以报"原点在内"——于是 cone_relint_direction 说锥空，cones_intersect_relint 假，VV3 与别的
# E 顶点消失：body_distance 返回 (inf, None)、inflated_membership 判错、G0 票三 10 个旋转里红 9 个。
# 审查的复现用 random.Random(seed) 直接生成四元数（种子 3、9 最坏）；这里沿用同一生成器。
#
# oracle（纪律 A）：E(T, B) 的 13 个顶点由上面 _vertices_of_tetra_box_E 用 Fraction 精确枚举
# （旋转不改变个数）；VV3 最近对的距离 0.1 是构造给定的（n 严格在两锥内部，见 test_invariance_geom）；
# 方块对方块的距离是逐轴间隙的欧氏范数（闭式）。都不经 covers3。

def _g6_rotation(seed: int):
    rng = random.Random(seed)
    q = [rng.gauss(0.0, 1.0) for _ in range(4)]
    n = math.sqrt(sum(c * c for c in q))
    w, x, y, z = (c / n for c in q)
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


def _rotated(P, R, s=1.0, t=(0.0, 0.0, 0.0)):
    from eab.kernel3d.geom3 import Polyhedron
    return Polyhedron([tuple(t[i] + s * (R[i][0] * p[0] + R[i][1] * p[1] + R[i][2] * p[2]) for i in range(3))
                       for p in P.verts], list(P.faces))


def _apply(R, v):
    return tuple(R[i][0] * v[0] + R[i][1] * v[1] + R[i][2] * v[2] for i in range(3))


@pytest.mark.parametrize("seed", range(3, 13))
def test_rotated_tetra_box_keeps_every_E_vertex_and_the_vv3_pair(seed):
    from eab.kernel3d.covers3 import cones_intersect_relint
    from eab.margin import INSIDE, OUTSIDE, body_distance, inflated_membership
    R = _g6_rotation(seed)
    T1, B1 = _rotated(_tetra(), R), _rotated(box(half=(1.0, 1.0, 1.0)), R)
    rep = g0_convex3(T1, B1, samples=60, seed=seed)
    assert rep.hull_vertices == rep.e_vertices == 13 and rep.hull_vertex_mismatch == 0, rep
    assert (rep.facet_local, rep.facet_global, rep.facet_degenerate) == (7, 7, 3), rep
    assert rep.mismatches == [] and rep.passed, rep
    assert cones_intersect_relint(T1, 3, B1, 2)
    r3 = 1.0 / math.sqrt(3.0)
    n = _apply(R, (r3, r3, -r3))
    X = tuple(B1.verts[2][i] + 0.1 * n[i] - T1.verts[3][i] for i in range(3))
    A = T1.translated(X)
    d, lab = body_distance(A, B1)
    assert abs(d - 0.1) <= 1e-12 and lab == ("VV3", ("vertex", 3), ("vertex", 2)), (d, lab)
    assert inflated_membership(A, B1, delta=0.2) == INSIDE
    assert inflated_membership(A, B1, delta=0.05) == OUTSIDE


@pytest.mark.parametrize("seed", range(3, 13))
def test_rotated_box_box_passes_the_three_votes(seed):
    R = _g6_rotation(seed)
    A = _rotated(box(half=(1.0, 1.0, 1.0)), R)
    B = _rotated(box(center=(0.3, 0.0, -0.2), half=(2.0, 0.5, 1.0)), R)
    rep = g0_convex3(A, B, samples=60, seed=seed)
    assert (rep.facet_local, rep.facet_global, rep.facet_degenerate) == (0, 0, 6), rep
    assert rep.hull_vertices == rep.e_vertices == 8 and rep.hull_vertex_mismatch == 0, rep
    assert rep.mismatches == [] and rep.passed, rep
    # 距离：同一旋转下 B 心 (3.5, 0.2, −2.9)、半宽 (2, 0.5, 3)，只有 x 向有缝 ⇒ 间距 0.5（闭式，
    # 面-面平行，最近对大量并列）；裕度层按它判违约 / 安全
    from eab.margin import INSIDE, OUTSIDE, body_distance, inflated_membership
    B2 = _rotated(box(center=(3.5, 0.2, -2.9), half=(2.0, 0.5, 3.0)), R)
    d, lab = body_distance(A, B2)
    assert abs(d - 0.5) <= 1e-12 and lab is not None, (d, lab)
    assert inflated_membership(A, B2, delta=0.6) == INSIDE
    assert inflated_membership(A, B2, delta=0.4) == OUTSIDE


@pytest.mark.parametrize("scale", [1e-3, 1.0, 1e3])
@pytest.mark.parametrize("seed", range(2, 8))
def test_closest_point_on_raw_minkowski_points_matches_the_box_distance(seed, scale):
    """G6 的旁证：原始 64 个 Minkowski 差点（大量共面共线）上，原点到凸包的距离相对误差 5.98。
    闭式：A = [−1,1]³、B 心 (3.5, 0.2, −2.9) 半宽 (2, 0.5, 3)，同一旋转下间距 = 0.5（只有 x 向有缝）。"""
    from eab.kernel3d.covers3 import closest_point_of_convex_hull_to_origin
    from eab.kernel3d.geom3 import norm, sub
    R = _g6_rotation(seed)
    A = _rotated(box(half=(1.0, 1.0, 1.0)), R, scale)
    B = _rotated(box(center=(3.5, 0.2, -2.9), half=(2.0, 0.5, 3.0)), R, scale)
    p = closest_point_of_convex_hull_to_origin([sub(b, a) for a in A.verts for b in B.verts])
    assert abs(norm(p) - 0.5 * scale) <= 1e-9 * scale, (norm(p), 0.5 * scale)
    # 原点在凸包内部（两块相交）时必须恰返回零向量
    B2 = _rotated(box(center=(1.5, 0.2, -0.9), half=(2.0, 0.5, 3.0)), R, scale)
    p2 = closest_point_of_convex_hull_to_origin([sub(b, a) for a in A.verts for b in B2.verts])
    assert norm(p2) == 0.0


@pytest.mark.parametrize("s", [1.0, 1e3])
def test_membership_without_facets_keeps_length_and_angle_apart(s):
    """G6 第二轮 minor：不给 facets 时，旧版把长度带 tol 同时当局部 facet 的角容差——tol = 1e-3·s、s = 1e3 时角容差
    1 rad，严格 EE facet 全被丢，分离的一对判"相交"（600 个随机偏移里 8 个）。oracle：暴力谓词 polyhedra_overlap。"""
    import random as _r

    from eab.kernel3d.geom3 import Polyhedron, box, mul, polyhedra_overlap, tetra
    rng = _r.Random(4)
    q = [rng.gauss(0, 1) for _ in range(4)]
    n = math.sqrt(sum(c * c for c in q))
    w, x, y, z = (c / n for c in q)
    R = ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
         (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
         (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))
    T = tetra((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    A = Polyhedron([mul(tuple(sum(R[i][j] * v[j] for j in range(3)) for i in range(3)), s) for v in T.verts],
                   list(T.faces))
    B0 = box(half=(1.0, 0.7, 0.5))
    B = Polyhedron([mul(v, s) for v in B0.verts], list(B0.faces))
    tol = 1e-3 * s
    rng = _r.Random(9)
    wrong, n_cmp = [], 0
    for _ in range(600):
        xo = mul(tuple(rng.uniform(-2.5, 2.5) for _ in range(3)), s)
        brute = polyhedra_overlap(A.translated(xo), B, tol)
        got = membership_convex3(A, B, xo, tol)
        if brute != 0 and got != 0:
            n_cmp += 1
            if brute != got:
                wrong.append((xo, brute, got))
    assert n_cmp > 500 and wrong == [], (n_cmp, len(wrong), wrong[:2])
