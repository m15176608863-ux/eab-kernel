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
**所以静力下限与运动上限由同一次求解同时给出，精确算术里二者相等——这是这一层的自校验结构。**
浮点里"相等"要靠核验，不靠定理：`limit_load` 返回 optimal 之前把荷载与机构平移到**接触形心**跑一遍
`check_duality`（相对判据），机构不容许、驱动不为 1、相对间隙或互补超标就抛 RuntimeError
（2026-09-24 订正：旧文"必然相等"在 G6 的大块体 + 黏聚算例上不成立，上限曾少 41.8%）。
门：tests/test_invariance_limit.py、tests/test_limit_scale.py::test_self_check_rejects_a_corrupted_mechanism。

与盖系统的接口：约束 yᵀw ≥ 0 的那组法向，正是盖枚举输出的完备清单。
换句话说，**"机构不得进入入口块"就是这里的运动学容许条件**——L1 与 L3 在此咬合。

## 数值（2026-09-24，G6 之后）

调用方的坐标可以是工程坐标（离原点 1e3–1e5 m）、单位可以是 SI（荷载 1e8 N、黏聚 1e6 Pa）。
`limit_load` 内部做两件对调用方透明、且精确可逆的事：
  · **力矩参考点移到接触点形心 o'**：调用方给的恒载/活荷载旋量按 m' = m − (o' − o) × f 平移到 o'，
    接触列直接关于 o' 构造；返回的机构（旋量）按对偶的规律 v_o = v_o' + (o' − o) × ω 变回调用方的 o。
    力臂于是 ~ 块体尺寸而不是 ~ 坐标量级——这从根上消除"大力臂"一类数值病
    （G6 critical 0：块体放在 (1000, 2000, 300) m、默认原点，黏聚上限行在比值检验里掉出，报 unbounded、α = ∞）。
  · **黏聚列用力的单位**：LP 里黏聚变量是黏聚力本身（单位方向列），上限行写成 Σ μ_coh + s = c·A；
    返回前换回文档化的口径（`lambdas` 是占 c·A 的比例，`row_duals` 是黏聚耗散）。
    旧写法把 c·A 乘进列里，列均衡后上限行的系数 ~ 1/(c·A·力臂)，SI 单位下落到阈值以下。
所有判据（活动接触、容许性、互补、间隙）都是**相对**的。门：tests/test_invariance_limit.py（纪律 F）。

**精确模型（2026-09-27 返修四）**：LP 是调用方数据的**精确**模型——接触列的力矩 (p − o′) × g 与荷载向形心的平移
都用有理数算（`_exact_wrench`、`_exact_shift`），浮点层只拿到它们的正确舍入，答案由 lp.py 对这个精确 LP 精确给出。
黏聚上限 c·A 也是精确乘积（reverify5：曾用 fl(c·A)）。唯一不精确的是模型定义本身：锥棱方向与黏聚方向取浮点
（锥与黏聚圆的 k 边形线性化）。返修三曾让 LP 对"浮点算出的派生数据"精确，
复核者 reverify4 的 critical 就出在这里：V 槽夹住的顶点上两个重合接触有一对夹持力，实数里合力矩为 0，浮点里各列的
r × g 各自舍入，3e16 的夹持力拼出舍入级的力矩，报"承载无限"（真值 0）。

**可分辨性（筛查，不是保证）**：数据本身可能带着舍入级的分量——θ = π 的推力带 sin π = 1.22e-16 的竖向分量，
数据的精确最优是 α = 8.17e15，物理上是荒谬值。解出之后沿**返回的那个机构**算 α 对活荷载输入舍入的一阶估计
U = Σ|y_i|·e_i / |yᵀW_live|（`_live_uncertainty`；e_i 见 `_wrench_rounding`，含调用方在工程坐标上算力矩带进的
u·|p|·|F|），报在 `LimitResult.uncertainty`。U > 1e-6 时把活荷载推 ±16 倍舍入、精确重解看实际变化：推后不可行
⇒ 报 infeasible；实测变化仍超标 ⇒ 抛 RuntimeError；否则照常返回并报实测值。荷载进 LP 之前**不做清洗**
（09-27 一度用 |M|/|F| 当长度清洗，近纯力偶上把真实力矩清掉、α 静默偏高 2–3.8 倍，已撤回）。
**U 不是界。** 它只看一个机构、只看活荷载：
  · 实数里的刀刃输入（荷载作用线恰过接触点、存在不做功也不耗散的自由机构）上，对偶最优面含零驱动方向，
    返回的机构给出 U ~ 1e-15，而活荷载在 ±16 倍舍入盒内一动，α 就跳到 0 或翻倍；同一问题换刚体坐标系（数据的
    舍入跟着变）答案也跟着变。复核者宽生成器（荷载常作用在接触点上）里约 3% 的 optimal 属此类（09-27 返修四
    重测：1498 例里 42 例、1645 例里 44 例）。这类输入的答案对**给定数据**精确，但对理想化前的真实构形不稳，
    任何有限精度的实现都做不到坐标系无关；
  · 接触几何（位置、法向）与恒载的舍入不计：两个重合接触被扰开 1e-15 就出现真实的力臂与楔入，状态可以在
    optimal 与 unbounded 之间翻（复核者 303#386）；α → 0 的近极限平衡态上 α 的相对精度可能远差于 U（实测 α ~ 1e-11
    时 1e-5 量级），那里应看 α 的绝对量；
  · UNBOUNDED：取最小可行荷载因子 α_min（> 0 时）的机构，一阶估计超标就推 ±16 倍舍入、重解原问题，要求"无界"这个
    结论本身仍在（推后不可行 ⇒ 报 infeasible；推后变成有限值 ⇒ 抛错不认证）。reverify5：曾要求 α_min 的相对精度 ≤ 1e-6，
    α_min 既不报给调用方、也不影响结论，工程坐标下把稳定的自锁误判成不认证。不推的情形有两种：α_min = 0（不靠活荷载
    就可行），以及 α_min > 0 但沿其机构的一阶估计 ≤ 1e-6——于是荷载线过接触点、沿锥棱的"刀刃自锁"可能被直接认证，
    而活荷载在 ±16 倍舍入盒内一动就有有限值（reverify6：专门构造的 UTM 小块体刀刃家族里，盒内有限值低到约 1.5e5；
    同一家族里认证与"不认证"只取决于这个一阶估计跨不跨 1e-6）；
  · 荷载恰好落在某个承载边界上（例：单个黏聚接触，力恰等于 μN + cA）也是刀刃：推 1e-15 就不可行，而返回的机构给出的
    U 可以很小（reverify5 在宽生成器里找到 2 例不属于"自由机构"的刀刃：202#2999 是这一类；11#1538 其实是活荷载作用线
    以 1.2e-16 的距离经过两个接触点、且有重合接触——属于上一条，reverify6 订正）；
  · 工程坐标（离原点 1e5–1e6 m）下，调用方关于原点算力矩 p × F 本身带 u·|p|·|F| 的舍入，e_i 如实计入它，于是离原点远、
    块体小时 α 的实测不确定度会超过 1e-6 而抛错不认证——这是输入本身的精度，不是求解器的（reverify5：1.6 万例里 5 例，
    α 约为自重的 29–490 倍、实测 1.1–1.9e-6）；
  · 推 16 倍舍入就不可行时报 infeasible，偏保守一侧。复核者宽生成器（limfuzz，荷载常作用在接触点上、接触常重合）
    返修四实测每 3000 例：推后不可行 0–7 例、抛错不认证 9–15 例（0.3–0.5%，全是数据精确最优 4.9e15–1.3e17 的舍入驱动值，
    b6468f3 在这些例上报 unbounded）；其余状态与 b6468f3 逐例相同，只有 1 例不同且是基线错（α = −3.3e-15，精确不可行）。
  门：tests/test_limit_fuzz.py::test_small_load_component_resolvability_has_three_regimes、
  ::test_a_large_first_order_uncertainty_alone_does_not_reject；tests/test_lp_certificates.py。

## 诚实条款

- **二维的摩擦锥线性化是精确的**（锥恰有两条极棱）；三维用 k 边内接棱锥，是**偏安全**的近似：
  内接 ⇒ 容许集变小 ⇒ 承载力不高于精确锥。量化：正 k 边形的内切圆半径是外接圆的 cos(π/k) 倍，
  所以内接棱锥 ⊇ 摩擦系数 μ·cos(π/k) 的精确圆锥——**承载力夹在 μ·cos(π/k) 与 μ 两个精确锥的解之间**。
  纯滑动（承载力正比于切向能力）时相对短缺 ∈ [0, 1 − cos(π/k)]：**摩擦阻力方向**（滑动方向的反向）正对一条棱时为 0，
  平分两棱时取到上界；k 为偶数时棱扇中心对称、按滑动方向说等价，k 为奇数时"滑动方向正对一条棱"恰是最坏情形
  （G6 第三轮 minor）。误差取决于阻力方向相对切向基架的夹角，**不随 k 单调**
  （互锁算例 4|k 时恰有一条棱落在荷载平面内而精确，k=5 反而明显变差）。
  门：tests/test_limit.py 的三个锥线性化门，tests/test_limit_scale.py 的 Patton 全格。
- **三维棱扇的朝向默认不随刚体转动协变。** 默认切向基架由 `_tangents(n)` 按全局坐标轴选取（球面上不存在处处连续的
  切向场，任何"默认"都做不到协变），所以把整个模型转一下，α 可以在上面的 [cos(π/k), 1] 夹逼内变。
  需要严格协变（或想让某条棱对准预期的摩擦阻力方向，即滑动方向的反向）时，给 `LimitContact.tangent`：基架 t₁ 取它在切平面上的投影，
  t₂ = n × t₁，随模型一起转即严格不变。门：tests/test_invariance_limit.py 的两个门。
- 刚体、小变形、接触位置在加载中**不变**——极限分析的标准前提。几何非线性不在内。
- 本模块只做**单个动体对固定边界**；多体（各体自由度并进同一组平衡方程、接触在两体间成对出现）在 `limit_multi.py`
  （M1，2026-10-10：`limit_load_multi` / `check_duality_multi` / `mechanism_is_admissible_multi`，有门、未经独立重审）。
- 本构目前只有库仑摩擦 + 可选黏聚力；抗拉一律为零（单边）。
- **破坏机构（对偶解）一般不唯一。** 承载力 α 唯一，但对偶最优集可以是一整个面：三维内接棱锥下，推力方向恰落在一条锥棱上时，机构的切向速度可以在该棱两侧 ±π/k 内任取（实测 cb2 滑动偏 −22.5°）；退化位形（对称、共面接触）下还可能混入其他零耗散分量。读破坏模式时不要读机构的逐分量取值，要问**某个候选机构是否属于对偶最优面**（容许、驱动为 1、上限 = α）。**"是否转动"不是一般的不变量**（2026-09-24 订正）：cb2 滑动时对偶最优面里既有纯平动 + 关联剪胀，也有带转动的机构，例如 μ=0.4 时 (1, 0, 0.4, 0.117, 0, −0.293)——返回哪一个取决于单纯形的主元顺序。只有当**任何**纯平动的上限都严格大于 α 时（如倾覆），"必带转动"才是不变量。门：tests/test_end_to_end_cb2.py::test_failure_mode_is_read_off_invariants_of_the_dual_face。
- **经盖接进来的接触不带黏聚。** `contacts_from_covers` 拿到的只有盖的代表面积（VF/FV 是整张面、EE 是 None），
  不是各接触分到的面片面积；照搬会把 c·A 高估（cb2 上 16 倍，不安全一侧）。在真正的面片分配实现之前，
  它对 cohesion > 0 一律抛 ValueError。门：tests/test_limit_contacts.py。
"""

from __future__ import annotations

import math

from dataclasses import dataclass, field
from fractions import Fraction
from math import cos, pi, sin

from .lp import OPTIMAL, UNBOUNDED, _fl, maximize

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


def _shift_wrench(w: list[float], d: Vec, dim: int) -> list[float]:
    """关于 o 的旋量 → 关于 o + d 的旋量：力不变，m' = m − d × f。精确的线性变换（只有舍入）。"""
    if dim == 2:
        return [w[0], w[1], w[2] - (d[0] * w[1] - d[1] * w[0])]
    f = w[:3]
    return [f[0], f[1], f[2],
            w[3] - (d[1] * f[2] - d[2] * f[1]),
            w[4] - (d[2] * f[0] - d[0] * f[2]),
            w[5] - (d[0] * f[1] - d[1] * f[0])]


def _exact_wrench(force: Vec, point: Vec, origin: Vec, dim: int) -> list[Fraction]:
    """`wrench` 的精确版：力取原浮点值，r = point − origin 与 r × force 用有理数精确算。

    为什么要精确（2026-09-27，reverify4 的 critical）：同一点上两个接触（顶点夹在 V 槽两壁之间）有一对互相抵消的
    夹持力，实数里它们的合力矩精确为 0；浮点里每列的 r × g 各自舍入，于是 3e16 的夹持力能拼出一个舍入级的力矩，
    LP 对这组**派生**数据精确地无界，报"承载无限"。力矩列精确之后，零合力的组合合力矩也精确为零。"""
    F = [Fraction(v) for v in force[:dim]]
    r = [Fraction(point[i]) - Fraction(origin[i]) for i in range(dim)]
    if dim == 2:
        return F + [r[0] * F[1] - r[1] * F[0]]
    return F + [r[1] * F[2] - r[2] * F[1], r[2] * F[0] - r[0] * F[2], r[0] * F[1] - r[1] * F[0]]


def _exact_shift(w: list[float], origin: Vec, to: Vec, dim: int) -> list[Fraction]:
    """关于 origin 的（浮点）旋量 → 关于 to 的精确旋量：m' = m − (to − origin) × f，全用有理数。"""
    W = [Fraction(v) for v in w]
    d = [Fraction(to[i]) - Fraction(origin[i]) for i in range(dim)]
    f = W[:dim]
    if dim == 2:
        return f + [W[2] - (d[0] * f[1] - d[1] * f[0])]
    return f + [W[3] - (d[1] * f[2] - d[2] * f[1]), W[4] - (d[2] * f[0] - d[0] * f[2]), W[5] - (d[0] * f[1] - d[1] * f[0])]


def _twist_back(y: list[float], d: Vec, dim: int) -> list[float]:
    """关于 o + d 的速度旋量 → 关于 o 的速度旋量（`_shift_wrench` 的对偶）：v_o = v_{o+d} + d × ω。
    于是对任意旋量 w 有 y_oᵀ w_o = y_{o+d}ᵀ w_{o+d}（功率不变）。"""
    if dim == 2:
        return [y[0] + y[2] * d[1], y[1] - y[2] * d[0], y[2]]
    om = y[3:]
    return [y[0] + (d[1] * om[2] - d[2] * om[1]),
            y[1] + (d[2] * om[0] - d[0] * om[2]),
            y[2] + (d[0] * om[1] - d[1] * om[0]),
            om[0], om[1], om[2]]


def _twist_forward(y: list[float], d: Vec, dim: int) -> list[float]:
    """关于 o 的速度旋量 → 关于 o + d 的速度旋量（`_twist_back` 的逆）：v_{o+d} = v_o − d × ω。"""
    if dim == 2:
        return [y[0] - y[2] * d[1], y[1] + y[2] * d[0], y[2]]
    om = y[3:]
    return [y[0] - (d[1] * om[2] - d[2] * om[1]),
            y[1] - (d[2] * om[0] - d[0] * om[2]),
            y[2] - (d[0] * om[1] - d[1] * om[0]),
            om[0], om[1], om[2]]


def _tangents(n: Vec, dim: int, tangent: Vec | None = None) -> list[Vec]:
    """切向基架。二维 t = n 转 +90°（随转动协变）。三维默认按全局坐标轴选 t₁（不协变，见诚实条款），
    给了 `tangent` 时取它在切平面上的投影；两种情况 t₂ = n × t₁。"""
    if dim == 2:
        return [(-n[1], n[0])]
    if tangent is None:
        a = (1.0, 0.0, 0.0) if abs(n[0]) < 0.9 else (0.0, 1.0, 0.0)
        t1 = (a[1] * n[2] - a[2] * n[1], a[2] * n[0] - a[0] * n[2], a[0] * n[1] - a[1] * n[0])
    else:
        nn = sum(v * v for v in n)
        tn = sum(t * v for t, v in zip(tangent, n)) / nn
        t1 = tuple(tangent[i] - tn * n[i] for i in range(3))
    ln = sum(v * v for v in t1) ** 0.5
    if not ln > 0.0:
        raise ValueError(f"tangent {tangent!r} has no component in the tangent plane of normal {n!r}")
    t1 = tuple(v / ln for v in t1)
    t2 = (n[1] * t1[2] - n[2] * t1[1], n[2] * t1[0] - n[0] * t1[2], n[0] * t1[1] - n[1] * t1[0])
    return [t1, t2]


def friction_generators(normal: Vec, mu: float, dim: int, k: int = 8,
                        tangent: Vec | None = None) -> list[Vec]:
    """库仑锥的棱方向（单位法向 + μ·切向）。二维恰两条（精确）；三维 k 条（内接，偏安全）。"""
    ts = _tangents(normal, dim, tangent)
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
    """极限分析看到的一个接触：位置、法向（固定体推动体的方向；构造时归一化为单位向量）、摩擦、可选黏聚力与面积。

    `tangent`（仅三维、可选）：内接棱锥的第一条棱朝向（取其在切平面上的投影）。不给则用全局基架
    `_tangents(n)`——它不随刚体转动协变（见模块诚实条款）。"""
    point: Vec
    normal: Vec
    mu: float = 0.0
    cohesion: float = 0.0          # 黏聚强度（与 area 相乘得到附加抗剪力）
    area: float = 0.0
    label: tuple | None = None
    tangent: Vec | None = None

    def __post_init__(self):
        """法向归一化（G6 第二轮 major：曾不检查也不归一，三维摩擦与黏聚承载力随 |n| 缩放——|n| = 1e-3 时报 500、
        真值 0.5，自校验照样放行）。|n| 为 0 或非有限时抛 ValueError。二维纯摩擦的锥角本就与 |n| 无关。"""
        m = max((abs(v) for v in self.normal), default=0.0)
        if not (m > 0.0 and all(math.isfinite(v) for v in self.normal)):   # NaN 在任一分量都拒：max() 对 NaN 的比较恒假

            raise ValueError(f"contact normal must be a finite nonzero vector, got {self.normal!r}")
        n = sum((v / m) ** 2 for v in self.normal) ** 0.5
        self.normal = tuple(v / m / n for v in self.normal)
        # G6 第四轮 minor：cohesion / area 为 NaN 或负数曾被 `cohesion > 0 and area > 0` 静默当成"无黏聚"，α 按纯摩擦给出、
        # 自校验照常通过；mu 为 NaN 只在 Fraction(nan) 处以无关信息报错。非有限输入要在入口响亮失败（与法向同一家族）
        for name in ("mu", "cohesion", "area"):
            v = getattr(self, name)
            if not (math.isfinite(v) and v >= 0.0):
                raise ValueError(f"contact {name} must be finite and non-negative, got {v!r}")


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

    **黏聚（2026-09-24，G6 major 23）**：盖的 `area` 是代表面积——VF/FV 是整张面的面积、EE 是 None——
    不是这个接触分到的接触面片面积。旧实现把它原样当黏聚面积：cb2 四个角点各拿到整张底面 16，
    c = 1 时承载 67 而非 7（黏聚项高估 16 倍，不安全一侧），EE 接触的黏聚被 `or 0.0` 静默丢掉。
    真正的面片分配（A/B 重叠多边形在接触面上的面积，分给共用该面的接触、Σ = 真实面片面积）实现之前，
    `cohesion > 0` 一律 ValueError；返回的接触 `area = 0`（不从盖继承，免得事后改 cohesion 时再被放大）。
    """
    if side not in _SIDES:
        raise ValueError(f"side must be one of {_SIDES}, got {side!r}")
    if cohesion > 0.0:
        raise ValueError(
            "contacts_from_covers cannot carry cohesion yet: a cover's `area` is the representative face area "
            "(the whole face for VF/FV, None for EE), not the contact patch this contact owns, so c·area would "
            "overstate cohesive capacity (16x on cb2) or silently drop it (EE). Build LimitContact objects with "
            "the actual patch areas instead.")
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
        out.append(LimitContact(p, tuple(c.normal), mu, 0.0, 0.0, c.label()))
    return out


# ------------------------------------------------------------------ LP 的列

@dataclass(slots=True)
class _Columns:
    cols: list[list[float]]          # 每列的旋量（不含 α 列与松弛列）
    owner: list[int]                 # 该列所属接触的下标
    row_of: list[int | None]         # 黏聚列所在黏聚行的下标；摩擦列为 None
    n_rows: int                      # 黏聚行数 = 带黏聚力（cohesion > 0 且 area > 0）的接触数
    cap: list[float] = field(default_factory=list)   # 各黏聚行的 c·A


def _build_columns(contacts: list[LimitContact], origin: Vec, dim: int, k: int, *,
                   unit_cohesion: bool = False) -> _Columns:
    """LP 的列：每个接触先是它的摩擦锥棱，若有黏聚力紧接着是它的黏聚列。

    `limit_load`、`check_duality`、`mechanism_is_admissible` 三处**共用**这一个定义——
    列序、黏聚列的插入位置、黏聚行编号只在这里写一次（审查 C1/C24：三处各造一遍就会错位）。
    黏聚列必须**有界**：|F_s| ≤ c·A 与法向压力无关，若写成无界非负射线，黏聚力可以无限放大、
    LP 直接报无界（2026-09-21 实测）。所以每个黏聚接触对应一行 Σλ_coh + s = 1。

    `unit_cohesion=True`（只给 `limit_load` 内部的 LP 用）：黏聚列取单位方向的旋量（变量是黏聚力本身，
    单位与摩擦列相同），上限行相应写成 Σμ + s = c·A。对外口径（check_duality 等）用默认的 c·A 倍列。
    """
    cols: list[list[float]] = []
    owner: list[int] = []
    row_of: list[int | None] = []
    cap: list[float] = []
    n_rows = 0
    for ci, ct in enumerate(contacts):
        for g in friction_generators(ct.normal, ct.mu, dim, k, ct.tangent):
            cols.append(wrench(g, ct.point, origin, dim))
            owner.append(ci)
            row_of.append(None)
        if ct.cohesion > 0.0 and ct.area > 0.0:
            mag = ct.cohesion * ct.area
            if dim == 2:
                t = _tangents(ct.normal, dim)[0]
                dirs = [tuple(sg * v for v in t) for sg in (1.0, -1.0)]
            else:
                t1, t2 = _tangents(ct.normal, dim, ct.tangent)
                dirs = [tuple(cos(2.0 * pi * j / k) * t1[i] + sin(2.0 * pi * j / k) * t2[i]
                              for i in range(3)) for j in range(k)]
            f = 1.0 if unit_cohesion else mag
            for d in dirs:
                cols.append(wrench(tuple(f * v for v in d), ct.point, origin, dim))
                owner.append(ci)
                row_of.append(n_rows)
            cap.append(mag)
            n_rows += 1
    return _Columns(cols, owner, row_of, n_rows, cap)


# ------------------------------------------------------------------ 极限荷载

@dataclass(slots=True)
class LimitResult:
    status: str
    alpha: float                         # 极限荷载因子
    lambdas: list[float]                 # 各列乘子，列序 = `_build_columns`（摩擦棱，随后该接触的黏聚列）
    mechanism: list[float]               # 对偶解的旋量段 = 破坏机构（二维 (vx,vy,ω)，三维 6 维旋量），关于调用方的 origin
    contact_forces: list[Vec] = field(default_factory=list)
    active: list[tuple] = field(default_factory=list)   # 乘子非零的接触标签
    iterations: int = 0
    row_duals: list[float] = field(default_factory=list)  # 各黏聚行的对偶乘子（黏聚耗散），行序同 `_build_columns`
    uncertainty: float = 0.0   # α 对活荷载输入舍入的一阶估计 U（沿返回的机构；**不是**界，见模块文档"可分辨性"）；UNBOUNDED 时为 0


_SELF_CHECK = 1e-7


_UNCERTAIN = 1e-6      # α 的输入舍入不确定度上限（见 `_live_uncertainty`）；超过即不认证
_FLIP = 16.0           # "分辨率内不可行"的扰动幅度：活荷载各分量舍入量级的 _FLIP 倍
_U_IN = 4.0 * 2.0 ** -53   # 调用方构造荷载旋量（三角函数、叉积、平移）的相对舍入量级


def _wrench_rounding(w: list[float], dim: int, R: float) -> list[float]:
    """旋量各分量（内部参考点下）的**输入舍入量级** e_i。

    力分量 e_F = u·|F|（旋转框架里每个分量都带整个力的舍入），力矩分量 e_M = u·(|M| + |F|·R)，u = _U_IN，
    R = 接触点到调用方 origin 的最大距离：调用方关于 origin 算力矩 p × F、以及内部平移 M − d × F，
    各带进 ~u·|p|·|F| 的舍入，块体放在工程坐标上时这一项主导。**不用 |M|/|F| 当长度**（2026-09-27 订正）：
    近纯力偶的荷载只剩舍入级的合力，|M|/|F| 被撑到 ~1e16，曾把另一荷载的真实力矩当噪声清零、α 静默偏高
    2–3.8 倍（复核者 reverify3 的 critical）。对刚体运动与单位缩放按量纲协变。"""
    fl, ml = _norm(w[:dim]), _norm(w[dim:])
    return [_U_IN * fl] * dim + [_U_IN * (ml + fl * R)] * (len(w) - dim)


def _live_uncertainty(y: list[float], live_c: list[float], e: list[float]) -> float:
    """U = Σ_i |y_i|·e_i / |yᵀW_live|：沿机构 y 看，α 对活荷载输入舍入的一阶相对敏感度（估计，**不是**界）。

    推导：机构 y 给出上限 α_y = R_y / (yᵀW_live)（R_y 是恒载与黏聚的功率，不含活荷载）。活荷载各分量
    扰动 |δ_i| ≤ e_i 时驱动变为 yᵀW_live + yᵀδ，于是**这个机构给出的上限** α_y 的相对变化 ≤ U。真正的 α 是所有机构上限
    的最小值：对偶退化时别的最优机构可能对扰动敏感得多（刀刃输入），所以 U 只是估计。U ~ 1 说明答案**完全靠舍入分量撑着**：
    θ = π 的水平推力带 sin π = 1.22e-16 的竖向分量、单点接触撑不住偏心自重时，浮点 LP 给 α = 8.17e15；
    无摩擦地面 + 带水平分量的恒载、θ = 3π/2 的"竖直"推力给 α = 5.44e15（与恒载大小无关——旧判据"α 超过
    自然荷载尺度 1e10 倍"在恒载 1e6 以上漏掉了它，复核者 res_probe 实测）。近自锁的真实答案 U ≈ u/余量，
    离自锁 1e-8 时 U ~ 6e-8，照常认证。"""
    drive = abs(sum(yi * li for yi, li in zip(y, live_c)))
    num = sum(abs(yi) * ei for yi, ei in zip(y, e))
    if drive == 0.0:
        return float("inf") if num > 0.0 else 0.0
    return num / drive


def limit_load(contacts: list[LimitContact], dead: list[float], live: list[float], *,
               dim: int = 3, origin: Vec | None = None, k: int = 8,
               tol: float = 1e-9, lp_tol: float | None = None) -> LimitResult:
    """max α s.t. Σ λ w + W_dead + α W_live = 0, λ ≥ 0（每个黏聚接触另有 Σλ_coh ≤ 1）。

    `dead` / `live` 是已经算好的、关于 `origin`（None = 坐标原点）的旋量（用 `wrench` 造）。
    返回的 `mechanism` 是对偶解的旋量段（关于 `origin`），即上限定理的破坏机构；`row_duals` 是各黏聚行的乘子；
    `contact_forces` 是每个接触上合成的力。内部把力矩参考点移到接触形心再解（见模块文档"数值"），对调用方透明。

    `tol`：活动判据，**相对**——`contact_forces` 与 `active` 忽略力的大小 ≤ tol·(最大列力) 的列。
    `lp_tol`：LP 的入基（最优性）相对阈值（None = lp.solve 的默认值）。它只影响迭代路径：
    LP 返回 optimal 前按固定阈值核验对偶可行性，放宽的 lp_tol 早停时会被清理（G6 minor 24）。

    返回 optimal 之前，在接触形心处跑 `check_duality`（相对判据 1e-7）：不容许、驱动 ≠ 1、
    相对间隙或互补超标即抛 RuntimeError——"自带上下限自校验"是代码行为，不是一句文档。
    """
    if origin is None:
        origin = (0.0,) * dim
    nw = 3 if dim == 2 else 6
    if len(dead) != nw or len(live) != nw:
        raise ValueError(f"dead/live must be {nw}-component wrenches for dim={dim}")
    # 内部参考点：接触点形心（没有接触时就用调用方的 origin）
    if contacts:
        oc = tuple(sum(ct.point[i] for ct in contacts) / len(contacts) for i in range(dim))
    else:
        oc = tuple(origin[:dim])
    dvec = tuple(oc[i] - origin[i] for i in range(dim))
    # 荷载平移到形心、接触列的力矩：一律用有理数精确算（见 `_exact_wrench`），LP 由此是调用方数据的**精确**模型；
    # 浮点层只拿到这些精确量的正确舍入。
    dead_x = _exact_shift(list(dead), origin, oc, dim)
    live_x = _exact_shift(list(live), origin, oc, dim)
    dead_c = [_fl(v) for v in dead_x]
    live_c = [_fl(v) for v in live_x]
    # 活荷载的输入舍入量级（不确定度 U 用，见下面"可分辨性"）。荷载本身**不做任何清洗**。
    Rmag = max((_norm(tuple(ct.point[i] - origin[i] for i in range(dim))) for ct in contacts), default=0.0)
    e_in = _wrench_rounding(live_c, dim, Rmag)
    C = _build_columns(contacts, oc, dim, k, unit_cohesion=True)
    Cx = [_exact_wrench(col[:dim], contacts[C.owner[j]].point, oc, dim) for j, col in enumerate(C.cols)]
    # 黏聚上限 c·A 也精确（reverify5：曾用浮点乘积 fl(c·A)，c = 0.1、A = 3 的刀刃上状态可翻）
    capx = [Fraction(0)] * C.n_rows
    for j, rj in enumerate(C.row_of):
        if rj is not None:
            ct = contacts[C.owner[j]]
            capx[rj] = Fraction(ct.cohesion) * Fraction(ct.area)

    def _solve(live_v: list[Fraction], sense: float = 1.0):
        """活荷载列 live_v 给精确值（Fraction）。"""
        colsx = Cx + [live_v]                          # α 也是一个非负变量
        ncol = len(colsx) + C.n_rows                   # 末尾追加各黏聚行的松弛变量
        zero = Fraction(0)
        AX = [[colsx[j][i] if j < len(colsx) else zero for j in range(ncol)] for i in range(nw)]
        bX = [-v for v in dead_x]
        for r_i in range(C.n_rows):
            row = [zero] * ncol
            for j, rj in enumerate(C.row_of):
                if rj == r_i:
                    row[j] = Fraction(1)
            row[len(colsx) + r_i] = Fraction(1)        # 松弛
            AX.append(row)
            bX.append(capx[r_i])                       # 力的单位：Σμ_coh + s = c·A（精确乘积）
        c = [0.0] * len(C.cols) + [sense] + [0.0] * C.n_rows      # sense = −1：最小可行荷载因子
        A = [[_fl(v) for v in row] for row in AX]
        b = [_fl(v) for v in bX]
        kw = {} if lp_tol is None else {"tol": lp_tol}
        return maximize(A, b, c, exact=(AX, bX, c), **kw)

    ia = len(C.cols)

    def _pushes(y):
        """沿机构 y 最敏感的方向把活荷载推 ±_FLIP 倍舍入量级（δ_i = ±sign(y_i)·_FLIP·e_i），精确重解原问题（max α）。"""
        push = [(1.0 if yi > 0.0 else -1.0 if yi < 0.0 else 0.0) * _FLIP * ei for yi, ei in zip(y, e_in)]
        return (_solve([li - Fraction(pi) for li, pi in zip(live_x, push)]),
                _solve([li + Fraction(pi) for li, pi in zip(live_x, push)]))

    def _resolvable(res):
        """(U, 判定, 迭代数)：判定 ∈ {"ok", "infeasible", "unresolved"}，见下面"可分辨性"注释。"""
        a0 = res.x[ia]
        y = list(res.y[:nw])
        U0 = _live_uncertainty(y, live_c, e_in)
        if U0 <= _UNCERTAIN:
            return U0, "ok", 0
        rm, rp = _pushes(y)
        its = rm.iterations + rp.iterations
        if "infeasible" in (rm.status, rp.status):
            return U0, "infeasible", its
        if rm.status == OPTIMAL and rp.status == OPTIMAL and a0 > 0.0:
            U = max(abs(rm.x[ia] - a0), abs(rp.x[ia] - a0)) / (_FLIP * a0)
            return U, ("ok" if U <= _UNCERTAIN else "unresolved"), its
        return U0, "unresolved", its

    r = _solve(live_x)
    # 可分辨性（筛查，不是保证；见模块文档"可分辨性"）：LP 对给定数据精确，但数据可能带着舍入级的分量（θ = π 的推力
    # 带 sin π 的竖向分量，数据的精确最优是 α = 8.17e15）。一阶估计 U（见 `_live_uncertainty`）≤ _UNCERTAIN 时照常返回——
    # 它**不是**界：只沿返回的这一个机构、只看活荷载，刀刃输入上可以严重低估（模块文档）。U 超标时**不**凭这个机构下结论：对偶退化时最优机构不唯一，近奇异基上的机构分量
    # 可达 ~1e16，一阶 U 会把普通推力判成"不可分辨"（09-27 实测宽模糊 2/1000）。改为把活荷载沿该机构最敏感的方向推
    # ±_FLIP 倍舍入量级（δ_i = ∓sign(y_i)·_FLIP·e_i），精确重解两次，看 α 的**实际**变化（`_resolvable`）：
    #   任一侧不可行（精确 Farkas）⇒ 报 infeasible（"在 16 倍输入舍入之内不可行"，答案靠舍入级分量撑着）；
    #   两侧都 optimal 且实测相对变化 / _FLIP ≤ _UNCERTAIN ⇒ 认证，uncertainty 报实测值；
    #   否则抛错不认证（本意就很小的荷载分量、离自锁 < ~1e-10 的几何：α 有意义但到不了 1e-6，不给假精度）。
    # UNBOUNDED 同样要查（复核者 reverify3：UTM 坐标下会倾覆的块体报"承载无限"，靠的是内部平移带进的舍入级力矩）：
    # 无界的前提是可行，所以对最小可行荷载因子 α_min 做同一检查；α_min = 0（不靠活荷载就可行）时不查——
    # 活荷载恰落在接触锥边界上的"刀刃自锁"因此不在检查范围内（模块文档"可分辨性"）。
    # 门：tests/test_limit_fuzz.py::test_small_load_component_resolvability_has_three_regimes（三个区间）、
    # tests/test_lp_certificates.py（任意恒载下的舍入驱动、近自锁在报告的 U 之内、退化机构不误判、UTM 倾覆）。
    if r.status == UNBOUNDED:
        # "无界"的前提是可行：取最小可行荷载因子 α_min 的机构，一阶估计超标时沿它推 ±16 倍舍入、重解**原问题**，
        # 看"无界"这个结论本身是否还在（reverify5：曾要求 α_min 的相对精度 ≤ 1e-6——α_min 既不报给调用方、也不影响
        # 无界结论，工程坐标下把稳定的自锁误判成不认证，40 个 UTM 摆放里 14 个）。
        rmin = _solve(live_x, -1.0)
        its = r.iterations + rmin.iterations
        if rmin.status == OPTIMAL and rmin.x[ia] > 0.0:
            y = list(rmin.y[:nw])
            U0 = _live_uncertainty(y, live_c, e_in)
            if U0 > _UNCERTAIN:
                rm, rp = _pushes(y)
                its += rm.iterations + rp.iterations
                if "infeasible" in (rm.status, rp.status):
                    return LimitResult("infeasible", float("nan"), [], [], iterations=its, uncertainty=U0)
                if not (rm.status == rp.status == UNBOUNDED):
                    raise RuntimeError(f"limit_load: unbounded capacity is not certified: pushing the live load by "
                                       f"{_FLIP:g}x its input rounding gives {rm.status}/{rp.status}")
        return LimitResult(UNBOUNDED, float("inf"), [], [], iterations=its)
    if r.status != OPTIMAL:
        return LimitResult(r.status, float("nan"), [], [], iterations=r.iterations)
    alpha = r.x[ia]
    U, verdict, its = _resolvable(r)
    if verdict == "infeasible":
        return LimitResult("infeasible", float("nan"), [], [], iterations=r.iterations + its, uncertainty=U)
    if verdict == "unresolved":
        raise RuntimeError(f"limit_load: load factor {alpha:.6e} has relative uncertainty {U:.1e} from input "
                           f"rounding (> {_UNCERTAIN:.0e}) and is not certified: it depends on rounding-level load "
                           f"components, near-self-locking geometry, or (at engineering coordinates) the caller's own "
                           f"moment rounding u·|p|·|F|")
    raw = r.x[:len(C.cols)]
    lam = [v / C.cap[rj] if rj is not None else v for v, rj in zip(raw, C.row_of)]
    # 各列的力（力的单位）：摩擦列 λ·g，黏聚列 μ·d
    fvec = [tuple(raw[j] * C.cols[j][i] for i in range(dim)) for j in range(len(C.cols))]
    fmag = [_norm(f) for f in fvec]
    fmax = max(fmag, default=0.0)
    on = [fm > tol * fmax for fm in fmag]
    forces: list[Vec] = [tuple(0.0 for _ in range(dim)) for _ in contacts]
    for j, ci in enumerate(C.owner):
        if on[j]:
            forces[ci] = tuple(forces[ci][i] + fvec[j][i] for i in range(dim))
    active = sorted({contacts[C.owner[j]].label for j in range(len(raw))
                     if on[j] and contacts[C.owner[j]].label is not None})
    mech = _twist_back(list(r.y[:nw]), dvec, dim)
    row_duals = [yv * cap for yv, cap in zip(r.y[nw:], C.cap)]
    res = LimitResult(OPTIMAL, alpha, lam, mech, forces, active, r.iterations, row_duals=row_duals,
                      uncertainty=U)
    d = check_duality(res, contacts, dead, live, dim=dim, origin=origin, k=k, tol=_SELF_CHECK)
    if not d["ok"]:
        raise RuntimeError(f"limit_load self-check failed (duality check at the contact centroid): "
                           f"{ {key: d[key] for key in ('admissible', 'worst_power_rel', 'drive', 'duality_gap_rel', 'complementarity')} }")
    return res


def mechanism_power(mech: list[float], ct: LimitContact, g: Vec, origin: Vec, dim: int) -> float:
    return sum(m * wi for m, wi in zip(mech, wrench(g, ct.point, origin, dim)))


def _dot(y: list[float], w: list[float]) -> float:
    return sum(m * wi for m, wi in zip(y, w))


def _adot(y: list[float], w: list[float]) -> float:
    return sum(abs(m * wi) for m, wi in zip(y, w))


def _powers(y: list[float], yr: list[float] | None, C: _Columns) -> tuple[list[float], list[float]]:
    """列 j 的约化功率 p_j = yᵀw_j (+ y_r) 及其舍入尺度 Σ|y_i w_ij| (+ |y_r|)。"""
    p, s = [], []
    for w, rj in zip(C.cols, C.row_of):
        extra = yr[rj] if (rj is not None and yr is not None) else 0.0
        p.append(_dot(y, w) + extra)
        s.append(_adot(y, w) + abs(extra))
    return p, s


def _norm(v) -> float:
    """欧氏范数，先按最大分量归一（1e160 量级的力平方不溢出，1e-200 量级的不下溢成 0）。"""
    m = max((abs(x) for x in v), default=0.0)
    if m == 0.0 or m == float("inf") or m != m:
        return m
    return m * sum((x / m) ** 2 for x in v) ** 0.5


def _speed_scale(y: list[float], C: _Columns, s: list[float], dim: int, loads=()) -> float:
    """机构的特征速度 V̂ = max(各列 Σ|y_i w_ij| / |f_j|，各荷载 Σ|y_i W_i| / |F_W|)。

    功率 ÷ 力 = 速度：V̂ 是机构在接触点（及荷载作用处）的速度量级，对刚体运动不变、随单位按速度缩放，
    与列的力量级（摩擦棱是单位向量、黏聚列是 c·A）无关。

    为什么需要它（2026-09-25，G6 复核 G2/G3）：只用列自己的 Σ|y_i w_ij| 作尺度时，与机构正交的列
    （倾覆时基面上的黏聚列：精确 p_j 与其尺度都恰为 0）尺度本身就是舍入噪声，p_j / 尺度 ≈ ±1，
    正确的最优机构被判不容许、互补 0.77、limit_load 自校验抛错（物理模糊测试 10/2000，基线答案经独立证书核验为最优）。
    于是每列的尺度取 Σ|y_i w_ij| + |f_j|·V̂：p_j ≥ −tol·尺度 说的是"该接触的贯入速度不超过机构速度量级的 tol 倍"。"""
    V = 0.0
    for w, sj in zip(C.cols, s):
        f = _norm(w[:dim])
        if f > 0.0:
            V = max(V, sj / f)
    for W in loads:
        f = _norm(W[:dim])
        if f > 0.0:
            V = max(V, _adot(y, W) / f)
    return V


def _scales(y: list[float], yr: list[float] | None, C: _Columns, dim: int, loads=()):
    """(p, 列尺度, 各黏聚行尺度 cap_r·V̂, V̂)：列尺度 = Σ|y_i w_ij| + |y_r| + |f_j|·V̂（见 `_speed_scale`）。"""
    p, s = _powers(y, yr, C)
    V = _speed_scale(y, C, s, dim, loads)
    scale = [sj + _norm(w[:dim]) * V for w, sj in zip(C.cols, s)]
    rscale = [cap * V for cap in C.cap]
    return p, scale, rscale, V


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

    **判据是相对的**（2026-09-24，G6 minor 3）：p_j ≥ −tol·(Σ_i|y_i w_ij| + |y_r| + |f_j|·V̂)，y_r ≥ −tol·c_rA_r·V̂，
    V̂ 是机构的特征速度（`_speed_scale`）。旧版用绝对 1e-7，SI 单位 + 工程坐标下（功率 ~ y_r·力臂 ~ 1e8）
    把正确的机构判成不容许；2026-09-24 版只用列自己的 Σ|y_i w_ij|，与机构正交的列尺度是舍入噪声，又把正确机构
    判成不容许（2026-09-25 订正，门：tests/test_limit_scale.py::test_columns_orthogonal_to_the_mechanism_…）。
    """
    if origin is None:
        origin = (0.0,) * dim
    nw = 3 if dim == 2 else 6
    if len(mech) != nw:
        raise ValueError(f"mechanism must have {nw} components for dim={dim}, got {len(mech)}")
    # 在接触形心判定（见 `check_duality`：调用方坐标系里的尺度被 |ω|·|o' − o| 放大，UTM 下放行贯入的机构）
    oc = (tuple(sum(ct.point[i] for ct in contacts) / len(contacts) for i in range(dim)) if contacts
          else tuple(origin[:dim]))
    mech = _twist_forward(list(mech), tuple(oc[i] - origin[i] for i in range(dim)), dim)
    C = _build_columns(contacts, oc, dim, k)
    if row_duals is not None and len(row_duals) != C.n_rows:
        raise ValueError(f"row_duals has {len(row_duals)} entries, contacts give {C.n_rows} cohesion rows")
    p, s, rs, _ = _scales(mech, row_duals, C, dim)
    if row_duals is not None and any(v < -tol * sr for v, sr in zip(row_duals, rs)):
        return False
    for pj, sj, rj in zip(p, s, C.row_of):
        if rj is not None and row_duals is None:
            continue
        if pj < -tol * sj:
            return False
    return True


def check_duality(res: LimitResult, contacts: list[LimitContact], dead: list[float],
                  live: list[float], *, dim: int = 3, origin: Vec | None = None,
                  k: int = 8, tol: float = 1e-7) -> dict:
    """静力下限与运动上限的自校验——这一层的核心结构，必须逐项成立。

    记 y = res.mechanism（旋量段）、y_r = res.row_duals（黏聚行），列 j 的约化功率
    p_j = yᵀw_j + (y_r[行(j)]，若 j 是黏聚列；摩擦列为 0)。LP 的对偶是 min bᵀy s.t. Aᵀy ≥ c，
    b = (−W_dead, 1, …, 1)，于是：

    · 机构容许（对偶可行）：p_j ≥ 0（每一列，含黏聚列），y_r ≥ 0（松弛列），**驱动 yᵀW_live ≥ 1**（α 列）
    · 强对偶：  α = −yᵀW_dead + Σ y_r   ← 上限定理的功率平衡（Σ y_r 是黏聚耗散）
    · 互补：    λ_j > 0 ⟹ p_j = 0；松弛 s_r = 1 − Σ_{j∈r} λ_j > 0 ⟹ y_r = 0；α > 0 ⟹ yᵀW_live = 1

    **全部判据是相对的**（2026-09-24，G6 minor 3 / critical 19；2026-09-25 加速度量级 V̂）：
      · 尺度：列 j 为 Σ_i|y_i w_ij| + |y_r| + |f_j|·V̂，黏聚行 r 为 c_rA_r·V̂，V̂ 是机构的特征速度
        （`_speed_scale`，含恒载与活荷载）。只用列自己的 Σ|y_i w_ij| 时，与机构正交的列（精确功率与尺度都为 0）
        的比值是 噪声/噪声 ≈ ±1，正确的最优机构被判不容许（G6 复核 G3）；
      · `admissible`：p_j ≥ −tol·尺度_j、y_r ≥ −tol·尺度_r、drive ≥ 1 − tol·max(1, Σ|y_i W_live,i|)。旧版用绝对 1e-7 且只在 α > tol 时看驱动：
        α = 0、机构为零的错解被判"容许、间隙 0、互补 0"（G6 critical 19 的自校验盲区）——零机构驱动为 0，现在不容许；
      · `duality_gap_rel` = |上限 − α| / G，G = |α| + Σ_i|y_i W_dead,i| + Σ|y_r| + |F_dead|·V̂
        （末项是恒载功率的量级：α = 0 时前几项可以全是舍入，G6 复核 case 147 曾报 duality_gap_rel = 1.0）；
      · `complementarity`（无量纲）：活动列（力 > tol·最大列力）上 |p_j| / 尺度_j 的最大值、
        未用满的黏聚行上 |y_r| / 尺度_r、α·驱动 > tol·G 时的 |驱动 − 1| / max(1, Σ|y_i W_live,i|)；
      · `ok` = admissible 且 duality_gap_rel ≤ tol 且 complementarity ≤ tol。
    `worst_power`、`duality_gap` 仍给出原始（有量纲）值，`worst_power_rel` 是 min_j p_j / 尺度_j。

    **静力一侧**（2026-09-27，G6 第二轮 major）：`static_residual_rel` = ‖Σλ_j w_j + W_dead + α·W_live‖ 按力、力矩分块
    除以各自的物理尺度（Σ|λ_j||w_j| + |W_dead| + α|W_live|，力矩块再加 力尺度 × 接触臂），另查 λ ≥ 0、各黏聚行 Σλ ≤ 1、
    α ≥ 0（`static_ok`）。旧版只查机构一侧，只能证明"α 不低于真值"——不安全的一侧；LP 列代码丢了参考点时 α = 15
    （闭式 10）照样 ok。
    **在接触形心判定**（同上，major）：荷载按 m' = m − d × f、机构按 v' = v − d × ω 平移到接触点形心 o'（浮点，
    舍入 ~u·|o' − o|/L），列在 o' 处用 `_build_columns` 的**浮点**路径独立构造。于是各尺度是物理尺度：旧版在调用方坐标系
    里判定，尺度被 |ω|·|o' − o| 放大 ~|p|/L 倍（UTM 下 ~4e6），tol = 1e-7 实际放宽成 O(1)，α×0.5、×2 都被放行。
    与 `limit_load` 的关系（纪律 A 的如实声明）：两边共用的只有锥棱与黏聚方向（`friction_generators`/`_tangents`，
    它们是模型定义）；力矩与荷载平移 `limit_load` 用有理数（`_exact_wrench`/`_exact_shift`），这里用浮点，互不共用。
    `res` 必须是用同一组 contacts / dim / k 算出的 optimal 结果；列数或对偶段长度对不上直接 ValueError，
    不做错位比较（审查 C1/C24：旧版只按摩擦棱重建列表，带黏聚力时与 res.lambdas 错位、且截掉了 y_r）。
    """
    if res.status != OPTIMAL:
        raise ValueError(f"check_duality needs an optimal LimitResult, got status={res.status!r}")
    if origin is None:
        origin = (0.0,) * dim
    nw = 3 if dim == 2 else 6
    oc = (tuple(sum(ct.point[i] for ct in contacts) / len(contacts) for i in range(dim)) if contacts
          else tuple(origin[:dim]))
    dvec = tuple(oc[i] - origin[i] for i in range(dim))
    C = _build_columns(contacts, oc, dim, k)
    if len(res.lambdas) != len(C.cols) or len(res.mechanism) != nw or len(res.row_duals) != C.n_rows:
        raise ValueError(
            f"result does not match these contacts/dim/k: {len(res.lambdas)} lambdas vs {len(C.cols)} columns, "
            f"{len(res.mechanism)} mechanism vs {nw}, {len(res.row_duals)} row duals vs {C.n_rows} rows")
    dead = _shift_wrench(list(dead), dvec, dim)
    live = _shift_wrench(list(live), dvec, dim)
    y, yr = _twist_forward(list(res.mechanism), dvec, dim), res.row_duals
    # 静力一侧：平衡残差（力、力矩分块，物理尺度）与 λ、黏聚行、α 的符号
    arm = max((_norm(tuple(ct.point[i] - oc[i] for i in range(dim))) for ct in contacts), default=0.0)
    lam = list(res.lambdas)
    resid = [sum(l * w[i] for l, w in zip(lam, C.cols)) + dead[i] + res.alpha * live[i] for i in range(nw)]
    fsc = sum(abs(l) * _norm(w[:dim]) for l, w in zip(lam, C.cols)) + _norm(dead[:dim]) + abs(res.alpha) * _norm(live[:dim])
    msc = (sum(abs(l) * _norm(w[dim:]) for l, w in zip(lam, C.cols)) + _norm(dead[dim:])
           + abs(res.alpha) * _norm(live[dim:]) + fsc * arm)
    static_rel = max(_norm(resid[:dim]) / fsc if fsc > 0.0 else _norm(resid[:dim]),
                     _norm(resid[dim:]) / msc if msc > 0.0 else _norm(resid[dim:]))
    rows_ok = all(sum(l for l, rj in zip(lam, C.row_of) if rj == r_i) <= 1.0 + tol for r_i in range(C.n_rows))
    static_ok = static_rel <= tol and min(lam, default=0.0) >= 0.0 and rows_ok and res.alpha >= 0.0
    power, pscale, rscale, V = _scales(y, yr, C, dim, loads=(dead, live))
    drive = _dot(y, live)
    # 驱动的舍入尺度：远坐标下 yᵀW_live 是平动项与转动项的大量相消（块体 2 cm、离原点 4000 km 时 Σ|y_i W_i| ~ 1e2，
    # 驱动读成 1 + 2⁻²³），判据按它相对化；无相消时 dscale ≈ 1，与旧判据相同（2026-09-27）
    dscale = max(1.0, _adot(y, live))
    upper = -_dot(y, dead) + sum(yr)
    G = abs(res.alpha) + _adot(y, dead) + sum(abs(v) for v in yr) + _norm(dead[:dim]) * V
    worst_raw = min(power + list(yr), default=0.0)
    worst_rel = 0.0
    for pj, sj in zip(power, pscale):
        if pj < 0.0:
            worst_rel = min(worst_rel, pj / sj if sj > 0.0 else -1.0)
    for v, sr in zip(yr, rscale):
        if v < 0.0:
            worst_rel = min(worst_rel, v / sr if sr > 0.0 else -1.0)
    admissible = worst_rel >= -tol and drive >= 1.0 - tol * dscale
    # 互补（无量纲）
    fmag = [abs(lam) * sum(v * v for v in w[:dim]) ** 0.5 for lam, w in zip(res.lambdas, C.cols)]
    fmax = max(fmag, default=0.0)
    comp = 0.0
    for fm, pj, sj in zip(fmag, power, pscale):
        if fm > tol * fmax and sj > 0.0:
            comp = max(comp, abs(pj) / sj)
    for r_i in range(C.n_rows):
        slack = 1.0 - sum(lam_j for lam_j, rj in zip(res.lambdas, C.row_of) if rj == r_i)
        if slack > tol and yr[r_i] != 0.0:
            comp = max(comp, abs(yr[r_i]) / rscale[r_i] if rscale[r_i] > 0.0 else 1.0)
    if res.alpha * abs(drive) > tol * G:
        comp = max(comp, abs(drive - 1.0) / dscale)
    gap = abs(upper - res.alpha)
    gap_rel = gap / G if G > 0.0 else gap
    return {"admissible": admissible, "worst_power": worst_raw, "worst_power_rel": worst_rel,
            "drive": drive, "upper_bound": upper, "alpha": res.alpha,
            "duality_gap": gap, "duality_gap_rel": gap_rel, "complementarity": comp,
            "static_residual_rel": static_rel, "static_ok": static_ok,
            "ok": admissible and gap_rel <= tol and comp <= tol and static_ok}
