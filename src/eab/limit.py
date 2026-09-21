"""L3 互补层第一块砖：**单边摩擦接触下的刚体极限分析**。

## 为什么先做它

L5 的 TIA 首枪只能给**剪胀比**（几何/运动学量）。要给"承载力"就必须有力学，
而写整套 DDA 时间步进既重复 bdda2 又答非所问——极限分析**直接给出破坏荷载，不需要时间步进**。

## 理论

下限定理（静力）：若存在一组容许接触力与外荷载平衡，则该荷载不大于极限荷载。
容许 = 单边（压不受拉）+ 库仑摩擦锥内。写成线性规划：

    max α   s.t.   Σ_ij λ_ij w_ij + W_dead + α·W_live = 0 ,  λ ≥ 0

其中 w_ij = (d_ij, (p_i − o) × d_ij) 是第 i 个接触第 j 条摩擦锥棱的**旋量**（wrench）。

上限定理（运动）：这个 LP 的**对偶解就是破坏机构**。对偶可行性 yᵀw_ij ≥ 0 说的正是
"虚速度场不得贯入任何接触"（符号约定见 `mechanism_is_admissible`：正 = 分离），
而强对偶 α* = −yᵀW_dead 就是上限定理的功率平衡。
**所以静力下限与运动上限由同一次求解同时给出，且必然相等——这是这一层的自校验结构。**

与盖系统的接口：约束 yᵀw ≥ 0 的那组法向，正是盖枚举输出的完备清单。
换句话说，**"机构不得进入入口块"就是这里的运动学容许条件**——L1 与 L3 在此咬合。

## 诚实条款

- **二维的摩擦锥线性化是精确的**（锥恰有两条极棱）；三维用 k 边内接棱锥，
  是**偏安全**的近似（内接 ⇒ 容许集变小 ⇒ 下限更保守），偏差量级 1 − cos(π/k)。
- 刚体、小变形、接触位置在加载中**不变**——极限分析的标准前提。几何非线性不在内。
- 只做**单个动体对固定边界**。多体机构需要把各体的自由度并进同一组平衡方程（未实现）。
- 本构目前只有库仑摩擦 + 可选黏聚力；抗拉一律为零（单边）。
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


def contacts_from_covers(covers, *, mu: float, cohesion: float = 0.0,
                         use_midpoint: bool = True) -> list[LimitContact]:
    """把盖枚举的输出接进来。接触点取见证段中点（或 B 侧点），法向取盖法向。"""
    out = []
    for c in covers:
        if c.normal is None or c.point_a is None or c.point_b is None:
            continue
        p = tuple((a + b) / 2.0 for a, b in zip(c.point_a, c.point_b)) if use_midpoint \
            else tuple(c.point_b)
        out.append(LimitContact(p, tuple(c.normal), mu, cohesion,
                                c.area or 0.0, c.label()))
    return out


# ------------------------------------------------------------------ 极限荷载

@dataclass(slots=True)
class LimitResult:
    status: str
    alpha: float                         # 极限荷载因子
    lambdas: list[float]                 # 各摩擦锥棱的乘子（静力场）
    mechanism: list[float]               # 对偶解 = 破坏机构（二维 (vx,vy,ω)，三维 6 维旋量）
    contact_forces: list[Vec] = field(default_factory=list)
    active: list[tuple] = field(default_factory=list)   # 乘子非零的接触标签
    iterations: int = 0


def limit_load(contacts: list[LimitContact], dead: list[float], live: list[float], *,
               dim: int = 3, origin: Vec | None = None, k: int = 8,
               tol: float = 1e-9) -> LimitResult:
    """max α s.t. Σ λ w + W_dead + α W_live = 0, λ ≥ 0。

    `dead` / `live` 是已经算好的旋量（用 `wrench` 造）。返回的 `mechanism` 是对偶解，
    即上限定理的破坏机构；`contact_forces` 是每个接触上合成的力。
    """
    if origin is None:
        origin = (0.0,) * dim
    nw = 3 if dim == 2 else 6
    cols: list[list[float]] = []
    owner: list[int] = []
    # 黏聚列必须**有界**：|F_s| ≤ c·A 与法向压力无关，若写成无界非负射线，
    # 黏聚力可以无限放大、LP 直接报无界（2026-09-21 实测）。每个黏聚接触加一行 Σλ + s = 1。
    coh_rows: list[list[int]] = []
    for ci, ct in enumerate(contacts):
        for g in friction_generators(ct.normal, ct.mu, dim, k):
            cols.append(wrench(g, ct.point, origin, dim))
            owner.append(ci)
        if ct.cohesion > 0.0 and ct.area > 0.0:
            idx: list[int] = []
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
                idx.append(len(cols) - 1)
            coh_rows.append(idx)
    cols.append(live)                                  # α 也是一个非负变量
    owner.append(-1)
    ncol = len(cols) + len(coh_rows)                   # 末尾追加各黏聚行的松弛变量
    A = [[cols[j][i] if j < len(cols) else 0.0 for j in range(ncol)] for i in range(nw)]
    b = [-v for v in dead]
    for r_i, idx in enumerate(coh_rows):
        row = [0.0] * ncol
        for j in idx:
            row[j] = 1.0
        row[len(cols) + r_i] = 1.0                     # 松弛
        A.append(row)
        b.append(1.0)
    c = [0.0] * (len(cols) - 1) + [1.0] + [0.0] * len(coh_rows)
    r = maximize(A, b, c, tol=tol * 1e-3)
    if r.status != OPTIMAL:
        return LimitResult(r.status, float("inf") if r.status == UNBOUNDED else float("nan"),
                           [], [], iterations=r.iterations)
    alpha = r.x[len(cols) - 1]
    lam = r.x[:len(cols) - 1]
    forces: list[Vec] = [tuple(0.0 for _ in range(dim)) for _ in contacts]
    for j, ci in enumerate(owner[:-1]):
        if lam[j] <= tol:
            continue
        g = cols[j][:dim]
        forces[ci] = tuple(forces[ci][i] + lam[j] * g[i] for i in range(dim))
    active = sorted({contacts[owner[j]].label for j in range(len(lam))
                     if lam[j] > tol and contacts[owner[j]].label is not None})
    return LimitResult(OPTIMAL, alpha, lam, list(r.y), forces, active, r.iterations)


def mechanism_power(mech: list[float], ct: LimitContact, g: Vec, origin: Vec, dim: int) -> float:
    return sum(m * wi for m, wi in zip(mech, wrench(g, ct.point, origin, dim)))


def mechanism_is_admissible(mech: list[float], contacts: list[LimitContact], *,
                            dim: int = 3, origin: Vec | None = None, k: int = 8,
                            tol: float = 1e-7) -> bool:
    """上限侧的自检：机构对**每一条**摩擦锥棱的虚功率 yᵀw **≥ 0**。

    符号约定要说清楚（2026-09-21 我先写反过一次，全部算例误报不容许）：
    `mech` 就是动体的虚速度旋量，法向取"固定体推动体"的方向，于是

        yᵀw > 0  ⟺  该锥棱上两体**分离**（容许，互补条件要求那里 λ = 0）
        yᵀw = 0  ⟺  该锥棱**活动**（正在滑动/受压的那一条）
        yᵀw < 0  ⟺  **贯入或超出摩擦锥**（不容许）

    所以容许条件是 ≥ 0，不是 ≤ 0。验算：倾覆机构 y = (0, 1/3, −1/3) 在左角给出
    yᵀw = 2/3 > 0（左角确实在抬起），在右趾给出 0（支点不动）。
    """
    if origin is None:
        origin = (0.0,) * dim
    for ct in contacts:
        for g in friction_generators(ct.normal, ct.mu, dim, k):
            if mechanism_power(mech, ct, g, origin, dim) < -tol:
                return False
    return True


def check_duality(res: LimitResult, contacts: list[LimitContact], dead: list[float],
                  live: list[float], *, dim: int = 3, origin: Vec | None = None,
                  k: int = 8, tol: float = 1e-7) -> dict:
    """静力下限与运动上限的自校验——这一层的核心结构，必须逐项成立。

    · 机构容许：yᵀw ≥ 0（每条锥棱）
    · 驱动归一：yᵀW_live ≥ 1
    · 强对偶：  α = −yᵀW_dead   ← 上限定理的功率平衡
    · 互补：    λ_j > 0 ⟹ yᵀw_j = 0
    """
    if origin is None:
        origin = (0.0,) * dim
    y = res.mechanism
    cols, gens = [], []
    for ct in contacts:
        for g in friction_generators(ct.normal, ct.mu, dim, k):
            cols.append(wrench(g, ct.point, origin, dim))
            gens.append((ct, g))
    worst_admissible = min((sum(m * wi for m, wi in zip(y, w)) for w in cols), default=0.0)
    drive = sum(m * wi for m, wi in zip(y, live))
    upper = -sum(m * wi for m, wi in zip(y, dead))
    comp = 0.0
    for j, w in enumerate(cols):
        if j < len(res.lambdas) and res.lambdas[j] > tol:
            comp = max(comp, abs(sum(m * wi for m, wi in zip(y, w))))
    return {"admissible": worst_admissible >= -tol, "worst_power": worst_admissible,
            "drive": drive, "upper_bound": upper, "alpha": res.alpha,
            "duality_gap": abs(upper - res.alpha), "complementarity": comp}
