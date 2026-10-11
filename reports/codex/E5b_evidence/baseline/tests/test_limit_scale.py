"""极限分析的"假不可行"回归门与尺度格子（审查 C0 / C21；纪律 B）。

缺陷：`limit_load` 把 tol 乘 1e-3 传给 LP，LP 又用绝对阈值判一阶段可行性；N = 100 时
人工变量和的舍入残差 ~2e-12 > 1e-12，于是可行问题返回 status='infeasible'、alpha=nan。
旧的 Patton 参数化恰好避开了失败格子。

**oracle（纪律 A）只用解析闭式**，与被测代码零共用：
  · 锯齿节理 Patton 律：承载比 = tan(ψ + φ)，tan ψ = 2·amp（齿面倾角），tan φ = μ；
  · 内接 k 棱锥 ⊇ 半顶角 atan(μ·cos(π/k)) 的精确圆锥（正 k 边形内切圆半径 = cos(π/k)·外接圆半径），
    所以承载比 ≥ tan(ψ + atan(μ·cos(π/k)))；本文件格子满足 tanψ·μ·(1+cos(π/k)) + cos(π/k)·μ² < 1，
    在此条件下该下界又 ≥ cos(π/k)·tan(ψ + φ)，即"相对短缺 ≤ 1 − cos(π/k)"（两条都直接断言）；
  · 方块滑动/倾覆：α* = min(μW, W·w/(2h))。
几何来自 tools/osteomorphic 与 enumerate_covers3——它们是被测链路的上游，不是 oracle。

**格子（纪律 B）**：分界点 μ = w/(2h)、μ = 0；一般位置 amp×μ 全格与非 4 倍数的 k；
尺度 荷载 ×1、×100、×1e4，几何 ×1e-3（盖枚举的 window/tol 随几何同比缩放）。
"""

import sys
from functools import lru_cache
from math import atan, cos, pi, sin, tan
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from osteomorphic import interlocking_pair  # noqa: E402

from eab.kernel3d.covers3 import enumerate_covers3  # noqa: E402
from eab.kernel3d.geom3 import Polyhedron  # noqa: E402
from eab.limit import (LimitContact, check_duality, contacts_from_covers, limit_load,  # noqa: E402
                       mechanism_is_admissible, wrench)

LOAD_SCALES = [1.0, 1e2, 1e4]
GEOM_SCALES = [1.0, 1e-3]


def _scaled(P, g):
    if g == 1.0:
        return P
    return Polyhedron([tuple(g * x for x in v) for v in P.verts], [tuple(f) for f in P.faces])


@lru_cache(maxsize=None)
def _interlock_covers(amp, g=1.0):
    A, L = interlocking_pair(nx=4, ny=2, amp=amp)
    A, L = _scaled(A, g), _scaled(L, g)
    cv = [c for c in enumerate_covers3(A, L, window=1e-6 * g, tol=1e-9 * g)
          if c.in_extent and c.normal]
    return A.centroid(), tuple(cv)


def _capacity_ratio(amp, mu, k, *, N=100.0, g=1.0):
    c0, cv = _interlock_covers(amp, g)
    cts = contacts_from_covers(list(cv), mu=mu)
    dead = wrench((0.0, 0.0, -N), c0, (0.0, 0.0, 0.0), 3)
    live = wrench((1.0, 0.0, 0.0), c0, (0.0, 0.0, 0.0), 3)
    r = limit_load(cts, dead, live, dim=3, origin=(0.0, 0.0, 0.0), k=k)
    return r, r.alpha / N


def _patton(amp, mu):
    return tan(atan(2.0 * amp) + atan(mu))


def _inscribed_lower(amp, mu, k):
    return tan(atan(2.0 * amp) + atan(mu * cos(pi / k)))


# 审查 C21 在未修代码上复现出的 9 个假不可行格子（amp, μ, k），含默认 k=8 的 (0.2, 0.1, 8)。
AUDITED_CELLS = [(0.1, 0.1, 9), (0.1, 0.2, 9), (0.2, 0.1, 8), (0.2, 0.1, 16), (0.25, 0.1, 11),
                 (0.25, 0.2, 7), (0.3, 0.1, 7), (0.3, 0.1, 16), (0.3, 0.2, 6)]


@pytest.mark.parametrize("amp,mu,k", AUDITED_CELLS)
def test_interlock_is_never_falsely_infeasible_on_the_audited_cells(amp, mu, k):
    """审查实测的假不可行格子：必须 optimal，且落在内接锥的解析夹逼里。"""
    r, ratio = _capacity_ratio(amp, mu, k)
    assert r.status == "optimal", (amp, mu, k, r.status)
    assert _inscribed_lower(amp, mu, k) - 1e-9 <= ratio <= _patton(amp, mu) + 1e-9


@pytest.mark.parametrize("amp,mu,k", [(0.2, 0.1, 8), (0.3, 0.1, 16)])
def test_plan_regression_cells_equal_patton(amp, mu, k):
    """计划 M0.a 的回归门：这两格 optimal 且等于 Patton（k 为 4 的倍数时本几何精确，
    原因见 test_limit.py 的锥线性化门）。"""
    r, ratio = _capacity_ratio(amp, mu, k)
    assert r.status == "optimal"
    assert ratio == pytest.approx(_patton(amp, mu), abs=1e-9)


AMPS = [0.10, 0.15, 0.20, 0.25, 0.30]
MUS = [0.0, 0.1, 0.2, 0.3, 0.35]


@pytest.mark.parametrize("k", [8, 16])
@pytest.mark.parametrize("mu", MUS)
@pytest.mark.parametrize("amp", AMPS)
def test_patton_sweep_is_optimal_and_inside_the_inscribed_cone_bracket(amp, mu, k):
    """amp × μ × k 全格：全部 optimal；承载比 ∈ [tan(ψ+φ)·cos(π/k), tan(ψ+φ)]，
    且不低于内切圆锥解 tan(ψ + atan(μ·cos(π/k)))。"""
    c = cos(pi / k)
    assert 2.0 * amp * mu * (1.0 + c) + c * mu * mu < 1.0      # 两个下界之间的蕴含条件
    r, ratio = _capacity_ratio(amp, mu, k)
    assert r.status == "optimal", (amp, mu, k, r.status)
    exact = _patton(amp, mu)
    assert exact * (1.0 - (1.0 - c)) - 1e-9 <= ratio <= exact + 1e-9, (amp, mu, k, ratio)
    assert ratio >= _inscribed_lower(amp, mu, k) - 1e-9, (amp, mu, k, ratio)


@pytest.mark.parametrize("g", GEOM_SCALES)
@pytest.mark.parametrize("s", LOAD_SCALES)
@pytest.mark.parametrize("amp,mu", [(0.2, 0.1), (0.25, 0.2), (0.3, 0.0)])
def test_interlock_capacity_ratio_is_invariant_to_load_and_geometry_units(amp, mu, s, g):
    """荷载 ×s、几何 ×g：承载比 α/N 与单位无关，必须仍是 Patton 值（k=8 本几何精确）。"""
    r, ratio = _capacity_ratio(amp, mu, 8, N=100.0 * s, g=g)
    assert r.status == "optimal", (amp, mu, s, g, r.status)
    assert ratio == pytest.approx(_patton(amp, mu), abs=1e-9), (amp, mu, s, g, ratio)


# ---------------------------------------------------------------- 二维方块的尺度格子

W0, BW0, BH0 = 10.0, 2.0, 3.0            # 分界 μ = BW/(2·BH) = 1/3


def _block(mu, s, g):
    W, BW, BH = W0 * s, BW0 * g, BH0 * g
    cts = [LimitContact((-BW / 2, 0.0), (0.0, 1.0), mu, label=("L",)),
           LimitContact((BW / 2, 0.0), (0.0, 1.0), mu, label=("R",))]
    dead = wrench((0.0, -W), (0.0, BH / 2), (0.0, 0.0), 2)
    live = wrench((1.0, 0.0), (0.0, BH), (0.0, 0.0), 2)
    return cts, dead, live, W


@pytest.mark.parametrize("g", GEOM_SCALES)
@pytest.mark.parametrize("s", LOAD_SCALES)
@pytest.mark.parametrize("mu", [0.2, 1.0 / 3.0, 0.8])
def test_slide_topple_closed_form_holds_across_units(mu, s, g):
    """α*/W = min(μ, w/(2h)) 与单位无关；分界 μ = 1/3 在格子里。
    破坏模式（活动集）也不得随单位变：滑动两角受力，倾覆只剩右趾（分界点上两者并存，不断言）。"""
    cts, dead, live, W = _block(mu, s, g)
    r = limit_load(cts, dead, live, dim=2, origin=(0.0, 0.0))
    assert r.status == "optimal", (mu, s, g, r.status)
    assert r.alpha / W == pytest.approx(min(mu, BW0 / (2.0 * BH0)), abs=1e-9)
    if mu < 1.0 / 3.0:
        assert r.active == [("L",), ("R",)], (mu, s, g, r.active)
    elif mu > 1.0 / 3.0:
        assert r.active == [("R",)], (mu, s, g, r.active)


@pytest.mark.parametrize("lp_tol", [None, 1e-10, 1e-12])
def test_old_tight_lp_tolerance_no_longer_breaks_feasibility(lp_tol):
    """`limit_load(lp_tol=…)` 直通 LP；即便显式传回旧代码的 1e-12，(0.2, 0.1, k=8) 也必须 optimal 且等于
    Patton——LP 的可行性阈值现在相对于均衡后的量级，不再是绝对的 1e-12。"""
    c0, cv = _interlock_covers(0.2)
    cts = contacts_from_covers(list(cv), mu=0.1)
    dead = wrench((0.0, 0.0, -100.0), c0, (0.0, 0.0, 0.0), 3)
    live = wrench((1.0, 0.0, 0.0), c0, (0.0, 0.0, 0.0), 3)
    r = limit_load(cts, dead, live, dim=3, origin=(0.0, 0.0, 0.0), k=8, lp_tol=lp_tol)
    assert r.status == "optimal", (lp_tol, r.status)
    assert r.alpha / 100.0 == pytest.approx(_patton(0.2, 0.1), abs=1e-9)


# ---------------------------------------------------------------- G6（2026-09-24）：工程坐标与 SI 单位

@pytest.mark.parametrize("W", [1e8, 2.6e8, 1e9, 1e11])
def test_si_rock_block_100_m_gives_the_closed_form(W):
    """G6 critical 19：二维岩块边长 100 m、SI 单位（W ~ 2.6e8 N/m），活荷载 = W 水平作用在块心高度：
    滑动 α = μ = 0.6（倾覆 α = 1 更大）。旧实现报 optimal、α = 0（活荷载旋量 > 2^33，α 列进不了基）。"""
    cts = [LimitContact((0.0, 0.0), (0.0, 1.0), 0.6, label=("L",)),
           LimitContact((100.0, 0.0), (0.0, 1.0), 0.6, label=("R",))]
    o = (0.0, 0.0)
    dead = wrench((0.0, -W), (50.0, 50.0), o, 2)
    live = wrench((W, 0.0), (50.0, 50.0), o, 2)
    r = limit_load(cts, dead, live, dim=2)
    assert r.status == "optimal"
    assert r.alpha == pytest.approx(0.6, rel=1e-12), (W, r.alpha)
    d = check_duality(r, cts, dead, live, dim=2)
    assert d["ok"], d


def _cb2_at(T, mu, W=26.5e3 * 4.0):
    """cb2 位形（上块 [−1,1]²×[0,1] 坐落下块顶面）整体平移到 T，四个角点接触手工给出（不经盖枚举，
    与 m2-geom 解耦）；恒载 W 作用在体心、活荷载 W 水平作用在顶面中心；调用方默认原点。α = min(μ, 1)。"""
    cts = [LimitContact((T[0] + sx, T[1] + sy, T[2]), (0.0, 0.0, 1.0), mu) for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]
    o = (0.0, 0.0, 0.0)
    dead = wrench((0.0, 0.0, -W), (T[0], T[1], T[2] + 0.5), o, 3)
    live = wrench((W, 0.0, 0.0), (T[0], T[1], T[2] + 1.0), o, 3)
    return cts, dead, live


UTM = (500000.0, 4400000.0, 100.0)


@pytest.mark.parametrize("mu", [0.3, 1.5])
@pytest.mark.parametrize("T", [(0.0, 0.0, 0.0), (1e3, 2e3, 50.0), UTM])
def test_cb2_at_utm_coordinates_with_the_default_origin(T, mu):
    """G6 critical 19：cb2 挪到 UTM 坐标 (5e5, 4.4e6, 100)、默认原点，旧实现两种 μ 都报 α = 0。"""
    cts, dead, live = _cb2_at(T, mu)
    r = limit_load(cts, dead, live, dim=3, k=8)
    assert r.status == "optimal"
    assert r.alpha == pytest.approx(min(mu, 1.0), rel=1e-9), (T, mu, r.alpha)
    assert check_duality(r, cts, dead, live, dim=3, k=8)["ok"]


@pytest.mark.parametrize("mu", [0.3, 1.5])
def test_cb2_at_utm_end_to_end_through_the_covers(mu):
    """同上，但接触由盖枚举在 UTM 坐标上产生（夹具几何 → 盖 → 接触 → LP 整条链）。"""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import test_end_to_end_cb2 as E
    from g2_bdda3d import load_case

    _, _, blocks, _ = load_case(E.CASES[0])

    def mv(P):
        return Polyhedron([tuple(v[i] + UTM[i] for i in range(3)) for v in P.verts], list(P.faces))

    covs = [c for c in enumerate_covers3(mv(blocks[2]), mv(blocks[1]), window=1e-6, tol=1e-9) if c.in_extent]
    assert len(covs) == 4
    cts = contacts_from_covers(covs, mu=mu)
    W = 26.5e3 * 4.0
    dead = wrench((0.0, 0.0, -W), (UTM[0], UTM[1], UTM[2] + 0.5), (0.0, 0.0, 0.0), 3)
    live = wrench((W, 0.0, 0.0), (UTM[0], UTM[1], UTM[2] + 1.0), (0.0, 0.0, 0.0), 3)
    r = limit_load(cts, dead, live, dim=3, k=8)
    assert r.status == "optimal" and r.alpha == pytest.approx(min(mu, 1.0), rel=1e-9), (mu, r.alpha)


@pytest.mark.parametrize("gs,ls", [(1e3, 1e7), (1e6, 1e10), (1e-6, 1e-8), (1e-3, 1e4)])
def test_end_to_end_grid_extends_to_mm_geometry_and_large_loads(gs, ls):
    """G6 critical 19：端到端 cb2 在 mm 几何（×1e3）+ 荷载 ×1e7 时旧实现报 α = 0（期望 3.0）。"""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import test_end_to_end_cb2 as E

    for mu in (0.3, 1.5):
        r, *_ = E._capacity(E.CASES[0], mu, (1.0, 0.0), geom_scale=gs, load_scale=ls)
        assert r.status == "optimal"
        assert r.alpha == pytest.approx(min(mu, 1.0) * E.W, rel=1e-9), (gs, ls, mu, r.alpha)


@pytest.mark.parametrize("cA", [1e10, 2e10, 1e12, 1e-10])
def test_single_contact_pure_cohesion_is_never_unbounded(cA):
    """G6 critical 0（二维）：单接触纯黏聚 α = cA。旧实现 cA ≥ 2e10 时黏聚上限行在比值检验里掉出，
    报 unbounded、α = ∞（承载力无穷——不安全一侧）。"""
    o = (0.0, 0.0)
    cts = [LimitContact((0.0, 0.0), (0.0, 1.0), 0.0, cohesion=cA, area=1.0)]
    r = limit_load(cts, wrench((0.0, -1.0), (0.0, 1.0), o, 2), wrench((1.0, 0.0), o, o, 2), dim=2, origin=o)
    assert r.status == "optimal", (cA, r.status, r.alpha)
    assert r.alpha == pytest.approx(cA, rel=1e-12)
    assert r.row_duals == pytest.approx([cA], rel=1e-12)


def _site_block(off, s=2.5e7, g=20.0, cA=1e7, mu=0.2, k=8):
    """G6 critical 0 的三维复现：40 × 24 m 的岩块（W = 10·s），四角各 cA 黏聚，放在工程坐标 off 处，默认原点。"""
    W = 10.0 * s
    hx, hy = 1.0 * g, 0.6 * g
    cts = [LimitContact((off[0] + sx * hx, off[1] + sy * hy, off[2]), (0.0, 0.0, 1.0), mu, cohesion=cA, area=1.0)
           for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]
    o = (0.0, 0.0, 0.0)
    dead = wrench((0.0, 0.0, -W), (off[0], off[1], off[2] + 0.5 * g), o, 3)
    live = wrench((cos(0.3), sin(0.3), 0.0), (off[0], off[1], off[2]), o, 3)
    return cts, dead, live, mu * W + 4.0 * cA


@pytest.mark.parametrize("off", [(0.0, 0.0, 0.0), (300.0, 0.0, 0.0), (1000.0, 0.0, 0.0), (1e3, 2e3, 300.0),
                                 (5e5, 4.2e6, 300.0)])
def test_site_block_with_cohesion_is_bounded_and_correct(off):
    """G6 critical 0（三维）：同一块体放在 (1000, 2000, 300) m、默认原点，旧实现报 unbounded、α = ∞
    （真值 ≈ 2.574e8）；x 向 1000 m 即触发。现在任何坐标下都必须 optimal、落在径向夹逼里、对偶自校验过。"""
    cts, dead, live, full = _site_block(off)
    r = limit_load(cts, dead, live, dim=3, k=8)
    assert r.status == "optimal", (off, r.status, r.alpha)
    assert cos(pi / 8) * full * (1 - 1e-9) <= r.alpha <= full * (1 + 1e-9), (off, r.alpha, full)
    ref = limit_load(*_site_block((0.0, 0.0, 0.0))[:3], dim=3, k=8)
    assert r.alpha == pytest.approx(ref.alpha, rel=1e-9)
    assert check_duality(r, cts, dead, live, dim=3, k=8)["ok"]


def test_large_cohesive_block_row_duals_carry_the_whole_upper_bound():
    """G6 major 1 (a)：50 × 30 × 25 m 岩块、c = 1 MPa、四角 375 m² 面片、μ = 0.3，推力 1 rad。
    旧实现 `_duals` 的绝对主元截断把两条黏聚行乘子置 0：row_duals = [3.52e8, 0, 0, 3.52e8]，上限少 41.8%。
    四角对称、推力过形心 ⇒ 四条黏聚行的耗散相等；上限 = α 到 1e-9。"""
    hx, hy = 25.0, 15.0
    W, mu, c, A = 26000.0 * 50 * 30 * 25, 0.3, 1e6, 375.0
    o = (0.0, 0.0, 0.0)
    cts = [LimitContact((sx * hx, sy * hy, 0.0), (0.0, 0.0, 1.0), mu, cohesion=c, area=A)
           for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]
    dead = wrench((0.0, 0.0, -W), (0.0, 0.0, 12.5), o, 3)
    live = wrench((cos(1.0), sin(1.0), 0.0), o, o, 3)
    r = limit_load(cts, dead, live, dim=3, origin=o, k=8)
    full = mu * W + 4.0 * c * A
    assert r.status == "optimal"
    assert cos(pi / 8) * full * (1 - 1e-9) <= r.alpha <= full * (1 + 1e-9)
    assert min(r.row_duals) == pytest.approx(max(r.row_duals), rel=1e-9), r.row_duals
    assert min(r.row_duals) > 1e8
    d = check_duality(r, cts, dead, live, dim=3, origin=o, k=8)
    assert d["ok"] and d["duality_gap_rel"] < 1e-9, d
    assert mechanism_is_admissible(r.mechanism, cts, dim=3, origin=o, k=8, row_duals=r.row_duals)


@pytest.mark.parametrize("origin", [None, (50.0, 80.0, 20.0), (5.0, -3.0, 2.0)])
def test_small_block_far_from_the_origin_returns_a_dual_feasible_mechanism(origin):
    """G6 major 1 (b)：1 × 0.6 × 0.5 m 块、底心 P = (50, 80, 20)、c = 1e5、μ = 0.6、k = 8、推力 1 rad。
    旧实现 origin = 0 时 α 对、但 phase 2 停在对偶不可行基（机构在一条接触列上功率 −0.33，贯入）。
    现在任何参考点：α 相同（G6 两种参考点下都是 60716.914250836）、机构容许、间隙 < 1e-9。"""
    P = (50.0, 80.0, 20.0)
    L, c, mu = 1.0, 1e5, 0.6
    hx, hy, hz = L / 2, 0.3 * L, 0.5 * L
    W = 26000.0 * (2 * hx) * (2 * hy) * hz
    A = (2 * hx) * (2 * hy) / 4
    cts = [LimitContact((P[0] + sx * hx, P[1] + sy * hy, P[2]), (0.0, 0.0, 1.0), mu, cohesion=c, area=A)
           for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]
    o = origin if origin is not None else (0.0, 0.0, 0.0)
    dead = wrench((0.0, 0.0, -W), (P[0], P[1], P[2] + 0.5 * hz), o, 3)
    live = wrench((cos(1.0), sin(1.0), 0.0), P, o, 3)
    r = limit_load(cts, dead, live, dim=3, origin=origin, k=8)
    assert r.status == "optimal"
    assert r.alpha == pytest.approx(60716.914250836, rel=1e-9)
    d = check_duality(r, cts, dead, live, dim=3, origin=origin, k=8)
    assert d["ok"] and d["worst_power_rel"] > -1e-9 and d["duality_gap_rel"] < 1e-9, d
    assert mechanism_is_admissible(r.mechanism, cts, dim=3, origin=origin, k=8, row_duals=r.row_duals)


def test_admissibility_is_judged_relative_to_the_power_scale():
    """G6 minor 3：5 × 3 × 2.5 m 块放在 (2000, 3000, 500) m、c = 1e5，旧 `check_duality` 用绝对 1e-7
    判容许，最差功率 −1.0e-7（相对 y_r ~ 3.5e5 是 3e-13 的舍入）⇒ 误判不容许。现在两处判据都是相对的。"""
    off = (2000.0, 3000.0, 500.0)
    W = 26000.0 * 5 * 3 * 2.5
    cts = [LimitContact((off[0] + sx * 2.5, off[1] + sy * 1.5, off[2]), (0.0, 0.0, 1.0), 0.6, cohesion=1e5,
                        area=3.75) for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]
    o = (0.0, 0.0, 0.0)
    dead = wrench((0.0, 0.0, -W), (off[0], off[1], off[2] + 1.25), o, 3)
    live = wrench((cos(0.3), sin(0.3), 0.0), off, o, 3)
    r = limit_load(cts, dead, live, dim=3, origin=o, k=8)
    assert r.status == "optimal"
    d = check_duality(r, cts, dead, live, dim=3, origin=o, k=8)
    assert d["admissible"] and d["ok"], d
    assert mechanism_is_admissible(r.mechanism, cts, dim=3, origin=o, k=8, row_duals=r.row_duals)
    # 牙：真正贯入的机构（在块底面处叠加一个向下的平动）仍须判不容许
    bad = list(r.mechanism)
    bad[2] -= 1e-3 * max(abs(v) for v in r.mechanism[:3])
    assert not mechanism_is_admissible(bad, cts, dim=3, origin=o, k=8, row_duals=r.row_duals)


def test_self_check_rejects_a_corrupted_mechanism(monkeypatch):
    """limit_load 的"自带上下限自校验"是代码行为：返回前在调用方坐标系里跑 check_duality，不过即抛错。
    牙：把"机构从接触形心变回调用方原点"的旋量变换写错一个号（注入到 limit_load 内部），参考点在远处时必须抛。"""
    import eab.limit as lim

    cts, dead, live = _cb2_at(UTM, 1.5)
    assert limit_load(cts, dead, live, dim=3, k=8).alpha == pytest.approx(1.0, rel=1e-9)

    def wrong(y, d, dim):
        om = y[3:]
        return [y[0] - (d[1] * om[2] - d[2] * om[1]), y[1] - (d[2] * om[0] - d[0] * om[2]),
                y[2] - (d[0] * om[1] - d[1] * om[0]), om[0], om[1], om[2]]

    monkeypatch.setattr(lim, "_twist_back", wrong)
    with pytest.raises(RuntimeError, match="self-check"):
        limit_load(cts, dead, live, dim=3, k=8)


def test_large_block_at_site_coordinates_is_admissible_under_relative_judgement():
    """G6 minor 3 的放大版：50 × 30 × 25 m、c = 1 MPa 的岩块放在 UTM 坐标、默认原点，机构功率量级
    ~ y_r·力臂 ~ 3.5e8 × 4.4e6，舍入 ~ 1e-2 远超绝对 1e-7——绝对判据必误判不容许，相对判据必须判容许。"""
    hx, hy = 25.0, 15.0
    W, mu, c, A = 26000.0 * 50 * 30 * 25, 0.3, 1e6, 375.0
    T = UTM
    o = (0.0, 0.0, 0.0)
    cts = [LimitContact((T[0] + sx * hx, T[1] + sy * hy, T[2]), (0.0, 0.0, 1.0), mu, cohesion=c, area=A)
           for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]
    dead = wrench((0.0, 0.0, -W), (T[0], T[1], T[2] + 12.5), o, 3)
    live = wrench((cos(1.0), sin(1.0), 0.0), T, o, 3)
    r = limit_load(cts, dead, live, dim=3, k=8)
    full = mu * W + 4.0 * c * A
    assert r.status == "optimal" and cos(pi / 8) * full * (1 - 1e-9) <= r.alpha <= full * (1 + 1e-9)
    d = check_duality(r, cts, dead, live, dim=3, k=8)
    assert d["admissible"] and d["ok"], d
    assert mechanism_is_admissible(r.mechanism, cts, dim=3, k=8, row_duals=r.row_duals)
    assert mechanism_is_admissible(r.mechanism, cts, dim=3, k=8)


@pytest.mark.parametrize("W", [1e-12, 1.0, 1e12])
@pytest.mark.parametrize("mu,active", [(0.2, [("L",), ("R",)]), (0.8, [("R",)])])
def test_active_set_and_contact_forces_do_not_depend_on_the_force_unit(W, mu, active):
    """活动判据相对于最大列力：荷载单位从 1e-12 到 1e12，二维方块滑动两角受力、倾覆只剩右趾，合力按 W 缩放。
    绝对判据（力 > 1e-9）在 W = 1e-12 时把真实接触力全部判成不活动（active = []）。"""
    cts = [LimitContact((-1.0, 0.0), (0.0, 1.0), mu, label=("L",)),
           LimitContact((1.0, 0.0), (0.0, 1.0), mu, label=("R",))]
    o = (0.0, 0.0)
    r = limit_load(cts, wrench((0.0, -10.0 * W), (0.0, 1.5), o, 2), wrench((W, 0.0), (0.0, 3.0), o, 2), dim=2)
    assert r.status == "optimal" and r.alpha == pytest.approx(min(mu * 10.0, 10.0 / 3.0), rel=1e-12)
    assert r.active == active, (W, mu, r.active)
    total = [sum(f[i] for f in r.contact_forces) for i in range(2)]
    assert total == pytest.approx([-r.alpha * W, 10.0 * W], rel=1e-12)


@pytest.mark.parametrize("f", [1e-12, 1.0, 1e12])
def test_admissibility_judgement_does_not_depend_on_units(f):
    """G6 minor 3 的单位格子：二维不对称块（右趾法向微倾）倾覆，放在 x = 1e8 mm（100 km）处、力的单位 ×f、默认原点。
    f = 1e-12 时机构 ~ 1/f，关于远原点的旋量分量 ~ 3e16，列功率的舍入 ~ 4 ≫ 绝对 1e-7——
    绝对判据把正确的机构判成不容许，相对判据（除以 Σ|y_i w_ij|）不受单位影响。α 与原点处的同一块体一致。"""
    def block(T, s, f):
        cts = [LimitContact((T - s, 0.0), (0.0, 1.0), 0.8, label=("L",)),
               LimitContact((T + 1.3 * s, 0.0), (0.02, 1.0), 0.8, label=("R",))]
        o = (0.0, 0.0)
        return cts, wrench((0.0, -10.0 * f), (T + 0.1 * s, 1.5 * s), o, 2), wrench((f, 0.0), (T, 3.0 * s), o, 2)

    ref = limit_load(*block(0.0, 1.0, 1.0), dim=2)
    cts, dead, live = block(1e8, 1e3, f)
    r = limit_load(cts, dead, live, dim=2)
    assert r.status == "optimal" and r.alpha == pytest.approx(ref.alpha, rel=1e-9)
    d = check_duality(r, cts, dead, live, dim=2)
    assert d["admissible"] and d["ok"], d
    assert mechanism_is_admissible(r.mechanism, cts, dim=2)
    assert r.active == ref.active


def _g6_rock_block(off, L=20.0, c=1e6, mu=0.6, th=0.3):
    """G6 critical 0 审查者的原复现：底 L × 0.6L、高 0.5L 的岩块（容重 26 kN/m³），四角各 0.15L² 的黏聚面片，
    SI 单位，块体放在工程坐标 off 处、调用方默认原点。L = 20 m、c = 1 MPa、μ = 0.6 时夹逼 [2.5632e8, 2.7744e8]。"""
    hx, hy, hz = L / 2, 0.3 * L, 0.5 * L
    W = 26000.0 * (2 * hx) * (2 * hy) * hz
    A = (2 * hx) * (2 * hy) / 4
    cts = [LimitContact((off[0] + sx * hx, off[1] + sy * hy, off[2]), (0.0, 0.0, 1.0), mu, cohesion=c, area=A)
           for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]
    o = (0.0, 0.0, 0.0)
    dead = wrench((0.0, 0.0, -W), (off[0], off[1], off[2] + 0.5 * hz), o, 3)
    live = wrench((cos(th), sin(th), 0.0), off, o, 3)
    return cts, dead, live, mu * W + 4.0 * c * A


@pytest.mark.parametrize("off", [(100.0, 0.0, 0.0), (300.0, 0.0, 0.0), (1000.0, 0.0, 0.0), (1000.0, 2000.0, 300.0),
                                 (5e5, 4.4e6, 300.0)])
def test_g6_rock_block_at_site_coordinates_is_bounded_and_translation_invariant(off):
    """G6 critical 0 原例：块在原点时 α = 2.5742639360650e8；x 向 300 m 以内正确，1000 m 起旧实现报
    unbounded、α = ∞（承载力无穷，不安全一侧），(1000, 2000, 300) 同样。现在任何坐标下 optimal、落在夹逼里，
    且与原点处的值一致到 1e-12（内部参考点取接触形心，平移前后 LP 逐位相同）。"""
    ref = limit_load(*_g6_rock_block((0.0, 0.0, 0.0))[:3], dim=3, k=8)
    assert ref.alpha == pytest.approx(257426393.6065, rel=1e-12)
    cts, dead, live, full = _g6_rock_block(off)
    r = limit_load(cts, dead, live, dim=3, k=8)
    assert r.status == "optimal", (off, r.status, r.alpha)
    assert cos(pi / 8) * full * (1 - 1e-9) <= r.alpha <= full * (1 + 1e-9)
    assert r.alpha == pytest.approx(ref.alpha, rel=1e-12), (off, r.alpha, ref.alpha)
    assert check_duality(r, cts, dead, live, dim=3, k=8)["ok"]
