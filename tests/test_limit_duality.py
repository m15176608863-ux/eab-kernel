"""带黏聚力时的对偶自校验（审查 C1 / C24）。

缺陷：`limit_load` 为每个黏聚接触在其摩擦列之后插入黏聚列，并加一行 Σλ_coh + s = 1（右端 1）；
而 `check_duality` 只用摩擦锥棱重建列表（下标与 res.lambdas 错位），上限又用 zip 截掉了黏聚行的
对偶乘子 ⇒ 带黏聚力时报出假对偶间隙（恰等于黏聚贡献 2cA）与假互补违约。

**oracle（纪律 A）**：
  · α 用解析闭式（2cA、μW + 2cA、倾覆 W·w/(2h)），与列构造无关；
  · 纯黏聚算例的破坏机构与黏聚行乘子用手算的对偶问题给出：
      min W·v_y + Σ_r y_r   s.t.  v_y ≥ |ω|（两角不贯入）、y_r ≥ cA·|v_x|（黏聚耗散）、v_x ≥ 1（驱动归一）
    ⇒ 唯一解 (v_x, v_y, ω) = (1, 0, 0)，y_r = cA —— 不经过 `_build_columns`。
  · 对偶间隙/互补/容许三项由 `check_duality` 计算，它与 `limit_load` **共用** `_build_columns`：
    这三项能证明"LP 解与它自己的列一致"，证明不了"列本身造对了"——后者由上面的解析 α 与手算机构负责。
    共用的风险：若 `_build_columns` 把黏聚列造错，两边一起错，对偶三项仍会绿；解析 α 门会红。

**格子（纪律 B）**：分界（μ=0 纯黏聚、倾覆/滑动分界附近的混合例）、一般位置（三维荷载方向 θ=0.3 rad，
与任何棱扇不对齐）、尺度（荷载 ×1、×100、×1e4，几何 ×1e-3）。
"""

from math import cos, pi, sin

import pytest

from eab.limit import (LimitContact, check_duality, limit_load, mechanism_is_admissible,
                       wrench)

LOAD_SCALES = [1.0, 1e2, 1e4]
GRID = [(s, g) for s in LOAD_SCALES for g in (1.0, 1e-3)]


def _assert_duality(r, cts, dead, live, dim, k=8, tol=1e-9):
    o = (0.0,) * dim
    d = check_duality(r, cts, dead, live, dim=dim, origin=o, k=k)
    scale = max(1.0, abs(r.alpha))
    assert d["admissible"], d
    assert d["duality_gap"] < tol * scale, d
    assert d["complementarity"] < tol * scale, d
    assert d["drive"] > 1.0 - 1e-9, d
    return d


# ---------------------------------------------------------------- 二维

def _pure_cohesion(s=1.0, g=1.0, c=3.0, area=1.0, W=10.0):
    """两角各黏聚 c·A，μ = 0，荷载作用在基面上（排除倾覆）⇒ α = 2cA。"""
    cts = [LimitContact((-1.0 * g, 0.0), (0.0, 1.0), 0.0, cohesion=c * s, area=area, label=("L",)),
           LimitContact((1.0 * g, 0.0), (0.0, 1.0), 0.0, cohesion=c * s, area=area, label=("R",))]
    dead = wrench((0.0, -W * s), (0.0, 0.0), (0.0, 0.0), 2)
    live = wrench((1.0, 0.0), (0.0, 0.0), (0.0, 0.0), 2)
    return cts, dead, live


@pytest.mark.parametrize("s,g", GRID)
def test_pure_cohesion_duality_gap_and_complementarity_vanish(s, g):
    cts, dead, live = _pure_cohesion(s, g)
    r = limit_load(cts, dead, live, dim=2, origin=(0.0, 0.0))
    assert r.status == "optimal"
    assert r.alpha == pytest.approx(6.0 * s, rel=1e-12)
    _assert_duality(r, cts, dead, live, 2)


def test_pure_cohesion_mechanism_and_row_duals_match_the_hand_solved_dual():
    """手算对偶：机构 (v_x, v_y, ω) = (1, 0, 0)，两条黏聚行乘子各 = cA = 3。
    同时钉住结果的形状：`mechanism` 恰是 3 维旋量（二维），黏聚行乘子另存在 `row_duals`。"""
    cts, dead, live = _pure_cohesion()
    r = limit_load(cts, dead, live, dim=2, origin=(0.0, 0.0))
    assert len(r.mechanism) == 3
    assert r.mechanism == pytest.approx([1.0, 0.0, 0.0], abs=1e-12)
    assert r.row_duals == pytest.approx([3.0, 3.0], abs=1e-12)
    upper = -sum(m * w for m, w in zip(r.mechanism, dead)) + sum(r.row_duals)   # bᵀy，手写
    assert upper == pytest.approx(r.alpha, abs=1e-12)


@pytest.mark.parametrize("s,g", GRID)
def test_friction_plus_cohesion_sliding_duality(s, g):
    """μ = 0.3、两角各 cA = 3、荷载在基面：α = μW + 2cA = 9（审查 C24 的复现例）。"""
    W = 10.0 * s
    cts = [LimitContact((-1.0 * g, 0.0), (0.0, 1.0), 0.3, cohesion=3.0 * s, area=1.0),
           LimitContact((1.0 * g, 0.0), (0.0, 1.0), 0.3, cohesion=3.0 * s, area=1.0)]
    dead = wrench((0.0, -W), (0.0, 0.0), (0.0, 0.0), 2)
    live = wrench((1.0, 0.0), (0.0, 0.0), (0.0, 0.0), 2)
    r = limit_load(cts, dead, live, dim=2, origin=(0.0, 0.0))
    assert r.status == "optimal"
    assert r.alpha / s == pytest.approx(9.0, abs=1e-9)
    _assert_duality(r, cts, dead, live, 2)


@pytest.mark.parametrize("s,g", GRID)
def test_cohesive_toe_plus_frictional_contacts_topple_duality(s, g):
    """审查 C1 的复现例：三个接触（左角带黏聚），W=10、h=3，荷载在顶部。
    α = min(μW + cA, W·w/(2h)) = min(1 + 3, 10/3) = 10/3（倾覆控制），且对偶三项成立。
    未修时这里报出 0.3333 的假互补违约（λ 的下标与重建的摩擦列错位）。"""
    W, BH, mu = 10.0 * s, 3.0 * g, 0.1
    cts = [LimitContact((-1.0 * g, 0.0), (0.0, 1.0), mu, cohesion=3.0 * s, area=1.0, label=("L",)),
           LimitContact((0.0, 0.0), (0.0, 1.0), mu, label=("M",)),
           LimitContact((1.0 * g, 0.0), (0.0, 1.0), mu, label=("R",))]
    dead = wrench((0.0, -W), (0.0, BH / 2), (0.0, 0.0), 2)
    live = wrench((1.0, 0.0), (0.0, BH), (0.0, 0.0), 2)
    r = limit_load(cts, dead, live, dim=2, origin=(0.0, 0.0))
    assert r.status == "optimal"
    assert r.alpha / s == pytest.approx(10.0 / 3.0, abs=1e-9)
    _assert_duality(r, cts, dead, live, 2)


# ---------------------------------------------------------------- 三维

@pytest.mark.parametrize("s,g", GRID)
@pytest.mark.parametrize("k", [5, 16])
def test_three_d_cohesive_block_duality_in_general_direction(k, s, g):
    """三维扁块四角接触（μ = 0.2、各 cA = 1.5），荷载在基面内沿 θ = 0.3 rad（不与任何棱扇对齐）。

    摩擦锥与黏聚多边形都是同一个正 k 边形扇 ⇒ α ∈ [cos(π/k), 1]·(μW + ΣcA)（径向函数夹逼，
    推导见 test_limit.py::_flat_block_ratio）。对偶三项必须成立。"""
    W, mu, cA = 10.0 * s, 0.2, 1.5 * s
    hx, hy = 1.0 * g, 0.6 * g
    cts = [LimitContact((sx * hx, sy * hy, 0.0), (0.0, 0.0, 1.0), mu, cohesion=cA, area=1.0)
           for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]
    o = (0.0, 0.0, 0.0)
    th = 0.3
    dead = wrench((0.0, 0.0, -W), (0.0, 0.0, 0.5 * g), o, 3)
    live = wrench((cos(th), sin(th), 0.0), o, o, 3)
    r = limit_load(cts, dead, live, dim=3, origin=o, k=k)
    assert r.status == "optimal"
    full = mu * W + 4.0 * cA
    assert cos(pi / k) * full - 1e-9 * full <= r.alpha <= full * (1.0 + 1e-9)
    assert len(r.mechanism) == 6 and len(r.row_duals) == 4
    _assert_duality(r, cts, dead, live, 3, k=k)


# ---------------------------------------------------------------- 牙：自校验真的会拒绝错解

def test_check_duality_rejects_a_mechanism_that_ignores_cohesion_rows():
    """把黏聚行乘子清零（等价于旧代码的 zip 截断）：上限少了 ΣcA，间隙必须报出来。"""
    cts, dead, live = _pure_cohesion()
    r = limit_load(cts, dead, live, dim=2, origin=(0.0, 0.0))
    r.row_duals = [0.0 for _ in r.row_duals]
    d = check_duality(r, cts, dead, live, dim=2, origin=(0.0, 0.0))
    assert d["duality_gap"] > 1.0
    assert not d["admissible"]            # y_r = 0 < cA·|v_x|：黏聚列的对偶可行性被破坏


def test_check_duality_refuses_a_result_built_with_another_k():
    """列数对不上（k 不同）就无法逐列对齐——必须拒绝，而不是静默错位比较。"""
    cts = [LimitContact((sx, sy, 0.0), (0.0, 0.0, 1.0), 0.3, cohesion=1.0, area=1.0)
           for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]
    o = (0.0, 0.0, 0.0)
    dead = wrench((0.0, 0.0, -10.0), (0.0, 0.0, 0.5), o, 3)
    live = wrench((1.0, 0.0, 0.0), o, o, 3)
    r = limit_load(cts, dead, live, dim=3, origin=o, k=8)
    with pytest.raises(ValueError):
        check_duality(r, cts, dead, live, dim=3, origin=o, k=16)


def test_slack_and_drive_complementarity_are_checked():
    """check_duality 文档里的另外两条互补也要有牙：
    · 黏聚行没用满（松弛 s_r > 0）⟹ y_r = 0：高黏聚方块被倾覆控制，黏聚只用掉一小部分；
    · α > 0 ⟹ yᵀW_live = 1：把机构整体放大 2 倍，驱动变成 2，必须报出来。"""
    W, BH = 10.0, 3.0
    cts = [LimitContact((-1.0, 0.0), (0.0, 1.0), 0.0, cohesion=100.0, area=1.0, label=("L",)),
           LimitContact((1.0, 0.0), (0.0, 1.0), 0.0, cohesion=100.0, area=1.0, label=("R",))]
    dead = wrench((0.0, -W), (0.0, BH / 2), (0.0, 0.0), 2)
    live = wrench((1.0, 0.0), (0.0, BH), (0.0, 0.0), 2)
    o = (0.0, 0.0)
    r = limit_load(cts, dead, live, dim=2, origin=o)
    assert r.alpha == pytest.approx(W * 1.0 / BH, abs=1e-9)            # 黏聚剪力在基面，挡不住倾覆
    d = _assert_duality(r, cts, dead, live, 2)
    assert r.row_duals == pytest.approx([0.0, 0.0], abs=1e-12)         # 转动机构在基面上无切向滑移
    r.row_duals = [0.5, 0.5]
    assert check_duality(r, cts, dead, live, dim=2, origin=o)["complementarity"] >= 0.5 - 1e-12
    r.row_duals = [0.0, 0.0]
    r.mechanism = [2.0 * v for v in r.mechanism]
    d2 = check_duality(r, cts, dead, live, dim=2, origin=o)
    assert d2["drive"] == pytest.approx(2.0) and d2["complementarity"] >= 1.0 - 1e-12
    assert d["complementarity"] < 1e-9


def test_argument_shape_guards():
    """文档化的拒绝：非 optimal 结果、机构维数不对、row_duals 行数不对，一律 ValueError。"""
    cts, dead, live = _pure_cohesion()
    o = (0.0, 0.0)
    r = limit_load(cts, dead, live, dim=2, origin=o)
    with pytest.raises(ValueError):
        mechanism_is_admissible(r.mechanism + list(r.row_duals), cts, dim=2, origin=o)
    with pytest.raises(ValueError):
        mechanism_is_admissible(r.mechanism, cts, dim=2, origin=o, row_duals=[1.0])
    bad = limit_load(cts[:1], dead, [0.0, 0.0, 0.0], dim=2, origin=o)   # 驱动为零 ⇒ α 无界
    assert bad.status != "optimal"
    with pytest.raises(ValueError):
        check_duality(bad, cts[:1], dead, [0.0, 0.0, 0.0], dim=2, origin=o)


def test_mechanism_admissibility_accounts_for_cohesion_rows():
    """机构容许性：黏聚不限制运动学（任何剪切都可用足够的耗散 y_r 抵偿），
    但给了 row_duals 时必须满足 yᵀw_coh + y_r ≥ 0。贯入的机构无论如何都不容许。"""
    cts, dead, live = _pure_cohesion()
    r = limit_load(cts, dead, live, dim=2, origin=(0.0, 0.0))
    o = (0.0, 0.0)
    assert mechanism_is_admissible(r.mechanism, cts, dim=2, origin=o)
    assert mechanism_is_admissible(r.mechanism, cts, dim=2, origin=o, row_duals=r.row_duals)
    assert not mechanism_is_admissible(r.mechanism, cts, dim=2, origin=o, row_duals=[0.0, 0.0])
    assert not mechanism_is_admissible([1.0, -0.5, 0.0], cts, dim=2, origin=o)   # 向下贯入
