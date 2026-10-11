"""E2 报告带：精确分类之外的显式、无舍入地板的长度报告。

旧凸路径以舍入后的 facet_gap 分支，旧凹回退再次用带舍入地板的浮点谓词；两者都能把远超调用方 tol 的答案吞成 0。
新门不跳过带内样本：凸对逐点对闭式欧氏距离；凹对逐点对已知 E 的闭式成员与边界距离，并明确保守报告带的不完备性。
纪律 A：主 oracle 仅用方块/L 形的闭式有理数区间与距离，不调用 exact/geom/covers 的任何几何原语。
"""

from fractions import Fraction as F

import pytest

from eab.kernel2d.covers import membership_convex


SQUARE = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
L_SHAPE = [(0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (1.0, 1.0), (1.0, 2.0), (0.0, 2.0)]


def _square_report(x, tol):
    """单位方块对：E = [-1,1]^2；仅用闭式坐标区间与欧氏距离平方。"""
    u, v = abs(F(x[0])), abs(F(x[1]))
    extent = max(u, v)
    state = 1 if extent < 1 else 0 if extent == 1 else -1
    distance2 = ((1 - extent) ** 2 if state >= 0 else
                 max(u - 1, 0) ** 2 + max(v - 1, 0) ** 2)
    return 0 if distance2 <= F(tol) ** 2 else state


@pytest.mark.parametrize("scale", [F(1, 1024), F(1), F(1024)])
@pytest.mark.parametrize("x", [(F(0), F(0)), (F(3, 4), F(0)), (F(5, 4), F(0)),
                              (F(5, 4), F(5, 4)), (F(1), F(1)), (F(-5, 4), F(3, 8))])
@pytest.mark.parametrize("tol", [F(0), F(1, 4), F(5, 16), F(1, 2)])
def test_convex_report_band_equals_closed_euclidean_boundary_distance(scale, x, tol):
    """旧口径 max facet gap 把外角方形带当欧氏带；新口径含精确阈值和角外点，逐格闭式零错且随单位缩放。"""
    sq = [(float(scale * u), float(scale * v)) for u, v in SQUARE]
    scaled_x = (scale * x[0], scale * x[1])
    assert membership_convex(sq, sq, scaled_x, scale * tol) == _square_report(x, tol)


def test_corner_report_band_does_not_swallow_points_beyond_euclidean_tol():
    """dx=dy=1/4，真实距离 sqrt(2)/4 > 5/16；旧 max gap=1/4 错吞成 0。闭式 oracle 不用被测原语。"""
    assert 2 * F(1, 4) ** 2 > F(5, 16) ** 2
    assert membership_convex(SQUARE, SQUARE, (F(5, 4), F(5, 4)), F(5, 16)) == -1


def test_tiny_report_tol_never_uses_rounded_facet_gap(monkeypatch):
    """旧 facet_gap 把 -1e16+0.4 舍入为 -1e16，误报接触；新门用闭式重叠区间，并禁止调用该构造量。"""
    from eab.kernel2d import covers
    a = [(1e16, 0.0), (1e16 + 2.0, 0.0), (1e16 + 2.0, 2.0), (1e16, 2.0)]
    b = [(0.1, 0.1), (0.4, 0.1), (0.4, 0.4), (0.1, 0.4)]
    x = (-1e16, 0.0)  # 精确平移后 A=[0,2]^2，B 严格在内，离 E 边界至少 0.4。
    assert membership_convex(a, b, x, 1e-30) == 1

    def forbidden(*args, **kwargs):
        raise AssertionError("facet_gap is a construction, never a report-band predicate")

    monkeypatch.setattr(covers, "facet_gap", forbidden)
    assert membership_convex(a, b, x, 1e-30) == 1


@pytest.mark.parametrize("scale", [F(1, 1024), F(1), F(1024)])
@pytest.mark.parametrize("sign", [-1, 0, 1])
def test_nonconvex_report_band_has_no_coordinate_roundoff_floor(scale, sign):
    """旧回退把 tol 抬到工程坐标舍入地板，吞掉真实间隙/侵入；新门在闭式 L 的竖直界面两侧逐点精确。"""
    delta = F(1, 2**32)
    offset = F(10**6)
    a = [(float(offset + scale * u), float(-offset + scale * v)) for u, v in SQUARE]
    b = [(float(offset + scale * u), float(-offset + scale * v)) for u, v in L_SHAPE]
    # E 在 y=1.5 的局部边界 x=1。x 的平移必须在 Fraction 上，不能先加到大坐标后舍入。
    x = (scale * (1 + sign * delta), scale * F(3, 2))
    assert membership_convex(a, b, x, scale * F(1, 2**60)) == -sign


@pytest.mark.parametrize("x,want", [((F(1), F(3, 2)), 0),
                                     ((F(1) - F(1, 2**60), F(3, 2)), 1),
                                     ((F(1) + F(1, 2**60), F(3, 2)), -1)])
def test_nonconvex_zero_tol_uses_exact_fraction_translation(x, want):
    """平移离边界小于 float 的 ulp，闭式 L 区间仍分清两侧；旧浮点 translate 会把三格全变成接触。"""
    assert membership_convex(SQUARE, L_SHAPE, x, 0.0) == want


@pytest.mark.parametrize("sign", [-1, 1])
def test_nonconvex_axis_witness_reports_the_exact_tol_boundary(sign):
    """竖直界面两侧距离恰 tol；四轴精确探针触及边界时必须报告 0，阈值减半则保留精确分类。"""
    delta = F(1, 2**40)
    x = (1 + sign * delta, F(3, 2))
    assert membership_convex(SQUARE, L_SHAPE, x, delta) == 0
    assert membership_convex(SQUARE, L_SHAPE, x, delta / 2) == -sign


def test_nonconvex_report_band_is_explicitly_conservative_not_complete():
    """E 的凹角(1,1)距 x=(7/8,7/8)为 sqrt(2)/8 < 3/16，但四轴探针都仍在 E 内。

    无完整非凸 E 构造时新实现不捏造边界见证，保留精确 1；这格明确记录保守报告带不是全欧氏带。
    """
    x, tol = (F(7, 8), F(7, 8)), F(3, 16)
    assert 2 * F(1, 8) ** 2 < tol ** 2
    assert membership_convex(SQUARE, L_SHAPE, x, tol) == 1


@pytest.mark.parametrize("x", [(F(i, 8), F(j, 8)) for i in range(5, 12) for j in range(5, 16)])
def test_every_nonconvex_zero_report_has_a_closed_boundary_distance_witness(x):
    """逐格检查无带外吞噬，而非只挑几个通过点；闭式距离取凹角两段及上/右外边界四段的最小值。"""
    u, v = x
    tol = F(3, 16)
    state = (-1 if u > 1 and v > 1 else
             0 if (u == 1 and v >= 1) or (v == 1 and u >= 1) else 1)
    distance2 = min((1 - u) ** 2 + max(1 - v, 0) ** 2,
                    (1 - v) ** 2 + max(1 - u, 0) ** 2,
                    (2 - u) ** 2 + max(v - 1, 0) ** 2,
                    (2 - v) ** 2 + max(u - 1, 0) ** 2)
    got = membership_convex(SQUARE, L_SHAPE, x, tol)
    assert got in (state, 0)
    if got == 0:
        assert distance2 <= tol ** 2
    if distance2 > tol ** 2:
        assert got == state
