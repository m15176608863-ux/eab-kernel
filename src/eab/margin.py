"""L2 裕度层：**安全距离即接触量**。这一层是"去岩石化"的铰链。

## 定理一 · 膨胀恒等式

把动体 A 按半径 δ 充气（Minkowski 加一个 δ-球 B_δ），入口块也只是充气同样一个球：

    E(A_δ, B) = B ⊕ (−A_δ) = B ⊕ (−(A ⊕ B_δ)) = B ⊕ (−A) ⊕ (−B_δ) = E(A,B) ⊕ B_δ

（末一步用球的对称性 −B_δ = B_δ。）于是

    「A 与 B 始终保持 δ 以上的间距」 ⟺ 「参考点不落进 E(A,B) 膨胀 δ 之后的集合」

**接触不再必须是物理挤压。** "离行人两米"与"不许贯入行人"是同一个几何命题，只差一次膨胀。

## 定理二 · 构型空间距离 = 工作空间距离

对 E 外的构型点 x：

    dist(x, E) = d(A + x, B)

（证：dist(x,E) = min{|x−u| : (A+u) ∩ B ≠ ∅} = 把两体推到相碰所需的最小平移 = 两体间距。）

这条把"构型点离障碍多远"与"两个物体离多远"划了等号，是裕度层全部数值内容的来源，
也是本层唯一需要**独立验证**的命题（凸情形可显式造出 E 直接量，见 `distance_to_convex_entrance`）。

## 定理三 · 裕度即接触

    margin_gap(x) = d(A+x, B) − δ  ；  ≤ 0 即「广义接触闭合」

于是约束 margin_gap ≥ 0 的 KKT 乘子就是**虚拟接触力**——整套接触力学（互补、摩擦、活动集）
原样适用于安全裕度问题，不需要另起炉灶。

## 定理四 · 球膨胀是 C^{1,1} 正则化

∂E 在顶点/棱处法向是**集值**的（法锥有非零立体角）；膨胀之后

    n(x) = (x − proj_E(x)) / |x − proj_E(x)|

处处**单值**，且因为凸集投影是非扩张映射，n 在 {dist ≥ δ} 上 Lipschitz，常数 ≤ 2/δ。
尖角变圆角，梯度不再跳——这对可微接触直接有用（见 `tests/test_margin.py` 的实测）。

## 口径与边界（诚实条款）

- **见证距离 ≠ 盖的 gap。** VF/FV 的 `gap` 是顶点到面**所在平面**的有符号距离；分离的凹体之间
  也常有顶点落在对方某面平面内侧（实测 −2.7）。两体间距必须用 `|point_a − point_b|`。
- **本层只在两体分离（或相触）时有数值意义；贯入由 `polyhedra_overlap` 先判。**
  贯入位形上盖枚举的 |point_a − point_b| **不是**间距，而是贯入深度一类的正数（2026-09-21
  审查实测 0.1 / 0.4 / 0.3 / 1.3，曾让 `margin_contacts` 返回 []、即回答"安全"——fail-unsafe）。
  所以三个入口在贯入时一致地回答"已违约"：`body_distance` 返回哨兵 `(0.0, ("PENETRATING",))`，
  `margin_contacts` 返回单个已闭合的哨兵接触（distance 0、margin_gap = −δ、normal None），
  `inflated_membership` 答 INSIDE；`margin_gap_from_frozen_cover` 对哨兵抛 ValueError（没有冻结盖）。
  违约多深要靠贯入深度（未实现）。贯入浅于 `geom_tol` 时按相触处理：见证距离 ≈ 0，裕度同样闭合。
  门：`tests/test_margin_penetration.py`。安全裕度问题本来就活在分离侧，这不是缺陷但必须写明。
- 距离由盖枚举给出，其**完备性**（法锥筛选不丢最近特征对）由 `g0_distance_completeness3` 看着。
"""

from __future__ import annotations

from dataclasses import dataclass

from .dual import Number
from .kernel3d.covers3 import closest_point_of_convex_hull_to_origin, enumerate_covers3
from .kernel3d.frozen import frozen_gap, frozen_normal
from .kernel3d.geom3 import (Polyhedron, Vec3, add, convex_hull_3d, norm, polyhedra_overlap,
                             sub, unit)

OUTSIDE, ON_BOUNDARY, INSIDE = -1, 0, 1
PENETRATING = "PENETRATING"            # 贯入哨兵标签：("PENETRATING",)


# ------------------------------------------------------------------ 见证与距离

def cover_witness(c) -> tuple[float, Vec3 | None] | None:
    """盖的见证：(特征对间距, 单位见证方向 B→A)。距离用 |point_a − point_b|，**不用 gap**。"""
    if c.point_a is None or c.point_b is None:
        return None
    v = sub(c.point_a, c.point_b)
    d = norm(v)
    return (d, unit(v) if d > 0.0 else None)


def body_distance(A: Polyhedron, B: Polyhedron, *, tol: float = 1e-9, geom_tol: float = 1e-9
                  ) -> tuple[float, tuple | None]:
    """两体间距及实现它的那个盖标签（盖路径）。

    贯入（`polyhedra_overlap(A, B, geom_tol) == 1`）时返回哨兵 `(0.0, ("PENETRATING",))`：
    此时盖的见证距离不是间距（见模块诚实条款），不许把它当距离报出去。
    完备性（不丢最近特征对）由 Phase 2 的距离完备性门保证。
    """
    if polyhedra_overlap(A, B, geom_tol) == 1:
        return 0.0, (PENETRATING,)
    best, lab = float("inf"), None
    for c in enumerate_covers3(A, B, window=float("inf"), tol=tol):
        if not c.in_extent:
            continue
        w = cover_witness(c)
        if w is not None and w[0] < best:
            best, lab = w[0], c.label()
    return best, lab


# ------------------------------------------------------------------ 裕度接触

@dataclass(slots=True)
class MarginContact:
    label: tuple
    distance: float          # 两体特征对间距（工作空间）
    margin_gap: float        # distance − delta；≤0 即广义接触闭合
    normal: Vec3 | None      # 单位见证方向 B→A，**单值**（C^{1,1}）；贯入哨兵为 None
    point_a: Vec3 | None     # 贯入哨兵为 None
    point_b: Vec3 | None

    @property
    def closed(self) -> bool:
        return self.margin_gap <= 0.0


def margin_contacts(A: Polyhedron, B: Polyhedron, *, delta: float, band: float = 0.0,
                    tol: float = 1e-9, geom_tol: float = 1e-9) -> list[MarginContact]:
    """裕度 δ 下的广义接触：间距 ≤ δ + band 的有效盖，按 margin_gap 升序。

    band 是"关注带"宽度（δ 之外还想看多远），band=0 只返回已闭合的广义接触。
    贯入（`polyhedra_overlap(A, B, geom_tol) == 1`）时返回**单个已闭合的哨兵**
    `MarginContact(("PENETRATING",), distance=0, margin_gap=−δ, normal=None)`——
    裕度谓词只回答"已违约"，与 `inflated_membership` 的 INSIDE 一致（fail-safe）。
    """
    if polyhedra_overlap(A, B, geom_tol) == 1:
        return [MarginContact((PENETRATING,), 0.0, 0.0 - delta, None, None, None)]
    out: list[MarginContact] = []
    for c in enumerate_covers3(A, B, window=float("inf"), tol=tol):
        if not c.in_extent:
            continue
        w = cover_witness(c)
        if w is None or w[0] > delta + band:
            continue
        out.append(MarginContact(c.label(), w[0], w[0] - delta, w[1], c.point_a, c.point_b))
    out.sort(key=lambda m: m.margin_gap)
    return out


def inflated_membership(A: Polyhedron, B: Polyhedron, *, delta: float, tol: float = 1e-9,
                        geom_tol: float = 1e-9, atol: float = 1e-12) -> int:
    """参考点相对膨胀入口块 E_δ 的位置：−1 外 / 0 边界 / 1 内（= 裕度已违约）。

    贯入时直接判"内"（见证距离失效，见模块诚实条款；由 `body_distance` 的贯入哨兵给出）。
    """
    d, lab = body_distance(A, B, tol=tol, geom_tol=geom_tol)
    if lab == (PENETRATING,):
        return INSIDE
    if d < delta - atol:
        return INSIDE
    if d > delta + atol:
        return OUTSIDE
    return ON_BOUNDARY


# ------------------------------------------------------------------ 凸情形的独立 oracle

def entrance_block_convex(A: Polyhedron, B: Polyhedron) -> Polyhedron:
    """显式造出 E(A,B) = conv{b − a}（**仅凸体**）。用作定理二的独立 oracle。"""
    return convex_hull_3d([sub(b, a) for a in A.verts for b in B.verts])


def nearest_point_on_convex_entrance(E: Polyhedron, x: Vec3) -> Vec3:
    """凸入口块上离构型点 x 最近的点。"""
    return add(x, closest_point_of_convex_hull_to_origin([sub(e, x) for e in E.verts]))


def distance_to_convex_entrance(E: Polyhedron, x: Vec3) -> float:
    return norm(sub(nearest_point_on_convex_entrance(E, x), x))


def inflated_normal(E: Polyhedron, x: Vec3) -> Vec3 | None:
    """∂E_δ 上的外法向：n(x) = unit(x − proj_E(x))。x 在 E 内则为 None（无定义）。

    **单值**，且 Lipschitz（常数 ≤ 2/δ）——这就是球膨胀的 C^{1,1} 正则化内容。
    """
    v = sub(x, nearest_point_on_convex_entrance(E, x))
    return unit(v) if norm(v) > 0.0 else None


# ------------------------------------------------------------------ 可微路径

def margin_gap_from_frozen_cover(A: Polyhedron, B: Polyhedron, label: tuple, x, delta,
                                 *, ee_sign: float = 1.0) -> Number:
    """冻结盖下的裕度间隙闭式：n·(a − b) − δ，支持对偶数（δ 也可以是一个导数通道）。

    仅当冻结的盖**正是实现最短距离的那一对特征**时，沿盖法向的 gap 等于见证距离——
    这由 float 路径的 `body_distance` 选出，是冻结组合结构的一部分。
    冻结路径接得住 `body_distance` 可能给出的全部盖种类：VF / FV / EE / VV3 / VE3 / EV3
    （低维盖的法向随平移 x 转动，按 x 计算；门：tests/test_frozen_lowdim.py）。
    贯入哨兵 ("PENETRATING",) 没有冻结盖，抛 ValueError。
    """
    if label and label[0] == PENETRATING:
        raise ValueError("bodies interpenetrate: there is no frozen cover (margin already violated)")
    n = frozen_normal(A, B, label, ee_sign, x=x)
    return frozen_gap(A, B, label, x, n) - delta
