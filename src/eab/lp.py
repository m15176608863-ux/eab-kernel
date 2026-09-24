"""稠密修正单纯形法（两阶段）。纯 Python、零依赖。

L3 极限分析要解的是小规模线性规划（变量数 ~ 接触数 × 摩擦锥棱数，约束数 = 位形自由度 + 黏聚行），
几十到几百量级，稠密够用。

标准型：  min cᵀx   s.t.  Ax = b,  x ≥ 0

返回里带**对偶解 y**：在极限分析里它就是破坏机构（上限定理的运动场），不是附属品。

## 契约（2026-09-24，G6 之后重写）

**要么答对，要么抛 RuntimeError，绝不静默给错。** 具体地：
  · 报 OPTIMAL 之前，在最终基上**重新求逆**，独立核验三件事：原始可行（`_guard_residual`：Ax = b、x ≥ 0 的
    相对后向误差）、对偶可行（全部约化成本 c_j − yᵀA_j ≥ −1e-9·(|c_j| + Σ|y_i A_ij|)）、相对对偶间隙。
    对偶核验与调用方的 `tol` **无关**：`tol` 放宽只会让单纯形早停，早停的基过不了核验，于是按固定阈值继续迭代
    （"清理"）；清理三轮仍过不了就抛错（G6 minor 24：放宽 lp_tol 曾静默返回次优）；
  · 报 UNBOUNDED 之前，用**原始未缩放的 A** 核验无界射线 d：d ≥ 0、每行 |A_i d| ≤ 1e-9·Σ_j|A_ij d_j|、cᵀd < 0。
    核验不过（比值检验把一条真正约束步长的行当成了噪声）就退回去在最大的正元上换基；实在无行可换才抛错
    （G6 critical 0：比值检验的绝对阈值曾让黏聚上限行掉出，报 unbounded、承载力 ∞）；
  · 报 INFEASIBLE 的依据是一阶段最优值（归一单位里 Σ人工 > 1e-8，相对于 max|b|），而一阶段的最优性同样经过
    上面的对偶核验——一阶段的对偶解就是 Farkas 不可行证书。
  · 终止**不是**无条件保证的：Bland 规则只在精确算术里保证有限步终止，浮点下"平局在容差内判定"会真的循环
    （G6 major 2：旧实现 k=128 时 409 步一周期）。现在的做法见下；仍超过 `max_iter` 就抛 RuntimeError。

## 做法

**尺度规整**（因子全是 2 的幂，乘除精确，不引入舍入）：
  1. 列均衡：A_j 乘 2^−e_j 使 max_i|A_ij| ∈ [0.5, 1)，c_j 同乘；x_j 最后乘回；
  2. 行均衡：行 i 乘 2^−e_i 使 max_j|A_ij| ∈ [0.5, 1)，b_i 同乘；对偶 y_i 最后乘回；
  3. 右端项归一：b 除以 s = 2^⌈log₂ max|b|⌉（**双向**：max|b| < 1 时同样归一；b ≡ 0 时 s = 1）。
     旧实现只在 max b > 1 时归一，于是 max|b| ≲ 1e-10 的不可行问题被判 OPTIMAL（G6 minor 4）；
  4. **目标归一**：c 乘 2^−e 使 max|c_j| ∈ [0.5, 1)，最优值与对偶 y 最后精确还原。旧实现目标行只随列因子缩放、
     入基检验用绝对 1e-10：活荷载旋量 > 2^33 时 α 列永远进不了基，报 OPTIMAL 且 α = 0（G6 critical 19）。
  于是所有阈值都作用在规整后的 O(1) 量级上；b 乘 2 的幂时整个求解逐位按比例（门：tests/test_lp_scale.py）。

**迭代**：修正单纯形，显式维护基逆 B⁻¹（每次换基做秩一更新，每 32 次换基从原始（规整后）数据重新求逆，
核验前必重新求逆）；x_B = B⁻¹b 每步从 b 重算——表格法的舍入漂移（G6 major 2 的"丢失可行性"）无处累积。
  · 入基：Dantzig（约化成本最负者），判据**相对**：r_j < −tol·(|c_j| + Σ_i|y_i A_ij|)；
  · 出基：Harris 两遍比值检验——先以可行性松弛 1e-9 求步长上界，再在不超过上界的行里取**主元最大**者；
    主元 ≥ 1e-9·max|d| 的"稳定行"优先，只有它们都不约束步长时才接受小主元；≤ 1e-13·max|d| 的元视为舍入噪声；
  · 防循环：记录访问过的基集合，**基重复即判循环**，改用扰动右端项（在当前基上把各基变量抬高互异的 ~1e-7，
    使问题非退化）继续；到最优后撤掉扰动，若基解不再可行，用对偶单纯形（同样相对阈值、同样检测循环）修复。
  · 对偶解 y 直接取 c_Bᵀ B⁻¹（重新求逆之后），不再另解 Bᵀy = c_B（G6 major 1：旧 `_duals` 用绝对主元截断，
    大块体带黏聚时对偶行乘子被置 0，上限少 41.8%）。
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
_PIV_NOISE = 1e-13        # 噪声线：d_i ≤ _PIV_NOISE·max|d| 视为 0
_DUAL_CHECK = 1e-9        # 对偶可行性核验（相对，与 tol 无关）
_GAP_CHECK = 1e-9         # 相对对偶间隙核验
_RAY_CHECK = 1e-9         # 无界射线核验（逐行相对）
_REINVERT = 32            # 每多少次换基重新求逆
_PERTURB = 1e-7           # 防循环扰动的基准幅度（规整单位）
_MAX_PERTURB = 6          # 一次优化里最多扰动几轮
_CLEANUP_ROUNDS = 3       # 核验不过时最多清理几轮
_EPS = 2.0 ** -52
_NOISE_ULPS = 100.0       # 舍入噪声线的安全系数（见 `_Revised.noise`）


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

    def noise(self, y: list[float]) -> float:
        """约化成本的**舍入噪声线**（每单位 ‖A_j‖₁）：ν = K·m·eps·κ∞(B)·‖y‖∞，r_j 的噪声 ≲ ν·‖A_j‖₁。

        为什么需要它（2026-09-25，G6 复核 G2/G3）：只用列自己的 |c_j| + Σ|y_k A_kj| 作相对尺度时，
        与机构正交的列（倾覆时基面上的黏聚列：精确 y 在其支撑上恰为 0）尺度本身就是舍入噪声，r_j / 尺度 ≈ ±1，
        默认容差下普通块体抛 "could not reach a verified optimal basis"（物理模糊测试 59/2000）。
        这些分量上的噪声来自 B⁻¹ 的计算（部分主元消元把 O(1) 的量混进精确为 0 的元），逐分量界量不到它；
        标准的**范数型**前向误差界 ‖δy‖∞ ≲ m·eps·κ∞(B)·‖y‖∞ 量得到。所以判据是
        r_j ≥ −(tol·(|c_j| + Σ|y_k A_kj|) + ν·‖A_j‖₁)：相对项管真实的约化成本，噪声线只吸收可证明的舍入。
        全部在规整单位里（行/列/目标都已归一），κ∞ 与 ‖y‖∞ 对 2 的幂缩放精确不变。
        B 良态时 ν ~ 1e-13·‖y‖∞：互不耦合的块里 1e-12 量级的目标系数照样被识别
        （tests/test_lp.py::test_tiny_objective_coefficients_are_not_ignored）。"""
        m = self.m
        ymax = max((abs(v) for v in y), default=0.0)
        if ymax == 0.0:
            return 0.0
        bnorm = max(sum(abs(self.cols[j][i]) for j in self.basis) for i in range(m))
        inorm = max(sum(abs(v) for v in row) for row in self.Binv)
        return _NOISE_ULPS * m * _EPS * bnorm * inorm * ymax

    def direction(self, e: int) -> list[float]:
        col = self.cols[e]
        return [_dot(row, col) for row in self.Binv]

    def reduced(self, cost: list[float], y: list[float], j: int) -> tuple[float, float]:
        r = cost[j] - _dot(y, self.cols[j])
        s = abs(cost[j]) + sum(abs(yk) * a for yk, a in zip(y, self.acols[j]))
        return r, s

    def violates(self, r: float, s: float, nu: float, j: int, tol: float) -> bool:
        """r_j < −(tol·s_j + ν·‖A_j‖₁)：约化成本在相对阈值与舍入噪声线之外为负。"""
        return r < -(tol * s + nu * self.csum[j])

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
        nu = self.noise(y)
        best, e = 0.0, -1
        for j in range(self.n + self.m):
            if not allowed[j] or self.inbasis[j]:
                continue
            r = cost[j] - _dot(y, self.cols[j])
            if r < 0.0 and r < best:
                s = abs(cost[j]) + sum(abs(yk) * a for yk, a in zip(y, self.acols[j]))
                if self.violates(r, s, nu, j, tol):
                    best, e = r, j
        return e

    def ratio(self, d: list[float], x: list[float], *, noise: float | None = None) -> int:
        """Harris 两遍比值检验。返回出基行；没有约束步长的行返回 −1（候选无界方向）。"""
        if noise is None:
            noise = _PIV_NOISE
        dmax = max((abs(v) for v in d), default=0.0)
        if dmax == 0.0:
            return -1
        lo, hi = noise * dmax, _PIV_STABLE * dmax
        theta = float("inf")
        for i, di in enumerate(d):
            if di > lo:
                t = (max(x[i], -_FEAS) + _FEAS) / di
                if t < theta:
                    theta = t
        if theta == float("inf"):
            return -1
        pick, pv = -1, 0.0
        for tier in (hi, lo):
            for i, di in enumerate(d):
                if di > tier and max(x[i], 0.0) / di <= theta:
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
            p = self.ratio(d, x)
            if p < 0:
                if not perturbed and ray_ok(e, d):
                    return UNBOUNDED, (e, d)
                p = self.ratio(d, x, noise=0.0)        # 射线不成立：有一行其实约束步长，接受小主元
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
                delta = [eps * (1.0 + ((i * 0.6180339887498949) % 1.0)) for i in range(self.m)]
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
            p = min(range(self.m), key=lambda i: x[i], default=-1)
            if p < 0 or x[p] >= -_FEAS:
                return
            y = self.duals(cost)
            nu = self.noise(y)
            rho = self.Binv[p]
            cand = []
            amax = 0.0
            for j in range(self.n + self.m):
                if not allowed[j] or self.inbasis[j]:
                    continue
                a = _dot(rho, self.cols[j])
                if a < 0.0:
                    r, s = self.reduced(cost, y, j)
                    cand.append((j, a, max(r, 0.0), max(tol, _DUAL_CHECK) * s + nu * self.csum[j]))
                amax = max(amax, abs(a))
            cand = [c for c in cand if -c[1] > _PIV_NOISE * amax]
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
        """max_j (−r_j − ν·‖A_j‖₁) / scale_j，只看允许的非基列（ν 见 `noise`：先扣掉可证明的舍入噪声）。"""
        y = self.duals(cost)
        nu = self.noise(y)
        worst = 0.0
        for j in range(self.n + self.m):
            if not allowed[j] or self.inbasis[j]:
                continue
            r, s = self.reduced(cost, y, j)
            excess = -r - nu * self.csum[j]
            if excess > 0.0:
                worst = max(worst, excess / s if s > 0.0 else float("inf"))
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
    A0, c0 = A, c
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
    art = sum(x[i] for i in range(m) if S.basis[i] >= n)
    if art > _INFEAS:
        return LPResult(INFEASIBLE, [0.0] * n, float("nan"), [0.0] * m, S.iters, list(S.basis))

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
    xn = [0.0] * n                            # 规整单位里的解
    for i in range(m):
        j = S.basis[i]
        if j < n:
            xn[j] = xb[i] if xb[i] > 0.0 else 0.0 if xb[i] >= -_FEAS else xb[i]
        elif abs(xb[i]) > _INFEAS:
            raise RuntimeError(f"simplex left an artificial variable at {xb[i]!r} in a redundant row")
    _guard_residual(A, b, xn)
    yq = S.duals(cost2)
    _guard_gap(cost2, xn, b, yq, S.noise(yq))
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
        if min(x, default=0.0) < -10.0 * _FEAS:
            S.dual_simplex(cost, allowed, ptol)       # 基解不可行（数值）：先修复原始可行性
            continue
        if S.dual_violation(cost, allowed) <= _DUAL_CHECK:
            return OPTIMAL, None
        ptol = min(ptol, _DUAL_CHECK) * 0.1
    raise RuntimeError(f"simplex phase {phase} could not reach a verified optimal basis "
                       f"(dual violation {S.dual_violation(cost, allowed)!r})")


def _ray(S: _Revised, e: int, d: list[float], ec: list[int]) -> list[float]:
    """规整单位里的射线 d'（x_e 增 1，基变量减 d_i；小负值截为 0）折回原单位：d_j = 2^ec_j·d'_j。"""
    n = S.n
    r = [0.0] * n
    r[e] = 1.0
    for i, di in enumerate(d):
        j = S.basis[i]
        if j < n:
            r[j] = max(-di, 0.0)
    return [ldexp(r[j], ec[j]) for j in range(n)]


def _ray_verifies(A0, c0, S: _Revised, e: int, d: list[float], ec: list[int]) -> bool:
    """用**原始未缩放**的 A、c 核验无界射线：d ≥ 0、逐行 |A_i d| ≤ 1e-9·Σ_j|A_ij d_j|、cᵀd < 0。
    逐行相对判据对行/列对角缩放不变。基里的人工变量若沿射线变化（d_i 不是噪声），射线不成立。"""
    n = S.n
    for i, di in enumerate(d):
        if S.basis[i] >= n and abs(di) > _PIV_NOISE * max(abs(v) for v in d):
            return False
    ray = _ray(S, e, d, ec)
    sums = []
    for row in A0:
        r = sum(a * v for a, v in zip(row, ray))
        s = sum(abs(a * v) for a, v in zip(row, ray))
        sums.append((r, s))
    smax = max((s for _, s in sums), default=0.0)
    for r, s in sums:
        if abs(r) > _RAY_CHECK * s + 1e-14 * smax:
            return False
    cd = sum(ci * v for ci, v in zip(c0, ray))
    sc = sum(abs(ci * v) for ci, v in zip(c0, ray))
    return cd < -_RAY_CHECK * sc


def _guard_residual(A: list[list[float]], b: list[float], x: list[float]) -> None:
    """粗差守卫：基解必须满足 Ax = b、x ≥ 0（到后向误差 _RESIDUAL_GUARD）。

    若在极小主元上失稳，读出来的基解会整行违反约束，而单纯形照样报 OPTIMAL——那是最坏的失败方式（静默给错值）。
    这里在均衡 + 归一后的单位里核对，健康求解的残差 ~1e-14，守卫阈值留七个量级的余地，只抓粗差。
    """
    xmax = max((abs(v) for v in x), default=0.0)
    for j, v in enumerate(x):
        if v < -_RESIDUAL_GUARD * (1.0 + xmax):
            raise RuntimeError(f"simplex lost primal feasibility: x[{j}] = {v!r} (scaled units)")
    for i, (Ai, bi) in enumerate(zip(A, b)):
        ax = sum(a * v for a, v in zip(Ai, x))
        scale = abs(bi) + sum(abs(a * v) for a, v in zip(Ai, x))
        if abs(ax - bi) > _RESIDUAL_GUARD * (1.0 + scale):
            raise RuntimeError(f"simplex lost feasibility: row {i} residual {ax - bi!r} "
                               f"(scaled units, row scale {scale!r})")


def _guard_gap(c: list[float], x: list[float], b: list[float], y: list[float], nu: float) -> None:
    """相对对偶间隙守卫（规整单位）：cᵀx 与 bᵀy 必须一致到 _GAP_CHECK·(Σ|c_j x_j| + Σ|y_k b_k|) + ν·‖b‖₁。
    ν 是 y 的舍入噪声线（`_Revised.noise`）：最优值为 0 的问题（α = 0）两边只剩舍入，只用相对项时 2e-17 的噪声
    也会超标（2026-09-25 模糊测试 1/3000）。"""
    p = sum(ci * xi for ci, xi in zip(c, x))
    d = sum(yi * bi for yi, bi in zip(y, b))
    scale = sum(abs(ci * xi) for ci, xi in zip(c, x)) + sum(abs(yi * bi) for yi, bi in zip(y, b))
    if abs(p - d) > _GAP_CHECK * scale + nu * sum(abs(v) for v in b) + 1e-300:
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
