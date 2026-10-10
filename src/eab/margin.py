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
  违约多深要靠贯入深度（未实现）。门：`tests/test_margin_penetration.py`。安全裕度问题本来就活在
  分离侧，这不是缺陷但必须写明。
  贯入守卫的可靠性等于 `polyhedra_overlap` 的可靠性：谓词漏判的贯入在这里同样漏判，本层不另设第二道谓词
  （G6 critical 的等高 X 交叉已由 m2-geom 的接触锥证人修复并合并，门：tests/test_geom3_overlap_witness.py）。
  谓词的有效分辨率是 max(geom_tol_eff, 1e-12·diag)，且按到面平面的距离计：深度不超过 geom_tol_eff·sin(接触面夹角)
  时判相触，深于相触分辨率 ctol = max(geom_tol_eff, 1e-12·diag) + 舍入地板（下一条）时一定给哨兵；(geom_tol_eff, ctol] 之间的贯入答"相触"
  （偏安全侧：接触判闭合，不当间距报）——这是 2026-10-10 统一成一把尺之后的口径（G6 第四轮 minor：此前这里仍写"深于 geom_tol_eff
  一定给哨兵"，与下一条矛盾）。
- **相触分辨率（纪律 F，2026-09-24 M0.2；2026-10-10 统一成一把尺 `contact_resolution`）。** 间距或贯入深度在
  ctol = max(geom_tol_eff, 1e-12·diag) + 舍入地板 以内即"相触"：`body_distance` 返回 **0.0**（标签是实现最小见证的那个盖），
  `margin_contacts` 里见证距离 ≤ ctol 的盖 distance 钳为 0、margin_gap = −δ、normal None（零距离处见证方向无定义；
  亚容差贯入时 a − b 还是反的）。谓词答"相触"而没有见证落在 ctol 内、或谓词答"贯入"，给哨兵。于是回答随贯入深度**单调**：
  分离 d → 相触 0 → 亚容差贯入 0 → 哨兵，
  成员判定 OUTSIDE → ON_BOUNDARY/INSIDE → INSIDE（修前浅于 geom_tol 的贯入把见证距离 ≈ 贯入深度当间距报出，
  δ < p 时答"安全"，比恰好相触还"安全"——G6 minor[28]）。代价：真实间距 ≤ geom_tol_eff 时报 0（在分辨率以下，
  且偏向安全侧）。门：`tests/test_margin_penetration.py::test_contact_resolution_is_monotone_in_depth`。
- **容差随尺度（纪律 F）。** `geom_tol=None`（默认）时 geom_tol_eff = max(1e-9·L, 64·eps·C)：L 是特征长度
  （`characteristic_length`：各体"首顶点到最远顶点"距离取小，刚体运动下不变、缩放下 ×s），C 是坐标量级
  （地板 64·eps·C 盖住工程坐标上顶点坐标自身的舍入）。显式给 `geom_tol` 时按**绝对长度**解释，但同样不低于
  舍入地板。`inflated_membership` 的边界带 `atol` 同理（默认 max(1e-12·L, 64·eps·C)）。修前两者都是绝对
  1e-9 / 1e-12：边长 1e-9 的整体嵌套答 OUTSIDE（C14 的尺度变体），1e5 坐标上相触的两体在 δ = 0 时答 OUTSIDE。
  盖枚举的 `tol`（法锥判据，作用在单位向量上，无量纲）不随尺度；M0.3 起它**只是**角度——covers3 不再把它当
  长度用（M0.2 曾把 1e-9 同时当绝对长度地板，块体 < 1 m 时间隙 ≤ 1e-9 的真最近 VE3 被丢，G6 第二轮 critical），
  面内/段内的长度带是另一个参数 `extent_tol`（本层用缺省：只有舍入地板）。
- **自校验（M0.3）。** 分离时盖路径的最小见证距离与 `brute_feature_distance`（全部特征对、不经法锥）在舍入内相等，
  否则抛 RuntimeError；相触分辨率内没有见证落在带内的（比 2·geom_tol_eff 还薄的体）按贯入处理。
  门：`tests/test_margin_resolution.py`。
- **并列裁决按枚举序。** 多个盖在舍入意义上同距（平行面、平行棱）时，`body_distance` 取枚举序第一个，
  `margin_contacts` 在同距组内也按枚举序排——变换保留顶点/面编号，所以刚体运动下标签逐字不变。
- 距离由盖枚举给出，其**完备性**（法锥筛选不丢最近特征对）由 `g0_distance_completeness3` 看着。
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from .dual import Number
from .kernel3d.covers3 import closest_point_of_convex_hull_to_origin, enumerate_covers3
from .kernel3d.frozen import frozen_gap, frozen_normal
from .kernel3d.geom3 import (Polyhedron, Vec3, add, brute_feature_distance, convex_hull_3d, norm,
                             polyhedra_overlap, sub, unit)

OUTSIDE, ON_BOUNDARY, INSIDE = -1, 0, 1
PENETRATING = "PENETRATING"            # 贯入哨兵标签：("PENETRATING",)

_EPS = sys.float_info.epsilon
REL_GEOM_TOL = 1e-9                    # 相触分辨率：特征长度 L 的相对量
REL_BOUNDARY_TOL = 1e-12               # inflated_membership 的边界带：L 的相对量
ROUNDING_C = 64.0                      # 舍入地板 c·eps·C 的系数 c


# ------------------------------------------------------------------ 容差政策（纪律 F）

def characteristic_length(*bodies: Polyhedron) -> float:
    """特征长度 L：各体"首顶点到最远顶点的距离"取最小。刚体运动下不变（顶点编号不变），缩放下 ×s；
    介于半径与直径之间。不用 AABB（旋转会改变它）。"""
    out = float("inf")
    for P in bodies:
        v0 = P.verts[0]
        out = min(out, max(norm(sub(v, v0)) for v in P.verts))
    return out


def coordinate_magnitude(*bodies: Polyhedron) -> float:
    """坐标量级 C = 全部顶点坐标分量的最大绝对值（舍入地板用）。"""
    return max(abs(c) for P in bodies for v in P.verts for c in v)


def rounding_floor(*bodies: Polyhedron) -> float:
    """c·eps·max(C, L)：顶点坐标自身的舍入，以及由它引起的有符号距离、间隙的舍入量级。"""
    return ROUNDING_C * _EPS * max(coordinate_magnitude(*bodies), characteristic_length(*bodies))


def effective_geom_tol(A: Polyhedron, B: Polyhedron, geom_tol: float | None = None) -> float:
    """相触分辨率：geom_tol=None 时 max(1e-9·L, 64·eps·C)；显式给出时按绝对长度，但不低于舍入地板。"""
    base = REL_GEOM_TOL * characteristic_length(A, B) if geom_tol is None else float(geom_tol)
    return max(base, rounding_floor(A, B))


def _tie_groups(items: list, key, window: float) -> list:
    """按 key 升序；key 相差 ≤ window（舍入意义上的并列）的一组内按枚举序（items 的原次序）排。"""
    order = sorted(range(len(items)), key=lambda i: key(items[i]))
    out: list = []
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and key(items[order[j + 1]]) - key(items[order[i]]) <= window:
            j += 1
        out.extend(items[k] for k in sorted(order[i:j + 1]))
        i = j + 1
    return out


# ------------------------------------------------------------------ 见证与距离

def cover_witness(c) -> tuple[float, Vec3 | None] | None:
    """盖的见证：(特征对间距, 单位见证方向 B→A)。距离用 |point_a − point_b|，**不用 gap**。"""
    if c.point_a is None or c.point_b is None:
        return None
    v = sub(c.point_a, c.point_b)
    d = norm(v)
    return (d, unit(v) if d > 0.0 else None)


def _witnesses(A: Polyhedron, B: Polyhedron, tol: float) -> list[tuple]:
    """全部有效且 in_extent 的盖及其见证 (盖, 见证距离, 单位见证方向)，按枚举序。"""
    out = []
    for c in enumerate_covers3(A, B, window=float("inf"), tol=tol):
        if not c.in_extent:
            continue
        w = cover_witness(c)
        if w is not None:
            out.append((c, w[0], w[1]))
    return out


def contact_resolution(A: Polyhedron, B: Polyhedron, geom_tol: float | None = None) -> float:
    """相触分辨率 ctol = max(geom_tol_eff, 谓词自己的分辨率 1e-12·diag) + 舍入地板——裕度层**唯一**的那把尺：
    见证距离 ≤ ctol 钳为 0；谓词答"相触"而没有见证落在 ctol 内才算贯入。
    G6 第三轮（Find 阶段报 critical、经验证定 major）：旧版钳零用 geom_tol_eff、收下见证表用 geom_tol_eff + 舍入，工程坐标下（|t| = 1e6 时舍入 ≈ geom_tol_eff）
    贯入深度落在两者之间的一对被当**正间距**报出、答"安全"；major：谓词把离面平面 ≤ 1e-12·diag（被测的那个体的对角线）的点
    判"在表面上"，两体尺寸比 ≥ 1e3 时这个带大于 geom_tol_eff，一个明明分离的小块经一次旋转被答成贯入。"""
    diag = max(A.metrics()[1], B.metrics()[1])
    return max(effective_geom_tol(A, B, geom_tol), 1e-12 * diag) + rounding_floor(A, B)


def _resolve(A: Polyhedron, B: Polyhedron, tol: float, geom_tol: float | None):
    """裕度层的共同前处理：(相触分辨率 ctol, 舍入地板, 见证表 | None=贯入, 是否在相触分辨率内)。

    自校验（M0.3，G6 第二轮两条 critical 之后）：分离时（谓词答 −1）盖路径的最小见证距离必须与
    `brute_feature_distance`（全部特征对、不经法锥）在舍入内相等，否则抛 RuntimeError——
    盖枚举漏掉最近特征对（报远处的盖、答"安全"）或见证点不在两体上（距离少报）都不许静默返回。
    相触时（谓词答 0）必须有见证落在相触分辨率 ctol 内；没有（比 2·ctol 还薄的体被分辨带"蚀穿"，或谓词在它自己的
    分辨率下看到了见证表看不到的接触）按贯入处理——三个入口一致答"已违约"，偏安全侧。
    """
    gtol = effective_geom_tol(A, B, geom_tol)
    ctol = contact_resolution(A, B, geom_tol)
    state = polyhedra_overlap(A, B, gtol)
    if state == 1:
        return ctol, 0.0, None, True
    wits = _witnesses(A, B, tol)
    dmin = min((w for _, w, _ in wits), default=float("inf"))
    rnd = rounding_floor(A, B)
    if state == 0:
        if dmin > ctol:
            return ctol, 0.0, None, True
        return ctol, rnd, wits, True
    truth = brute_feature_distance(A, B)
    if abs(dmin - truth) > 4.0 * rnd:
        raise RuntimeError(f"margin self-check failed: the covers give distance {dmin!r} but the nearest feature pair "
                           f"is {truth!r} apart (rounding {rnd:.3g}); the cover enumeration "
                           + ("missed the nearest pair" if dmin > truth else "returned witnesses off the bodies"))
    return ctol, rnd, wits, dmin <= ctol


def body_distance(A: Polyhedron, B: Polyhedron, *, tol: float = 1e-9, geom_tol: float | None = None
                  ) -> tuple[float, tuple | None]:
    """两体间距及实现它的那个盖标签（盖路径）。

    贯入深于 geom_tol_eff（`polyhedra_overlap(A, B, geom_tol_eff) == 1`）时返回哨兵 `(0.0, ("PENETRATING",))`：
    此时盖的见证距离不是间距（见模块诚实条款），不许把它当距离报出去。
    间距或贯入深度在相触分辨率 ctol（`contact_resolution`）以内时返回 **0.0** 与实现最小见证的盖标签。
    geom_tol=None 时 geom_tol_eff 随尺度（见 `effective_geom_tol`）。舍入意义上同距的盖按枚举序取第一个。
    完备性（不丢最近特征对）由 Phase 2 的距离完备性门保证。
    """
    ctol, rnd, wits, contact = _resolve(A, B, tol, geom_tol)
    if wits is None:
        return 0.0, (PENETRATING,)
    if not wits:
        return (0.0 if contact else float("inf")), None
    c, w, _ = _tie_groups(wits, lambda t: t[1], rnd)[0]
    return (0.0 if contact and w <= ctol else w), c.label()


# ------------------------------------------------------------------ 裕度接触

@dataclass(slots=True)
class MarginContact:
    label: tuple
    distance: float          # 两体特征对间距（工作空间）；相触分辨率内钳为 0
    margin_gap: float        # distance − delta；≤0 即广义接触闭合
    normal: Vec3 | None      # 单位见证方向 B→A，**单值**（C^{1,1}）；贯入哨兵与相触（distance 0）为 None
    point_a: Vec3 | None     # 贯入哨兵为 None
    point_b: Vec3 | None

    @property
    def closed(self) -> bool:
        return self.margin_gap <= 0.0


def margin_contacts(A: Polyhedron, B: Polyhedron, *, delta: float, band: float = 0.0,
                    tol: float = 1e-9, geom_tol: float | None = None) -> list[MarginContact]:
    """裕度 δ 下的广义接触：间距 ≤ δ + band 的有效盖，按 margin_gap 升序（舍入意义上的并列按枚举序）。

    band 是"关注带"宽度（δ 之外还想看多远），band=0 只返回已闭合的广义接触。
    贯入深于 geom_tol_eff 时返回**单个已闭合的哨兵**
    `MarginContact(("PENETRATING",), distance=0, margin_gap=−δ, normal=None)`——
    裕度谓词只回答"已违约"，与 `inflated_membership` 的 INSIDE 一致（fail-safe）。
    两体在相触分辨率 ctol（`contact_resolution`）内时，见证距离 ≤ ctol 的盖 distance 钳为 0、
    margin_gap = −δ、normal None——与 `body_distance` 的 0.0 一致，结果随贯入深度单调。
    """
    ctol, rnd, wits, contact = _resolve(A, B, tol, geom_tol)
    if wits is None:
        return [MarginContact((PENETRATING,), 0.0, 0.0 - delta, None, None, None)]
    out: list[MarginContact] = []
    for c, w, n in wits:
        if contact and w <= ctol:
            w, n = 0.0, None
        if w > delta + band:
            continue
        out.append(MarginContact(c.label(), w, w - delta, n, c.point_a, c.point_b))
    return _tie_groups(out, lambda m: m.margin_gap, rnd)


def boundary_band(A: Polyhedron, B: Polyhedron, atol: float | None = None) -> float:
    """`inflated_membership` 的边界带：atol=None 时 max(1e-12·L, 64·eps·C)；显式给出时不低于舍入地板。"""
    base = REL_BOUNDARY_TOL * characteristic_length(A, B) if atol is None else float(atol)
    return max(base, rounding_floor(A, B))


def inflated_membership(A: Polyhedron, B: Polyhedron, *, delta: float, tol: float = 1e-9,
                        geom_tol: float | None = None, atol: float | None = None) -> int:
    """参考点相对膨胀入口块 E_δ 的位置：−1 外 / 0 边界 / 1 内（= 裕度已违约）。

    贯入时直接判"内"（见证距离失效，见模块诚实条款；由 `body_distance` 的贯入哨兵给出）。
    |d − δ| ≤ 边界带（`boundary_band`，随尺度）即"边界"；相触分辨率内 d = 0，故 δ = 0 时答边界。
    """
    d, lab = body_distance(A, B, tol=tol, geom_tol=geom_tol)
    if lab == (PENETRATING,):
        return INSIDE
    band = boundary_band(A, B, atol)
    if d < delta - band:
        return INSIDE
    if d > delta + band:
        return OUTSIDE
    return ON_BOUNDARY


# ------------------------------------------------------------------ 凸情形的独立 oracle

def entrance_block_convex(A: Polyhedron, B: Polyhedron) -> Polyhedron:
    """显式造出 E(A,B) = conv{b − a}（**仅凸体**）。用作定理二的独立 oracle。

    凸包的容差带上**原坐标**的舍入地板：差点本身只有 L 量级，噪声却是 eps·|原坐标|（工程坐标下 1e5 ~ 1e6），
    凸包自己只看得见差点坐标，算出的地板小 5 个量级，只能靠 ×100 逐级放大自救（M0.3 之前）。"""
    pts = [sub(b, a) for a in A.verts for b in B.verts]
    lo, hi = A.aabb()[0], A.aabb()[1]
    L = max(norm(sub(hi, lo)), norm(sub(*reversed(B.aabb()))), rounding_floor(A, B))
    return convex_hull_3d(pts, tol=max(1e-12, 4.0 * rounding_floor(A, B) / L))


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
    相触分辨率内（`body_distance` 报 0.0）这里给的是该盖的**有符号**间隙（|gap| ≤ geom_tol_eff，亚容差贯入时为负），
    不是钳过的 0——冻结路径是解析式，不做择支。
    贯入哨兵 ("PENETRATING",) 没有冻结盖，抛 ValueError。
    """
    if label and label[0] == PENETRATING:
        raise ValueError("bodies interpenetrate: there is no frozen cover (margin already violated)")
    n = frozen_normal(A, B, label, ee_sign, x=x)
    return frozen_gap(A, B, label, x, n) - delta
