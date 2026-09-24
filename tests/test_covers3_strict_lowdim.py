"""一维盖 VE3 / EV3 的 strict 字段与"低维盖不按 strict 过滤"——审查 C10。

缺陷：`ve3_cover` / `ev3_cover` 把 strict 写成字面量 True（违反 Cover3.strict 的契约
"法锥相对内部条件严格成立"），于是 `enumerate_covers3` 对低维盖的 `c.strict` 过滤是死代码。
审查实测：**只把 strict 算对而保留过滤**会破坏距离完备性——平行棱-棱最近对（EEP 退化）
只由边界态 VE3/EV3 表达（ee_cover 对平行棱返回 None），过滤一有牙就把它滤掉。

所以这里有两道门：
  1. strict 如实：轴对齐几何的边界态 → False；一般位置 → True；
  2. 距离完备性不依赖 strict：边界态 VE3/EV3 必须仍被枚举出来，且最小见证距离 == 解析距离。
     （这一条在旧代码上是绿的——字面量 True 让它侥幸通过；它守的是"只修一半"的回归。）

oracle（纪律 A）：
  · strict 的真值由解析论证给出（写在各测试里），不调用 edge_arc_contains / vertex_cone_contains；
  · 两个轴对齐方块的距离 = 各轴间隙的欧氏范数（闭式），不调用 brute_feature_distance。
纪律 B：分界（gy = gz 对称、gy ≠ gz 非对称、一个间隙 1e-3 很小）、尺度 ×1e-3 / ×1 / ×1e3。
"""

import math

import pytest

from eab.kernel3d.covers3 import enumerate_covers3, ev3_cover, ve3_cover
from eab.kernel3d.geom3 import add, box, mul, norm, sub, tetra, unit


def _diag_pair(gy: float, gz: float, s: float):
    """B = [−1,1]³·s；A 是 x 向完全落在 B 的 x 范围内的小方块，其 (y_min, z_min) 棱
    恰在 B 的 (y=1, z=1) 棱外侧 (gy, gz)·s 处。两棱平行（都沿 x），最近对只能由
    A 的棱端点 × B 的棱（VE3）表达；B 的棱端点投影落在 A 的棱段外（EV3 in_extent=False）。

    解析距离 = s·hypot(gy, gz)。
    strict 的解析真值：分离方向 n ∝ (0, gy, gz)。B 的棱弧是 +y 到 +z 的四分之一圆，
    gy, gz > 0 ⇒ n 在弧的相对内部；A 棱端点的法锥是卦限 (∓x, −y, −z)，−n 的 x 分量为 0
    ⇒ −n 落在该锥的**面**上（边界）⇒ strict 必为 False。
    """
    B = box(half=(s, s, s))
    hy, hz = 0.3 * s, 0.35 * s
    A = box(center=(0.2 * s, s + gy * s + hy, s + gz * s + hz), half=(0.4 * s, hy, hz))
    return A, B, s * math.hypot(gy, gz)


PARAMS = [(0.3, 0.3), (0.2, 0.05), (1e-3, 0.7)]
SCALES = [1e-3, 1.0, 1e3]


@pytest.mark.parametrize("scale", SCALES)
@pytest.mark.parametrize("gy,gz", PARAMS)
def test_parallel_edge_edge_nearest_pair_ve3_is_boundary_state(gy, gz, scale):
    A, B, dist = _diag_pair(gy, gz, scale)
    covs = [c for c in enumerate_covers3(A, B, window=float("inf"), tol=1e-9 * scale) if c.in_extent]
    ve3 = [c for c in covs if c.kind == "VE3" and abs(norm(sub(c.point_a, c.point_b)) - dist) <= 1e-9 * scale]
    assert ve3, [(c.kind, c.strict, norm(sub(c.point_a, c.point_b))) for c in covs]
    for c in ve3:
        assert c.strict is False, c.label()                 # 边界态：如实报非严格


@pytest.mark.parametrize("scale", SCALES)
@pytest.mark.parametrize("gy,gz", PARAMS)
def test_parallel_edge_edge_nearest_pair_ev3_is_boundary_state(gy, gz, scale):
    """同一几何交换 A/B：最近对变成 EV3（A 的棱 × B 的顶点）。"""
    Asmall, Bbig, dist = _diag_pair(gy, gz, scale)
    covs = [c for c in enumerate_covers3(Bbig, Asmall, window=float("inf"), tol=1e-9 * scale)
            if c.in_extent]
    ev3 = [c for c in covs if c.kind == "EV3" and abs(norm(sub(c.point_a, c.point_b)) - dist) <= 1e-9 * scale]
    assert ev3, [(c.kind, c.strict, norm(sub(c.point_a, c.point_b))) for c in covs]
    for c in ev3:
        assert c.strict is False, c.label()


@pytest.mark.parametrize("scale", SCALES)
@pytest.mark.parametrize("gy,gz", PARAMS)
def test_distance_completeness_does_not_depend_on_strict(gy, gz, scale):
    """最小见证距离 == 解析距离（两个方向都测）。若有人把 strict 算对却保留低维盖的
    strict 过滤，这里 VE3/EV3 被滤掉，最小见证距离变成 inf 或偏大——必红。"""
    A, B, dist = _diag_pair(gy, gz, scale)
    for P, Q in ((A, B), (B, A)):
        covs = [c for c in enumerate_covers3(P, Q, window=float("inf"), tol=1e-9 * scale) if c.in_extent]
        got = min((norm(sub(c.point_a, c.point_b)) for c in covs), default=float("inf"))
        assert abs(got - dist) <= 1e-9 * max(scale, dist), (got, dist)


def test_stacked_boxes_corner_over_edge_is_not_strict():
    """审查原例：上块角点正悬在下块棱上方 0.05（法向 +z）。弧判据 = 0（+z 是弧端点），
    锥判据 = 0（−z 是卦限的棱）⇒ VE3 与同角点的 VF/EE 一样 strict=False。"""
    lower = box(center=(0.0, -3.0, -1.0), half=(2.0, 2.0, 1.0))     # 顶棱 y=−1, z=0 沿 x
    upper = box(center=(0.0, 0.0, 1.05), half=(1.0, 1.0, 1.0))      # 顶点 0 = (−1, −1, 0.05)
    e = next(e for e in lower.edges()
             if all(lower.verts[i][1] == -1.0 and lower.verts[i][2] == 0.0 for i in e))
    c = ve3_cover(upper, 0, lower, e, 1e-12)
    assert c is not None and abs(c.gap - 0.05) < 1e-12 and abs(c.normal[2] - 1.0) < 1e-12
    assert c.strict is False
    covs = enumerate_covers3(upper, lower, window=1.0, tol=1e-12)
    low = [c for c in covs if c.kind in ("VE3", "EV3")]
    assert low, [c.label() for c in covs]
    assert not any(c.strict for c in low), [(c.label(), c.strict) for c in low]
    # 对称：交换角色，同一对特征以 EV3 出现，同样非严格
    c2 = ev3_cover(lower, e, upper, 0, 1e-12)
    assert c2 is not None and c2.strict is False


@pytest.mark.parametrize("scale", SCALES)
def test_generic_vertex_over_edge_is_strict(scale):
    """一般位置：四面体顶点沿 n = unit(0,1,1) 悬在方块棱外 0.05。
    解析真值：n 严格在棱弧 (+y, +z) 内；顶点三条入射棱 e_i = n + 小扰动，(−n)·e_i ≈ −1 < 0
    ⇒ −n 严格在顶点法锥内 ⇒ strict = True。"""
    s = scale
    lower = box(center=(0.0, -3.0 * s, -1.0 * s), half=(2.0 * s, 2.0 * s, 1.0 * s))
    e = next(e for e in lower.edges()
             if all(abs(lower.verts[i][1] + s) < 1e-15 * s and abs(lower.verts[i][2]) < 1e-15 * s for i in e))
    n = unit((0.0, 1.0, 1.0))
    apex = add((0.0, -s, 0.0), mul(n, 0.05 * s))
    T = tetra(apex, add(apex, add(mul(n, s), (0.3 * s, 0.0, 0.0))),
              add(apex, add(mul(n, s), (-0.3 * s, 0.0, 0.0))),
              add(apex, add(mul(n, s), (0.0, 0.3 * s, -0.3 * s))))
    ia = T.verts.index(apex)
    c = ve3_cover(T, ia, lower, e, 1e-12 * s)
    assert c is not None and abs(c.gap - 0.05 * s) < 1e-9 * s
    assert c.strict is True
    c2 = ev3_cover(lower, e, T, ia, 1e-12 * s)
    assert c2 is not None and c2.strict is True


# ================================================================ G6 critical 6：小间隙、工程坐标下的 VE3 / EV3
#
# 缺陷（covers3.py:80）：ve3_cover / ev3_cover 用 unit(a − q) 造分离方向，q = p0 + d·s 的舍入给出
# ∝ eps·|坐标|/间隙 的**棱向分量**；edge_arc_contains 对单位向量的正交性用绝对容差 tol + 1e-12，
# 于是间隙 < 1e-7（原点）或 < 1e-5（坐标 1e3）时真最近对被拒，body_distance 报 2.0000001 而非 1e-7，
# margin_contacts 返回 []、inflated_membership 答 OUTSIDE——在裕度层存在的那个近接触区间里 fail-unsafe。
#
# oracle（纪律 A）：解析距离 = g（楔的屋脊沿 x；棱锥尖端悬在屋脊正上方 g，投影落在屋脊段内；
# 两坡面 45°，尖端到坡面平面的投影落在坡面之外 ⇒ 最近特征就是屋脊）。不调用任何距离原语。
# 纪律 B：间隙 1e-5 / 1e-7 / 1e-9（分界：原点处的旧失效点 1e-7）、非轴对齐（随机旋转）、
# 工程坐标（平移 1e3，含非轴对齐方向）、两个参数顺序（VE3 与 EV3）。

import random as _random  # noqa: E402

from eab.kernel3d.geom3 import Polyhedron, convex_hull_3d, merge_coplanar  # noqa: E402
from eab.margin import INSIDE, OUTSIDE, body_distance, inflated_membership, margin_contacts  # noqa: E402


def _rot(seed: int):
    if seed == 0:
        return ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    rng = _random.Random(6100 + seed)
    q = [rng.gauss(0.0, 1.0) for _ in range(4)]
    n = math.sqrt(sum(c * c for c in q))
    w, x, y, z = (c / n for c in q)
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


def _ridge_and_spike(g: float, seed: int, t):
    """B：屋脊沿 x、坡 45° 的楔（面已归并）；A：尖端 (0.3, 0, g) 朝下的细棱锥。整体经旋转 + 平移。
    返回 (A, B, 尖端下标, 屋脊棱)。编号在变换前定好，变换只动坐标。"""
    B0 = merge_coplanar(convex_hull_3d([(x, y, z) for x in (-2.0, 2.0)
                                        for (y, z) in ((0.0, 0.0), (-1.0, -1.0), (1.0, -1.0))]))
    c, s = math.cos(0.5), math.sin(0.5)
    apex = (0.3, 0.0, g)
    A0 = Polyhedron([apex] + [(0.3 + c * x - s * y, s * x + c * y, g + 1.0)
                              for x, y in ((0.2, 0.0), (-0.1, 0.17), (-0.1, -0.17))],
                    [(0, 2, 1), (0, 3, 2), (0, 1, 3), (1, 2, 3)])
    assert A0.volume() > 0
    ridge = next(e for e in B0.edges() if B0.verts[e[0]][2] == 0.0 and B0.verts[e[1]][2] == 0.0)
    R = _rot(seed)

    def mv(P):
        return Polyhedron([tuple(t[i] + R[i][0] * p[0] + R[i][1] * p[1] + R[i][2] * p[2] for i in range(3))
                           for p in P.verts], list(P.faces))
    return mv(A0), mv(B0), 0, ridge


SMALL_GAP_PLACEMENTS = [(0, (0.0, 0.0, 0.0)), (3, (0.0, 0.0, 0.0)), (0, (1000.0, 0.0, 0.0)),
                        (0, (1000.0, 700.0, 300.0)), (1, (1000.0, 700.0, 300.0)), (2, (-600.0, 800.0, 20.0))]


@pytest.mark.parametrize("seed,t", SMALL_GAP_PLACEMENTS,
                         ids=[f"R{a}-t{max(abs(c) for c in b):g}" for a, b in SMALL_GAP_PLACEMENTS])
@pytest.mark.parametrize("g", [1e-5, 1e-7, 1e-9])
def test_small_gap_vertex_over_ridge_keeps_the_true_nearest_pair(g, seed, t):
    A, B, apex, ridge = _ridge_and_spike(g, seed, t)
    noise = 1e3 * 2.220446049250313e-16 * (max(abs(c) for c in t) + 4.0)
    tol = 1e-12                                   # 间隙 1e-9 时显式取更小的 tol，否则按"相触"处理
    c = ve3_cover(A, apex, B, ridge, tol)
    assert c is not None, "真最近对 VE3 被拒"
    assert abs(c.gap - g) <= noise and c.in_extent and c.strict
    for X, Y, kind in ((A, B, "VE3"), (B, A, "EV3")):
        d, lab = body_distance(X, Y, tol=tol, geom_tol=tol)
        assert abs(d - g) <= noise, (d, g, lab)
        assert lab is not None and lab[0] == kind, lab
        # 裕度层：间距 < δ 绝不能答"安全"；δ < 间距则是真安全
        assert inflated_membership(X, Y, delta=10 * g, tol=tol, geom_tol=tol) == INSIDE
        assert margin_contacts(X, Y, delta=10 * g, tol=tol, geom_tol=tol)
        assert inflated_membership(X, Y, delta=0.5 * g, tol=tol, geom_tol=tol) == OUTSIDE


@pytest.mark.parametrize("seed,t", SMALL_GAP_PLACEMENTS[:4],
                         ids=[f"R{a}-t{max(abs(c) for c in b):g}" for a, b in SMALL_GAP_PLACEMENTS[:4]])
def test_small_gap_with_the_margin_defaults(seed, t):
    """裕度层默认参数（tol = geom_tol = 1e-9）下，间隙 1e-7 的近接触：距离正确、δ = 1e-6 判违约。"""
    g = 1e-7
    A, B, _, _ = _ridge_and_spike(g, seed, t)
    noise = 1e3 * 2.220446049250313e-16 * (max(abs(c) for c in t) + 4.0)
    d, lab = body_distance(A, B)
    assert abs(d - g) <= noise and lab[0] == "VE3", (d, lab)
    assert inflated_membership(A, B, delta=1e-6) == INSIDE
    assert margin_contacts(A, B, delta=1e-6)
    assert inflated_membership(B, A, delta=1e-6) == INSIDE


def test_ve3_direction_is_orthogonal_to_the_edge_by_construction():
    """按构造正交：远坐标、小间隙下 VE3 / EV3 的法向与棱方向的点积在 eps 量级（旧实现 ∝ eps·|坐标|/间隙）。"""
    from eab.kernel3d.geom3 import dot
    for seed, t in SMALL_GAP_PLACEMENTS:
        A, B, apex, ridge = _ridge_and_spike(1e-7, seed, t)
        tdir = B.edge_dir(ridge)
        c = ve3_cover(A, apex, B, ridge, 1e-12)
        assert c is not None and abs(dot(c.normal, tdir)) <= 1e-13, (seed, t)
        c2 = ev3_cover(B, ridge, A, apex, 1e-12)
        assert c2 is not None and abs(dot(c2.normal, tdir)) <= 1e-13, (seed, t)


@pytest.mark.parametrize("seed,t", SMALL_GAP_PLACEMENTS,
                         ids=[f"R{a}-t{max(abs(c) for c in b):g}" for a, b in SMALL_GAP_PLACEMENTS])
@pytest.mark.parametrize("g", [1e-5, 1e-7])
def test_frozen_low_dim_normal_is_orthogonal_and_gives_the_gap(g, seed, t):
    """冻结路径（frozen.py，可微的"片"）与 float 路径同一口径：VE3 / EV3 的法向按构造垂直于棱，
    margin_gap_from_frozen_cover 在 δ = 0 时给出的正是间隙 g。旧的单遍残差 w − s·d 留着 ∝ eps/g 的
    棱向分量，g = 1e-7 时冻结间隙的误差 ~ 1e-9·|a − 棱起点|（这里 ~2%）。"""
    from eab.kernel3d.frozen import frozen_normal
    from eab.kernel3d.geom3 import dot
    from eab.margin import margin_gap_from_frozen_cover
    A, B, apex, ridge = _ridge_and_spike(g, seed, t)
    noise = 1e3 * 2.220446049250313e-16 * (max(abs(c) for c in t) + 4.0)
    tdir = B.edge_dir(ridge)
    zero = (0.0, 0.0, 0.0)
    for X, Y, lab in ((A, B, ("VE3", ("vertex", apex), ("edge", ridge[0], ridge[1]))),
                      (B, A, ("EV3", ("edge", ridge[0], ridge[1]), ("vertex", apex)))):
        n = frozen_normal(X, Y, lab, x=zero)
        assert abs(dot(n, tdir)) <= 1e-13, (lab[0], dot(n, tdir))
        assert abs(margin_gap_from_frozen_cover(X, Y, lab, zero, 0.0) - g) <= noise, lab[0]

