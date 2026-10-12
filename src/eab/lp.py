"""稠密修正单纯形法（两阶段）。纯 Python、零依赖。

L3 极限分析要解的是小规模线性规划（变量数 ~ 接触数 × 摩擦锥棱数，约束数 = 位形自由度 + 黏聚行），
几十到几百量级，稠密够用。

标准型：  min cᵀx   s.t.  Ax = b,  x ≥ 0

返回里带**对偶解 y**：在极限分析里它就是破坏机构（上限定理的运动场），不是附属品。

## 契约（返修三，2026-09-27）

**答案对给定的数据精确成立。** 浮点数是二进有理数，`Fraction(float)` 无损，所以"给定的 LP"本身可以精确处理；
调用方还可以直接给精确数据（`exact=`），浮点矩阵只当它的近似喂给浮点层——在浮点里算不精确的派生量（极限分析里
每列的力矩 r × g、荷载向形心的平移）应当精确地给，否则"精确"只是对一个已经带了舍入的派生问题精确（reverify4 的
critical：两个重合接触上一对夹持力的力矩各列各自舍入，3e16 的夹持力拼出一个舍入级的力矩，报"承载无限"）。
两层（`solve`）：
  · 浮点修正单纯形（`_float_solve`）只给**候选**：状态 + 基（+ 无界时的入基列）；
  · 有理数层（`_Exact.certify`）在原始数据上精确核验候选：OPTIMAL 核 x_B = B⁻¹b ≥ 0（人工变量为 0）与每列约化成本
    ≥ 0（弱对偶即最优）；UNBOUNDED 核可行 + d = B⁻¹A_e ≤ 0 + c_e − c_Bᵀd < 0；INFEASIBLE 核一阶段对偶的 Farkas 条件
    yᵀA ≤ 0、yᵀb > 0。核验不过（或浮点层抛错）就用有理数修正单纯形（`_exact_simplex`，Dantzig 定价、退化过多改
    Bland，精确算术里有限步终止）从候选基热启动或从人工基冷启动走完，再核一次。
返回的 x、y、obj、ray 是精确解各舍入一次的浮点数（超出浮点范围给 ±inf）；浮点层的任何数值失败（奇异、超限、循环、
溢出）都只是"没有候选"，不抛给调用方。逐列的符号判定先用浮点带严格误差界过滤（相对部分 + 次正规/下溢的绝对部分，
见 `_Exact.reduced_sign`），误差界之内的列才用有理数重算——结论与全用有理数相同，只是快。
注意 INFEASIBLE 的 y 是精确 Farkas 证书各分量舍入一次的结果：极少数情形（reverify4：789/56400）舍入后的浮点 y
在浮点里核不出 yᵀb > 0；它的精确性由这里保证，调用方不必也不能用浮点数重核。
性能：每次求解都做 m × m 的有理数求逆，m 大时慢（稠密 101 × 300 约 95 s）；极限分析的 m ≲ 30，不在此列。
有理数兜底用 Dantzig 定价、只在连续退化时改 Bland，最坏情况是指数级：浮点层失败（例如一个 max|A_j| ≲ 1e-298 而
|c_j| ≳ 1e10 的列让 ldexp 溢出）又碰上 Klee–Minty 立方体，m = 20 要 2²⁰−1 次换基，452 s 后撞上换基上限 1e6、
抛错（reverify5/6）。正常路径下浮点层给出的候选只需几次精确换基。

为什么这样（09-21 → 09-27 三轮复核的教训）：浮点阈值兑现不了"绝不静默给错"。绝对阈值让右端项 1e-11 的行整行违反
也被放行（G6）；噪声线 ∝ κ(B) 在病态但合理的基上静默早停（返修一，critical）；返修二把六类阈值都改成"相对量 +
舍入噪声项"，复核者仍构造出纯对角缩放报 UNBOUNDED、行违约 67% 被放行、相对差 1e-10 的可行 LP 报 INFEASIBLE、
ν 封顶导致 50% 次优。每补一个阈值就有反例从另一侧钻出来。精确核验之后，下面"做法"里的全部阈值都只影响速度。

**可分辨性不是 LP 层的事**：数据本身可能带着舍入级的分量（θ = π 的推力带 sin π），浮点数据的精确最优可以是物理上
荒谬的 8e15。那由调用方判断（limit.py 的"可分辨性"）。

## 做法

**尺度规整**（因子全是 2 的幂，乘除精确，不引入舍入）：
  1. 列均衡：A_j 乘 2^−e_j 使 max_i|A_ij| ∈ [0.5, 1)，c_j 同乘；x_j 最后乘回；
  2. 行均衡：行 i 乘 2^−e_i 使 max_j|A_ij| ∈ [0.5, 1)，b_i 同乘；对偶 y_i 最后乘回；
  3. 右端项归一：b 除以 s = 2^⌈log₂ max|b|⌉（**双向**：max|b| < 1 时同样归一；b ≡ 0 时 s = 1）。
     旧实现只在 max b > 1 时归一，于是 max|b| ≲ 1e-10 的不可行问题被判 OPTIMAL（G6 minor 4）；
  4. **目标归一**：c 乘 2^−e 使 max|c_j| ∈ [0.5, 1)，最优值与对偶 y 最后精确还原。旧实现目标行只随列因子缩放、
     入基检验用绝对 1e-10：活荷载旋量 > 2^33 时 α 列永远进不了基，报 OPTIMAL 且 α = 0（G6 critical 19）。
  5. **变量自然尺度** ν_j = min(1, max_i |b_i|/|A_ij|)（`_natural_scales`）：右端项全局归一之后，各变量的量级
     仍可跨十个量级；原始可行性的一切阈值（Harris 松弛、负值判定、一阶段判不可行）都乘 ν_j。ν = 1 的普通变量
     行为逐位不变。
  于是浮点层的阈值都作用在规整后的量级上。这些规整只影响浮点层（候选的质量与速度），不影响答案。

**迭代**：修正单纯形，显式维护基逆 B⁻¹（每次换基做秩一更新，每 32 次换基从原始（规整后）数据重新求逆，
核验前必重新求逆）；x_B = B⁻¹b 每步从 b 重算——表格法的舍入漂移（G6 major 2 的"丢失可行性"）无处累积。
  · 入基：Dantzig（约化成本最负者），判据**相对**：r_j < −tol·(|c_j| + Σ_i|y_i A_ij|)；
  · 出基：Harris 两遍比值检验——先以可行性松弛 1e-9·ν 求步长上界，再在不超过上界的行里取**主元最大**者；
    主元 ≥ 1e-9·max|d| 的"稳定行"优先；主路径上 ≤ 1e-13·max|d| 的元视为舍入噪声（对输入里 cos(π/2) 这种
    垃圾元稳健），射线核验不过之后的退路改用逐分量噪声线 Σ_k|B⁻¹_ik||A_ke|（看得见真实的小尺度行）；
  · 防循环：记录访问过的基集合，**基重复即判循环**，改用扰动右端项（在当前基上把各基变量抬高互异的 ~1e-7·ν，
    使问题非退化）继续；到最优后撤掉扰动，若基解不再可行，用对偶单纯形（同样相对阈值、同样检测循环）修复。
  · 对偶解 y 直接取 c_Bᵀ B⁻¹（重新求逆之后），不再另解 Bᵀy = c_B（G6 major 1：旧 `_duals` 用绝对主元截断，
    大块体带黏聚时对偶行乘子被置 0，上限少 41.8%）。

以上都是浮点层（候选）的做法。门：tests/test_lp.py、tests/test_lp_scale.py、tests/test_lp_fail_loud.py、
tests/test_lp_certificates.py（精确层的牙：`test_a_lying_float_layer_cannot_change_the_answer`）。
"""

from __future__ import annotations

from dataclasses import dataclass
from eab.construction import scalar_rational
from fractions import Fraction
from math import frexp, ldexp

INFEASIBLE, OPTIMAL, UNBOUNDED = "infeasible", "optimal", "unbounded"


@dataclass(slots=True)
class LPResult:
    status: str
    x: list[float]
    obj: float
    y: list[float]            # 对偶解（等式约束的乘子）
    iterations: int
    basis: list[int]          # 各行的基变量下标；≥ n 的是留在基里的人工变量（冗余行）
    ray: list[float] | None = None   # UNBOUNDED 时：经原始 A 核验过的无界射线（原单位，cᵀd < 0）
    exact_x: tuple[Fraction, ...] | None = None  # OPTIMAL 的原始数据精确见证；浮点字段只是显示视图
    exact_y: tuple[Fraction, ...] | None = None



_FEAS = 1e-9              # 原始可行性松弛（规整单位，max|b| ∈ [0.5, 1)）：Harris 比值检验、基解的小负值
_INFEAS = 1e-8            # 一阶段最优值超过它即判不可行（规整单位 ⇒ 相对于 max|b|）
_PIV_STABLE = 1e-9        # 稳定主元：d_i > _PIV_STABLE·max|d|
_PIV_NOISE = 1e-12        # 逐分量噪声线：d_i ≤ _PIV_NOISE·Σ_k|B⁻¹_ik||A_ke| 视为 0（射线核验、退路比值检验、对偶单纯形）
_PIV_NOISE_GLOBAL = 1e-13 # 全局噪声线：d_i ≤ 1e-13·max|d| 视为 0（主路径比值检验，见 `_Revised.ratio`）
_DUAL_CHECK = 1e-9        # 对偶可行性核验（相对，与 tol 无关）
_RAY_CHECK = 1e-9         # 无界射线核验（逐行相对）
_REINVERT = 32            # 每多少次换基重新求逆
_PERTURB = 1e-7           # 防循环扰动的基准幅度（规整单位）
_MAX_PERTURB = 6          # 一次优化里最多扰动几轮
_CLEANUP_ROUNDS = 3       # 核验不过时最多清理几轮
_U_ENTRY = 8.0 * 2.0 ** -53   # 输入元自身的舍入量级（相对 min(行尺度, 列尺度)），见 `_ray_verifies`
_NOISE_FLOOR = 1e-12      # 带条件数余量的舍入噪声底：约化成本（×S，`dual_violation`）、Farkas 证书的列（×nz）
_EPS = 2.0 ** -52


def _exp2(v: float) -> int:
    """|v| = mant·2^e、mant ∈ [0.5, 1) 的 e（v = 0 时为 0）。规整因子一律记成指数、用 ldexp 施加：
    乘除 2 的幂精确，且因子本身不会上溢（2^1031 这类因子不可表示，但 ldexp(x, 1031) 在结果可表示时照样精确）。"""
    if v == 0.0:
        return 0
    return frexp(abs(v))[1]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


class _Revised:
    """规整后问题上的修正单纯形。列 0..n−1 是原变量，n..n+m−1 是人工变量（单位列）。"""

    def __init__(self, A: list[list[float]], b: list[float], max_iter: int):
        m, n = len(A), (len(A[0]) if A else 0)
        self.nu = _natural_scales(A, b)                        # 各变量（含人工）的自然尺度，见 `_natural_scales`
        self.m, self.n = m, n
        self.cols = [[A[i][j] for i in range(m)] for j in range(n)]
        self.cols += [[1.0 if i == k else 0.0 for i in range(m)] for k in range(m)]
        self.acols = [[abs(v) for v in col] for col in self.cols]
        self.csum = [sum(col) for col in self.acols]          # ‖A_j‖₁
        self.b = b
        self.basis = list(range(n, n + m))
        self.inbasis = [False] * n + [True] * m
        self.Binv = [[1.0 if i == k else 0.0 for k in range(m)] for i in range(m)]
        self.since_inv = 0
        self.iters = 0
        self.max_iter = max_iter

    # ---- 线性代数
    def reinvert(self) -> None:
        m = self.m
        M = [[self.cols[self.basis[k]][i] for k in range(m)] + [1.0 if i == r else 0.0 for r in range(m)]
             for i in range(m)]
        big = max((abs(v) for row in M for v in row[:m]), default=0.0)
        for c in range(m):
            p = max(range(c, m), key=lambda i: abs(M[i][c]))
            if not abs(M[p][c]) > 1e-14 * big:
                raise RuntimeError("simplex basis became numerically singular")
            M[c], M[p] = M[p], M[c]
            pv = M[c][c]
            M[c] = [v / pv for v in M[c]]
            for i in range(m):
                if i != c and M[i][c] != 0.0:
                    f = M[i][c]
                    M[i] = [a - f * bb for a, bb in zip(M[i], M[c])]
        self.Binv = [row[m:] for row in M]
        self.since_inv = 0

    def xB(self, b: list[float]) -> list[float]:
        return [_dot(row, b) for row in self.Binv]

    def ftol(self, b: list[float]) -> list[float]:
        """各基变量的原始可行性容差 max(_FEAS·ν_j, x_B[i] = Σ_k B⁻¹_ik b_k 这个点积自身的舍入界 8u·Σ_k|B⁻¹_ik||b_k|)。

        第一项按变量的自然尺度（见 `_natural_scales`）：右端项 1e-11 的行，其松弛变量不许负到 −1e-9。
        第二项按舍入：x_B = −1e-30 这种值可能只是点积的舍入，不是违反。系数是真实的点积舍入界 8u，
        不是 1e-12：病态基上 Σ|B⁻¹||b| 可达 1e5，1e-12 的系数会把 x_B = −1e-7 的基判成"可行"、不再修复，
        α 偏离精确最优 3e-7（09-27 精确有理数对照实测）。它只用来**判定**违反（触发对偶单纯形修复、最后截断负值），不进 Harris 比值检验的松弛：病态基上
        Σ|B⁻¹||b| 可以很大，放进松弛会让基变量合法地负到 ~1e-7、解越出可行域（09-27 精确有理数对照实测：
        α 偏高 1.7e-7，不安全一侧）。"""
        return [max(_FEAS * self.nu[self.basis[i]], _U_ENTRY * sum(abs(a) * abs(bk) for a, bk in zip(row, b)))
                for i, row in enumerate(self.Binv)]

    def duals(self, cost: list[float]) -> list[float]:
        m = self.m
        y = [0.0] * m
        for i in range(m):
            cb = cost[self.basis[i]]
            if cb != 0.0:
                row = self.Binv[i]
                for k in range(m):
                    y[k] += cb * row[k]
        return y

    def direction(self, e: int) -> list[float]:
        col = self.cols[e]
        return [_dot(row, col) for row in self.Binv]

    def dnoise(self, e: int) -> list[float]:
        """d = B⁻¹A_e 各分量的**逐分量**舍入尺度 Σ_k|B⁻¹_ik|·|A_ke|（不是全局 max|d|）。

        2026-09-27：比值检验原来把 d_i ≤ 1e-13·max|d| 一律当噪声。旧写法黏聚上限行在规整单位里的真实系数只有
        ~2.5e-15（其余行 ~1），这一行的 d_i = 7e-15 是真信号（它的舍入量级 ~1e-30），却被全局噪声线扔掉，
        于是报出伪无界射线。"""
        col = self.acols[e]
        return [sum(abs(a) * c for a, c in zip(row, col)) for row in self.Binv]

    def reduced(self, cost: list[float], y: list[float], j: int) -> tuple[float, float]:
        r = cost[j] - _dot(y, self.cols[j])
        s = abs(cost[j]) + sum(abs(yk) * a for yk, a in zip(y, self.acols[j]))
        return r, s

    def pivot(self, p: int, e: int, d: list[float]) -> None:
        self.iters += 1
        if self.iters > self.max_iter:
            raise RuntimeError(f"simplex did not terminate in {self.max_iter} iterations")
        piv = d[p]
        rowp = [v / piv for v in self.Binv[p]]
        for i in range(self.m):
            if i != p and d[i] != 0.0:
                f = d[i]
                self.Binv[i] = [a - f * bb for a, bb in zip(self.Binv[i], rowp)]
        self.Binv[p] = rowp
        self.inbasis[self.basis[p]] = False
        self.inbasis[e] = True
        self.basis[p] = e
        self.since_inv += 1
        if self.since_inv >= _REINVERT:
            self.reinvert()

    # ---- 定价与比值检验
    def price(self, cost: list[float], y: list[float], allowed: list[bool], tol: float) -> int:
        best, e = 0.0, -1
        for j in range(self.n + self.m):
            if not allowed[j] or self.inbasis[j]:
                continue
            r = cost[j] - _dot(y, self.cols[j])
            if r < 0.0 and r < best:
                s = abs(cost[j]) + sum(abs(yk) * a for yk, a in zip(y, self.acols[j]))
                if r < -tol * s:
                    best, e = r, j
        return e

    def ratio(self, d: list[float], x: list[float], dn: list[float] | None, *, noise: float | None = None) -> int:
        """Harris 两遍比值检验。返回出基行；没有约束步长的行返回 −1（候选无界方向）。

        两种噪声线（2026-09-27）：
          · `dn is None`（主路径）：d_i ≤ _PIV_NOISE_GLOBAL·max|d| 视为 0。对输入里的舍入垃圾（cos(π/2) = 6e-17
            这种元）稳健——逐分量噪声线会把它当真信号、在它上面换基，基随即奇异（09-27 实测宽模糊 11/1000）；
          · `dn` 给定（射线核验不过之后的退路）：d_i ≤ noise·dn_i 视为 0，dn = `dnoise` 是逐分量舍入尺度。
            真实的小尺度行（旧写法黏聚上限行的 d_i = 7e-15，其舍入量级 ~1e-30）在这里才看得见。
        稳定主元层 d_i > _PIV_STABLE·max|d| 优先。"""
        dmax = max((abs(v) for v in d), default=0.0)
        if dmax == 0.0:
            return -1
        hi = _PIV_STABLE * dmax
        if dn is None:
            lo_i = [(_PIV_NOISE_GLOBAL if noise is None else noise) * dmax] * len(d)
        else:
            lo_i = [(_PIV_NOISE if noise is None else noise) * v for v in dn]
        theta = float("inf")
        for i, di in enumerate(d):
            if di > lo_i[i]:
                f = _FEAS * self.nu[self.basis[i]]      # Harris 松弛只按自然尺度，**不**含舍入项（见 `ftol`）
                t = (max(x[i], -f) + f) / di
                if t < theta:
                    theta = t
        if theta == float("inf"):
            return -1
        pick, pv = -1, 0.0
        for tier in (hi, None):
            for i, di in enumerate(d):
                if di > (lo_i[i] if tier is None else max(tier, lo_i[i])) and max(x[i], 0.0) / di <= theta:
                    if di > pv or (di == pv and self.basis[i] < self.basis[pick]):
                        pick, pv = i, di
            if pick >= 0:
                return pick
        return -1

    # ---- 主循环
    def optimize(self, cost: list[float], allowed: list[bool], tol: float, ray_data) -> tuple[str, list | None]:
        """从当前（原始可行的）基出发做原始单纯形。返回 (OPTIMAL, None) 或 (UNBOUNDED, (e, d))。

        `ray_data=(A0, c0, ec)` 给出无界射线核验的原始未缩放数据；None 表示一阶段不接受无界射线。
        核验不过就在最大的正元上换基。"""
        b_work = self.b
        perturbed, n_perturb = False, 0
        seen: set[tuple[int, ...]] = {tuple(sorted(self.basis))}
        while True:
            x = self.xB(b_work)
            y = self.duals(cost)
            e = self.price(cost, y, allowed, tol)
            if e < 0:
                if not perturbed:
                    return OPTIMAL, None
                # 撤掉扰动：基不变、y 不变（对偶可行）；基解若不再可行就用对偶单纯形修复
                b_work, perturbed = self.b, False
                self.dual_simplex(cost, allowed, tol)
                seen = {tuple(sorted(self.basis))}
                continue
            d = self.direction(e)
            p = self.ratio(d, x, None)
            if p < 0:
                if (not perturbed and ray_data is not None
                        and _ray_verifies(ray_data[0], ray_data[1], self, e, d, ray_data[2])):
                    return UNBOUNDED, (e, d)
                p = self.ratio(d, x, self.dnoise(e))   # 射线不成立：有一行其实约束步长——按逐分量噪声线再找
                if p < 0:
                    p = self.ratio(d, x, None, noise=0.0)   # 仍找不到：接受任何正主元
                if p < 0:
                    if perturbed:                     # 扰动下的伪射线：撤扰动重来
                        b_work, perturbed = self.b, False
                        self.dual_simplex(cost, allowed, tol)
                        seen = {tuple(sorted(self.basis))}
                        continue
                    raise RuntimeError("simplex found an improving direction that fails the unbounded-ray check "
                                       "and has no positive pivot")
            self.pivot(p, e, d)
            key = tuple(sorted(self.basis))
            if key in seen:                           # 基重复 ⇒ 循环：扰动右端项
                n_perturb += 1
                if n_perturb > _MAX_PERTURB:
                    raise RuntimeError("simplex keeps cycling after repeated right-hand-side perturbation")
                x = self.xB(b_work)
                eps = _PERTURB * (4.0 ** (n_perturb - 1))
                delta = [eps * self.nu[self.basis[i]] * (1.0 + ((i * 0.6180339887498949) % 1.0)) for i in range(self.m)]
                shift = [0.0] * self.m
                for i in range(self.m):
                    col = self.cols[self.basis[i]]
                    for k in range(self.m):
                        shift[k] += (delta[i] - min(x[i], 0.0)) * col[k]
                b_work = [bk + sk for bk, sk in zip(b_work, shift)]
                perturbed = True
                seen = {key}
            else:
                seen.add(key)

    def dual_simplex(self, cost: list[float], allowed: list[bool], tol: float) -> None:
        """对偶单纯形：当前基对偶可行（约化成本 ≥ −tol 相对），把原始不可行的基变量换出去。"""
        seen: set[tuple[int, ...]] = {tuple(sorted(self.basis))}
        while True:
            x = self.xB(self.b)
            ft = self.ftol(self.b)
            p = min(range(self.m), key=lambda i: x[i] / ft[i], default=-1)
            if p < 0 or x[p] >= -ft[p]:
                return
            y = self.duals(cost)
            rho = self.Binv[p]
            cand = []
            amax = 0.0
            for j in range(self.n + self.m):
                if not allowed[j] or self.inbasis[j]:
                    continue
                a = _dot(rho, self.cols[j])
                if a < 0.0:
                    r, s = self.reduced(cost, y, j)
                    cand.append((j, a, max(r, 0.0), max(tol, _DUAL_CHECK) * s))
                amax = max(amax, abs(a))
            cand = [c for c in cand if -c[1] > _PIV_NOISE_GLOBAL * amax]
            if not cand:
                raise RuntimeError("dual simplex cleanup: no entering column (basis cannot be repaired)")
            theta = min((r + slack) / -a for _, a, r, slack in cand)
            e, best = -1, 0.0
            for j, a, r, s in cand:
                if r / -a <= theta and -a > best:
                    e, best = j, -a
            self.pivot(p, e, self.direction(e))
            key = tuple(sorted(self.basis))
            if key in seen:
                raise RuntimeError("dual simplex cleanup is cycling")
            seen.add(key)

    def dual_violation(self, cost: list[float], allowed: list[bool]) -> float:
        """（浮点层的启发式，决定何时把候选交给精确层；答案的正确性由 `_Exact.certify` 保证。）
        最优性核验量：max_j (−r_j − _NOISE_FLOOR·S)⁺·ν_j / |cᵀx|，取遍允许的非基列（规整单位）；≤ _DUAL_CHECK 即通过。

        分子是"列 j 还能把目标改进多少"的估计：约化成本 × 该变量的自然尺度 ν_j（步长的量级；实测步长 0.67
        对 ν 0.67、5.7e-4 对 ν 2.6e-3），先扣掉约化成本的舍入噪声底 _NOISE_FLOOR·S，S = max_j(|c_j| + Σ|y_k A_kj|)。
        分母是目标本身。判据因此是**目标的相对改进量** ≤ 1e-9。|cᵀx| = 0 时任何超出噪声底的负约化成本都不通过。

        演变（2026-09-27）：逐列尺度 −r_j/(|c_j| + Σ|y A_j|) 对与对偶解正交的列是 噪声/噪声（假抛错 59/2000）；
        "逐列 + 舍入噪声线 ν ∝ κ(B)"在病态基上盖过真约化成本，早停、静默 infeasible 或 α 偏低 67%（复核者实测）；
        纯全局尺度 −r_j/S ≤ 1e-9 在目标只有 S 的 1e-4 时放过相对 1e-7 的次优（精确有理数对照实测 −1.36e-7）。"""
        y = self.duals(cost)
        x = self.xB(self.b)
        obj = abs(sum(cost[self.basis[i]] * x[i] for i in range(self.m)))
        S = 0.0
        red = []
        for j in range(self.n + self.m):
            if not allowed[j]:
                continue
            r, sj = self.reduced(cost, y, j)
            S = max(S, sj)
            if not self.inbasis[j] and r < 0.0:
                red.append((r, j))
        worst = 0.0
        for r, j in red:
            excess = (-r - _NOISE_FLOOR * S) * self.nu[j]
            if excess > 0.0:
                worst = max(worst, excess / obj if obj > 0.0 else float("inf"))
        return worst

def solve(A: list[list[float]], b: list[float], c: list[float], *,
          tol: float = 1e-10, max_iter: int = 20000, exact=None) -> LPResult:
    """min cᵀx s.t. Ax = b, x ≥ 0。**答案对给定的数据精确成立**（见模块文档"契约"）。

    `exact`：可选的精确数据 (A, b, c)（Fraction 或 int），给了就以它为准，A/b/c 只当它的浮点近似喂给浮点层
    （调用方在浮点里算不精确的派生量——例如力矩 r × g——应当精确地给，见 limit.py）。不给时精确数据就是 A/b/c 本身。

    两层：浮点修正单纯形（`_float_solve`）只负责给出**候选**（状态 + 基 + 入基列）；有理数层在原始数据上
    精确核验这个候选（`_Exact.certify`），核验不过就从候选基（能热启动时）或从头用有理数 Bland 单纯形走完
    （`_exact_simplex`）。浮点层抛出的任何 RuntimeError（奇异基、迭代超限、循环）都只导致冷启动的有理数求解。
    返回的 x、y、obj、ray 都是精确解经一次舍入得到的浮点数。`tol` 只影响浮点层的迭代路径（速度），不影响答案。
    """
    m, n = len(A), len(c)
    if m == 0:
        cx = [Fraction(v) for v in (exact[2] if exact is not None else c)]   # 精确目标为准（reverify5：m = 0 曾忽略 exact=）
        neg = [j for j in range(n) if cx[j] < 0]
        if neg:
            ray = [1.0 if j == neg[0] else 0.0 for j in range(n)]
            return LPResult(UNBOUNDED, [0.0] * n, float("-inf"), [], 0, [], ray)
        return LPResult(OPTIMAL, [0.0] * n, 0.0, [], 0, [],
                        exact_x=(Fraction(0),) * n, exact_y=())
    X = _Exact(A, b, c, exact)
    try:
        cand = _float_solve(A, b, c, tol=tol, max_iter=max_iter, flip=X.flip)
    except (RuntimeError, ArithmeticError, ValueError):   # 奇异、超限、循环、ldexp 溢出……都只是候选没了
        cand = None
    if cand is not None:
        res = X.certify(*cand)
        if res is not None:
            return res
    st, basis, e, iters = _exact_simplex(X, cand[1] if cand is not None else None)
    res = X.certify(st, basis, e, (cand[3] if cand is not None else 0) + iters)
    if res is None:                                   # 有理数单纯形的输出必过精确证书；到这里是实现缺陷
        raise RuntimeError(f"internal error: exact simplex result ({st}) failed its exact certificate")
    return res


def _float_solve(A: list[list[float]], b: list[float], c: list[float], *,
                 tol: float, max_iter: int, flip: list[bool] | None = None) -> tuple[str, list[int], int, int]:
    """浮点两阶段修正单纯形。返回候选 (status, basis, entering, iterations)：basis 按"b 取负规整后的系统"编号
    （列 j < n 是原变量，n + i 是第 i 行的人工变量），entering 只对 UNBOUNDED 有意义（射线沿它增大）。
    b 的符号、行列尺度、右端项与目标尺度自动规整（见模块文档）。候选的正确性**不**在这里保证。"""
    m, n = len(A), len(c)
    A0, c0 = A, c
    A = [row[:] for row in A]
    b = b[:]
    # 规整 b ≥ 0：取负哪些行由 `_Exact` 按**精确** b 的符号定（flip），两层逐行相同，基的编号两层通用
    flipped = [i for i in range(m) if (flip[i] if flip is not None else b[i] < 0.0)]
    for i in flipped:
        A[i] = [-v for v in A[i]]
        b[i] = -b[i]
    # 均衡：先列后行，因子全是 2 的幂（精确）。基的编号不受影响。
    ec = [-_exp2(max((abs(A[i][j]) for i in range(m)), default=0.0)) for j in range(n)]
    A = [[ldexp(A[i][j], ec[j]) for j in range(n)] for i in range(m)]
    cq = [ldexp(c[j], ec[j]) for j in range(n)]
    er = [-_exp2(max((abs(v) for v in A[i]), default=0.0)) for i in range(m)]
    A = [[ldexp(v, er[i]) for v in A[i]] for i in range(m)]
    b = [ldexp(b[i], er[i]) for i in range(m)]
    es = _exp2(max(b, default=0.0))           # 右端项双向归一（b ≡ 0 时不动）
    b = [ldexp(v, -es) for v in b]
    ek = -_exp2(max((abs(v) for v in cq), default=0.0))      # 目标归一
    cq = [ldexp(v, ek) for v in cq]

    S = _Revised(A, b, max_iter)
    N = n + m

    # ---- 一阶段：min Σ 人工
    cost1 = [0.0] * n + [1.0] * m
    allow1 = [True] * N
    _certified_optimize(S, cost1, allow1, tol, None, phase=1)
    x = S.xB(b)
    ft1 = S.ftol(b)
    art = sum(max(0.0, x[i] - ft1[i]) / S.nu[S.basis[i]] for i in range(m) if S.basis[i] >= n)
    if art > _INFEAS:
        return INFEASIBLE, list(S.basis), -1, S.iters

    # 人工变量若仍在基里（退化），换出去：取该行 (B⁻¹A) 绝对值最大的原变量列；换不出说明该行冗余，留着（值恒 0）
    for i in range(m):
        if S.basis[i] >= n:
            rho = S.Binv[i]
            best, e = 0.0, -1
            for j in range(n):
                if not S.inbasis[j]:
                    a = abs(_dot(rho, S.cols[j]))
                    if a > best:
                        best, e = a, j
            if e >= 0 and best > _PIV_STABLE * max(abs(v) for v in rho):
                S.pivot(i, e, S.direction(e))
    S.reinvert()

    # ---- 二阶段：真目标，人工变量不许入基
    cost2 = cq + [0.0] * m
    allow2 = [True] * n + [False] * m
    st, info = _certified_optimize(S, cost2, allow2, tol, (A0, c0, ec), phase=2)
    if st == UNBOUNDED:
        return UNBOUNDED, list(S.basis), info[0], S.iters
    return OPTIMAL, list(S.basis), -1, S.iters


_U = 2.0 ** -53
_TINY = 2.0 ** -1074          # 最小的正次正规数：取整落进次正规区时的绝对误差上界
_EXACT_PIVOT_CAP = 1_000_000  # 有理数单纯形的换基上限：有限步终止但最坏是指数级（Klee–Minty m = 20 需 2²⁰−1 次），超过即抛错


def _fl(v: Fraction) -> float:
    """有理数 → 浮点（正确舍入）；超出浮点范围时给 ±inf 而不是抛 OverflowError（近奇异基上精确解可以超出范围）。"""
    try:
        return scalar_rational(v, allow_underflow=True)  # Display/candidate; exact certificate is retained.
    except OverflowError:
        return float("inf") if v > 0 else float("-inf")


class _Exact:
    """原始数据的有理数副本（b 取负规则与 `_float_solve` 相同），以及三种状态的**精确证书**。

    Fraction(float) 无损，所以这里核验的就是调用方给的那个 LP 本身，不是它的近似。
    逐列的符号判定（约化成本 ≥ 0、Farkas 的 yᵀA_j ≤ 0）先用浮点算、带严格的舍入误差界过滤：误差界之外的符号
    直接定论，误差界之内的那一列才用有理数重算——结论与全用有理数逐位相同，只是快。"""

    def __init__(self, A: list[list[float]], b: list[float], c: list[float], exact=None):
        m, n = len(A), len(c)
        self.m, self.n = m, n
        if exact is None:
            AE, bE, cE = ([[Fraction(v) for v in row] for row in A], [Fraction(v) for v in b], [Fraction(v) for v in c])
        else:
            AE, bE, cE = ([[Fraction(v) for v in row] for row in exact[0]], [Fraction(v) for v in exact[1]],
                          [Fraction(v) for v in exact[2]])
        # 取负哪些行按**精确** b 的符号定，并交给 `_float_solve` 用同一份——精确 b = −1e-400 而浮点 b = −0.0 时，
        # 曾经两层按各自的符号取负，有理数冷启动的人工基不可行，抛内部错误（reverify5，1464 例里 138 例）。
        self.flip = [bE[i] < 0 for i in range(m)]
        self.A = [[-v for v in AE[i]] if self.flip[i] else AE[i] for i in range(m)]
        self.b = [-v if self.flip[i] else v for i, v in enumerate(bE)]
        self.c = cE
        self.cf = [_fl(v) for v in cE]
        self.Af = [[_fl(v) for v in row] for row in self.A]
        self.colf = [[self.Af[i][j] for i in range(m)] for j in range(n)]

    def col(self, j: int) -> list[Fraction]:
        if j < self.n:
            return [self.A[i][j] for i in range(self.m)]
        return [Fraction(int(i == j - self.n)) for i in range(self.m)]

    def inverse(self, basis: list[int]) -> list[list[Fraction]] | None:
        """B⁻¹（高斯-若尔当，精确）；B 奇异返回 None。"""
        m = self.m
        cols = [self.col(j) for j in basis]
        M = [[cols[k][i] for k in range(m)] + [Fraction(int(i == r)) for r in range(m)] for i in range(m)]
        for cc in range(m):
            p = next((i for i in range(cc, m) if M[i][cc] != 0), None)
            if p is None:
                return None
            M[cc], M[p] = M[p], M[cc]
            pv = M[cc][cc]
            if pv != 1:
                M[cc] = [v / pv for v in M[cc]]
            for i in range(m):
                f = M[i][cc]
                if i != cc and f != 0:
                    M[i] = [a - f * bb for a, bb in zip(M[i], M[cc])]
        return [row[m:] for row in M]

    def reduced_sign(self, cost: list[Fraction], costf: list[float], y: list[Fraction], yf: list[float],
                     j: int) -> tuple[int, float]:
        """原变量列 j 的约化成本 r_j = cost_j − yᵀA_j 的**精确**符号（−1/0/+1）与一个浮点估值。

        浮点估值 s 的误差界（相对部分 + 绝对部分）：
          相对：y、A、cost 各自取整 ≤ u·|·|，乘积与 m 项求和的舍入 ≤ γ_{m+1}·(|cost_j| + Σ|y_i A_ij|)，
                合计取 (m+6)·u·a·1.0625，a = |cost_j| + Σ|y_i A_ij|（浮点算）；
          绝对：取整落进次正规数或下溢成 0 时相对界不成立，每个量的绝对误差 ≤ 2⁻¹⁰⁷⁴——y_i 下溢时误差是
                2⁻¹⁰⁷⁴·|A_ij|（A = 1e300 时就是 5e-24！复核者 reverify4 实测过静默错 2 倍与死循环），A_ij 下溢时是
                |y_i|·2⁻¹⁰⁷⁴，乘积下溢每项 2⁻¹⁰⁷⁴；合计 2·2⁻¹⁰⁷⁴·(Σ|A_ij| + Σ|y_i| + m + 2)。
        |s| > E 时符号即定论，否则用有理数重算；出现 inf/nan（溢出）时一律用有理数。"""
        col = self.colf[j]
        s = costf[j]
        a = abs(s)
        sa = 0.0
        for yi, v in zip(yf, col):
            sa += abs(v) + abs(yi)
            if v != 0.0:
                t = yi * v
                s -= t
                a += abs(t)
        E = (self.m + 6) * _U * a * 1.0625 + 2.0 * _TINY * (sa + self.m + 2)
        if s > E:                                          # 溢出成 inf/nan 时两个比较都不成立，自然落到有理数
            return 1, s
        if s < -E:
            return -1, s
        r = cost[j] - sum((y[i] * self.A[i][j] for i in range(self.m) if self.A[i][j] != 0), Fraction(0))
        return (r > 0) - (r < 0), _fl(r)

    def certify(self, status: str, basis: list[int], e: int, iters: int) -> LPResult | None:
        """精确核验候选；成立则返回（浮点化的）结果，不成立返回 None。

        · OPTIMAL：x_B = B⁻¹b ≥ 0、基里的人工变量恰为 0；y = c_Bᵀ B⁻¹；每个原变量列 r_j = c_j − yᵀA_j ≥ 0。
          于是 x 可行、y 对偶可行、cᵀx = bᵀy——弱对偶即最优，精确成立；
        · UNBOUNDED：同上的原始可行；d = B⁻¹A_e 各分量 ≤ 0（人工变量行 = 0）、c_e − c_Bᵀd < 0——
          x + t·(e_e − d) 对所有 t ≥ 0 可行且目标无下界；
        · INFEASIBLE：y = 1_artᵀ B⁻¹（一阶段对偶）满足 yᵀA_j ≤ 0（每个原变量列）且 yᵀb > 0——Farkas。"""
        m, n = self.m, self.n
        if len(basis) != m or len(set(basis)) != m or any(not (0 <= j < n + m) for j in basis):
            return None
        Binv = self.inverse(basis)
        if Binv is None:
            return None
        zero = Fraction(0)
        if status == INFEASIBLE:
            cb = [Fraction(int(j >= n)) for j in basis]
            y = [sum((cb[i] * Binv[i][k] for i in range(m) if cb[i] != 0), zero) for k in range(m)]
            if not sum((yk * bk for yk, bk in zip(y, self.b)), zero) > 0:
                return None
            yf = [_fl(v) for v in y]
            zc, zf = [zero] * n, [0.0] * n                 # 以 0 为"成本"：yᵀA_j ≤ 0 ⇔ 0 − yᵀA_j ≥ 0
            for j in range(n):
                if self.reduced_sign(zc, zf, y, yf, j)[0] < 0:
                    return None
            yo = [_fl(-v if self.flip[i] else v) for i, v in enumerate(y)]
            return LPResult(INFEASIBLE, [0.0] * n, float("nan"), yo, iters, list(basis))
        xB = [sum((r * bb for r, bb in zip(row, self.b) if r != 0), zero) for row in Binv]
        for i, j in enumerate(basis):
            if xB[i] < 0 or (j >= n and xB[i] != 0):
                return None
        cb = [self.c[j] if j < n else zero for j in basis]
        y = [sum((cb[i] * Binv[i][k] for i in range(m) if cb[i] != 0), zero) for k in range(m)]
        if status == UNBOUNDED:
            if not (0 <= e < n) or e in basis:
                return None
            ce = self.col(e)
            d = [sum((r * a for r, a in zip(row, ce) if a != 0), zero) for row in Binv]
            for i, j in enumerate(basis):
                if d[i] > 0 or (j >= n and d[i] != 0):
                    return None
            if not self.c[e] - sum((cb[i] * d[i] for i in range(m)), zero) < 0:
                return None
            ray = [0.0] * n
            ray[e] = 1.0
            for i, j in enumerate(basis):
                if j < n:
                    ray[j] = _fl(-d[i])
            return LPResult(UNBOUNDED, [0.0] * n, float("-inf"), [0.0] * m, iters, list(basis), ray)
        if status != OPTIMAL:
            return None
        yf = [_fl(v) for v in y]
        inb = set(basis)
        for j in range(n):
            if j not in inb and self.reduced_sign(self.c, self.cf, y, yf, j)[0] < 0:
                return None
        xe = [zero] * n
        for i, j in enumerate(basis):
            if j < n:
                xe[j] = xB[i]
        obj = sum((cj * xj for cj, xj in zip(self.c, xe) if xj != 0), zero)
        yo = [_fl(-v if self.flip[i] else v) for i, v in enumerate(y)]
        return LPResult(OPTIMAL, [_fl(v) for v in xe], _fl(obj), yo, iters, list(basis),
                        exact_x=tuple(xe), exact_y=tuple(-v if self.flip[i] else v for i, v in enumerate(y)))


def _exact_simplex(X: _Exact, start: list[int] | None) -> tuple[str, list[int], int, int]:
    """有理数两阶段**修正**单纯形。返回 (status, basis, entering, pivots)。

    只维护精确的 B⁻¹（m × m，秩一更新）；定价用 Dantzig（`reduced_sign` 的浮点过滤 + 有理数定论），连续
    2m + 10 次退化换基后改用 Bland（最小下标入基、最小基下标出基），精确算术里由此有限步终止。
    热启动：给定的基非奇异、且其基解精确可行（人工变量为 0）时直接从它开始二阶段；否则从人工基冷启动一阶段。"""
    m, n = X.m, X.n
    N = n + m
    zero, one = Fraction(0), Fraction(1)
    pivots = 0

    def run(Binv, basis, xB, cost, costf, allowed, phase2):
        nonlocal pivots
        degenerate, bland = 0, False
        while True:
            if pivots > _EXACT_PIVOT_CAP:                   # 精确算术里有限步终止，但最坏是指数级——这里如实报没算完
                raise RuntimeError(f"exact simplex exceeded {_EXACT_PIVOT_CAP} pivots without finishing (the worst case "
                                   f"of Dantzig/Bland pricing is exponential, e.g. a Klee-Minty cube); no answer is returned")
            cb = [cost[j] for j in basis]
            y = [sum((cb[i] * Binv[i][k] for i in range(m) if cb[i] != 0), zero) for k in range(m)]
            yf = [_fl(v) for v in y]
            inb = set(basis)
            enter, best = -1, 0.0
            for j in allowed:
                if j in inb:
                    continue
                if j < n:
                    sg, s = X.reduced_sign(cost, costf, y, yf, j)
                else:                                   # 人工列 e_k：r = cost_j − y_k
                    r = cost[j] - y[j - n]
                    sg, s = (r > 0) - (r < 0), _fl(r)
                if sg < 0:
                    if bland:
                        enter = j
                        break
                    if enter < 0 or s < best:
                        enter, best = j, s
            if enter < 0:
                return OPTIMAL, -1
            ce = X.col(enter)
            d = [sum((r * a for r, a in zip(row, ce) if a != 0), zero) for row in Binv]
            leave, theta = -1, None
            for i in range(m):
                if phase2 and basis[i] >= n and d[i] != 0:
                    rt = zero                           # 人工变量必须留在 0：任何非零分量都在 0 步长处挡住
                elif d[i] > 0:
                    rt = xB[i] / d[i]
                else:
                    continue
                if theta is None or rt < theta or (rt == theta and basis[i] < basis[leave]):
                    theta, leave = rt, i
            if leave < 0:
                return UNBOUNDED, enter
            degenerate = degenerate + 1 if theta == 0 else 0
            if degenerate > 2 * m + 10:
                bland = True
            pv = d[leave]
            rowp = [v / pv for v in Binv[leave]]
            for i in range(m):
                if i != leave and d[i] != 0:
                    f = d[i]
                    Binv[i] = [a - f * bb for a, bb in zip(Binv[i], rowp)]
                    xB[i] -= theta * f
            Binv[leave] = rowp
            xB[leave] = theta
            basis[leave] = enter
            pivots += 1

    basis = Binv = xB = None
    if start is not None and len(start) == m and len(set(start)) == m and all(0 <= j < N for j in start):
        B0 = X.inverse(list(start))
        if B0 is not None:
            x0 = [sum((r * bb for r, bb in zip(row, X.b) if r != 0), zero) for row in B0]
            if all(x0[i] >= 0 and (start[i] < n or x0[i] == 0) for i in range(m)):
                basis, Binv, xB = list(start), B0, x0
    if basis is None:                                 # 冷启动一阶段：人工基 = 单位阵
        basis = list(range(n, N))
        Binv = [[Fraction(int(i == k)) for k in range(m)] for i in range(m)]
        xB = list(X.b)
        cost1 = [zero] * n + [one] * m
        run(Binv, basis, xB, cost1, [_fl(v) for v in cost1], list(range(N)), False)
        if any(basis[i] >= n and xB[i] != 0 for i in range(m)):
            return INFEASIBLE, basis, -1, pivots
    for i in range(m):                                # 把值为 0 的人工变量换出基（任意非零原变量元都行）
        if basis[i] >= n:
            inb = set(basis)
            for j in range(n):
                if j in inb:
                    continue
                a = sum((Binv[i][k] * X.A[k][j] for k in range(m) if X.A[k][j] != 0), zero)
                if a != 0:
                    ce = X.col(j)
                    d = [sum((r * v for r, v in zip(row, ce) if v != 0), zero) for row in Binv]
                    rowp = [v / a for v in Binv[i]]
                    for r_ in range(m):
                        if r_ != i and d[r_] != 0:
                            Binv[r_] = [p - d[r_] * q for p, q in zip(Binv[r_], rowp)]
                    Binv[i] = rowp
                    basis[i] = j
                    pivots += 1
                    break
    xB = [sum((r * bb for r, bb in zip(row, X.b) if r != 0), zero) for row in Binv]
    cost2 = X.c + [zero] * m
    st, e = run(Binv, basis, xB, cost2, X.cf + [0.0] * m, list(range(n)), True)
    return st, basis, e, pivots


def _certified_optimize(S: _Revised, cost: list[float], allowed: list[bool], tol: float, ray_data,
                        *, phase: int) -> tuple[str, object]:
    """浮点层的优化 + 清理：最终基上重新求逆，约化成本 ≥ −_DUAL_CHECK（相对）；不过就收紧定价阈值再迭代，
    三轮仍不过也照样交出候选（精确层会判定）。这里的一切阈值只影响候选的质量，不影响答案。"""
    ptol = tol
    for _ in range(_CLEANUP_ROUNDS):
        st, info = S.optimize(cost, allowed, ptol, ray_data)
        if st == UNBOUNDED:
            if phase == 1:
                raise RuntimeError("phase one reported unbounded (impossible in exact arithmetic)")
            return st, info
        S.reinvert()
        x = S.xB(S.b)
        ft = S.ftol(S.b)
        if any(x[i] < -10.0 * ft[i] for i in range(S.m)):
            S.dual_simplex(cost, allowed, ptol)       # 基解不可行（数值）：先修复原始可行性
            continue
        if S.dual_violation(cost, allowed) <= _DUAL_CHECK:
            return OPTIMAL, None
        ptol = min(ptol, _DUAL_CHECK) * 0.1
    return OPTIMAL, None                              # 核验没过也交出去：精确层会判定并在必要时接着走


def _ray(S: _Revised, e: int, d: list[float], ec: list[int]) -> list[float]:
    """规整单位里的射线 d'（x_e 增 1，基变量减 d_i）折回原单位：d_j = 2^ec_j·d'_j。

    **清洗**：|d_i| ≤ _PIV_NOISE·max(1, max|d|) 的分量置 0（2026-09-27）。它们是 B⁻¹ 秩一更新累积误差级别的噪声
    （宽模糊实测：本该为 0 的分量读成 3.87e-33、1.58e-17），留着会让它们所在的行在逐行相对核验里成为
    噪声/噪声 ≈ 1。负的 d_i（基变量沿射线增大）同样按此清洗后取 max(−d_i, 0)。"""
    n = S.n
    cut = _PIV_NOISE * max(1.0, max((abs(v) for v in d), default=0.0))
    r = [0.0] * n
    r[e] = 1.0
    for i, di in enumerate(d):
        j = S.basis[i]
        if j < n and -di > cut:
            r[j] = -di
    return [ldexp(r[j], ec[j]) for j in range(n)]


def _ray_verifies(A0, c0, S: _Revised, e: int, d: list[float], ec: list[int]) -> bool:
    """用**原始未缩放**的 A、c 核验（清洗后的）无界射线 d：d ≥ 0、cᵀd < 0，且逐行
        |A_i d| ≤ 1e-9·Σ_j|A_ij d_j| + _U_ENTRY·Σ_{A_ij ≠ 0} min(max_k|A_ik|, max_k|A_kj|)·|d_j| 。
    第二项是**输入元自身的舍入**（后向误差：射线对每个非零元扰动不超过 8u·min(行尺度, 列尺度) 的 A 精确成立）——
    cos(π/2) = 6e-17 这种元在它所在行里是垃圾，不是约束。两项都**逐行**，没有跨行的全局量：旧版的噪声项
    1e-14·max_i(行尺度) 让旧写法里右端项 1 的黏聚上限行（其余行 ~1e16）整行违反也照样核验通过、报 unbounded
    （复核者 LP 层探针，2026-09-27 订正）。基里的人工变量若沿射线变化（d_i 不是噪声），射线不成立。"""
    n = S.n
    dmax = max((abs(v) for v in d), default=0.0)
    for i, di in enumerate(d):
        if S.basis[i] >= n and abs(di) > _PIV_NOISE * max(1.0, dmax):
            return False
    ray = _ray(S, e, d, ec)
    m = len(A0)
    colmax = [max((abs(A0[i][j]) for i in range(m)), default=0.0) for j in range(n)]
    for row in A0:
        rmax = max((abs(a) for a in row), default=0.0)
        r = sum(a * v for a, v in zip(row, ray))
        s = sum(abs(a * v) for a, v in zip(row, ray))
        unc = _U_ENTRY * sum(min(rmax, colmax[j]) * v for j, (a, v) in enumerate(zip(row, ray)) if a != 0.0 and v != 0.0)
        if abs(r) > _RAY_CHECK * s + unc:
            return False
    cd = sum(ci * v for ci, v in zip(c0, ray))
    sc = sum(abs(ci * v) for ci, v in zip(c0, ray))
    return cd < -_RAY_CHECK * sc

def _natural_scales(A: list[list[float]], b: list[float]) -> list[float]:
    """各变量在规整单位里的**自然尺度** ν_j = min(1, max_i |b_i|/|A_ij|)（取遍 A_ij ≠ 0 且 b_i ≠ 0 的行；
    没有这样的行时 ν_j = 1）；人工变量 k 的列是单位向量 e_k，ν = min(1, |b_k|)（b_k = 0 时 1）。

    为什么要它（2026-09-27）：行、列均衡与右端项**全局**归一之后，所有可行性阈值（Harris 松弛、负值截断、
    一阶段判不可行）原本都是绝对量 ~1e-9，而右端项可以跨十个量级——旧写法的黏聚上限行 Σλ_coh + s = 1、
    列里乘了 c·A ~ 7e10，归一后这一行的右端只有 1.5e-11，松弛变量可以"合法地"负到 −1e-9，
    等于把黏聚上限放大 67 倍。按 ν 缩放阈值后，普通变量（ν = 1）的行为逐位不变，只有自然尺度小的变量阈值变紧。
    对行/列的 2 的幂缩放协变。"""
    m = len(A)
    n = len(A[0]) if m else 0
    nu = []
    for j in range(n):
        best = 0.0
        for i in range(m):
            a = abs(A[i][j])
            if a > 0.0 and b[i] != 0.0:
                best = max(best, abs(b[i]) / a)
        nu.append(min(1.0, best) if best > 0.0 else 1.0)
    for k in range(m):
        nu.append(min(1.0, abs(b[k])) if b[k] != 0.0 else 1.0)
    return nu


def maximize(A: list[list[float]], b: list[float], c: list[float], **kw) -> LPResult:
    """max cᵀx s.t. Ax = b, x ≥ 0。`exact=(A, b, c)` 同 `solve`（c 是 max 的目标）。"""
    ex = kw.pop("exact", None)
    if ex is not None:
        ex = (ex[0], ex[1], [-v for v in ex[2]])
    res = solve(A, b, [-v for v in c], exact=ex, **kw)
    if res.status == OPTIMAL:
        return LPResult(res.status, res.x, -res.obj, [-v for v in res.y],
                        res.iterations, res.basis, exact_x=res.exact_x,
                        exact_y=tuple(-v for v in res.exact_y) if res.exact_y is not None else None)
    if res.status == UNBOUNDED:
        return LPResult(UNBOUNDED, res.x, float("inf"), res.y, res.iterations, res.basis, res.ray)
    return res
