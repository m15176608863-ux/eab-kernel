"""稠密单纯形法（两阶段 + Bland 规则）。纯 Python、零依赖。

L3 极限分析要解的是小规模线性规划（变量数 ~ 接触数 × 摩擦锥棱数，约束数 = 位形自由度），
几十到几百量级，稠密表格够用。

标准型：  min cᵀx   s.t.  Ax = b,  x ≥ 0

**为什么用 Bland 规则而不是最陡下降**：Bland 规则保证有限步终止（不循环），
而极限分析的 LP 天然高度退化（多个接触共面、对称位形），最陡下降在退化顶点上会循环。
代价是迭代数可能多一些——这里规模小，不值得为速度换正确性。

返回里带**对偶解 y**：在极限分析里它就是破坏机构（上限定理的运动场），不是附属品。

**尺度规整（2026-09-22，审查 C0/C21 及其尺度格子）**：`tol` 是绝对阈值，而 A、b 带着用户的单位
（荷载 N/kN、几何 m/mm、黏聚列 ∝ c·A）。旧代码的三种静默失败：
  · 一阶段结束时人工变量和的舍入残差 ~ eps·max|b|·(主元数)，N = 100 时就有 ~2e-12，拿它与绝对的
    tol = 1e-12 比，可行问题被判成 INFEASIBLE（互锁块 (amp, μ, k) = (0.2, 0.1, 8) 等 9 格）；
  · 列量级悬殊（黏聚列 ~1e4 与单位约束行并存）时在 ~3e-10 的主元上失稳，读出的基解整行违反 Ax = b
    （残差 ~1e3），却照样报 OPTIMAL（荷载 ×1e4 的三维黏聚算例，承载力超出解析上界）；
  · 一阶段的入基检验数是舍入噪声时核心报 UNBOUNDED，被当成 INFEASIBLE（一阶段目标有下界 0，
    精确算术里不可能无界）。现在一阶段只看人工变量和。
现在求解前做三步，因子**全是 2 的幂**（乘除都精确，不引入任何舍入）：
  1. 列均衡：A_j 乘 2^−e_j 使 max_i|A_ij| ∈ [0.5, 1)，c_j 同乘；x_j 最后乘回；
  2. 行均衡：行 i 乘 2^−e_i 使 max_j|A_ij| ∈ [0.5, 1)，b_i 同乘；对偶 y_i 最后乘回；
  3. 右端项归一：b 除以 s = 2^⌈log₂ max b⌉（仅当 max b > 1），x 乘回 s；y 与 b 无关，不动。
于是一阶段可行性阈值、比值检验的并列容差、主元阈值都作用在**均衡后**的量级上（相对阈值）；
对 max|b| > 1 的问题，b 乘 2 的幂时整个求解逐位按比例（门：tests/test_lp_scale.py）。
返回前再核对一次 Ax = b（`_guard_residual`）：数值失稳就抛 RuntimeError，不静默给错值。
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
    basis: list[int]


def _pivot(T: list[list[float]], basis: list[int], r: int, c: int) -> None:
    piv = T[r][c]
    T[r] = [v / piv for v in T[r]]
    for i in range(len(T)):
        if i != r and T[i][c] != 0.0:
            f = T[i][c]
            T[i] = [a - f * b for a, b in zip(T[i], T[r])]
    basis[r] = c


def _simplex_core(T: list[list[float]], basis: list[int], ncols: int, *,
                  allowed: set[int] | None, tol: float, max_iter: int) -> tuple[str, int]:
    """在给定表格上跑单纯形。最后一行是（负的）目标行。Bland 规则：入基取最小可行下标。"""
    it = 0
    m = len(T) - 1
    while it < max_iter:
        it += 1
        enter = -1
        for j in range(ncols):
            if allowed is not None and j not in allowed:
                continue
            if T[m][j] < -tol:
                enter = j
                break
        if enter < 0:
            return OPTIMAL, it
        leave, best = -1, None
        for i in range(m):
            if T[i][enter] > tol:
                ratio = T[i][-1] / T[i][enter]
                # Bland：比值相同时取**基变量下标最小**的行，防循环
                if best is None or ratio < best - tol or (abs(ratio - best) <= tol
                                                          and basis[i] < basis[leave]):
                    leave, best = i, ratio
        if leave < 0:
            return UNBOUNDED, it
        _pivot(T, basis, leave, enter)
    raise RuntimeError(f"simplex did not terminate in {max_iter} iterations")


def _rhs_scale(b: list[float]) -> float:
    """b（已规整为 ≥ 0）的归一因子：max b ≤ 1 时为 1，否则为不小于 max b 的最小 2 的幂。"""
    bmax = max(b, default=0.0)
    if not bmax > 1.0:
        return 1.0
    mant, e = frexp(bmax)                    # bmax = mant·2^e，mant ∈ [0.5, 1)
    return ldexp(1.0, e)


def _pow2_inv(v: float) -> float:
    """2^−e，其中 |v| = mant·2^e、mant ∈ [0.5, 1)——乘上它 |v| 落进 [0.5, 1)。v = 0 时返回 1。精确。"""
    if v == 0.0:
        return 1.0
    _, e = frexp(abs(v))
    return ldexp(1.0, -e)


_RESIDUAL_GUARD = 1e-7


def solve(A: list[list[float]], b: list[float], c: list[float], *,
          tol: float = 1e-10, max_iter: int = 20000) -> LPResult:
    """min cᵀx s.t. Ax = b, x ≥ 0。b 的符号、行列尺度与右端项尺度自动规整（见模块文档）。

    `tol` 作用在均衡 + 右端项归一化之后的问题上：一阶段可行性判据是 Σ人工变量 > tol，
    折回原单位即相对于各行量级与 max(1, max|b|) 的阈值。
    返回前核对 Ax = b 的后向误差；若表格在主元中数值失稳（基解不再满足约束），抛 RuntimeError，
    **不**静默返回一个错的"最优"。
    """
    m, n = len(A), len(c)
    if m == 0:
        return LPResult(OPTIMAL, [0.0] * n, 0.0, [], 0, [])
    A = [row[:] for row in A]
    b = b[:]
    # 规整 b ≥ 0。**被取负的行，其对偶乘子最后要翻回来**：
    # 约束 −A_i x = −b_i 的乘子 y 对应原约束 A_i x = b_i 的乘子 −y。
    # 不翻的话 yᵀb 与最优值差符号，强对偶看上去就不成立（2026-09-21 实测 7/12 组报红）。
    flipped = [i for i in range(m) if b[i] < 0.0]
    for i in flipped:
        A[i] = [-v for v in A[i]]
        b[i] = -b[i]
    # 均衡：先列后行，因子全是 2 的幂（精确）。x = D·x'，c' = D·c；行 i 乘 r_i ⇒ y_i = r_i·y'_i。
    cs = [_pow2_inv(max(abs(A[i][j]) for i in range(m))) for j in range(n)]
    A = [[A[i][j] * cs[j] for j in range(n)] for i in range(m)]
    cq = [c[j] * cs[j] for j in range(n)]
    rs = [_pow2_inv(max((abs(v) for v in A[i]), default=0.0)) for i in range(m)]
    A = [[v * rs[i] for v in A[i]] for i in range(m)]
    b = [b[i] * rs[i] for i in range(m)]
    # 右端项尺度归一（精确：2 的幂）。x 最后乘回 s；y = c_Bᵀ B⁻¹ 与 b 无关，不动。
    s = _rhs_scale(b)
    if s != 1.0:
        b = [v / s for v in b]

    # ---- 一阶段：引入人工变量，min Σ 人工
    T = [A[i] + [1.0 if k == i else 0.0 for k in range(m)] + [b[i]] for i in range(m)]
    obj = [0.0] * (n + m) + [0.0]
    for i in range(m):                       # 目标行 = −Σ(含人工变量的行)，消去人工列
        for j in range(n + m + 1):
            obj[j] -= T[i][j]
    for k in range(m):
        obj[n + k] = 0.0
    T.append(obj)
    basis = list(range(n, n + m))
    _, it1 = _simplex_core(T, basis, n + m, allowed=set(range(n)) | set(range(n, n + m)),
                           tol=tol, max_iter=max_iter)
    # 可行性**只**看人工变量和（均衡 + 归一之后，这里的绝对 tol 在原单位里是相对阈值）。
    # 一阶段目标有下界 0，精确算术里不可能无界；核心若报 UNBOUNDED，只能是某个入基检验数是
    # ~1e-12 的舍入噪声而该列又无正元——那是"已到最优"，不是"不可行"（旧代码把它判成 INFEASIBLE）。
    if -T[m][-1] > tol:
        return LPResult(INFEASIBLE, [0.0] * n, float("nan"), [0.0] * m, it1, basis)

    # 人工变量若仍在基里（退化），设法换出（取该行绝对值最大的元做主元）；换不出说明该行冗余，直接丢
    for i in range(m - 1, -1, -1):
        if basis[i] >= n:
            piv = max(range(n), key=lambda j: abs(T[i][j]), default=None)
            if piv is not None and abs(T[i][piv]) > tol:
                _pivot(T, basis, i, piv)
            else:
                del T[i]
                del basis[i]
    m2 = len(T) - 1

    # ---- 二阶段：换成真目标，去掉人工列
    for i in range(len(T)):
        T[i] = T[i][:n] + [T[i][-1]]
    obj = cq[:] + [0.0]
    for i in range(m2):
        if abs(cq[basis[i]]) > 0.0:
            f = cq[basis[i]]
            for j in range(n + 1):
                obj[j] -= f * T[i][j]
    T[m2] = obj
    st, it2 = _simplex_core(T, basis, n, allowed=None, tol=tol, max_iter=max_iter)
    if st == UNBOUNDED:
        return LPResult(UNBOUNDED, [0.0] * n, float("-inf"), [0.0] * m, it1 + it2, basis)

    xn = [0.0] * n                            # 均衡 + 归一单位里的解
    for i in range(m2):
        xn[basis[i]] = T[i][-1]
    _guard_residual(A, b, xn)
    x = [xn[j] * cs[j] * s for j in range(n)]
    # 对偶：y' 解 B'ᵀ y' = c'_B（均衡后的数据），再按行因子折回；取负的行再翻号
    yq = _duals(A, cq, basis, m, n, tol)
    y = [yq[i] * rs[i] for i in range(m)]
    for i in flipped:
        y[i] = -y[i]
    return LPResult(OPTIMAL, x, sum(ci * xi for ci, xi in zip(c, x)), y, it1 + it2, basis)


def _guard_residual(A: list[list[float]], b: list[float], x: list[float]) -> None:
    """粗差守卫：基解必须满足 Ax = b、x ≥ 0（到后向误差 _RESIDUAL_GUARD）。

    表格法每次主元都在累积舍入；若在极小主元上失稳，读出来的基解会整行违反约束，
    而单纯形照样报 OPTIMAL——那是最坏的失败方式（静默给错值）。这里在均衡 + 归一后的单位里核对，
    健康求解的残差 ~1e-14，守卫阈值留七个量级的余地，只抓粗差。
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


def _duals(A: list[list[float]], c: list[float], basis: list[int], m: int, n: int,
           tol: float) -> list[float]:
    """解 Bᵀ y = c_B（B = 基列）。基不满秩时用最小二乘退化解（冗余行的乘子取 0）。"""
    cols = [j for j in basis if j < n]
    if not cols:
        return [0.0] * m
    # Bᵀ y = c_B  →  行 = 基列，未知 = y
    M = [[A[i][j] for i in range(m)] + [c[j]] for j in cols]
    y = [0.0] * m
    rows = len(M)
    piv_of: list[int] = []
    r = 0
    for col in range(m):
        p = max(range(r, rows), key=lambda i: abs(M[i][col]), default=None)
        if p is None or abs(M[p][col]) <= tol:
            continue
        M[r], M[p] = M[p], M[r]
        pv = M[r][col]
        M[r] = [v / pv for v in M[r]]
        for i in range(rows):
            if i != r and abs(M[i][col]) > 0.0:
                f = M[i][col]
                M[i] = [a - f * bb for a, bb in zip(M[i], M[r])]
        piv_of.append(col)
        r += 1
        if r == rows:
            break
    for i, col in enumerate(piv_of):
        y[col] = M[i][-1]
    return y


def maximize(A: list[list[float]], b: list[float], c: list[float], **kw) -> LPResult:
    """max cᵀx s.t. Ax = b, x ≥ 0。"""
    res = solve(A, b, [-v for v in c], **kw)
    if res.status == OPTIMAL:
        return LPResult(res.status, res.x, -res.obj, [-v for v in res.y],
                        res.iterations, res.basis)
    if res.status == UNBOUNDED:
        return LPResult(UNBOUNDED, res.x, float("inf"), res.y, res.iterations, res.basis)
    return res
