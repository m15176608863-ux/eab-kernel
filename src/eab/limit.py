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
返回 optimal 之前必须核验给定数据与保留的有理数见证：`check_duality` 在调用方原点独立重建精确模型，
静力、容许性、驱动约束、强对偶或互补不成立就抛 RuntimeError
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
活动接触显示采用相对筛选；静力、容许性、互补和间隙均在有理数上精确核。门：tests/test_invariance_limit.py（纪律 F）。

**精确模型（2026-09-27 返修四）**：LP 是调用方数据的**精确**模型——接触列的力矩 (p − o′) × g 与荷载向形心的平移
都用有理数算（`_exact_wrench`、`_exact_shift`），浮点层只拿到它们的正确舍入，答案由 lp.py 对这个精确 LP 精确给出。
黏聚上限 c·A 也是精确乘积（reverify5：曾用 fl(c·A)）。唯一不精确的是模型定义本身：锥棱方向与黏聚方向取浮点
（锥与黏聚圆的 k 边形线性化）。返修三曾让 LP 对"浮点算出的派生数据"精确，
复核者 reverify4 的 critical 就出在这里：V 槽夹住的顶点上两个重合接触有一对夹持力，实数里合力矩为 0，浮点里各列的
r × g 各自舍入，3e16 的夹持力拼出舍入级的力矩，报"承载无限"（真值 0）。

**可分辨性（报告，不改答案，E4）**：LP 的 status/alpha 对给定数据精确。输入本身可能包含舍入级分量，
`uncertainty` 报沿一个返回机构的活荷载一阶敏感度 U（不是界，也不覆盖所有对偶最优面/几何/恒载的不确定性）。
U > 1e-6 时将活荷载沿该机构推 ±16 倍输入舍入并精确重解，仅把邻域结果写入 `resolvability_statuses`：
- resolved：该筛查未发现超阈变化（不是工程精度保证）；
- nearby_infeasible：至少一个邻域问题不可行；原问题 status/alpha 不变；
- unresolved：邻域变化超阈，或原无界问题在邻域变为有限值；原问题答案不变。
未作分辨性检查的原始 infeasible 用 not_applicable。筛查不再抛“不认证”异常或以邻域 infeasible 替换原始精确答案。
UNBOUNDED 沿最小可行荷载的机构作相同报告；alpha_min=0 和一阶 U 小的刀刃仍可能逃过筛查，resolved 绝不等于稳定性证书。
输入荷载不清洗；单体舍入量级仍包含调用方构造力矩引入的 u*|p-origin|*|F|。多体只使用各体自身的参考点/臂长。
门：tests/test_limit_fuzz.py、tests/test_lp_certificates.py、tests/test_limit_exact_selfcheck.py。

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

## 精确自校验（E4）

静力残差、强对偶间隙、互补与机构容许性全部是有理数等式/符号；没有 tol×恒载/接触力总量的分辨率限制。
返回 alpha/lambdas/mechanism/row_duals 为带不可变 exact 见证的 float 视图；复制保留，算术和 JSON 往返不保留。
纯 float 手工值按其二进制精确值核，Fraction 可表达任意 k 的 alpha×(1-10**(-k)) 注入。
门：tests/test_limit_exact_selfcheck.py；contact_forces/active 仍只是按 tol 截断的展示量，静力证明来自 lambdas。
"""

from __future__ import annotations

import math

from dataclasses import dataclass, field
from fractions import Fraction
from math import cos, pi, sin

from .lp import OPTIMAL, UNBOUNDED, _fl, maximize
from .construction import sqrt_rational, scalar_rational, unit_rational

Vec = tuple[float, ...]


# ------------------------------------------------------------------ 旋量

def _construction_float(value: Fraction) -> float:
    """Round a completed exact construction; never silently erase its range."""
    result = scalar_rational(value)
    if result == 0.0 and value:
        raise ArithmeticError("nonzero wrench/twist construction is below binary64 range")
    return result


def wrench(force: Vec, point: Vec, origin: Vec, dim: int) -> list[float]:
    """Force at point about origin (3 components in 2D, 6 in 3D).

    Form the lever and determinant exactly from the given inputs, then round
    once. Intermediate overflow/underflow cannot erase a representable result;
    an unrepresentable nonzero construction raises. Gate: test_r8fix_wrench.
    """
    return [_construction_float(v) for v in _exact_wrench(force, point, origin, dim)]


def _shift_wrench(w: list[float], d: Vec, dim: int) -> list[float]:
    """Shift a wrench from o to o+d: form m - d cross f exactly, then round."""
    return [_construction_float(v) for v in _exact_shift(w, (0,)*dim, d, dim)]


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


def _twist_transform(y, d, dim, sign):
    # LP calls this with Fractions: retain those exact certificates. Only
    # floating callers request final floating output, after cancellation.
    floating = any(isinstance(v, float) for v in (*y, *d))
    y, d = list(Fraction(_mapped_value) for _mapped_value in y), tuple(Fraction(_mapped_value) for _mapped_value in d)
    if dim == 2:
        result = [y[0] + sign*y[2]*d[1], y[1] - sign*y[2]*d[0], y[2]]
    else:
        om = y[3:]
        result = [y[0] + sign*(d[1]*om[2] - d[2]*om[1]),
                  y[1] + sign*(d[2]*om[0] - d[0]*om[2]),
                  y[2] + sign*(d[0]*om[1] - d[1]*om[0]), *om]
    return [_construction_float(v) for v in result] if floating else result


def _twist_back(y: list[float], d: Vec, dim: int) -> list[float]:
    """Shift a twist from o+d to o: v_o = v_(o+d) + d cross omega.

    Rational callers retain exact certificates; floating callers round only
    the final result. The exact map is power-dual to _shift_wrench.
    """
    return _twist_transform(y, d, dim, 1)


def _twist_forward(y: list[float], d: Vec, dim: int) -> list[float]:
    """Shift a twist from o to o+d; exact inverse of _twist_back."""
    return _twist_transform(y, d, dim, -1)


def _tangents(n: Vec, dim: int, tangent: Vec | None = None) -> list[Vec]:
    """切向基架。二维 t = n 转 +90°（随转动协变）。三维默认按全局坐标轴选 t₁（不协变，见诚实条款），
    给了 `tangent` 时先精确投影、以精确平方比较相对噪声窗口，再构造单位方向；两种情况 t₂ = n × t₁。
    门：test_r9_tangent_frame_is_invariant_to_representable_direction_scale。
    """
    if dim == 2:
        return [(-n[1], n[0])]
    n = tuple(Fraction(_mapped_value) for _mapped_value in n)
    if tangent is None:
        a = (1, 0, 0) if abs(n[0]) < 0.9 else (0, 1, 0)
        t1 = (a[1] * n[2] - a[2] * n[1], a[2] * n[0] - a[0] * n[2], a[0] * n[1] - a[1] * n[0])
    else:
        tangent = tuple(Fraction(_mapped_value) for _mapped_value in tangent)
        nn = sum(v * v for v in n)
        tn = sum(t * v for t, v in zip(tangent, n)) / nn
        t1 = tuple(tangent[i] - tn * n[i] for i in range(3))
        # 被测量是投影 |t1|，它的噪声是 ~u·|tangent| 的舍入（纪律 F）：tangent 与 n 在舍入内平行时 t1 是逐分量的舍入垃圾，
        # 归一化后不在切平面内（n·t1 可达 0.17），内接棱锥被歪斜、承载力静默高估 19%（G6 第五轮 minor）。说不清就报错。
        relative_noise = Fraction(64) * Fraction(2.220446049250313e-16)
        if sum(v * v for v in t1) <= relative_noise**2 * sum(v * v for v in tangent):
            raise ValueError(f"tangent {tangent!r} is parallel to normal {n!r} within rounding; it has no resolvable "
                             f"component in the tangent plane")
    if not any(t1):
        raise ValueError(f"tangent {tangent!r} has no component in the tangent plane of normal {n!r}")
    t1 = unit_rational(t1)
    # The model defines t2 = n cross the returned binary64 t1. Complete each
    # cross-product subtraction exactly before rounding that final component.
    first = tuple(Fraction(_mapped_value) for _mapped_value in t1)
    t2 = tuple(scalar_rational(v) for v in (
        n[1] * first[2] - n[2] * first[1], n[2] * first[0] - n[0] * first[2],
        n[0] * first[1] - n[1] * first[0]))
    return [t1, t2]


def friction_generators(normal: Vec, mu: float, dim: int, k: int = 8,
                        tangent: Vec | None = None) -> list[Vec]:
    """库仑锥的棱方向（单位法向 + μ·切向）。二维恰两条；三维 k 条。

    Complete each component in Fraction before its final binary64 view. The
    3D model retains the supplied frame and libm angular coefficients; it does
    not claim an exact transcendental cone. Gate:
    test_public_friction_generators_round_complete_component.
    """
    ts = _tangents(normal, dim, tangent)
    if dim == 2:
        t = ts[0]
        return [tuple(scalar_rational(Fraction(normal[i]) + Fraction(mu) * Fraction(t[i])) for i in range(2)),
                tuple(scalar_rational(Fraction(normal[i]) - Fraction(mu) * Fraction(t[i])) for i in range(2))]
    t1, t2 = ts
    out = []
    for j in range(k):
        a = 2.0 * pi * j / k
        cosine, sine = Fraction(cos(a)), Fraction(sin(a))
        out.append(tuple(scalar_rational(Fraction(normal[i]) + Fraction(mu) *
                         (cosine * Fraction(t1[i]) + sine * Fraction(t2[i]))) for i in range(3)))
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
        exact = tuple(Fraction(_mapped_value) for _mapped_value in self.normal)
        square = sum(v*v for v in exact)
        # Model directions are rounded only after the complete normalization.
        # In particular v/m/n can round a representable subnormal component
        # twice; no rounded norm or scaled component is an intermediate here.
        self.normal = unit_rational(exact)
        # G6 第四轮 minor：cohesion / area 为 NaN 或负数曾被 `cohesion > 0 and area > 0` 静默当成"无黏聚"，α 按纯摩擦给出、
        # 自校验照常通过；mu 为 NaN 只在 Fraction(nan) 处以无关信息报错。非有限输入要在入口响亮失败（与法向同一家族）
        for name, v in (("mu", self.mu), ("cohesion", self.cohesion), ("area", self.area)):
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
            p = tuple(_construction_float((Fraction(a) + Fraction(b))/2) for a, b in zip(c.point_a, c.point_b))
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
    uncertainty: float = 0.0   # α 对活荷载输入舍入的一阶估计 U（沿返回的机构；**不是**界，见模块文档"可分辨性"）；UNBOUNDED 报最小可行荷载机构的 U
    resolvability: str = "not_applicable"  # resolved / nearby_infeasible / unresolved; never changes status/alpha
    resolvability_statuses: tuple[str, ...] = ()  # exact statuses after minus/plus input-rounding perturbation


_SELF_CHECK = 1e-7


_UNCERTAIN = 1e-6      # 可分辨性报告阈值；只触发邻域筛查，不改变原问题答案
_FLIP = 16.0           # "分辨率内不可行"的扰动幅度：活荷载各分量舍入量级的 _FLIP 倍
_U_IN = 4.0 * 2.0 ** -53   # 调用方构造荷载旋量（三角函数、叉积、平移）的相对舍入量级


def _wrench_rounding(w: list[float], dim: int, R: float) -> list[Fraction]:
    """旋量各分量（内部参考点下）的**输入舍入量级** e_i。

    力分量 e_F = u·|F|（旋转框架里每个分量都带整个力的舍入），力矩分量 e_M = u·(|M| + |F|·R)，u = _U_IN，
    R = 接触点到调用方 origin 的最大距离：调用方关于 origin 算力矩 p × F、以及内部平移 M − d × F，
    各带进 ~u·|p|·|F| 的舍入，块体放在工程坐标上时这一项主导。**不用 |M|/|F| 当长度**（2026-09-27 订正）：
    近纯力偶的荷载只剩舍入级的合力，|M|/|F| 被撑到 ~1e16，曾把另一荷载的真实力矩当噪声清零、α 静默偏高
    2–3.8 倍（复核者 reverify3 的 critical）。对刚体运动与单位缩放按量纲协变。"""
    # This is an input-error estimate, not an exact irrational norm. Approximate
    # only a dimensionless norm in [1,sqrt(n)], then retain its rational scale;
    # neither a subnormal load nor its smaller noise budget is displayed first.
    def scaled_norm(values):
        values = tuple(_rational(v) for v in values)
        scale = max((abs(_mapped_value) for _mapped_value in values), default=Fraction(0))
        if not scale:
            return Fraction(0)
        squared = sum((v/scale)**2 for v in values)
        return Fraction(sqrt_rational(squared)) * scale

    fl, ml = scaled_norm(w[:dim]), scaled_norm(w[dim:])
    u = Fraction(_U_IN)
    return [u * fl] * dim + [u * (ml + fl * Fraction(R))] * (len(w) - dim)


def _live_uncertainty(y: list[float], live_c: list[float], e: list[float]) -> float:
    """U = Σ_i |y_i|·e_i / |yᵀW_live|：沿机构 y 看，α 对活荷载输入舍入的一阶相对敏感度（估计，**不是**界）。

    推导：机构 y 给出上限 α_y = R_y / (yᵀW_live)（R_y 是恒载与黏聚的功率，不含活荷载）。活荷载各分量
    扰动 |δ_i| ≤ e_i 时驱动变为 yᵀW_live + yᵀδ，于是**这个机构给出的上限** α_y 的相对变化 ≤ U。真正的 α 是所有机构上限
    的最小值：对偶退化时别的最优机构可能对扰动敏感得多（刀刃输入），所以 U 只是估计。U ~ 1 说明答案**完全靠舍入分量撑着**：
    θ = π 的水平推力带 sin π = 1.22e-16 的竖向分量、单点接触撑不住偏心自重时，浮点 LP 给 α = 8.17e15；
    无摩擦地面 + 带水平分量的恒载、θ = 3π/2 的"竖直"推力给 α = 5.44e15（与恒载大小无关——旧判据"α 超过
    自然荷载尺度 1e10 倍"在恒载 1e6 以上漏掉了它，复核者 res_probe 实测）。近自锁的真实答案 U ≈ u/余量，
    离自锁 1e-8 时 U ~ 6e-8，照常认证。"""
    # Exact LP witnesses and exact noise scales survive even when their float
    # views are inf/zero. Only the completed dimensionless ratio is displayed.
    try:
        y, live_c, e = (tuple(_rational(v) for v in values) for values in (y, live_c, e))
    except (ValueError, OverflowError):
        return float("nan")  # explicitly classified unresolved by both callers
    drive = abs(sum(yi * li for yi, li in zip(y, live_c)))
    num = sum(abs(yi) * ei for yi, ei in zip(y, e))
    if drive == 0.0:
        return float("inf") if num > 0.0 else 0.0
    return _fl(num / drive)


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

    返回 optimal 之前，精确运行 `check_duality`：静力、容许性、驱动、强对偶或互补不成立即抛 RuntimeError——"自带上下限自校验"是代码行为，不是一句文档。
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
    e_in = _wrench_rounding(live_x, dim, Rmag)
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
        push = [((yi > 0) - (yi < 0)) * Fraction(_FLIP) * ei for yi, ei in zip(y, e_in)]
        return (_solve([li - Fraction(pi) for li, pi in zip(live_x, push)]),
                _solve([li + Fraction(pi) for li, pi in zip(live_x, push)]))

    def _resolvable(res):
        """报告原解对输入舍入的分辨性；邻域问题的状态绝不能替换原问题的精确答案。"""
        a0 = _lp_values(res.x, res.exact_x)[ia]
        y = _lp_values(res.y, res.exact_y)[:nw]
        U0 = _live_uncertainty(y, live_x, e_in)
        if not math.isfinite(U0):
            return U0, "unresolved", 0, ()
        if U0 <= _UNCERTAIN:
            return U0, "resolved", 0, ()
        rm, rp = _pushes(y)
        its = rm.iterations + rp.iterations
        statuses = (rm.status, rp.status)
        if "infeasible" in statuses:
            return U0, "nearby_infeasible", its, statuses
        if rm.status == OPTIMAL and rp.status == OPTIMAL and a0 > 0.0:
            am = _lp_values(rm.x, rm.exact_x)[ia]
            ap = _lp_values(rp.x, rp.exact_x)[ia]
            U = _fl(max(abs(am-a0), abs(ap-a0))/(Fraction(_FLIP)*a0))
            return U, ("resolved" if U <= _UNCERTAIN else "unresolved"), its, statuses
        return U0, "unresolved", its, statuses

    r = _solve(live_x)
    if r.status == UNBOUNDED:
        rmin = _solve(live_x, -1.0)
        its = r.iterations + rmin.iterations
        U0, resolution, statuses = 0.0, "resolved", ()
        if rmin.status == OPTIMAL and _lp_values(rmin.x, rmin.exact_x)[ia] > 0:
            y = _lp_values(rmin.y, rmin.exact_y)[:nw]
            U0 = _live_uncertainty(y, live_x, e_in)
            if not math.isfinite(U0):
                resolution = "unresolved"
            elif U0 > _UNCERTAIN:
                rm, rp = _pushes(y)
                its += rm.iterations + rp.iterations
                statuses = (rm.status,rp.status)
                resolution = ("nearby_infeasible" if "infeasible" in statuses else
                              "resolved" if rm.status == rp.status == UNBOUNDED else "unresolved")
        return LimitResult(UNBOUNDED,float("inf"),[],[],iterations=its,uncertainty=U0,
                           resolvability=resolution,resolvability_statuses=statuses)
    if r.status != OPTIMAL:
        return LimitResult(r.status,float("nan"),[],[],iterations=r.iterations)
    U, resolution, its, statuses = _resolvable(r)
    rx, ry = _lp_values(r.x,r.exact_x), _lp_values(r.y,r.exact_y)
    alpha = _ExactFloat(rx[ia])
    raw = rx[:len(C.cols)]
    lam = [_ExactFloat(v / capx[rj] if rj is not None else v) for v, rj in zip(raw, C.row_of)]
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
    dx = tuple(Fraction(oc[i]) - Fraction(origin[i]) for i in range(dim))
    mech = [_ExactFloat(v) for v in _twist_back(ry[:nw], dx, dim)]
    row_duals = [_ExactFloat(yv * cap) for yv, cap in zip(ry[nw:], capx)]
    res = LimitResult(OPTIMAL, alpha, lam, mech, forces, active, r.iterations, row_duals=row_duals,
                      uncertainty=U,resolvability=resolution,resolvability_statuses=statuses)
    d = check_duality(res, contacts, dead, live, dim=dim, origin=origin, k=k, tol=_SELF_CHECK)
    if not d["ok"]:
        raise RuntimeError(f"limit_load self-check failed (duality check at the contact centroid): "
                           f"{ {key: d[key] for key in ('admissible', 'worst_power_rel', 'drive', 'duality_gap_rel', 'complementarity')} }")
    return res


def mechanism_power(mech: list[float], ct: LimitContact, g: Vec, origin: Vec, dim: int) -> float:
    return _construction_float(sum(Fraction(m)*wi for m, wi in
                                   zip(mech, _exact_wrench(g, ct.point, origin, dim))))


def _norm(v) -> float:
    """Checked final root for finite report inputs; explicit infinities stay reports.

    No scaling division is rounded before the final norm. A finite supplied
    vector whose exact norm is outside binary64 range raises, rather than
    creating a spurious infinity/zero in the report.
    """
    if any(not math.isfinite(x) for x in v):
        return math.hypot(*v)
    return sqrt_rational(sum(Fraction(x)**2 for x in v))


class _ExactFloat(float):
    """float 显示视图，附不可变的有理数 exact 见证。

    普通算术按 float 执行且不继承见证；检查器显式调用 _rational 读取见证。
    list/copy 保留标量见证；float()、算术与 JSON 往返会丢失，此后按新给定数精确核。
    """
    def __new__(cls, exact):
        exact = Fraction(exact)
        obj = super().__new__(cls, _fl(exact))
        object.__setattr__(obj, "_exact", exact)
        return obj

    @property
    def exact(self):
        return self._exact

    def __setattr__(self, name, value):
        raise AttributeError("exact witness is immutable")

    def __reduce__(self):
        return (_ExactFloat, (self.exact,))


def _rational(v):
    """显式提升证书视图；普通 float/Fraction 是调用方给定的精确数。非有限输入报错。"""
    if isinstance(v, _ExactFloat):
        if float(v) != _fl(v.exact):
            raise ValueError("float view does not match its exact witness")
        return v.exact
    try:
        return Fraction(v)
    except (ValueError, OverflowError) as exc:
        raise ValueError("self-check requires finite exact data") from exc


def _lp_values(values, exact):
    """未改的 LP 浮点视图保留证书；手改项（含亚 ulp 的 Fraction 改动）按新值核。"""
    if exact is None or len(values) != len(exact):
        return [_rational(v) for v in values]
    return [e if type(v) is float and v == _fl(e) else _rational(v) for v, e in zip(values, exact)]


def _check_columns(contacts, origin, dim, k):
    """独立静力重建：只共用锥方向的模型定义，不调用 LP 的 _exact_wrench / _exact_shift。

    黏聚列精确乘 c*A，力矩独立计算。门：test_self_check_catches_columns_that_lose_the_reference_point。
    """
    C = _build_columns(contacts, origin, dim, k, unit_cohesion=True)
    cols = []
    caps = [Fraction(0)] * C.n_rows
    for j, col in enumerate(C.cols):
        ct = contacts[C.owner[j]]
        rj = C.row_of[j]
        cap = Fraction(ct.cohesion) * Fraction(ct.area) if rj is not None else Fraction(1)
        if rj is not None:
            caps[rj] = cap
        f = [Fraction(v) * cap for v in col[:dim]]
        p = [Fraction(ct.point[i]) - Fraction(origin[i]) for i in range(dim)]
        moment = ([p[0]*f[1] - p[1]*f[0]] if dim == 2 else
                  [p[1]*f[2]-p[2]*f[1], p[2]*f[0]-p[0]*f[2], p[0]*f[1]-p[1]*f[0]])
        cols.append(f + moment)
    C.cols, C.cap = cols, caps
    return C


def _exact_duality_report(alpha, lam, yr, cols, row_of, dead, live, y):
    """逐项有理数精确核验；*_rel 为无量纲显示，complementarity 为原始乘积，均不参与判定。"""
    alpha = _rational(alpha)
    lam, yr, y = ([_rational(v) for v in seq] for seq in (lam, yr, y))
    dead, live = ([_rational(v) for v in seq] for seq in (dead, live))
    residual = [sum(l*w[i] for l,w in zip(lam,cols)) + d + alpha*v for i,(d,v) in enumerate(zip(dead,live))]
    row_slack = [1-sum(l for l,rj in zip(lam,row_of) if rj == ri) for ri in range(len(yr))]
    static_ok = (all(v == 0 for v in residual) and all(l >= 0 for l in lam)
                 and all(v >= 0 for v in row_slack) and alpha >= 0)
    power = [sum(yi*wi for yi,wi in zip(y,w)) + (yr[rj] if rj is not None else 0)
             for w,rj in zip(cols,row_of)]
    drive = sum(yi*wi for yi,wi in zip(y,live))
    upper = -sum(yi*wi for yi,wi in zip(y,dead)) + sum(yr)
    gap = abs(upper-alpha)
    admissible = all(p >= 0 for p in power) and all(v >= 0 for v in yr) and drive >= 1
    comp = [l*p for l,p in zip(lam,power)] + [s*v for s,v in zip(row_slack,yr)] + [alpha*(drive-1)]
    complementary = all(v == 0 for v in comp)
    # 显示量逐分量归一；是否拒绝只看上面的有理数等式和符号。
    static_rel = max((abs(r)/(sum(abs(l*w[i]) for l,w in zip(lam,cols))+abs(dead[i])+abs(alpha*live[i]))
                      if r else Fraction(0) for i,r in enumerate(residual)), default=Fraction(0))
    denom = abs(alpha)+sum(abs(yi*wi) for yi,wi in zip(y,dead))+sum(abs(v) for v in yr)
    gap_rel = gap/denom if denom else gap
    worst = min(power+yr, default=Fraction(0))
    pscale = [sum(abs(yi*wi) for yi,wi in zip(y,w)) + (abs(yr[rj]) if rj is not None else 0)
              for w,rj in zip(cols,row_of)]
    worst_rel = min([Fraction(0)] + [p/s if s else p for p,s in zip(power,pscale)]
                    + [Fraction(-1) for v in yr if v < 0])
    return {"admissible": admissible, "worst_power": _fl(worst), "worst_power_rel": _fl(worst_rel),
            "drive": _fl(drive), "upper_bound": _fl(upper), "alpha": _fl(alpha),
            "duality_gap": _fl(gap), "duality_gap_rel": _fl(gap_rel),
            "complementarity": _fl(max((abs(v) for v in comp), default=Fraction(0))),
            "static_residual_rel": _fl(static_rel), "static_ok": static_ok,
            "static_residual_exact": tuple(str(v) for v in residual),
            "duality_gap_exact": str(gap), "complementarity_exact": tuple(str(v) for v in comp),
            "ok": admissible and gap == 0 and complementary and static_ok}


def mechanism_is_admissible(mech: list[float], contacts: list[LimitContact], *,
                            dim: int = 3, origin: Vec | None = None, k: int = 8,
                            tol: float = 1e-7, row_duals: list[float] | None = None) -> bool:
    """给定数的精确机构容许性：每根锥棱功率 >= 0，任意小的负号也拒绝。

    tol 仅保留调用兼容，不放宽答案。不提供 row_duals 时只核摩擦列（黏聚耗散未知）。
    带见证的返回标量按见证核；手工 float 机构按其精确二进制值核。
    """
    if origin is None:
        origin = (0.0,) * dim
    nw = 3 if dim == 2 else 6
    if len(mech) != nw:
        raise ValueError(f"mechanism must have {nw} components for dim={dim}, got {len(mech)}")
    C = _check_columns(contacts, origin, dim, k)
    if row_duals is not None and len(row_duals) != C.n_rows:
        raise ValueError(f"row_duals has {len(row_duals)} entries, contacts give {C.n_rows} cohesion rows")
    y = [_rational(v) for v in mech]
    yr = None if row_duals is None else [_rational(v) for v in row_duals]
    if yr is not None and any(v < 0 for v in yr):
        return False
    return all(sum(yi*wi for yi,wi in zip(y,w)) + (yr[rj] if rj is not None else 0) >= 0
               for w,rj in zip(C.cols,C.row_of) if rj is None or yr is not None)


def check_duality(res: LimitResult, contacts: list[LimitContact], dead: list[float],
                  live: list[float], *, dim: int = 3, origin: Vec | None = None,
                  k: int = 8, tol: float = 1e-7) -> dict:
    """同一给定数据上的有理数自校验：平衡、非负、黏聚上限、功率、驱动、强对偶、互补逐项精确。

    不以恒载/接触力尺度判答案；任意非零可表示误差都拒绝（Fraction 可超越 float 分辨率）。
    tol 仅调用兼容，*_rel 仅显示。正确返回值保留 LP 的精确原始/对偶见证，避免把显示舍入认作残差；
    修改项不复用旧见证。静力由 lambdas 核对；contact_forces/active 是截断展示字段，不是证书。
    _check_columns 独立重建力矩，不共用 LP 力矩/荷载平移原语。这不是新的独立 G6 审查。
    """
    if res.status != OPTIMAL:
        raise ValueError(f"check_duality needs an optimal LimitResult, got status={res.status!r}")
    if origin is None:
        origin = (0.0,) * dim
    nw = 3 if dim == 2 else 6
    C = _check_columns(contacts, origin, dim, k)
    if len(res.lambdas) != len(C.cols) or len(res.mechanism) != nw or len(res.row_duals) != C.n_rows:
        raise ValueError("result does not match these contacts/dim/k")
    if len(dead) != nw or len(live) != nw:
        raise ValueError(f"dead/live must have {nw} components")
    return _exact_duality_report(res.alpha,res.lambdas,res.row_duals,C.cols,C.row_of,dead,live,res.mechanism)
