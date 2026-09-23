"""求解器的契约：**要么答对，要么抛错，绝不静默给错**（M0 之后的设计承诺，在此钉成门）。

背景：M0 前的求解器在三维扁块四角黏聚、荷载 ×1e4 时，基解已不满足 Ax = b 却照样报 optimal，
承载力超出解析上界（见 reports/l3_limit_analysis.md「M0 之后」）。修复后默认容差下答对；
2026-09-24 文档核查者又发现：显式传很紧的 lp_tol（如 1e-12）时同一算例会抛 RuntimeError（残差守卫）——
这正是契约允许的"抛错"一支，但此前没有门看着。本文件把契约本身钉住：
在一组刻意刁钻的容差与尺度上，结果只能是 (a) optimal 且落在解析夹逼内，或 (b) 抛 RuntimeError。

oracle：径向夹逼 α ∈ [cos(π/k), 1]·(μW + ΣcA)，纸笔推出（推导见 test_limit_duality.py 同名算例 docstring），
不调用求解器内部。
"""

from math import cos, pi, sin

import pytest

from eab.limit import LimitContact, limit_load, wrench


def _cohesive_block(s, g):
    W, mu, cA = 10.0 * s, 0.2, 1.5 * s
    hx, hy = 1.0 * g, 0.6 * g
    cts = [LimitContact((sx * hx, sy * hy, 0.0), (0.0, 0.0, 1.0), mu, cohesion=cA, area=1.0)
           for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]
    o = (0.0, 0.0, 0.0)
    dead = wrench((0.0, 0.0, -W), (0.0, 0.0, 0.5 * g), o, 3)
    live = wrench((cos(0.3), sin(0.3), 0.0), o, o, 3)
    return cts, dead, live, mu * W + 4.0 * cA


@pytest.mark.parametrize("lp_tol", [None, 1e-9, 1e-12, 1e-14])
@pytest.mark.parametrize("s,g", [(1.0, 1.0), (1e4, 1.0), (1e4, 1e-3), (1e-3, 1e3)])
@pytest.mark.parametrize("k", [5, 16])
def test_answer_is_correct_or_the_solver_raises(lp_tol, s, g, k):
    cts, dead, live, full = _cohesive_block(s, g)
    try:
        r = limit_load(cts, dead, live, dim=3, origin=(0.0, 0.0, 0.0), k=k, lp_tol=lp_tol)
    except RuntimeError:
        return                                        # 契约允许：数值崩溃必须抛出
    assert r.status == "optimal", (lp_tol, s, g, k, r.status)
    assert cos(pi / k) * full * (1 - 1e-9) <= r.alpha <= full * (1 + 1e-9), (lp_tol, s, g, k, r.alpha, full)


def test_default_tolerance_answers_the_audited_case():
    """默认容差下，审查那个曾经静默给错的算例必须**答出来**（不许靠抛错回避）。"""
    cts, dead, live, full = _cohesive_block(1e4, 1.0)
    r = limit_load(cts, dead, live, dim=3, origin=(0.0, 0.0, 0.0), k=16)
    assert r.status == "optimal"
    assert cos(pi / 16) * full * (1 - 1e-9) <= r.alpha <= full * (1 + 1e-9)
