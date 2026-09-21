"""稠密单纯形法（两阶段 + Bland 规则）。纯 Python、零依赖。

L3 极限分析要解的是小规模线性规划（变量数 ~ 接触数 × 摩擦锥棱数，约束数 = 位形自由度），
几十到几百量级，稠密表格够用。

标准型：  min cᵀx   s.t.  Ax = b,  x ≥ 0

**为什么用 Bland 规则而不是最陡下降**：Bland 规则保证有限步终止（不循环），
而极限分析的 LP 天然高度退化（多个接触共面、对称位形），最陡下降在退化顶点上会循环。
代价是迭代数可能多一些——这里规模小，不值得为速度换正确性。

返回里带**对偶解 y**：在极限分析里它就是破坏机构（上限定理的运动场），不是附属品。
"""

from __future__ import annotations

from dataclasses import dataclass

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


def solve(A: list[list[float]], b: list[float], c: list[float], *,
          tol: float = 1e-10, max_iter: int = 20000) -> LPResult:
    """min cᵀx s.t. Ax = b, x ≥ 0。b 的符号自动规整。"""
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
    st, it1 = _simplex_core(T, basis, n + m, allowed=set(range(n)) | set(range(n, n + m)),
                            tol=tol, max_iter=max_iter)
    if st == UNBOUNDED or -T[m][-1] > tol:
        return LPResult(INFEASIBLE, [0.0] * n, float("nan"), [0.0] * m, it1, basis)

    # 人工变量若仍在基里（退化），设法换出；换不出说明该行冗余，直接丢
    for i in range(m - 1, -1, -1):
        if basis[i] >= n:
            piv = next((j for j in range(n) if abs(T[i][j]) > tol), None)
            if piv is not None:
                _pivot(T, basis, i, piv)
            else:
                del T[i]
                del basis[i]
    m2 = len(T) - 1

    # ---- 二阶段：换成真目标，去掉人工列
    for i in range(len(T)):
        T[i] = T[i][:n] + [T[i][-1]]
    obj = c[:] + [0.0]
    for i in range(m2):
        if abs(c[basis[i]]) > 0.0:
            f = c[basis[i]]
            for j in range(n + 1):
                obj[j] -= f * T[i][j]
    T[m2] = obj
    st, it2 = _simplex_core(T, basis, n, allowed=None, tol=tol, max_iter=max_iter)
    if st == UNBOUNDED:
        return LPResult(UNBOUNDED, [0.0] * n, float("-inf"), [0.0] * m, it1 + it2, basis)

    x = [0.0] * n
    for i in range(m2):
        x[basis[i]] = T[i][-1]
    # 对偶：y = c_B ᵀ B⁻¹，可从目标行的松弛读出；这里直接用 A、基解回算最稳
    y = _duals(A, c, basis, m, n, tol)
    for i in flipped:
        y[i] = -y[i]
    return LPResult(OPTIMAL, x, sum(ci * xi for ci, xi in zip(c, x)), y, it1 + it2, basis)


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
