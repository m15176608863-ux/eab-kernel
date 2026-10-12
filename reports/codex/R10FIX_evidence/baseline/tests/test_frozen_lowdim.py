"""冻结路径必须接得住 `body_distance` 可能给出的**全部**盖种类（审查 2026-09-21 · C11）。

缺陷：一般位置下 `body_distance` 约一半返回 VE3/EV3（凸 tetra+box 400 样本：387 分离，
VE3 134 + EV3 63），而 `frozen_normal`/`frozen_gap` 只有 VF/FV/EE/VV3 分支，直接 ValueError——
可微裕度路径对一半位形崩溃；旧测试把白名单 `lab[0] in (VF, FV, EE, VV3)` 写成了前置条件。

oracle 与共用原语（纪律 A）：
  · **见证距离** `body_distance` 的 d 来自 covers3 的 ve3_cover/ev3_cover——它与被测的冻结分支
    用的是**同一个原语**（顶点到棱所在直线的正交投影残差），只是两份独立代码。二者一起错
    （例如都忘了减去沿棱分量）时这一票抓不到，所以另设两票：
  · **值与梯度 vs 暴力距离** `brute_feature_distance`（geom3：全部特征对取最小，不看法锥、不看盖），
    梯度用它的中心差分。它的点-棱距离走 `_seg_seg_distance` 的钳位参数化，与投影残差同属
    "点到直线投影"一族，但它不经过冻结路径、也不经过盖枚举；
  · **定理二的凸 oracle**：显式造 E(A,B)=conv{b−a}，量构型点到 E 的距离与最近点方向
    （`closest_point_of_convex_hull_to_origin` 的单形枚举）。这一票与投影残差**零共用**：
    距离函数的梯度必为膨胀法向 unit(x − proj_E x)，冻结路径的 ∂gap/∂x 必须等于它。
"""

import math
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from osteomorphic import interlocking_pair  # noqa: E402

from eab.dual import Dual  # noqa: E402
from eab.kernel3d.frozen import frozen_ee_sign, frozen_gap, frozen_normal  # noqa: E402
from eab.kernel3d.geom3 import (Polyhedron, box, brute_feature_distance, polyhedra_overlap,  # noqa: E402
                                tetra)
from eab.margin import (body_distance, entrance_block_convex,  # noqa: E402
                        margin_gap_from_frozen_cover, nearest_point_on_convex_entrance)

W = 4                       # 通道 0..2 = 平移 x，通道 3 = 裕度 δ


def _pair(s: float = 1.0):
    A = tetra((0.0, 0.0, 0.0), (0.6 * s, 0.0, 0.0), (0.0, 0.5 * s, 0.0), (0.1 * s, 0.1 * s, 0.55 * s))
    B = box(center=(0.0, 0.0, 0.0), half=(0.5 * s, 0.45 * s, 0.4 * s))
    return A, B


def _sign_for(At, B, lab):
    if lab[0] == "EE":
        return frozen_ee_sign(At, B, (lab[1][1], lab[1][2]), (lab[2][1], lab[2][2]))
    return 1.0


def _dual_translation(x):
    return tuple(Dual.seed(x[k], W, k) for k in range(3))


def _brute_grad(A, B, x, h):
    g = []
    for k in range(3):
        xp = list(x)
        xm = list(x)
        xp[k] += h
        xm[k] -= h
        g.append((brute_feature_distance(A.translated(tuple(xp)), B)
                  - brute_feature_distance(A.translated(tuple(xm)), B)) / (2.0 * h))
    return g


def _check_one(A, B, x, *, scale, delta0=0.05, grad_h=None, found=None):
    """body_distance 的标签送进冻结路径：不崩、值 = 见证距离、∂/∂δ ≡ −1；返回 (标签, 对偶间隙)。"""
    At = A.translated(x)
    d, lab = found if found is not None else body_distance(At, B)
    sign = _sign_for(At, B, lab)
    # 形式一（审查的复现口径）：已平移的体、零平移
    g0 = margin_gap_from_frozen_cover(At, B, lab, (0.0, 0.0, 0.0), 0.0, ee_sign=sign)
    assert abs(g0 - d) < 1e-12 * max(1.0, scale), (x, lab, g0, d)
    # 形式二（可微口径）：未平移的体 + 对偶平移 + 对偶裕度
    g = margin_gap_from_frozen_cover(A, B, lab, _dual_translation(x), Dual.seed(delta0, W, 3),
                                     ee_sign=sign)
    assert abs(g.v - (d - delta0)) < 1e-12 * max(1.0, scale), (x, lab, g.v, d)
    assert g.e[3] == -1.0
    # 梯度 = 单位向量（距离函数的梯度），且与暴力距离的中心差分一致
    gn = math.sqrt(sum(g.e[k] ** 2 for k in range(3)))
    assert abs(gn - 1.0) < 1e-12, (x, lab, g.e)
    if grad_h is not None:
        bg = _brute_grad(A, B, x, grad_h)
        assert max(abs(bg[k] - g.e[k]) for k in range(3)) < 1e-6, (x, lab, g.e, bg)
    return lab, g


def _separated_draws(A, B, seed, n, span):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        x = (rng.uniform(-span, span), rng.uniform(-span, span), rng.uniform(-span, span))
        if polyhedra_overlap(A.translated(x), B, 1e-12) == -1:
            out.append(x)
    return out


# ---------------------------------------------------------------- 一般位置：审查的 400 样本原样

def test_every_body_distance_label_enters_the_frozen_path_convex_400():
    """审查口径原样（seed 0、400 次、[-2.2,2.2]³）：分离样本全部进冻结路径，零崩溃。

    值：冻结 gap 与见证距离 < 1e-12；δ 通道 ≡ −1；梯度是单位向量且等于暴力距离的中心差分。
    牙：标签种类必须真的含大量 VE3 / EV3（否则这道门就绕开了被修的分支）。
    """
    A, B = _pair()
    xs = _separated_draws(A, B, 0, 400, 2.2)
    assert len(xs) > 350
    kinds: dict[str, int] = {}
    for x in xs:
        lab, _ = _check_one(A, B, x, scale=1.0, grad_h=1e-6)
        kinds[lab[0]] = kinds.get(lab[0], 0) + 1
    assert kinds.get("VE3", 0) >= 60 and kinds.get("EV3", 0) >= 30, kinds


@pytest.mark.parametrize("scale", [1e-3, 1e3])
def test_every_body_distance_label_enters_the_frozen_path_scaled(scale):
    """尺度格（纪律 B）：几何与平移同乘 1e-3 / 1e3，门的相对精度不变。"""
    A, B = _pair(scale)
    xs = _separated_draws(A, B, 1, 120, 2.2 * scale)
    kinds: dict[str, int] = {}
    for x in xs:
        lab, _ = _check_one(A, B, x, scale=scale, grad_h=1e-6 * scale)
        kinds[lab[0]] = kinds.get(lab[0], 0) + 1
    assert kinds.get("VE3", 0) >= 10 and kinds.get("EV3", 0) >= 5, kinds


def test_low_dim_frozen_gradient_is_the_inflated_normal_of_the_explicit_entrance_block():
    """零共用原语的一票（定理二）：E = conv{b−a} 显式造出，dist(x,E) 与 unit(x − proj_E x)
    分别就是冻结 VE3/EV3 分支的值与 ∂/∂x。"""
    A, B = _pair()
    E = entrance_block_convex(A, B)
    xs = _separated_draws(A, B, 0, 400, 2.2)
    seen = {"VE3": 0, "EV3": 0}
    for x in xs:
        At = A.translated(x)
        _, lab = body_distance(At, B)
        if lab[0] not in seen or seen[lab[0]] >= 12:
            continue
        seen[lab[0]] += 1
        g = margin_gap_from_frozen_cover(A, B, lab, _dual_translation(x), Dual.const(0.0, W))
        p = nearest_point_on_convex_entrance(E, x)
        r = tuple(x[k] - p[k] for k in range(3))
        dist = math.sqrt(sum(c * c for c in r))
        assert abs(g.v - dist) < 1e-12, (x, lab, g.v, dist)
        assert max(abs(g.e[k] - r[k] / dist) for k in range(3)) < 1e-12, (x, lab, g.e, r)
        if seen == {"VE3": 12, "EV3": 12}:
            break
    assert seen == {"VE3": 12, "EV3": 12}, seen


# ---------------------------------------------------------------- 分界点：VE3 与 VF / VV3 的切换处

def _edge(P: Polyhedron, i: int, j: int) -> tuple[int, int]:
    return next(e for e in P.edges() if set(e) == {i, j})


# 顶点 0 在原点、其余三点都在 z ≥ 0.4：顶点 0 是 −z 方向（及其附近方向）的极点
_SHARP_DOWN = ((0.0, 0.0, 0.0), (0.3, 0.1, 0.4), (-0.1, 0.3, 0.4), (0.1, -0.3, 0.45))
# 顶点 0 在原点、其余三点都在 x ≥ 0.4：顶点 0 是 −x 方向的极点
_SHARP_LEFT = ((0.0, 0.0, 0.0), (0.4, 0.1, 0.3), (0.4, 0.3, -0.1), (0.45, -0.3, 0.1))


@pytest.mark.parametrize("t", [0.2, 1e-4])
@pytest.mark.parametrize("case", ["VE3|VF(top)", "VE3|VF(+x)", "VE3|VV3"])
def test_ve3_matches_vf_and_vv3_at_the_switching_boundary(case, t):
    """分界点（纪律 B）：顶点的投影残差恰好等于相邻面法向（VE3↔VF），或投影恰好落在棱端点
    （VE3↔VV3）。两侧的冻结盖在分界上必须给出**同一个**值与梯度（距离函数 C¹）。
    真值 t 与法向是构造给定的，另用暴力距离复核 t。"""
    B = box(half=(0.5, 0.45, 0.4))
    e56 = ("edge",) + _edge(B, 5, 6)           # +x 面(3) 与顶面(1) 的公共棱，沿 y
    ve3 = ("VE3", ("vertex", 0), e56)
    shape, x, other, n_true = {
        # 残差 = +z = 顶面法向：VE3 与 VF(顶面) 并列
        "VE3|VF(top)": (_SHARP_DOWN, (0.5, 0.05, 0.4 + t), ("VF", ("vertex", 0), ("face", 1)), (0.0, 0.0, 1.0)),
        # 残差 = +x = 前面法向：VE3 与 VF(+x 面) 并列
        "VE3|VF(+x)": (_SHARP_LEFT, (0.5 + t, 0.05, 0.4), ("VF", ("vertex", 0), ("face", 3)), (1.0, 0.0, 0.0)),
        # 投影恰在棱端点 5=(0.5,−0.45,0.4)：VE3 与 VV3 并列
        "VE3|VV3": (_SHARP_DOWN, (0.5 + 0.6 * t, -0.45, 0.4 + 0.8 * t), ("VV3", ("vertex", 0), ("vertex", 5)),
                    (0.6, 0.0, 0.8)),
    }[case]
    Ad = tetra(*shape)
    At = Ad.translated(x)
    assert polyhedra_overlap(At, B, 1e-12) == -1
    assert abs(brute_feature_distance(At, B) - t) < 1e-12
    d, _ = body_distance(At, B)
    assert abs(d - t) < 1e-12
    for lab in (ve3, other):
        g = margin_gap_from_frozen_cover(Ad, B, lab, _dual_translation(x), Dual.const(0.0, W))
        assert abs(g.v - t) < 1e-12, (x, lab, g)
        assert max(abs(g.e[k] - n_true[k]) for k in range(3)) < 1e-12, (x, lab, g.e)


@pytest.mark.parametrize("t", [0.2, 1e-4])
def test_ev3_matches_fv_at_the_switching_boundary(t):
    """EV3 的镜像分界：A 的棱（方块底面与 +x 面的公共棱）正对 B 的尖顶，残差 = −z，
    即 B→A 法向 +z = −n_A(底面)：EV3 与 FV(底面) 并列。"""
    Bd = tetra((0.0, 0.0, 0.0), (0.3, 0.1, -0.4), (-0.1, 0.3, -0.4), (0.1, -0.3, -0.45))
    A0 = box(half=(0.5, 0.45, 0.4))
    x = (-0.5, 0.05, 0.4 + t)                   # 方块底面 z = t，+x 面 x = 0
    e12 = _edge(A0, 1, 2)                       # 底面(0) 与 +x 面(3) 的公共棱，沿 y
    At = A0.translated(x)
    assert polyhedra_overlap(At, Bd, 1e-12) == -1
    assert abs(brute_feature_distance(At, Bd) - t) < 1e-12
    for lab in [("EV3", ("edge",) + e12, ("vertex", 0)), ("FV", ("face", 0), ("vertex", 0))]:
        g = margin_gap_from_frozen_cover(A0, Bd, lab, _dual_translation(x), Dual.const(0.0, W))
        assert abs(g.v - t) < 1e-12, (lab, g)
        assert max(abs(g.e[k] - (0.0, 0.0, 1.0)[k]) for k in range(3)) < 1e-12, (lab, g.e)


# ---------------------------------------------------------------- 凹块：互锁块上抽样一遍

@pytest.mark.parametrize("kw,seed", [(dict(nx=4, ny=2, amp=0.25), 1),
                                     (dict(nx=5, ny=2, amp=0.3, phase=1.0), 8)])
def test_every_body_distance_label_enters_the_frozen_path_interlocking(kw, seed):
    """凹的互锁块（对称 nx=4 与非对称 nx=5）上随机分离位形：同样零崩溃、值 = 见证距离 =
    暴力距离、δ 通道 −1；低维盖另对暴力距离做梯度中心差分。

    互锁块上低维标签较稀（实测约 1/10）；为控制耗时（暴力距离每次 ~30 ms）只取 6 个样本，
    种子选成前 6 个里至少出现一个 VE3/EV3，并**断言**它出现——门不许退化成只走面盖。
    """
    A, L = interlocking_pair(**kw)
    rng = random.Random(seed)
    n = 0
    kinds: dict[str, int] = {}
    while n < 6:
        x = (rng.uniform(-1.2, 1.2), rng.uniform(-0.6, 0.6), rng.uniform(0.02, 0.5))
        At = A.translated(x)
        if polyhedra_overlap(At, L, 1e-12) != -1:
            continue
        n += 1
        d, lab = body_distance(At, L)
        assert abs(d - brute_feature_distance(At, L)) < 1e-9, (x, lab)
        lab, _ = _check_one(A, L, x, scale=1.0, found=(d, lab),
                            grad_h=1e-6 if lab[0] in ("VE3", "EV3", "VV3") else None)
        kinds[lab[0]] = kinds.get(lab[0], 0) + 1
    assert kinds.get("VE3", 0) + kinds.get("EV3", 0) >= 1, kinds


def test_frozen_normal_rejects_unknown_and_penetration_labels():
    A, B = _pair()
    with pytest.raises(ValueError):
        frozen_normal(A, B, ("FF", ("face", 0), ("face", 1)))
    with pytest.raises(ValueError):
        frozen_gap(A, B, ("FF", ("face", 0), ("face", 1)), (0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    with pytest.raises(ValueError):
        margin_gap_from_frozen_cover(A, B, ("PENETRATING",), (0.0, 0.0, 0.0), 0.05)
