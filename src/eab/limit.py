"""L3 互补层第一块砖：**单边摩擦接触下的刚体极限分析**。

## 为什么先做它

L5 的 TIA 首枪只能给**剪胀比**（几何/运动学量）。要给"承载力"就必须有力学，
而写整套 DDA 时间步进既重复 bdda2 又答非所问——极限分析**直接给出破坏荷载，不需要时间步进**。

## 理论

下限定理（静力）：若存在一组容许接触力与外荷载平衡，则该荷载不大于极限荷载。
容许 = 单边（压不受拉）+ 库仑摩擦锥内。写成线性规划：

    max α   s.t.   Σ_ij λ_ij w_ij + W_dead + α·W_live = 0 ,  λ ≥ 0

其中 w_ij = (d_ij, (p_i − o) × d_ij) 是第 i 个接触第 j 条摩擦锥棱的**旋量**（wrench）。
黏聚力是**有界**的附加抗剪（|F_s| ≤ c·A，与法向压力无关）：每个黏聚接触再加一组黏聚列和一行
Σλ_coh + s = 1（右端 1）。

上限定理（运动）：这个 LP 的**对偶解就是破坏机构**。对偶变量分两段 y = (y_w, y_r)：
y_w 是动体的虚速度旋量（`LimitResult.mechanism`），y_r 是各黏聚行的乘子（`LimitResult.row_duals`，
= 该接触的黏聚耗散）。对偶可行性 y_wᵀw_ij ≥ 0 说的正是"虚速度场不得贯入任何接触"
（符号约定见 `mechanism_is_admissible`：正 = 分离），而强对偶
α* = −y_wᵀW_dead + Σ y_r 就是上限定理的功率平衡（外力功率 = 黏聚耗散；摩擦在关联流动下不耗散）。
**所以静力下限与运动上限由同一次求解同时给出，且必然相等——这是这一层的自校验结构。**

与盖系统的接口：约束 yᵀw ≥ 0 的那组法向，正是盖枚举输出的完备清单。
换句话说，**"机构不得进入入口块"就是这里的运动学容许条件**——L1 与 L3 在此咬合。

## 诚实条款

- **二维的摩擦锥线性化是精确的**（锥恰有两条极棱）；三维用 k 边内接棱锥，是**偏安全**的近似：
  内接 ⇒ 容许集变小 ⇒ 承载力不高于精确锥。量化：正 k 边形的内切圆半径是外接圆的 cos(π/k) 倍，
  所以内接棱锥 ⊇ 摩擦系数 μ·cos(π/k) 的精确圆锥——**承载力夹在 μ·cos(π/k) 与 μ 两个精确锥的解之间**。
  纯滑动（承载力正比于切向能力）时相对短缺 ∈ [0, 1 − cos(π/k)]：滑动方向正对一条棱时为 0，
  平分两棱时取到上界。误差取决于滑动方向相对 `_tangents` 切向基架的夹角，**不随 k 单调**
  （互锁算例 4|k 时恰有一条棱落在荷载平面内而精确，k=5 反而明显变差）。
  门：tests/test_limit.py 的三个锥线性化门，tests/test_limit_scale.py 的 Patton 全格。
- 刚体、小变形、接触位置在加载中**不变**——极限分析的标准前提。几何非线性不在内。
- 只做**单个动体对固定边界**。多体机构需要把各体的自由度并进同一组平衡方程（未实现）。
- 本构目前只有库仑摩擦 + 可选黏聚力；抗拉一律为零（单边）。
- **破坏机构（对偶解）一般不唯一。** 承载力 α 唯一，但对偶最优集可以是一整个面：三维内接棱锥下，推力方向恰落在一条锥棱上时，机构的切向速度可以在该棱两侧 ±π/k 内任取（实测 cb2 滑动偏 −22.5°）；退化位形（对称、共面接触）下还可能混入其他零耗散分量。读破坏模式时应读**不变量**（是否转动、支点速度是否为零、功率平衡），不要读机构的逐分量取值。门：tests/test_end_to_end_cb2.py::test_failure_mode_is_read_off_the_dual_mechanism。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import cos, pi, sin

from .lp import OPTIMAL, UNBOUNDED, maximize

Vec = tuple[float, ...]


# ------------------------------------------------------------------ 旋量

def wrench(force: Vec, point: Vec, origin: Vec, dim: int) -> list[float]:
    """力 `force` 作用于 `point` 时相对 `origin` 的旋量。二维 3 维、三维 6 维。"""
    r = tuple(point[i] - origin[i] for i in range(dim))
    if dim == 2:
        return [force[0], force[1], r[0] * force[1] - r[1] * force[0]]
    return [force[0], force[1], force[2],
            r[1] * force[2] - r[2] * force[1],
            r[2] * force[0] - r[0] * force[2],
            r[0] * force[1] - r[1] * force[0]]


def _tangents(n: Vec, dim: int) -> list[Vec]:
    if dim == 2:
        return [(-n[1], n[0])]
    a = (1.0, 0.0, 0.0) if abs(n[0]) < 0.9 else (0.0, 1.0, 0.0)
    t1 = (a[1] * n[2] - a[2] * n[1], a[2] * n[0] - a[0] * n[2], a[0] * n[1] - a[1] * n[0])
    ln = sum(v * v for v in t1) ** 0.5
    t1 = tuple(v / ln for v in t1)
    t2 = (n[1] * t1[2] - n[2] * t1[1], n[2] * t1[0] - n[0] * t1[2], n[0] * t1[1] - n[1] * t1[0])
    return [t1, t2]


def friction_generators(normal: Vec, mu: float, dim: int, k: int = 8) -> list[Vec]:
    """库仑锥的棱方向（单位法向 + μ·切向）。二维恰两条（精确）；三维 k 条（内接，偏安全）。"""
    ts = _tangents(normal, dim)
    if dim == 2:
        t = ts[0]
        return [tuple(normal[i] + mu * t[i] for i in range(2)),
                tuple(normal[i] - mu * t[i] for i in range(2))]
    t1, t2 = ts
    out = []
    for j in range(k):
        a = 2.0 * pi * j / k
        out.append(tuple(normal[i] + mu * (cos(a) * t1[i] + sin(a) * t2[i]) for i in range(3)))
    return out


# ------------------------------------------------------------------ 接触

@dataclass(slots=True)
class LimitContact:
    """极限分析看到的一个接触：位置、法向（固定体推动体的方向）、摩擦、可选黏聚力与面积。"""
    point: Vec
    normal: Vec
    mu: float = 0.0
    cohesion: float = 0.0          # 黏聚强度（与 area 相乘得到附加抗剪力）
    area: float = 0.0
    label: tuple | None = None


_SIDES = ("a", "b", "mid")


def contacts_from_covers(covers, *, mu: float, cohesion: float = 0.0,
                         side: str = "a") -> list[LimitContact]:
    """把盖枚举的输出接进来：每个带法向与两侧见证点的盖变成一个接触，法向取盖法向（B → A）。

    接触点取哪一侧（`side`）：
      · "a"（默认）：A 侧见证点。极限分析求的是动体 A 的平衡，接触力作用在 A 的表面上。
      · "b"：B 侧见证点；"mid"：见证段中点。
    gap > 0 的盖（窗口内尚未闭合）上，"mid" / "b" 把摩擦力的作用线沿法向挪开 gap/2 / gap，
    切向力的力矩因此错 μ·gap/2 / μ·gap：2×2×3 块、gap = 0.3 的倾覆承载从 10/3 变成
    10/3.15 / 10/3.3，而 "a" 与 gap 无关（审查 C4；门：tests/test_limit_contacts.py）。
    """
    if side not in _SIDES:
        raise ValueError(f"side must be one of {_SIDES}, got {side!r}")
    out = []
    for c in covers:
        if c.normal is None or c.point_a is None or c.point_b is None:
            continue
        if side == "a":
            p = tuple(c.point_a)
        elif side == "b":
            p = tuple(c.point_b)
        else:
            p = tuple((a + b) / 2.0 for a, b in zip(c.point_a, c.point_b))
        out.append(LimitContact(p, tuple(c.normal), mu, cohesion,
                                c.area or 0.0, c.label()))
    return out


# ------------------------------------------------------------------ LP 的列

@dataclass(slots=True)
class _Columns:
    cols: list[list[float]]          # 每列的旋量（不含 α 列与松弛列）
    owner: list[int]                 # 该列所属接触的下标
    row_of: list[int | None]         # 黏聚列所在黏聚行的下标；摩擦列为 None
    n_rows: int                      # 黏聚行数 = 带黏聚力（cohesion > 0 且 area > 0）的接触数


def _build_columns(contacts: list[LimitContact], origin: Vec, dim: int, k: int) -> _Columns:
    """LP 的列：每个接触先是它的摩擦锥棱，若有黏聚力紧接着是它的黏聚列。

    `limit_load`、`check_duality`、`mechanism_is_admissible` 三处**共用**这一个定义——
    列序、黏聚列的插入位置、黏聚行编号只在这里写一次（审查 C1/C24：三处各造一遍就会错位）。
    黏聚列必须**有界**：|F_s| ≤ c·A 与法向压力无关，若写成无界非负射线，黏聚力可以无限放大、
    LP 直接报无界（2026-09-21 实测）。所以每个黏聚接触对应一行 Σλ_coh + s = 1。
    """
    cols: list[list[float]] = []
    owner: list[int] = []
    row_of: list[int | None] = []
    n_rows = 0
    for ci, ct in enumerate(contacts):
        for g in friction_generators(ct.normal, ct.mu, dim, k):
            cols.append(wrench(g, ct.point, origin, dim))
            owner.append(ci)
            row_of.append(None)
        if ct.cohesion > 0.0 and ct.area > 0.0:
            mag = ct.cohesion * ct.area
            if dim == 2:
                t = _tangents(ct.normal, dim)[0]
                dirs = [tuple(sg * v for v in t) for sg in (1.0, -1.0)]
            else:
                t1, t2 = _tangents(ct.normal, dim)
                dirs = [tuple(cos(2.0 * pi * j / k) * t1[i] + sin(2.0 * pi * j / k) * t2[i]
                              for i in range(3)) for j in range(k)]
            for d in dirs:
                cols.append(wrench(tuple(mag * v for v in d), ct.point, origin, dim))
                owner.append(ci)
                row_of.append(n_rows)
            n_rows += 1
    return _Columns(cols, owner, row_of, n_rows)


# ------------------------------------------------------------------ 极限荷载

@dataclass(slots=True)
class LimitResult:
    status: str
    alpha: float                         # 极限荷载因子
    lambdas: list[float]                 # 各列乘子，列序 = `_build_columns`（摩擦棱，随后该接触的黏聚列）
    mechanism: list[float]               # 对偶解的旋量段 = 破坏机构（二维 (vx,vy,ω)，三维 6 维旋量）
    contact_forces: list[Vec] = field(default_factory=list)
    active: list[tuple] = field(default_factory=list)   # 乘子非零的接触标签
    iterations: int = 0
    row_duals: list[float] = field(default_factory=list)  # 各黏聚行的对偶乘子（黏聚耗散），行序同 `_build_columns`


def limit_load(contacts: list[LimitContact], dead: list[float], live: list[float], *,
               dim: int = 3, origin: Vec | None = None, k: int = 8,
               tol: float = 1e-9, lp_tol: float | None = None) -> LimitResult:
    """max α s.t. Σ λ w + W_dead + α W_live = 0, λ ≥ 0（每个黏聚接触另有 Σλ_coh ≤ 1）。

    `dead` / `live` 是已经算好的旋量（用 `wrench` 造）。返回的 `mechanism` 是对偶解的旋量段，
    即上限定理的破坏机构；`row_duals` 是各黏聚行的乘子；`contact_forces` 是每个接触上合成的力。

    `tol`：λ 的活动判据——`contact_forces` 与 `active` 忽略 λ ≤ tol 的列。
    `lp_tol`：传给 LP 的主元/可行性容差（None = lp.solve 的默认值）。LP 的一阶段可行性判据相对于
    右端项（荷载）的尺度，见 lp.py。**不再**把 tol 缩小 1e-3 当 LP 容差：那样 N = 100 时一阶段
    舍入残差 ~2e-12 就超过 1e-12，可行问题被静默判成 infeasible（审查 C0/C21）。
    """
    if origin is None:
        origin = (0.0,) * dim
    nw = 3 if dim == 2 else 6
    C = _build_columns(contacts, origin, dim, k)
    cols = C.cols + [live]                             # α 也是一个非负变量
    ncol = len(cols) + C.n_rows                        # 末尾追加各黏聚行的松弛变量
    A = [[cols[j][i] if j < len(cols) else 0.0 for j in range(ncol)] for i in range(nw)]
    b = [-v for v in dead]
    for r_i in range(C.n_rows):
        row = [0.0] * ncol
        for j, rj in enumerate(C.row_of):
            if rj == r_i:
                row[j] = 1.0
        row[len(cols) + r_i] = 1.0                     # 松弛
        A.append(row)
        b.append(1.0)
    c = [0.0] * len(C.cols) + [1.0] + [0.0] * C.n_rows
    r = maximize(A, b, c) if lp_tol is None else maximize(A, b, c, tol=lp_tol)
    if r.status != OPTIMAL:
        return LimitResult(r.status, float("inf") if r.status == UNBOUNDED else float("nan"),
                           [], [], iterations=r.iterations)
    alpha = r.x[len(C.cols)]
    lam = r.x[:len(C.cols)]
    forces: list[Vec] = [tuple(0.0 for _ in range(dim)) for _ in contacts]
    for j, ci in enumerate(C.owner):
        if lam[j] <= tol:
            continue
        g = C.cols[j][:dim]
        forces[ci] = tuple(forces[ci][i] + lam[j] * g[i] for i in range(dim))
    active = sorted({contacts[C.owner[j]].label for j in range(len(lam))
                     if lam[j] > tol and contacts[C.owner[j]].label is not None})
    return LimitResult(OPTIMAL, alpha, lam, list(r.y[:nw]), forces, active, r.iterations,
                       row_duals=list(r.y[nw:]))


def mechanism_power(mech: list[float], ct: LimitContact, g: Vec, origin: Vec, dim: int) -> float:
    return sum(m * wi for m, wi in zip(mech, wrench(g, ct.point, origin, dim)))


def _dot(y: list[float], w: list[float]) -> float:
    return sum(m * wi for m, wi in zip(y, w))


def mechanism_is_admissible(mech: list[float], contacts: list[LimitContact], *,
                            dim: int = 3, origin: Vec | None = None, k: int = 8,
                            tol: float = 1e-7, row_duals: list[float] | None = None) -> bool:
    """上限侧的自检：机构对**每一条**摩擦锥棱的虚功率 yᵀw **≥ 0**。

    符号约定要说清楚（2026-09-21 我先写反过一次，全部算例误报不容许）：
    `mech` 就是动体的虚速度旋量，法向取"固定体推动体"的方向，于是

        yᵀw > 0  ⟺  该锥棱上两体**分离**（容许，互补条件要求那里 λ = 0）
        yᵀw = 0  ⟺  该锥棱**活动**（正在滑动/受压的那一条）
        yᵀw < 0  ⟺  **贯入或超出摩擦锥**（不容许）

    所以容许条件是 ≥ 0，不是 ≤ 0。验算：倾覆机构 y = (0, 1/3, −1/3) 在左角给出
    yᵀw = 2/3 > 0（左角确实在抬起），在右趾给出 0（支点不动）。

    黏聚列不限制运动学：黏聚抗剪有界，任何剪切滑移只需付出有限耗散 y_r ≥ max(0, max_j −yᵀw_coh,j)，
    所以不给 `row_duals` 时黏聚列不参与判定；给了（`LimitResult.row_duals`）时按 LP 的对偶可行性
    逐列检查 yᵀw_coh + y_r ≥ 0 与 y_r ≥ 0。列由 `_build_columns` 给出（与 `limit_load` 共用）。
    `mech` 必须恰是旋量段（二维 3 维、三维 6 维）。
    """
    if origin is None:
        origin = (0.0,) * dim
    nw = 3 if dim == 2 else 6
    if len(mech) != nw:
        raise ValueError(f"mechanism must have {nw} components for dim={dim}, got {len(mech)}")
    C = _build_columns(contacts, origin, dim, k)
    if row_duals is not None:
        if len(row_duals) != C.n_rows:
            raise ValueError(f"row_duals has {len(row_duals)} entries, contacts give {C.n_rows} cohesion rows")
        if any(v < -tol for v in row_duals):
            return False
    for w, rj in zip(C.cols, C.row_of):
        if rj is None:
            if _dot(mech, w) < -tol:
                return False
        elif row_duals is not None and _dot(mech, w) + row_duals[rj] < -tol:
            return False
    return True


def check_duality(res: LimitResult, contacts: list[LimitContact], dead: list[float],
                  live: list[float], *, dim: int = 3, origin: Vec | None = None,
                  k: int = 8, tol: float = 1e-7) -> dict:
    """静力下限与运动上限的自校验——这一层的核心结构，必须逐项成立。

    记 y = res.mechanism（旋量段）、y_r = res.row_duals（黏聚行），列 j 的约化功率
    p_j = yᵀw_j + (y_r[行(j)]，若 j 是黏聚列；摩擦列为 0)。LP 的对偶是 min bᵀy s.t. Aᵀy ≥ c，
    b = (−W_dead, 1, …, 1)，于是：

    · 机构容许：p_j ≥ 0（每一列，含黏聚列），y_r ≥ 0（松弛列）
    · 驱动归一：yᵀW_live ≥ 1
    · 强对偶：  α = −yᵀW_dead + Σ y_r   ← 上限定理的功率平衡（Σ y_r 是黏聚耗散）
    · 互补：    λ_j > 0 ⟹ p_j = 0；松弛 s_r = 1 − Σ_{j∈r} λ_j > 0 ⟹ y_r = 0；α > 0 ⟹ yᵀW_live = 1

    列由 `_build_columns` 给出，与 `limit_load` **共用**（纪律 A 的如实声明）：这里验证的是
    "LP 的解与它自己的列一致"，不能替代对列构造本身的门（闭式 α、手算机构，见 tests/test_limit_duality.py）。
    `res` 必须是用同一组 contacts / dim / k 算出的 optimal 结果；列数或对偶段长度对不上直接 ValueError，
    不做错位比较（审查 C1/C24：旧版只按摩擦棱重建列表，带黏聚力时与 res.lambdas 错位、且截掉了 y_r）。
    """
    if res.status != OPTIMAL:
        raise ValueError(f"check_duality needs an optimal LimitResult, got status={res.status!r}")
    if origin is None:
        origin = (0.0,) * dim
    nw = 3 if dim == 2 else 6
    C = _build_columns(contacts, origin, dim, k)
    if len(res.lambdas) != len(C.cols) or len(res.mechanism) != nw or len(res.row_duals) != C.n_rows:
        raise ValueError(
            f"result does not match these contacts/dim/k: {len(res.lambdas)} lambdas vs {len(C.cols)} columns, "
            f"{len(res.mechanism)} mechanism vs {nw}, {len(res.row_duals)} row duals vs {C.n_rows} rows")
    y, yr = res.mechanism, res.row_duals
    power = [_dot(y, w) + (yr[rj] if rj is not None else 0.0) for w, rj in zip(C.cols, C.row_of)]
    worst_admissible = min(power + list(yr), default=0.0)
    drive = _dot(y, live)
    upper = -_dot(y, dead) + sum(yr)
    comp = 0.0
    for lam_j, p_j in zip(res.lambdas, power):
        if lam_j > tol:
            comp = max(comp, abs(p_j))
    for r_i in range(C.n_rows):
        slack = 1.0 - sum(lam_j for lam_j, rj in zip(res.lambdas, C.row_of) if rj == r_i)
        if slack > tol:
            comp = max(comp, abs(yr[r_i]))
    if res.alpha > tol:
        comp = max(comp, abs(drive - 1.0))
    return {"admissible": worst_admissible >= -tol, "worst_power": worst_admissible,
            "drive": drive, "upper_bound": upper, "alpha": res.alpha,
            "duality_gap": abs(upper - res.alpha), "complementarity": comp}
