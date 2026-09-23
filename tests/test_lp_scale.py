"""lp.solve 的尺度门（审查 C0 / C21：一阶段可行性用了绝对阈值；及尺度格子逼出的两处同源缺陷）。

缺陷：一阶段结束时人工变量和的舍入残差 ~ eps·|b|·(主元数)，而判据是绝对的 `残差 > tol`；
荷载单位一放大（b ~ 1e2…1e6），可行问题就被静默判成 INFEASIBLE。按纪律 B 把列量级也放进格子后，
又逼出：列放大 1e2/1e4 时同样假不可行；一阶段入基检验数是舍入噪声时被当成"不可行"。

**oracle（纪律 A）**：
  · 可行性、有界性由构造保证：取 x0 ≥ 0、b = A·x0；c > 0 ⇒ cᵀx ≥ 0；
  · **最优性证书** `_certify`（本文件自算，不调用 lp.py 的任何原语）：x 原始可行（Ax = b、x ≥ 0）、
    y 对偶可行（c − Aᵀy ≥ 0）、对偶间隙 cᵀx − bᵀy = 0 ⇒ x 最优（LP 对偶定理）。每个被比较的解都先过证书；
  · 蜕变关系（解析性质）：b → s·b 最优值 ×s；行 i 乘 r_i 可行集不变；列 j 与 c_j 同乘 f 最优值不变。
    **共用声明**：蜕变比较的参照值也来自 solve；若 solve 在参照问题上就错、且错得与尺度无关，蜕变关系
    本身抓不到——所以参照解同样先过 `_certify`，证书才是独立真值。

**格子（纪律 B）**：
  · 尺度：b × {1, 1e2, 1e4, 1e6}；行 × 1e-3（几何缩小后力矩行变小）；列 × {1e2, 1e4, 1e-4}（黏聚列 ∝ c·A）；
  · 一般位置：A 取 U(−1, 1) 实数（非整数、无对称），x0 半数分量为零（退化顶点）；
  · 分界：一例 b 含零行（该行恰在可行性边界上）。
"""

import random

import pytest

from eab.lp import OPTIMAL, solve

SCALES = [1.0, 1e2, 1e4, 1e6]


def _system(seed, m=6, n=40, zero_row=False):
    rng = random.Random(seed)
    A = [[rng.uniform(-1.0, 1.0) for _ in range(n)] for _ in range(m)]
    x0 = [rng.uniform(0.0, 1.0) if rng.random() < 0.5 else 0.0 for _ in range(n)]
    if zero_row:
        # 第 0 行只在 x0 的零分量上有系数 ⇒ b_0 = 0 恰好：一个落在边界上的行
        A[0] = [0.0 if x0[j] > 0.0 else A[0][j] for j in range(n)]
    b = [sum(A[i][j] * x0[j] for j in range(n)) for i in range(m)]
    c = [rng.uniform(0.1, 1.0) for _ in range(n)]
    return A, b, c


def _residual(A, x, b):
    """max_i |A_i x − b_i| / (|b_i| + Σ_j |A_ij x_j| + 1)：相对后向误差，本文件自算。"""
    worst = 0.0
    for Ai, bi in zip(A, b):
        ax = sum(a * v for a, v in zip(Ai, x))
        scale = abs(bi) + sum(abs(a * v) for a, v in zip(Ai, x)) + 1.0
        worst = max(worst, abs(ax - bi) / scale)
    return worst


def _certify(A, b, c, r, rel=1e-9):
    """最优性证书（独立 oracle）：原始可行 + 对偶可行 + 零对偶间隙，全部相对量级判定。"""
    assert r.status == OPTIMAL, r.status
    xmax = max(abs(v) for v in r.x)
    assert _residual(A, r.x, b) < 1e-12
    assert min(r.x) >= -1e-12 * (1.0 + xmax)
    for j in range(len(c)):
        yAj = sum(r.y[i] * A[i][j] for i in range(len(A)))
        mag = abs(c[j]) + sum(abs(r.y[i] * A[i][j]) for i in range(len(A)))
        assert c[j] - yAj >= -rel * (1.0 + mag), (j, c[j] - yAj)
    primal = sum(cj * xj for cj, xj in zip(c, r.x))
    dual = sum(yi * bi for yi, bi in zip(r.y, b))
    assert abs(primal - dual) <= rel * (1.0 + abs(primal)), (primal, dual)
    assert r.obj == pytest.approx(primal, rel=1e-12, abs=1e-12)


# 种子 45/64/82/117 在未修的 lp.py 上 b×1e4 即判不可行（审查复现：200 个种子里 10 个），
# 其余在 b×1e6 上大面积判不可行。种子 0..3 为一般位置对照。
SEEDS = [0, 1, 2, 3, 45, 64, 82, 117]


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("s", SCALES)
def test_scaled_rhs_stays_optimal_and_objective_is_homogeneous(seed, s):
    """b → s·b：必须仍判最优且过证书，最优值恰为 s 倍（LP 对右端项正齐次）。"""
    A, b, c = _system(seed)
    ref = solve(A, b, c)
    _certify(A, b, c, ref)
    bs = [s * v for v in b]
    r = solve(A, bs, c)
    assert r.status == OPTIMAL, (seed, s, r.status)
    _certify(A, bs, c, r)
    assert r.obj == pytest.approx(s * ref.obj, rel=1e-9), (seed, s, r.obj, s * ref.obj)


@pytest.mark.parametrize("s", SCALES)
def test_boundary_row_with_zero_rhs_stays_optimal_under_scaling(s):
    """分界格子：一行 b_i = 0（可行集贴在该行的边界上）。缩放后仍最优、过证书、值齐次。"""
    A, b, c = _system(7, zero_row=True)
    assert b[0] == 0.0
    ref = solve(A, b, c)
    _certify(A, b, c, ref)
    bs = [s * v for v in b]
    r = solve(A, bs, c)
    _certify(A, bs, c, r)
    assert r.obj == pytest.approx(s * ref.obj, rel=1e-9)


@pytest.mark.parametrize("seed", SEEDS)
def test_row_scaling_by_1e_minus_3_does_not_change_the_answer(seed):
    """行 × 1e-3（几何缩小时力矩行整体变小）：可行集不变 ⇒ 状态与最优值不变。"""
    A, b, c = _system(seed)
    ref = solve(A, b, c)
    _certify(A, b, c, ref)
    A2 = [row[:] for row in A]
    b2 = b[:]
    for i in (1, 3, 5):
        A2[i] = [1e-3 * v for v in A2[i]]
        b2[i] = 1e-3 * b2[i]
    for s in SCALES:
        bs = [s * v for v in b2]
        r = solve(A2, bs, c)
        assert r.status == OPTIMAL, (seed, s, r.status)
        _certify(A2, bs, c, r)
        assert r.obj == pytest.approx(s * ref.obj, rel=1e-9), (seed, s)


# 种子 9/18/42/48 在未修的 lp.py 上，十列放大 1e2/1e4 后判不可行（可行性由构造保证）。
COLSCALE_SEEDS = [0, 1, 9, 18, 42, 48]


@pytest.mark.parametrize("f", [1e2, 1e4, 1e-4])
@pytest.mark.parametrize("seed", COLSCALE_SEEDS)
def test_column_scaling_does_not_change_the_answer(seed, f):
    """列 j 乘 f、c_j 乘 f（变量换元 x_j' = x_j / f）：可行集与最优值不变——解析性质。
    极限分析里黏聚列 ∝ c·A、摩擦列 ~1，列量级悬殊是常态。荷载同时 ×1e4。"""
    A, b, c = _system(seed)
    ref = solve(A, b, c)
    _certify(A, b, c, ref)
    cols = random.Random(1000 + seed).sample(range(len(c)), 10)
    A2 = [row[:] for row in A]
    c2 = c[:]
    for j in cols:
        for i in range(len(A2)):
            A2[i][j] *= f
        c2[j] *= f
    for s in (1.0, 1e4):
        bs = [s * v for v in b]
        r = solve(A2, bs, c2)
        assert r.status == OPTIMAL, (seed, f, s, r.status)
        _certify(A2, bs, c2, r)
        assert r.obj == pytest.approx(s * ref.obj, rel=1e-9), (seed, f, s)


def test_phase_one_rounding_noise_is_not_reported_as_infeasible():
    """种子 9、tol = 1e-12：一阶段收敛后某列检验数是 ~1e-12 的舍入噪声、该列又无正元，
    未修代码把"一阶段无界"（精确算术里不可能）当成 INFEASIBLE。现在必须最优并过证书。"""
    A, b, c = _system(9)
    for s in SCALES:
        bs = [s * v for v in b]
        r = solve(A, bs, c, tol=1e-12)
        assert r.status == OPTIMAL, (s, r.status)
        _certify(A, bs, c, r)


def test_numerical_breakdown_raises_instead_of_returning_a_wrong_optimum(monkeypatch):
    """lp.py 的声称（纪律 C）：基解若不再满足 Ax = b（表格失稳），solve 抛 RuntimeError。
    这里人为在二阶段结束后把表格一行的右端项拨偏 0.1，模拟失稳。"""
    import eab.lp as lp

    real = lp._simplex_core

    def corrupt(T, basis, ncols, *, allowed, tol, max_iter):
        st, it = real(T, basis, ncols, allowed=allowed, tol=tol, max_iter=max_iter)
        if allowed is None:                     # 二阶段
            T[0][-1] += 0.1
        return st, it

    A, b, c = _system(0)
    assert solve(A, b, c).status == OPTIMAL
    monkeypatch.setattr(lp, "_simplex_core", corrupt)
    with pytest.raises(RuntimeError):
        solve(A, b, c)


@pytest.mark.parametrize("seed", SEEDS)
def test_power_of_two_rhs_scaling_is_bitwise_proportional(seed):
    """lp.py 模块文档的声称（纪律 C）：max|b| > 1 时，b 乘 2 的幂 ⇒ x 逐位乘同一个 2 的幂、
    y 逐位不变、主元序列不变。（归一因子是 2 的幂，除法与回乘都是精确的。）"""
    A, b, c = _system(seed)
    b = [4.0 * v for v in b]
    assert max(abs(v) for v in b) > 1.0
    ref = solve(A, b, c)
    for p in (10, 20, 40):
        s = 2.0 ** p
        r = solve(A, [s * v for v in b], c)
        assert r.status == ref.status == OPTIMAL
        assert r.x == [s * v for v in ref.x]
        assert r.y == ref.y
        assert r.basis == ref.basis and r.iterations == ref.iterations


@pytest.mark.parametrize("seed", SEEDS + [9])
def test_status_is_invariant_to_rhs_scale_even_at_a_tight_tolerance(seed):
    """tol=1e-12（limit.py 过去传进来的值）：状态不得随荷载单位改变，且都过证书。"""
    A, b, c = _system(seed)
    for s in SCALES:
        bs = [s * v for v in b]
        r = solve(A, bs, c, tol=1e-12)
        assert r.status == OPTIMAL, (seed, s, r.status)
        _certify(A, bs, c, r)
