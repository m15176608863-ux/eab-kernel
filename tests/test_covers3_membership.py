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
    """退化输入上 conv{b − a} 的三角网格会保留落在 facet 内部/棱上的点——它们不是 E 的顶点。
    票三必须只数极点：tetra vs box 的 E 恰有 13 个顶点（上面的精确枚举），box vs box 恰 8 个。"""
    truth = _vertices_of_tetra_box_E()
    assert len(truth) == 13
    from eab.kernel3d.g03 import _hull_extreme_vertices
    from eab.kernel3d.geom3 import convex_hull_3d, sub
    T, B = _tetra(), box(half=(1.0, 1.0, 1.0))
    hull = convex_hull_3d([sub(b, a) for a in T.verts for b in B.verts], tol=1e-12)
    got = {tuple(round(c, 7) + 0.0 for c in v) for v in _hull_extreme_vertices(hull)}
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
