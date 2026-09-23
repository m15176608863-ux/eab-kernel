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
from math import atan, cos, pi, tan
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from osteomorphic import interlocking_pair  # noqa: E402

from eab.kernel3d.covers3 import enumerate_covers3  # noqa: E402
from eab.kernel3d.geom3 import Polyhedron  # noqa: E402
from eab.limit import LimitContact, contacts_from_covers, limit_load, wrench  # noqa: E402

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
