"""G6 第四轮 kernel-2d-readers 镜头：二维核三处"判据少了被测方向自己的噪声"（第三轮那句话的第四、五、六处遗漏）。

1. facet_gap 的 VE/EV facet 把短边（T 形顶点边）的原始外法向当整个 E 的半平面：方向噪声 rfl/|e| × 杠杆距离 D ≫ 成员容差，
   凸块成员判定在离该 facet 远处静默答错（critical：压进 1e-6 却答"分离"）。
2. vv_cover 的活跃判据没加分离方向 unit(a − b) 自身的噪声 rfl/|a − b|：方向恰在交锥边界时 strict 随刚体运动对半翻转（major）。
3. enumerate_covers / first_entrance_for_vertex 的边内带没有杠杆项 |a − b0|·rfl/|e|²：顶点恰投影在短边端点时盖随刚体运动随机出入（minor）。
oracle：暴力 polygons_overlap（纪律 A）；不变性按纪律 F 的刚体运动扫描。"""

from __future__ import annotations

import math
import random
from fractions import Fraction as F

import pytest

from eab.kernel2d.covers import enumerate_covers, membership_convex, vv_cover
from eab.kernel2d.geom import polygons_overlap, translate
from test_kernel2d_covers_e3 import strict_vv_oracle, independent_cover_oracle


def _rot(P, th, T=(0.0, 0.0)):
    c, s = math.cos(th), math.sin(th)
    return [(T[0] + c * x - s * y, T[1] + s * x + c * y) for x, y in P]


SQUARE = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]


def _fan_overlap_independent(A, B, x):
    """本门A凸四边形、B从右下角可见全边界；显式扇片+内联Fraction全投影SAT。
    不调用被测路径的耳切、exact/geom几何原语，平移不在浮点上做。
    """
    A = [(F(u) + F(x[0]), F(v) + F(x[1])) for u, v in A]
    B = [(F(u), F(v)) for u, v in B]
    left = [(A[0], A[1], A[2]), (A[0], A[2], A[3])]
    right = [(B[1], B[2], B[3]), (B[1], B[3], B[4]), (B[1], B[4], B[0])]
    states = []
    for a in left:
        for b in right:
            status = 1
            for P in (a, b):
                for i in range(3):
                    p, q = P[i], P[(i + 1) % 3]
                    nx, ny = q[1] - p[1], p[0] - q[0]
                    ap = [nx*u + ny*v for u, v in a]
                    bp = [nx*u + ny*v for u, v in b]
                    overlap = min(max(ap), max(bp)) - max(min(ap), min(bp))
                    status = min(status, (overlap > 0) - (overlap < 0))
            states.append(status)
    return max(states)


@pytest.mark.parametrize("h", [1e-3, 1e-5, 1e-7])
@pytest.mark.parametrize("C", [1e3, 1e5])
@pytest.mark.parametrize("th", [0.3, 1.1, 2.9, 4.4])
def test_membership_far_from_a_t_vertex_short_edge_agrees_with_brute(h, C, th):
    """B = 单位方块、左边被 T 形顶点拆成长边 + 长 h 的短边；A = 0.1 方块，右侧压进 B 左侧 1e-6（≫ 舍入），位置离短边 0.3 远。
    刚体旋转 th、平移到 C 后：暴力谓词答 1（Fraction 可证），membership_convex 必须也答 1——旧版短边法向偏 ~eps·C/h rad，
    乘杠杆 0.3 后把参考点判到 facet 外侧（critical）。
    E2旧门的浮点translate/容差oracle改成独立显式扇片Fraction SAT；每个答案精确一致，且1e-6余量
    大于坐标舍入界时仍守刚体不变（不再依靠链法向抹平边界）。原24格及分离/贯入两侧全部保留。"""
    B0 = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, h)]
    A0 = [(0.0, 0.0), (0.1, 0.0), (0.1, 0.1), (0.0, 0.1)]
    x0 = (-0.1 + 1e-6, 0.45)
    c, s = math.cos(th), math.sin(th)
    A = _rot(A0, th)
    B = _rot(B0, th, (C, C))
    x = (C + c * x0[0] - s * x0[1], C + s * x0[0] + c * x0[1])
    assert 1e-6 > 64 * math.ulp(max(C, 1.0))
    brute = _fan_overlap_independent(A, B, x)
    assert brute == 1
    assert membership_convex(A, B, x, 0.0) == 1, (h, C, th)
    # 同一位形把 A 拉开 2e-6（分离 1e-6）：两边都答 −1
    x2 = (x[0] - 2e-6 * c, x[1] - 2e-6 * s)
    assert _fan_overlap_independent(A, B, x2) == -1 == membership_convex(A, B, x2, 0.0)


@pytest.mark.parametrize("g", [1e-6, 1e-7, 1e-8])
@pytest.mark.parametrize("C", [1e3, 1e5])
def test_vv_cover_strictness_is_invariant_when_the_separation_direction_is_on_the_cone_boundary(g, C):
    """A = 单位方块（顶点 0 = 左下角，−N_A = [0°, 90°]），B = 三角（顶点 0 = 原点，N_B = [−45°, 45°]），交锥 [0°, 45°]；
    A 平移 (g, 0)：分离方向恰为 0°（交锥边界）。E3 保留全部 31 姿态，strict 与独立 Fraction 邻点支持 oracle 逐格精确一致；
    舍入后数据在边界两侧确实可能不同，不再用噪声把两侧伪装成同一答案。"""
    A0 = SQUARE
    B0 = [(0.0, 0.0), (-1.0, 1.0), (-1.0, -1.0)]
    base = vv_cover(translate(A0, (g, 0.0)), 0, B0, 0, 0.0)
    assert base is not None
    assert base.strict is strict_vv_oracle(translate(A0,(g,0.0)),0,B0,0)
    signatures = []
    for k in range(31):
        th = 0.2 * k
        A = _rot(translate(A0, (g, 0.0)), th, (C, C))
        B = _rot(B0, th, (C, C))
        c = vv_cover(A, 0, B, 0, 0.0)
        assert c is not None, (g, C, th)
        assert c.strict is strict_vv_oracle(A,0,B,0), (g,C,th)
        signatures.append(c.strict)
    assert len(signatures) == 31


@pytest.mark.parametrize("h", [1e-4, 1e-5])
@pytest.mark.parametrize("C", [1e3, 1e5])
def test_ve_cover_in_segment_band_is_invariant_for_a_vertex_over_a_short_edge_endpoint(h, C):
    """B = 单位方块、顶边被 T 形顶点拆出长 h 的短边 (1, 1)→(1 − h, 1)；A = 三角、底顶点正好在短边起点 (1 − h, 1) 上方高度 0.2
    （投影参数恰为 1）。31 个姿态 + 平移到 C：每格完整标签/strict 集对独立精确 oracle 一致；
    保留原网格，不再要求舍入数据必须仍精确投影在端点。"""
    B0 = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (1.0 - h, 1.0), (0.0, 1.0)]
    # 顶点高度 0.2：到 B 真角点 (1, 1) 的方向离其法锥边界 h/0.2 rad——与长度容差张的角 tol/h 分得开（不许恰落在容差边界上）
    A0 = [(1.0 - h, 1.2), (1.0 - h + 0.3, 1.6), (1.0 - h - 0.3, 1.6)]
    base = {c.label() for c in enumerate_covers(A0, B0, window=0.5)}
    assert ("VE", 0, 2) in base, base
    for k in range(31):
        th = 0.2 * k
        A = _rot(A0, th, (C, C))
        B = _rot(B0, th, (C, C))
        labels = {(c.kind,c.a_index,c.b_index,c.strict) for c in enumerate_covers(A,B,window=0.5)}
        assert labels == independent_cover_oracle(A,B,0.5), (h,C,th)


def test_a_polygon_that_folds_back_on_itself_is_rejected_loudly():
    """G6 第四轮 minor：边界沿自己的边折回的"尖刺"多边形（顶点 (1,0) 落在边 (0,0)→(2,0) 上、边 (2,0)→(1,0) 折回，再凹拐
    回起点）：面积 > 0、凸包深度 0、总转角恰 2π——三道凸性检查都放过，却造出深陷凸包的非凸 E、成员判定静默答反。
    折回（转角 ≈ ±π）要清晰报错。"""
    P = [(0.0, 0.0), (2.0, 0.0), (1.0, 0.0), (0.5, 1.0)]
    from eab.kernel2d.covers import convex_entrance_block
    with pytest.raises(ValueError, match="folds back"):
        convex_entrance_block(P, SQUARE)
    with pytest.raises(ValueError, match="folds back"):
        convex_entrance_block(SQUARE, P)
