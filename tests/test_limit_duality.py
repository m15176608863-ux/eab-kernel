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
    # 订正（2026-09-25）：原断言 complementarity ≥ 0.5 绑的是旧归一化（|y_r| / G）。互补违约现以该行自身的
    # 耗散量级 c·A·V̂ 为尺度（V̂ 为机构特征速度，见 limit._speed_scale），注入的 y_r = 0.5 相对 c·A = 100 为
    # 0.5 / (100·V̂) ≈ 5e-3——仍比 tol = 1e-7 大四个数量级以上。牙没变，刻度换了：断言"远超容差且 ok 为假"。
    dbad = check_duality(r, cts, dead, live, dim=2, origin=o)
    assert dbad["complementarity"] > 1e3 * 1e-7 and not dbad["ok"]
    r.row_duals = [0.0, 0.0]
    r.mechanism = [2.0 * v for v in r.mechanism]
    d2 = check_duality(r, cts, dead, live, dim=2, origin=o)
    # 订正（2026-09-27）：驱动违约现按驱动点积自身的舍入尺度 max(1, Σ|y_i W_i|) 相对化（远坐标下平动与转动大量
    # 相消，旧的绝对 |驱动 − 1| 把 2⁻²³ 的舍入判成违约）。放大 2 倍时尺度为 2，读数 |2 − 1| / 2 = 0.5，仍是容差的 5e6 倍。
    assert d2["drive"] == pytest.approx(2.0) and d2["complementarity"] >= 0.5 - 1e-12 and not d2["ok"]
    assert d["complementarity"] < 1e-9


def test_unused_cohesion_row_complementarity_is_checked_on_the_slack_branch():
    """未用满的黏聚行 ⟹ y_r = 0，这条互补必须由 check_duality 的**松弛分支**报出来（复核者 R5：上面那道门注入的
    y_r 经由活动黏聚列的功率被看到，把松弛分支整个删掉它照样绿）。

    构造：两个无摩擦黏聚接触上的方块，活荷载竖直向上、过形心——纯提离，α = W 时**全零接触力**恰好平衡。
    LP 在这个退化最优点上可以合法地选一对互相抵消的黏聚剪力（实测 L 用 +cA、R 用 −cA，两行用满），
    所以这里把原始解换成同样最优的全零解（先核验它 ok），两行松弛都是满的。注入的 y_r 于是只能从松弛分支读出：
    活动列路径没有受力列可看，驱动不变。
    牙：把松弛分支删掉（`if slack > tol and yr[r_i] != 0.0` 恒假），complementarity 读 0，本门红。"""
    W = 10.0
    o = (0.0, 0.0)
    cts = [LimitContact((-1.0, 0.0), (0.0, 1.0), 0.0, cohesion=100.0, area=1.0, label=("L",)),
           LimitContact((1.0, 0.0), (0.0, 1.0), 0.0, cohesion=100.0, area=1.0, label=("R",))]
    dead = wrench((0.0, -W), (0.0, 1.5), o, 2)
    live = wrench((0.0, 1.0), (0.0, 1.5), o, 2)
    r = limit_load(cts, dead, live, dim=2, origin=o)
    assert r.status == "optimal" and r.alpha == pytest.approx(W, rel=1e-12)
    assert r.row_duals == pytest.approx([0.0, 0.0], abs=1e-12)
    r.lambdas = [0.0] * len(r.lambdas)                                  # 同样最优的全零原始解
    d = check_duality(r, cts, dead, live, dim=2, origin=o)
    assert d["ok"] and d["complementarity"] < 1e-9, d
    for row in range(2):
        r.row_duals = [0.5 if i == row else 0.0 for i in range(2)]
        dbad = check_duality(r, cts, dead, live, dim=2, origin=o)
        assert dbad["complementarity"] > 1e3 * 1e-7 and not dbad["ok"], (row, dbad)


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


# ---------------------------------------------------------------- G6 major 15：黏聚列与 row_duals 的有牙门
#
# 旧门的黏聚算例全是等值 cA、关于原点镜像、参考点在原点、只沿 +x 推——三个变异（黏聚列力矩反号、二维黏聚单向、
# row_duals 反序）全套 1209 照绿。下面三组门各针对一个变异，变异注入 `_build_columns` / `limit_load` 内部验证过会红
# （记录见提交说明）。纪律 E：位形不关于接触形心对称、cA 互不相等、参考点取非对称点。

_QUAD = [(-1.0, -0.6, 0.0), (1.2, -0.5, 0.0), (0.9, 0.7, 0.0), (-0.8, 0.6, 0.0)]
_CA = [1.0, 2.0, 1.5, 0.5]


def _asym_cohesive_block(origin, *, mu=0.2, k=16, th=0.3, tangent=None, live_at=(0.3, -0.1, 0.4)):
    cts = [LimitContact(p, (0.0, 0.0, 1.0), mu, cohesion=cA, area=1.0, label=(f"c{i}",), tangent=tangent)
           for i, (p, cA) in enumerate(zip(_QUAD, _CA))]
    dead = wrench((0.0, 0.0, -10.0), (0.1, 0.05, 0.7), origin, 3)
    live = wrench((cos(th), sin(th), 0.0), live_at, origin, 3)
    return cts, dead, live


@pytest.mark.parametrize("k", [8, 16])
def test_cohesive_capacity_is_independent_of_the_moment_reference_point(k):
    """(a) 变异"黏聚列力矩反号"的门：不对称四边形底、四个互不相等的 cA、推力作用在块内偏心高处（有扭转与倾覆分量），
    参考点取 (0,0,0)、(5,−3,2)、(−0.7,0.4,−11)：α 必须相同（物理不变量），且对偶自校验过。"""
    alphas = []
    for o in [(0.0, 0.0, 0.0), (5.0, -3.0, 2.0), (-0.7, 0.4, -11.0)]:
        cts, dead, live = _asym_cohesive_block(o, k=k)
        r = limit_load(cts, dead, live, dim=3, origin=o, k=k)
        assert r.status == "optimal"
        assert check_duality(r, cts, dead, live, dim=3, origin=o, k=k)["ok"]
        alphas.append(r.alpha)
    assert alphas[1] == pytest.approx(alphas[0], rel=1e-9) and alphas[2] == pytest.approx(alphas[0], rel=1e-9)
    assert 0.0 < alphas[0] < 0.2 * 10.0 + sum(_CA)
    # （G6 第二轮 minor：limit_load 总在接触形心求解，上面的 α 相等本身是空断言。有内容的是：返回的机构关于调用方
    # origin，必须按速度旋量规律变换 v_{o2} = v_{o1} − (o2 − o1) × ω；check_duality 的静力一侧用独立的浮点列核对了 λ。）
    mechs = []
    for o in [(0.0, 0.0, 0.0), (5.0, -3.0, 2.0)]:
        cts, dead, live = _asym_cohesive_block(o, k=k)
        mechs.append(limit_load(cts, dead, live, dim=3, origin=o, k=k).mechanism)
    om = mechs[0][3:]
    d = (5.0, -3.0, 2.0)
    v2 = [mechs[0][0] - (d[1] * om[2] - d[2] * om[1]), mechs[0][1] - (d[2] * om[0] - d[0] * om[2]),
          mechs[0][2] - (d[0] * om[1] - d[1] * om[0])]
    assert mechs[1][:3] == pytest.approx(v2, rel=1e-9, abs=1e-9) and mechs[1][3:] == pytest.approx(om, rel=1e-12)


def test_two_d_cohesion_reference_point_invariance_with_unequal_contacts():
    """(a) 的二维版：两接触 cA = 3、1，推力作用在高处（有倾覆），参考点 (0,0) 与 (0.7,−1.3) 给出同一个 α。"""
    alphas = []
    for o in [(0.0, 0.0), (0.7, -1.3)]:
        cts = [LimitContact((-1.0, 0.0), (0.0, 1.0), 0.2, cohesion=3.0, area=1.0),
               LimitContact((1.5, 0.0), (0.0, 1.0), 0.2, cohesion=1.0, area=1.0)]
        dead = wrench((0.0, -10.0), (0.1, 1.0), o, 2)
        live = wrench((1.0, 0.0), (0.0, 1.2), o, 2)
        r = limit_load(cts, dead, live, dim=2, origin=o)
        assert r.status == "optimal"
        assert check_duality(r, cts, dead, live, dim=2, origin=o)["ok"]
        alphas.append(r.alpha)
    assert alphas[1] == pytest.approx(alphas[0], rel=1e-9)


@pytest.mark.parametrize("sign", [1.0, -1.0])
def test_two_d_pure_cohesion_resists_both_directions(sign):
    """(b) 变异"二维黏聚单向"的门：纯黏聚两接触（cA = 3、3），沿 +x 与 −x 推，α 都 = ΣcA = 6
    （旧门只推 +x；把黏聚方向 (+t, −t) 改成 (+t, +t) 时 −x 给出 0）。"""
    cts, dead, _ = _pure_cohesion()
    live = wrench((sign, 0.0), (0.0, 0.0), (0.0, 0.0), 2)
    r = limit_load(cts, dead, live, dim=2, origin=(0.0, 0.0))
    assert r.status == "optimal" and r.alpha == pytest.approx(6.0, rel=1e-12), (sign, r.alpha)
    assert r.row_duals == pytest.approx([3.0, 3.0], rel=1e-12)


@pytest.mark.parametrize("th", [0.0, 0.7, 2.0, 3.3, 4.9])
def test_three_d_pure_cohesion_resists_every_direction(th):
    """(b) 的三维版：纯黏聚（μ = 0）四角 cA 不等，推力沿 θ 且作用在 cA 加权形心（全部黏聚同向发挥时无扭转），
    显式切向基架对准**摩擦阻力方向**（推力的反向）⇒ α = ΣcA 精确；对准推力本身时偶数 k 等价、奇数 k 恰是最坏情形
    cos(π/k)·ΣcA（limit.py 诚实条款；G6 第四轮 regress 镜头：旧文档串写"对准推力 ⇒ 精确"，且只跑 k = 8 永远看不见）；
    默认基架 ⇒ α ∈ [cos(π/k), 1]·ΣcA。"""
    u = (cos(th), sin(th), 0.0)
    nu = (-u[0], -u[1], 0.0)
    q = tuple(sum(cA * p[i] for p, cA in zip(_QUAD, _CA)) / sum(_CA) for i in range(2)) + (0.0,)
    o = (0.0, 0.0, 0.0)
    for tangent, k, want in ((u, 8, "exact"), (nu, 8, "exact"), (nu, 5, "exact"), (nu, 7, "exact"),
                             (u, 5, "worst"), (u, 7, "worst"), (None, 8, "band"), (None, 5, "band")):
        cts, dead, _ = _asym_cohesive_block(o, mu=0.0, k=k, tangent=tangent)
        live = wrench(u, q, o, 3)
        r = limit_load(cts, dead, live, dim=3, origin=o, k=k)
        assert r.status == "optimal", (th, tangent, k)
        if want == "exact":
            assert r.alpha == pytest.approx(sum(_CA), rel=1e-12), (th, k, r.alpha)
        elif want == "worst":
            assert r.alpha == pytest.approx(cos(pi / k) * sum(_CA), rel=1e-12), (th, k, r.alpha)
        else:
            assert cos(pi / k) * sum(_CA) * (1 - 1e-12) <= r.alpha <= sum(_CA) * (1 + 1e-12), (th, k, r.alpha)


def test_unequal_cohesion_row_duals_are_aligned_with_their_contacts():
    """(c) 变异"row_duals 反序"的门：二维纯黏聚 cA = 3（左）、1（右），推 +x。手算对偶（见文件头）唯一：
    机构 (1, 0, 0)、y_r = (cA_L, cA_R) = (3, 1)。反序后 check_duality 必须判不容许（黏聚列功率 −2）。"""
    cts = [LimitContact((-1.0, 0.0), (0.0, 1.0), 0.0, cohesion=3.0, area=1.0),
           LimitContact((1.0, 0.0), (0.0, 1.0), 0.0, cohesion=1.0, area=1.0)]
    o = (0.0, 0.0)
    dead = wrench((0.0, -10.0), (0.0, 0.0), o, 2)
    live = wrench((1.0, 0.0), (0.0, 0.0), o, 2)
    r = limit_load(cts, dead, live, dim=2, origin=o)
    assert r.alpha == pytest.approx(4.0, rel=1e-12)
    assert r.mechanism == pytest.approx([1.0, 0.0, 0.0], abs=1e-12)
    assert r.row_duals == pytest.approx([3.0, 1.0], rel=1e-12)
    assert check_duality(r, cts, dead, live, dim=2, origin=o)["ok"]
    r.row_duals = r.row_duals[::-1]
    d = check_duality(r, cts, dead, live, dim=2, origin=o)
    assert not d["admissible"] and d["worst_power"] == pytest.approx(-2.0, rel=1e-12)


def test_three_d_row_duals_equal_each_contacts_cohesive_dissipation():
    """(c) 的三维版：纯黏聚四角 cA = (1, 2, 1.5, 0.5)，推力过 cA 加权形心、切向基架对准推力。
    沿推力的单位平动是一个最优机构，第 i 行黏聚耗散 = cA_i·|v_t| = cA_i——注入它，自校验必须通过。
    **订正（2026-09-27）**：原说明写"唯一最优机构"，不成立。黏聚圆做了 k 边形线性化，对偶面上有一族最优机构
    （LP 层改为精确之后实测：带转动的机构 row_duals = (0.969, 1.561, 1.801, 0.669)，同样通过自校验）；
    旧门能过只因浮点层恰好选中了平动。对整个对偶面都成立的是：α = Σ cA、行对偶之和 = α（无恒载做功）、自校验通过。"""
    th = 0.3
    u = (cos(th), sin(th), 0.0)
    q = tuple(sum(cA * p[i] for p, cA in zip(_QUAD, _CA)) / sum(_CA) for i in range(2)) + (0.0,)
    o = (5.0, -3.0, 2.0)
    cts, dead, _ = _asym_cohesive_block(o, mu=0.0, k=8, tangent=u)
    live = wrench(u, q, o, 3)
    r = limit_load(cts, dead, live, dim=3, origin=o, k=8)
    assert r.alpha == pytest.approx(sum(_CA), rel=1e-12)
    assert sum(r.row_duals) == pytest.approx(r.alpha, rel=1e-12) and min(r.row_duals) >= 0.0
    assert check_duality(r, cts, dead, live, dim=3, origin=o, k=8)["ok"]
    r.mechanism = list(u) + [0.0, 0.0, 0.0]                  # 关于 origin 的平动旋量：v = u、ω = 0
    r.row_duals = list(_CA)
    assert check_duality(r, cts, dead, live, dim=3, origin=o, k=8)["ok"]
    r.row_duals = list(_CA[::-1])                              # 牙：行对偶错配，自校验必须不通过
    assert not check_duality(r, cts, dead, live, dim=3, origin=o, k=8)["ok"]


def test_check_duality_rejects_a_zero_mechanism():
    """G6 critical 19 的自校验盲区：旧 `check_duality` 只在 α > tol 时看驱动，α = 0 + 零机构被判
    "容许、间隙 0、互补 0"。驱动 yᵀW_live ≥ 1 是 α 列的对偶约束：零机构（驱动 0）必须判不容许。"""
    cts, dead, live = _pure_cohesion()
    r = limit_load(cts, dead, live, dim=2, origin=(0.0, 0.0))
    r.alpha, r.mechanism, r.row_duals = 0.0, [0.0, 0.0, 0.0], [0.0, 0.0]
    r.lambdas = [0.0 for _ in r.lambdas]
    d = check_duality(r, cts, dead, live, dim=2, origin=(0.0, 0.0))
    assert d["drive"] == 0.0 and not d["admissible"] and not d["ok"]


# ---------------------------------------------------------------- G6 第三轮 minor：静力侧四项辅助子检查没有牙

def test_static_side_sub_checks_reject_hand_edited_results():
    """check_duality 的黏聚行 Σλ ≤ 1、λ ≥ 0、α ≥ 0 三项对 limit_load 自产的 optimal 是冗余的（精确 LP 已保证），
    只在调用方手工构造 LimitResult 时才有分辨力——所以此前把任一项改成恒真全套照绿。这里取两条黏聚缝上的倾覆方块，
    对同一黏聚行的两根反向列各加 0.75（合力不变、Σλ = 1.5）、各减 0.2（合力不变、一根变负）、α 取负（荷载反向），
    三种手改都必须被 static_ok / ok 拒绝；未改的结果必须通过。"""
    from eab.limit import LimitContact, check_duality, limit_load, wrench
    W, BH = 10.0, 3.0
    cts = [LimitContact((-1.0, 0.0), (0.0, 1.0), 0.0, cohesion=100.0, area=1.0, label=("L",)),
           LimitContact((1.0, 0.0), (0.0, 1.0), 0.0, cohesion=100.0, area=1.0, label=("R",))]
    dead = wrench((0.0, -W), (0.0, BH / 2), (0.0, 0.0), 2)
    live = wrench((1.0, 0.0), (0.0, BH), (0.0, 0.0), 2)
    kw = dict(dim=2, origin=(0.0, 0.0))
    r = limit_load(cts, dead, live, **kw)
    assert r.status == "optimal" and check_duality(r, cts, dead, live, **kw)["ok"]
    # 列序：每个接触 [摩擦棱 ±, 黏聚列 ±]——lam[2]、lam[3] 是左缝的两根反向黏聚列
    r = limit_load(cts, dead, live, **kw)
    lam = list(r.lambdas); lam[2] += 0.75; lam[3] += 0.75; r.lambdas = lam
    chk = check_duality(r, cts, dead, live, **kw)
    assert not chk["static_ok"] and not chk["ok"], chk
    r = limit_load(cts, dead, live, **kw)
    lam = list(r.lambdas); lam[2] -= 0.2; lam[3] -= 0.2; r.lambdas = lam
    assert min(r.lambdas) < 0.0
    chk = check_duality(r, cts, dead, live, **kw)
    assert not chk["static_ok"] and not chk["ok"], chk
    r = limit_load(cts, dead, live, **kw)
    r.alpha = -r.alpha
    chk = check_duality(r, cts, dead, [-v for v in live], **kw)
    assert not chk["static_ok"], chk
