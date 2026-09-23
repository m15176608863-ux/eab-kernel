"""盖 → 极限分析接触的接缝（审查 C4）：接触点取在哪一侧。

缺陷：`contacts_from_covers` 默认取见证段中点（或 B 侧点）。gap > 0 的盖（窗口内的"悬浮"盖）
会把摩擦力作用线沿法向挪开 gap/2（或 gap），切向力矩错 μ·gap/2；2×2×3 方块、gap = 0.3 的
倾覆算例给出 3.1746 而刚体真值是 3.3333。力作用在动体 A 上，接触点应取 A 侧见证点。

**oracle（纪律 A）**：刚体倾覆闭式 α* = W·(w/2)/h（绕趾转动：抗倾覆力矩 W·w/2，
荷载作用在块顶、力臂 h，**与块离地的 gap 无关**）；以及接触点的 z 坐标 = 块底面高度 gap
（由构造给出）。盖由 enumerate_covers3 产生——它是被测链路的上游，不是 oracle。
中点 / B 侧的偏差也有闭式：力臂变成 h + gap/2、h + gap ⇒ α = W·(w/2)/(h + gap/2)、W·(w/2)/(h + gap)。

**格子（纪律 B）**：gap ∈ {0（分界：恰接触）, 0.1, 0.3}；μ ∈ {0.2（滑动控制）, 1.0（倾覆控制）}；
尺度 荷载 ×1、×100、×1e4，几何 ×1e-3（窗口与盖枚举 tol 同比缩放）。
"""

from math import cos, pi

import pytest

from eab.kernel3d.covers3 import enumerate_covers3
from eab.kernel3d.geom3 import Polyhedron
from eab.limit import contacts_from_covers, limit_load, wrench

W0, HALF_W, H = 10.0, 1.0, 3.0            # 2 × 2 × 3 方块：倾覆 α* = W·1/3，滑动 α* = μW


def _box(cx, cy, cz, lx, ly, lz):
    xs = (cx - lx / 2, cx + lx / 2)
    ys = (cy - ly / 2, cy + ly / 2)
    zs = (cz - lz / 2, cz + lz / 2)
    v = [(x, y, z) for x in xs for y in ys for z in zs]

    def i(a, b, c):
        return a * 4 + b * 2 + c

    f = [(i(0, 0, 0), i(0, 0, 1), i(0, 1, 1), i(0, 1, 0)), (i(1, 0, 0), i(1, 1, 0), i(1, 1, 1), i(1, 0, 1)),
         (i(0, 0, 0), i(1, 0, 0), i(1, 0, 1), i(0, 0, 1)), (i(0, 1, 0), i(0, 1, 1), i(1, 1, 1), i(1, 1, 0)),
         (i(0, 0, 0), i(0, 1, 0), i(1, 1, 0), i(1, 0, 0)), (i(0, 0, 1), i(1, 0, 1), i(1, 1, 1), i(0, 1, 1))]
    return Polyhedron(v, f)


def _hovering_block(gap, mu, *, side=None, s=1.0, g=1.0):
    """块底面在 z = gap（离地），地面顶面 z = 0。自重作用在体心，横向力作用在块顶。"""
    ground = _box(0.0, 0.0, -0.5 * g, 10.0 * g, 10.0 * g, 1.0 * g)
    blk = _box(0.0, 0.0, (H / 2 + gap) * g, 2 * HALF_W * g, 2 * HALF_W * g, H * g)
    cv = [c for c in enumerate_covers3(blk, ground, window=0.5 * g, tol=1e-9 * g)
          if c.in_extent and c.normal]
    kw = {} if side is None else {"side": side}
    cts = contacts_from_covers(cv, mu=mu, **kw)
    o = (0.0, 0.0, 0.0)
    W = W0 * s
    dead = wrench((0.0, 0.0, -W), (0.0, 0.0, (H / 2 + gap) * g), o, 3)
    live = wrench((1.0, 0.0, 0.0), (0.0, 0.0, (H + gap) * g), o, 3)
    r = limit_load(cts, dead, live, dim=3, origin=o, k=8)
    return r, cts, cv


GRID = [(1.0, 1.0), (1e2, 1.0), (1e4, 1.0), (1.0, 1e-3), (1e4, 1e-3)]


@pytest.mark.parametrize("s,g", GRID)
@pytest.mark.parametrize("gap", [0.0, 0.1, 0.3])
def test_toppling_capacity_is_independent_of_the_gap(gap, s, g):
    """默认（A 侧）：倾覆承载 = W·(w/2)/h = 3.3333·s，与 gap 无关；接触点都在块底面 z = gap 上。"""
    r, cts, cv = _hovering_block(gap, 1.0, s=s, g=g)
    assert cv and all(abs(c.gap - gap * g) < 1e-9 * g for c in cv), [c.gap for c in cv]
    assert all(abs(ct.point[2] - gap * g) < 1e-12 for ct in cts)
    assert r.status == "optimal"
    assert r.alpha / s == pytest.approx(W0 * HALF_W / H, rel=1e-9)


@pytest.mark.parametrize("gap", [0.0, 0.1, 0.3])
def test_sliding_capacity_is_independent_of_the_gap(gap):
    """滑动控制（μ = 0.2）：承载 = μW·ρ，ρ ∈ [cos(π/8), 1]；k=8 的棱扇对 x 向荷载的具体值与
    接触点高度无关——gap 取任何值答案都与 gap = 0 相同。"""
    r0, *_ = _hovering_block(0.0, 0.2)
    r, *_ = _hovering_block(gap, 0.2)
    assert r.status == "optimal" and r0.status == "optimal"
    assert cos(pi / 8) * 0.2 * W0 - 1e-9 <= r.alpha <= 0.2 * W0 + 1e-9
    assert r.alpha == pytest.approx(r0.alpha, rel=1e-12)


@pytest.mark.parametrize("gap", [0.1, 0.3])
def test_midpoint_and_b_side_shift_the_line_of_action_by_the_documented_amount(gap):
    """文档化的偏差（纪律 C：docstring 里写的量有门）：中点把作用线抬高 gap/2、B 侧抬高 gap，
    倾覆承载分别变成 W·(w/2)/(h + gap/2)、W·(w/2)/(h + gap)。"""
    rm, ctm, _ = _hovering_block(gap, 1.0, side="mid")
    rb, ctb, _ = _hovering_block(gap, 1.0, side="b")
    ra, cta, _ = _hovering_block(gap, 1.0, side="a")
    assert all(abs(ct.point[2] - gap / 2) < 1e-12 for ct in ctm)
    assert all(abs(ct.point[2]) < 1e-12 for ct in ctb)
    assert all(abs(ct.point[2] - gap) < 1e-12 for ct in cta)
    assert ra.alpha == pytest.approx(W0 * HALF_W / H, rel=1e-9)
    assert rm.alpha == pytest.approx(W0 * HALF_W / (H + gap / 2), rel=1e-9)
    assert rb.alpha == pytest.approx(W0 * HALF_W / (H + gap), rel=1e-9)


def test_unknown_side_is_rejected():
    with pytest.raises(ValueError):
        _hovering_block(0.1, 1.0, side="left")
