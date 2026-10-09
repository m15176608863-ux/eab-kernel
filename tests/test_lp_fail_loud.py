"""求解器的契约：**要么答对，要么抛错，绝不静默给错**（M0 之后的设计承诺，在此钉成门）。

背景：M0 前的求解器在三维扁块四角黏聚、荷载 ×1e4 时，基解已不满足 Ax = b 却照样报 optimal，
承载力超出解析上界（见 reports/l3_limit_analysis.md「M0 之后」）。修复后默认容差下答对；
2026-09-24 文档核查者又发现：显式传很紧的 lp_tol（如 1e-12）时同一算例会抛 RuntimeError（残差守卫）——
这正是契约允许的"抛错"一支，但此前没有门看着。本文件把契约本身钉住：
在一组刻意刁钻的容差与尺度上，结果只能是 (a) optimal 且落在解析夹逼内，或 (b) 抛 RuntimeError。
2026-10-10：M0.2 的精确 LP 之后，本文件的 32 格在 HEAD 上全部走 (a)（docs/canon_map.md 附录 A.9 复跑 raises 0 / answered 32）；
(b) 仍是契约允许的一支，只是这组格子上不再出现。

oracle：径向夹逼 α ∈ [cos(π/k), 1]·(μW + ΣcA)，纸笔推出（推导见 test_limit_duality.py 同名算例 docstring），
不调用求解器内部。
"""

from math import cos, pi, sin

import pytest

from eab.limit import LimitContact, check_duality, limit_load, wrench


def _cohesive_block(s, g):
    W, mu, cA = 10.0 * s, 0.2, 1.5 * s
    hx, hy = 1.0 * g, 0.6 * g
    cts = [LimitContact((sx * hx, sy * hy, 0.0), (0.0, 0.0, 1.0), mu, cohesion=cA, area=1.0)
           for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]
    o = (0.0, 0.0, 0.0)
    dead = wrench((0.0, 0.0, -W), (0.0, 0.0, 0.5 * g), o, 3)
    live = wrench((cos(0.3), sin(0.3), 0.0), o, o, 3)
    return cts, dead, live, mu * W + 4.0 * cA


@pytest.mark.parametrize("lp_tol", [None, 1e-9, 1e-12, 1e-14, 1e-4, 1e-3])     # 1e-4/1e-3：G6 minor 24 的放宽方向
@pytest.mark.parametrize("s,g", [(1.0, 1.0), (1e4, 1.0), (1e4, 1e-3), (1e-3, 1e3)])
@pytest.mark.parametrize("k", [5, 16])
def test_answer_is_correct(lp_tol, s, g, k):
    """（2026-09-27 收紧，G6 第二轮 major）M0.2 起 LP 对给定数据精确、浮点层的失败不抛给调用方，所以这些格子——包括显式
    传很紧 lp_tol 的——一律必须答对、不许抛错。旧版在这里放行 RuntimeError，"一律答对"的声称没有门。"""
    cts, dead, live, full = _cohesive_block(s, g)
    r = limit_load(cts, dead, live, dim=3, origin=(0.0, 0.0, 0.0), k=k, lp_tol=lp_tol)
    assert r.status == "optimal", (lp_tol, s, g, k, r.status)
    assert cos(pi / k) * full * (1 - 1e-9) <= r.alpha <= full * (1 + 1e-9), (lp_tol, s, g, k, r.alpha, full)


def test_default_tolerance_answers_the_audited_case():
    """默认容差下，审查那个曾经静默给错的算例必须**答出来**（不许靠抛错回避）。"""
    cts, dead, live, full = _cohesive_block(1e4, 1.0)
    r = limit_load(cts, dead, live, dim=3, origin=(0.0, 0.0, 0.0), k=16)
    assert r.status == "optimal"
    assert cos(pi / 16) * full * (1 - 1e-9) <= r.alpha <= full * (1 + 1e-9)


# ---------------------------------------------------------------- G6（2026-09-24）：默认容差必须答出来的普通输入

def _si_block(L, c, mu, off=(0.0, 0.0, 0.0), th=0.3):
    """SI 单位的岩块：底 L × 0.6L、高 0.5L（容重 26 kN/m³），四角各一块 L²·0.15 m² 的黏聚面片，
    黏聚强度 c（Pa），块体放在工程坐标 off 处；推力在底面内沿 θ，调用方用**默认原点**（坐标原点）。
    纯滑动的径向夹逼：α ∈ [cos(π/k), 1]·(μW + 4cA)（推导同 test_limit_duality 的同名算例）。"""
    hx, hy, hz = L / 2, 0.3 * L, 0.5 * L
    W = 26000.0 * (2 * hx) * (2 * hy) * hz
    A = (2 * hx) * (2 * hy) / 4
    cts = [LimitContact((off[0] + sx * hx, off[1] + sy * hy, off[2]), (0.0, 0.0, 1.0), mu, cohesion=c, area=A)
           for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]
    o = (0.0, 0.0, 0.0)
    dead = wrench((0.0, 0.0, -W), (off[0], off[1], off[2] + 0.5 * hz), o, 3)
    live = wrench((cos(th), sin(th), 0.0), off, o, 3)
    return cts, dead, live, mu * W + 4.0 * c * A


@pytest.mark.parametrize("k", [4, 6, 8, 12, 16, 32])
@pytest.mark.parametrize("th", [0.0, 0.1, 0.3, 0.5, 0.785])
def test_si_cohesive_block_answers_at_the_default_tolerance(k, th):
    """G6 major 2 (a)：5 × 3 × 2.5 m、c = 100 kPa、μ = 0.6 的普通岩块，默认 lp_tol、默认 k=8 与 k=16 时
    旧实现对几乎所有非轴向推力抛 "lost feasibility"。这里**不许抛**：必须 optimal 且落在径向夹逼里。"""
    L = 5.0
    hx, hy, hz = L / 2, 1.5, 1.25
    W = 26000.0 * 5.0 * 3.0 * 2.5
    cts = [LimitContact((sx * hx, sy * hy, 0.0), (0.0, 0.0, 1.0), 0.6, cohesion=1e5, area=3.75)
           for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]
    o = (0.0, 0.0, 0.0)
    dead = wrench((0.0, 0.0, -W), (0.0, 0.0, hz), o, 3)
    live = wrench((cos(th), sin(th), 0.0), o, o, 3)
    full = 0.6 * W + 4.0 * 1e5 * 3.75
    r = limit_load(cts, dead, live, dim=3, origin=o, k=k)
    assert r.status == "optimal", (k, th, r.status)
    assert cos(pi / k) * full * (1 - 1e-9) <= r.alpha <= full * (1 + 1e-9), (k, th, r.alpha, full)


@pytest.mark.parametrize("k", [8, 64, 127, 128, 129, 256])
def test_fine_cone_does_not_cycle(k):
    """G6 major 2 (b)：无量纲块（W = 10、cA = 0.01、μ = 1），旧实现 k = 128 时 Bland 规则在浮点下循环
    （409 步一周期，"did not terminate"），k = 256 抛残差守卫。现在必须答出来、落在径向夹逼里。"""
    o = (0.0, 0.0, 0.0)
    cts = [LimitContact((sx, 0.6 * sy, 0.0), (0.0, 0.0, 1.0), 1.0, cohesion=0.01, area=1.0)
           for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]
    r = limit_load(cts, wrench((0.0, 0.0, -10.0), (0.0, 0.0, 0.5), o, 3),
                   wrench((cos(0.3), sin(0.3), 0.0), o, o, 3), dim=3, origin=o, k=k)
    full = 10.0 + 0.04
    assert r.status == "optimal", (k, r.status)
    assert cos(pi / k) * full * (1 - 1e-9) <= r.alpha <= full * (1 + 1e-9), (k, r.alpha)


@pytest.mark.parametrize("off", [(0.0, 0.0, 0.0), (50.0, 80.0, 20.0), (300.0, 500.0, 120.0), (1e3, 2e3, 300.0),
                                 (2e3, 3e3, 500.0)])
def test_site_coordinate_sweep_answers_with_verified_duality(off):
    """G6 major 2 的扫描（及 major 1 / minor 3 的对偶侧）：块体尺寸 1/5/20 m × 黏聚 0/1e4/1e5/1e6 Pa × μ 0.3/0.6
    × 推力方向 0.3/1.0 rad，放在工程坐标 off 处、调用方默认原点、默认容差。每一格必须 optimal、在夹逼内，
    且 check_duality 过（相对判据：容许、相对间隙 < 1e-9、互补 < 1e-7）。"""
    for L in (1.0, 5.0, 20.0):
        for c in (0.0, 1e4, 1e5, 1e6):
            for mu in (0.3, 0.6):
                for th in (0.3, 1.0):
                    cts, dead, live, full = _si_block(L, c, mu, off, th)
                    r = limit_load(cts, dead, live, dim=3, k=8)
                    tag = (off, L, c, mu, th)
                    assert r.status == "optimal", (tag, r.status)
                    assert cos(pi / 8) * full * (1 - 1e-9) <= r.alpha <= full * (1 + 1e-9), (tag, r.alpha, full)
                    d = check_duality(r, cts, dead, live, dim=3, k=8)
                    assert d["admissible"] and d["duality_gap_rel"] < 1e-9 and d["complementarity"] < 1e-7, (tag, d)
