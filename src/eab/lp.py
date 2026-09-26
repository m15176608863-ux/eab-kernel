"""稠密修正单纯形法（两阶段）。纯 Python、零依赖。

L3 极限分析要解的是小规模线性规划（变量数 ~ 接触数 × 摩擦锥棱数，约束数 = 位形自由度 + 黏聚行），
几十到几百量级，稠密够用。

标准型：  min cᵀx   s.t.  Ax = b,  x ≥ 0

返回里带**对偶解 y**：在极限分析里它就是破坏机构（上限定理的运动场），不是附属品。

## 契约（2026-09-24，G6 之后重写；09-27 M0.2 返修二补全）

**要么答对，要么抛 RuntimeError，绝不静默给错。三种状态各带一张证书，证书过不了就抛错：**
  · OPTIMAL：最终基上**重新求逆**后核验
      原始可行（`_guard_residual`：逐行 |A_i x − b_i| ≤ 1e-7·(|b_i| + Σ|A_ij x_j|) + 舍入噪声项，逐变量 x_j ≥ −…）、
      最优性（`_Revised.dual_violation`：各列"还能把目标改进多少" = 约化成本 × 变量自然尺度，相对目标值 ≤ 1e-9）、
      相对对偶间隙（`_guard_gap`）。
    这些核验与调用方的 `tol` **无关**：`tol` 放宽只会让单纯形早停，早停的基过不了核验，于是收紧定价阈值继续迭代
    （"清理"），三轮仍过不了就抛错（G6 minor 24）；
  · UNBOUNDED：射线 d 先清洗（B⁻¹ 误差级别的分量置 0），再用**原始未缩放的 A** 逐行核验
    |A_i d| ≤ 1e-9·Σ_j|A_ij d_j| + 8u·Σ_j min(行尺度, 列尺度)·|d_j|、d ≥ 0、cᵀd < 0（`_ray_verifies`）。
    核验不过就退回去换基（先按逐分量噪声线找行，再接受任何正主元），实在无行可换才抛错；
  · INFEASIBLE：一阶段的对偶 y 就是 Farkas 证书（yᵀA ≤ 0、yᵀb > 0），在原始数据上核验（`_farkas_verifies`），
    过不了就抛错（09-27 之前一阶段 Σ人工 > 1e-8 就直接报，复核者实测有尺度极差的可行问题被静默判为不可行）；
    证书随结果返回（`LPResult.y`）。
  · 终止**不是**无条件保证的：Bland 规则只在精确算术里保证有限步终止，浮点下"平局在容差内判定"会真的循环
    （G6 major 2：旧实现 k=128 时 409 步一周期）。现在的做法见下；仍超过 `max_iter` 就抛 RuntimeError。

**阈值的统一原则（09-27）：每个阈值 = max(按问题尺度的相对量, 按舍入量级的噪声量)，没有与问题无关的绝对数，
也没有随 κ(B) 膨胀的量。** 这次返修前后踩过的坑，每一个都是违反了这条：
  · 逐列相对的最优性判据：与对偶解正交的列 噪声/噪声 ≈ 1，假抛错（59/2000）；
  · "逐列 + 噪声线 ν ∝ κ(B)"：病态但合理的基上噪声线盖过真约化成本，早停，静默 infeasible、α 偏低 67%；
  · 全局尺度 S 的最优性判据：目标只有 S 的 1e-4 时放过相对 1e-7 的次优；
  · 可行性与残差的绝对下限 ~1e-9：右端项全局归一后 1e-11 的行（旧写法的黏聚上限行）整行违反照样放行；
  · 射线核验的跨行噪声项 1e-14·max(行尺度)：同一行被吞掉，报伪 unbounded。

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
  于是所有阈值都作用在规整后的量级上；b 乘 2 的幂时整个求解逐位按比例（门：tests/test_lp_scale.py）。

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

门：tests/test_lp.py、tests/test_lp_scale.py、tests/test_lp_fail_loud.py、tests/test_lp_certificates.py。
"""

from __future__ import annotations

from dataclasses import dataclass
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


_RESIDUAL_GUARD = 1e-7    # 原始后向误差守卫（规整单位，只抓粗差）
_FEAS = 1e-9              # 原始可行性松弛（规整单位，max|b| ∈ [0.5, 1)）：Harris 比值检验、基解的小负值
_INFEAS = 1e-8            # 一阶段最优值超过它即判不可行（规整单位 ⇒ 相对于 max|b|）
_PIV_STABLE = 1e-9        # 稳定主元：d_i > _PIV_STABLE·max|d|
_PIV_NOISE = 1e-12        # 逐分量噪声线：d_i ≤ _PIV_NOISE·Σ_k|B⁻¹_ik||A_ke| 视为 0（射线核验、退路比值检验、对偶单纯形）
_PIV_NOISE_GLOBAL = 1e-13 # 全局噪声线：d_i ≤ 1e-13·max|d| 视为 0（主路径比值检验，见 `_Revised.ratio`）
_DUAL_CHECK = 1e-9        # 对偶可行性核验（相对，与 tol 无关）
_GAP_CHECK = 1e-9         # 相对对偶间隙核验
_RAY_CHECK = 1e-9         # 无界射线核验（逐行相对）
_REINVERT = 32            # 每多少次换基重新求逆
_PERTURB = 1e-7           # 防循环扰动的基准幅度（规整单位）
_MAX_PERTURB = 6          # 一次优化里最多扰动几轮
_CLEANUP_ROUNDS = 3       # 核验不过时最多清理几轮
_U_ENTRY = 8.0 * 2.0 ** -53   # 输入元自身的舍入量级（相对 min(行尺度, 列尺度)），见 `_ray_verifies`
_NOISE_FLOOR = 1e-12      # 带条件数余量的舍入噪声底：约化成本（×S，`dual_violation`）、Farkas 证书的列（×nz）
_CERT_NOISE = 64.0 * 2.0 ** -53   # 舍入噪声底 ≈ 7e-15（×自然尺度）：残差、间隙、Farkas 证书的 yᵀb
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
    def optimize(self, cost: list[float], allowed: list[bool], tol: float, ray_ok) -> tuple[str, list | None]:
        """从当前（原始可行的）基出发做原始单纯形。返回 (OPTIMAL, None) 或 (UNBOUNDED, (e, d))。

        `ray_ok(e, d)` 在核验无界射线时调用（原始未缩放数据上）；核验不过就在最大的正元上换基。"""
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
                if not perturbed and ray_ok(e, d):
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
        """最优性核验量：max_j (−r_j − _NOISE_FLOOR·S)⁺·ν_j / |cᵀx|，取遍允许的非基列（规整单位）；≤ _DUAL_CHECK 即通过。

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
          tol: float = 1e-10, max_iter: int = 20000) -> LPResult:
    """min cᵀx s.t. Ax = b, x ≥ 0。b 的符号、行列尺度、右端项与目标尺度自动规整（见模块文档）。

    `tol` 是入基（最优性）判据的相对阈值：列 j 入基当且仅当 r_j < −tol·(|c_j| + Σ|y_i A_ij|)。
    它**不**决定返回什么：OPTIMAL 必过固定阈值的原始/对偶/间隙核验，UNBOUNDED 必过射线核验，
    INFEASIBLE 必过一阶段的对偶核验；过不了就继续迭代或抛 RuntimeError。
    """
    m, n = len(A), len(c)
    if m == 0:
        neg = [j for j in range(n) if c[j] < 0.0]
        if neg:
            ray = [1.0 if j == neg[0] else 0.0 for j in range(n)]
            return LPResult(UNBOUNDED, [0.0] * n, float("-inf"), [], 0, [], ray)
        return LPResult(OPTIMAL, [0.0] * n, 0.0, [], 0, [])
    A0, c0, bvec0 = A, c, list(b)
    A = [row[:] for row in A]
    b = b[:]
    # 规整 b ≥ 0。**被取负的行，其对偶乘子最后要翻回来**：
    # 约束 −A_i x = −b_i 的乘子 y 对应原约束 A_i x = b_i 的乘子 −y（2026-09-21 实测 7/12 组报红）。
    flipped = [i for i in range(m) if b[i] < 0.0]
    for i in flipped:
        A[i] = [-v for v in A[i]]
        b[i] = -b[i]
    # 均衡：先列后行，因子全是 2 的幂（精确）。x = D·x'，c' = D·c；行 i 乘 r_i ⇒ y_i = r_i·y'_i。
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

    def ray_ok(e: int, d: list[float]) -> bool:
        return _ray_verifies(A0, c0, S, e, d, ec)

    # ---- 一阶段：min Σ 人工
    cost1 = [0.0] * n + [1.0] * m
    allow1 = [True] * N
    _certified_optimize(S, cost1, allow1, tol, lambda e, d: False, phase=1)
    x = S.xB(b)
    ft1 = S.ftol(b)
    # 各行按自身右端项的尺度计；舍入量级以内的人工变量值不算
    art = sum(max(0.0, x[i] - ft1[i]) / S.nu[S.basis[i]] for i in range(m) if S.basis[i] >= n)
    if art > _INFEAS:
        # Farkas 证书（2026-09-27）：一阶段的对偶 y 满足 yᵀA_j ≤ 0（原变量列约化成本 ≥ 0）与 yᵀb = Σ人工 > 0。
        # 在**原始未缩放**数据上核验；核验不过就抛错——"不可行"与"最优""无界"一样必须带证书，不许静默
        # （复核者实测：尺度极差的可行问题曾被静默判为 infeasible）。证书随结果返回（LPResult.y）。
        yq1 = S.duals(cost1)
        y1 = [ldexp(yq1[i], er[i]) for i in range(m)]
        for i in flipped:
            y1[i] = -y1[i]
        ymax = max((abs(v) for v in yq1), default=0.0)
        ybar = [ldexp(ymax, er[i]) for i in range(m)]        # 各行乘子的量级（原单位）：舍入噪声 ~ eps·ȳ_i
        if not _farkas_verifies(A0, bvec0, y1, ybar):
            raise RuntimeError("phase one ended with positive infeasibility but the Farkas certificate "
                               "does not verify on the original data; refusing to report infeasible")
        return LPResult(INFEASIBLE, [0.0] * n, float("nan"), y1, S.iters, list(S.basis))

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
    st, info = _certified_optimize(S, cost2, allow2, tol, ray_ok, phase=2)
    if st == UNBOUNDED:
        e, d = info
        ray = _ray(S, e, d, ec)
        return LPResult(UNBOUNDED, [0.0] * n, float("-inf"), [0.0] * m, S.iters, list(S.basis), ray)

    xb = S.xB(b)
    ft2 = S.ftol(b)
    xn = [0.0] * n                            # 规整单位里的解
    for i in range(m):
        j = S.basis[i]
        if j < n:
            xn[j] = xb[i] if xb[i] > 0.0 else 0.0 if xb[i] >= -ft2[i] else xb[i]
        elif abs(xb[i]) > max(_INFEAS * S.nu[j], ft2[i]):
            raise RuntimeError(f"simplex left an artificial variable at {xb[i]!r} in a redundant row")
    _guard_residual(A, b, xn, S.nu)
    yq = S.duals(cost2)
    _guard_gap(cost2, xn, b, yq)
    x = [ldexp(xn[j], ec[j] + es) for j in range(n)]
    y = [ldexp(yq[i], er[i] - ek) for i in range(m)]
    for i in flipped:
        y[i] = -y[i]
    return LPResult(OPTIMAL, x, sum(ci * xi for ci, xi in zip(c0, x)), y, S.iters, list(S.basis))


def _certified_optimize(S: _Revised, cost: list[float], allowed: list[bool], tol: float, ray_ok,
                        *, phase: int) -> tuple[str, object]:
    """优化 + 独立核验：最终基上重新求逆，约化成本必须 ≥ −_DUAL_CHECK（相对）；不过就收紧定价阈值再迭代。"""
    ptol = tol
    for _ in range(_CLEANUP_ROUNDS):
        st, info = S.optimize(cost, allowed, ptol, ray_ok)
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
    raise RuntimeError(f"simplex phase {phase} could not reach a verified optimal basis "
                       f"(dual violation {S.dual_violation(cost, allowed)!r})")


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

def _guard_residual(A: list[list[float]], b: list[float], x: list[float], nu: list[float]) -> None:
    """粗差守卫：基解必须满足 Ax = b、x ≥ 0（逐行、逐变量相对，规整单位）。

    若在极小主元上失稳，读出来的基解会整行违反约束，而单纯形照样报 OPTIMAL——那是最坏的失败方式（静默给错值）。
    判据：|A_i x − b_i| ≤ _RESIDUAL_GUARD·(|b_i| + Σ_j|A_ij x_j|) + _CERT_NOISE·X·Σ_j|A_ij|ν_j，
    x_j ≥ −_RESIDUAL_GUARD·ν_j·max(1, X)，X = max_j |x_j|/ν_j。第二项是**舍入噪声项**：b_i = 0、各项贡献本身
    只有舍入量级的行（x_j 是 ~eps·ν_j 的噪声）在纯相对判据下是 噪声/噪声 ≈ 1；噪声项按变量的自然尺度计，
    不按全局最大值计，所以右端项 1e-11 的行照样查得出整行违反。
    **没有与问题无关的绝对下限**（2026-09-27 订正）：旧判据 ≤ 1e-7·(1 + 行尺度) 里的"1"是绝对量，右端项全局归一后
    量级 1e-11 的行（旧写法里 c·A 乘进列、上限行右端 1 的黏聚行）整行违反 99% 也照样放行，
    报 optimal、α 高估 75%（复核者 LP 层探针 39/48 静默给错）。"""
    X = max((abs(v) / nu[j] for j, v in enumerate(x)), default=0.0)   # 最大变量，以其自然尺度计
    for j, v in enumerate(x):
        if v < -_RESIDUAL_GUARD * nu[j] * max(1.0, X):
            raise RuntimeError(f"simplex lost primal feasibility: x[{j}] = {v!r} (scaled units, natural scale {nu[j]!r})")
    for i, (Ai, bi) in enumerate(zip(A, b)):
        ax = sum(a * v for a, v in zip(Ai, x))
        scale = abs(bi) + sum(abs(a * v) for a, v in zip(Ai, x))
        noise = _CERT_NOISE * X * sum(abs(a) * nu[j] for j, a in enumerate(Ai))
        if abs(ax - bi) > _RESIDUAL_GUARD * scale + noise:
            raise RuntimeError(f"simplex lost feasibility: row {i} residual {ax - bi!r} "
                               f"(scaled units, row scale {scale!r})")

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


def _farkas_verifies(A0: list[list[float]], b0: list[float], y: list[float], ybar: list[float]) -> bool:
    """Farkas 证书核验（原始未缩放数据）：yᵀb > 0 显著，且每列 yᵀA_j ≤ 0（到舍入）。

    判据（ȳ_i = max|y'|·2^{er_i}：规整单位里乘子的最大量级、折回原单位；nz_j = Σ_i ȳ_i|A_ij|，nb = Σ_i ȳ_i|b_i|）：
      列：    yᵀA_j ≤ 1e-9·Σ_i|y_i A_ij| + _NOISE_FLOOR·nz_j     （y 的噪声带条件数放大：实测到 7.2e-15·nz）
      右端：  yᵀb  > 1e-9·Σ_i|y_i b_i| + _CERT_NOISE·nb        （只需高出舍入底：恒载 (1, −1e12) 的水平分量
                                                                 无物可挡时 yᵀb/nb = 1e-12，仍是真不可行）
      分离：  yᵀb / nb ≥ 1e3·max_j (yᵀA_j)⁺ / nz_j             （证书的余量远大于它容许的列违约）
    只用逐项相对判据时，与证书正交的列（精确 yᵀA_j = 0）是 噪声/噪声 ≈ 1（09-27 实测 48/1000 假抛错）。
    容差版 Farkas 的含义：若 x ≥ 0 可行，则 yᵀb = Σ_j (yᵀA_j) x_j ≤ Σ_j ε_j x_j，于是任何可行解都得比问题的
    自然尺度大 ~1e3 倍以上——"不可行"即"在这个分辨率内不可行"。"""
    m = len(A0)
    n = len(A0[0]) if m else 0
    yb = sum(y[i] * b0[i] for i in range(m))
    sb = sum(abs(y[i] * b0[i]) for i in range(m))
    nb = sum(ybar[i] * abs(b0[i]) for i in range(m))
    if not (yb > 0.0 and yb > 1e-9 * sb + _CERT_NOISE * nb):
        return False
    worst = 0.0
    for j in range(n):
        v = sum(y[i] * A0[i][j] for i in range(m))
        sc = sum(abs(y[i] * A0[i][j]) for i in range(m))
        nz = sum(ybar[i] * abs(A0[i][j]) for i in range(m))
        if v > 1e-9 * sc + _NOISE_FLOOR * nz:
            return False
        if v > 0.0 and nz > 0.0:
            worst = max(worst, v / nz)
    return yb >= 1e3 * worst * nb

def _guard_gap(c: list[float], x: list[float], b: list[float], y: list[float]) -> None:
    """相对对偶间隙守卫（规整单位）：|cᵀx − bᵀy| ≤ _GAP_CHECK·(Σ|c_j x_j| + Σ|y_i b_i|) + 噪声项。

    噪声项 _CERT_NOISE·(max|y|·Σ|b_i| + max|c|·Σ|x_j|)：最优值恰为 0 的问题（α = 0 的极限状态）里各项都是
    舍入量级，纯相对判据是 噪声/噪声 ≈ 1（2026-09-27 实测 16/12000 假抛错，间隙 1e-17 对尺度 1e-17）。"""
    p = sum(ci * xi for ci, xi in zip(c, x))
    d = sum(yi * bi for yi, bi in zip(y, b))
    scale = sum(abs(ci * xi) for ci, xi in zip(c, x)) + sum(abs(yi * bi) for yi, bi in zip(y, b))
    noise = _CERT_NOISE * (max((abs(v) for v in y), default=0.0) * sum(abs(v) for v in b)
                            + max((abs(v) for v in c), default=0.0) * sum(abs(v) for v in x))
    if abs(p - d) > _GAP_CHECK * scale + noise:
        raise RuntimeError(f"simplex duality gap {p - d!r} exceeds {_GAP_CHECK} relative (scale {scale!r})")

def maximize(A: list[list[float]], b: list[float], c: list[float], **kw) -> LPResult:
    """max cᵀx s.t. Ax = b, x ≥ 0。"""
    res = solve(A, b, [-v for v in c], **kw)
    if res.status == OPTIMAL:
        return LPResult(res.status, res.x, -res.obj, [-v for v in res.y],
                        res.iterations, res.basis)
    if res.status == UNBOUNDED:
        return LPResult(UNBOUNDED, res.x, float("inf"), res.y, res.iterations, res.basis, res.ray)
    return res
