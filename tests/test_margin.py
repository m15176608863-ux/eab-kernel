"""L2 裕度层的门：四条定理各有一道，外加牙。"""

import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from osteomorphic import interlocking_pair, interlocking_pair_generic  # noqa: E402

from eab import dual as D  # noqa: E402
from eab.dual import Dual, convergence_order, val  # noqa: E402
from eab.kernel3d.covers3 import vertex_cone_contains  # noqa: E402
from eab.kernel3d.frozen import frozen_ee_sign  # noqa: E402
from eab.kernel3d.geom3 import (box, brute_feature_distance, norm, polyhedra_overlap,  # noqa: E402
                                sub, tetra, unit)
from eab.margin import (INSIDE, ON_BOUNDARY, OUTSIDE, body_distance,  # noqa: E402
                        distance_to_convex_entrance, entrance_block_convex,
                        inflated_membership, inflated_normal, margin_contacts,
                        margin_gap_from_frozen_cover, nearest_point_on_convex_entrance)


def _small_convex_pair():
    A = tetra((0.0, 0.0, 0.0), (0.6, 0.0, 0.0), (0.0, 0.5, 0.0), (0.1, 0.1, 0.55))
    B = box(center=(0.0, 0.0, 0.0), half=(0.5, 0.45, 0.4))
    return A, B


# ---------------------------------------------------------------- 定理二

@pytest.mark.parametrize("seed", range(3))
def test_config_space_distance_equals_body_distance(seed):
    """dist(x, E) == d(A+x, B)。凸情形显式造 E 作独立 oracle —— 这是裕度层的数值根。"""
    A, B = _small_convex_pair()
    E = entrance_block_convex(A, B)
    rng = random.Random(seed)
    n = 0
    for _ in range(60):
        x = (rng.uniform(-2.2, 2.2), rng.uniform(-2.2, 2.2), rng.uniform(-2.2, 2.2))
        At = A.translated(x)
        if polyhedra_overlap(At, B, 1e-12) != -1:
            continue
        d_config = distance_to_convex_entrance(E, x)
        d_body, lab = body_distance(At, B)
        assert lab is not None
        assert abs(d_config - d_body) < 1e-9, (x, d_config, d_body)
        assert abs(d_body - brute_feature_distance(At, B)) < 1e-9
        n += 1
    assert n > 40, f"only {n} separated samples"   # 实测 54-59；掉下来说明采样器坏了


def test_body_distance_is_not_the_cover_gap():
    """口径钉死：见证距离用 |point_a - point_b|，不是盖的 gap（凹体上 gap 会给 -2.7）。"""
    A, L = interlocking_pair(nx=4, ny=2, amp=0.25)
    sep = A.translated((0.008, -0.01, 0.048))
    assert polyhedra_overlap(sep, L, 1e-12) == -1
    d, _ = body_distance(sep, L)
    assert abs(d - brute_feature_distance(sep, L)) < 1e-9
    assert d > 0.0


# ---------------------------------------------------------------- 定理一 / 定理三

@pytest.mark.parametrize("delta", [0.02, 0.05, 0.12])
def test_inflated_membership_tracks_the_margin(delta):
    """膨胀恒等式的可观测后果：裕度违约 <=> 参考点落进 E_delta。"""
    A, B = _small_convex_pair()
    lift = A.translated((0.0, 0.0, 1.2))
    d0, _ = body_distance(lift, B)
    assert d0 > delta
    assert inflated_membership(lift, B, delta=delta) == OUTSIDE
    onb = A.translated((0.0, 0.0, 1.2 - (d0 - delta)))
    assert inflated_membership(onb, B, delta=delta, atol=1e-9) == ON_BOUNDARY
    closer = A.translated((0.0, 0.0, 1.2 - (d0 - delta) - 0.01))
    assert inflated_membership(closer, B, delta=delta) == INSIDE


def test_margin_contacts_are_generalized_contacts():
    """裕度接触 = 间距 <= delta 的有效盖；margin_gap <= 0 即闭合。"""
    A, B = _small_convex_pair()
    At = A.translated((0.0, 0.0, 1.2))
    d0, _ = body_distance(At, B)
    delta = d0 * 1.5
    ms = margin_contacts(At, B, delta=delta)
    assert ms, "裕度放大到 1.5 倍间距后必须有广义接触闭合"
    assert all(m.closed for m in ms)
    assert ms[0].margin_gap == pytest.approx(d0 - delta, abs=1e-12)
    assert ms[0].normal is not None and abs(norm(ms[0].normal) - 1.0) < 1e-12
    assert margin_contacts(At, B, delta=d0 * 0.5) == []


# ---------------------------------------------------------------- 定理四：C^{1,1}

def test_inflated_normal_is_lipschitz():
    """凸集投影非扩张 => 膨胀法向 Lipschitz，常数 <= 2/delta。"""
    A, B = _small_convex_pair()
    E = entrance_block_convex(A, B)
    rng = random.Random(11)
    delta = 0.25
    pts = []
    while len(pts) < 12:
        x = (rng.uniform(-2.5, 2.5), rng.uniform(-2.5, 2.5), rng.uniform(-2.5, 2.5))
        d = distance_to_convex_entrance(E, x)
        if delta <= d <= 3.0 * delta:
            pts.append(x)
    worst = 0.0
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            ni, nj = inflated_normal(E, pts[i]), inflated_normal(E, pts[j])
            dx = norm(sub(pts[i], pts[j]))
            if dx > 0:
                worst = max(worst, norm(sub(ni, nj)) / dx)
    assert worst <= 2.0 / delta + 1e-9, worst


def test_inflation_turns_a_set_valued_normal_into_a_single_valued_one():
    """把"尖角变圆角"钉死：E 的一个顶点处法锥有非零立体角，故未膨胀时同一最近特征
    对应**多个**法向；膨胀之后每个构型点只有**一个**法向，且随点连续。
    """
    A, B = _small_convex_pair()
    E = entrance_block_convex(A, B)
    delta = 0.3
    rng = random.Random(5)
    found = None
    for vi in range(len(E.verts)):
        dirs = []
        for _ in range(300):
            d = unit((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1)))
            if vertex_cone_contains(E, vi, d, 1e-9) == 1:
                dirs.append(d)
        if len(dirs) >= 2:
            best = max(((a, b) for i, a in enumerate(dirs) for b in dirs[i + 1:]),
                       key=lambda ab: norm(sub(ab[0], ab[1])))
            if norm(sub(best[0], best[1])) > 0.25:
                found = (vi, best)
                break
    assert found is not None, "没找到有非零立体角法锥的 E 顶点"
    vi, (d1, d2) = found
    v = E.verts[vi]
    x1 = tuple(v[k] + delta * d1[k] for k in range(3))
    x2 = tuple(v[k] + delta * d2[k] for k in range(3))
    assert norm(sub(nearest_point_on_convex_entrance(E, x1), v)) < 1e-9
    assert norm(sub(nearest_point_on_convex_entrance(E, x2), v)) < 1e-9
    n1, n2 = inflated_normal(E, x1), inflated_normal(E, x2)
    assert norm(sub(n1, d1)) < 1e-9 and norm(sub(n2, d2)) < 1e-9
    assert norm(sub(n1, n2)) > 0.2
    assert abs(norm(sub(n1, n2)) - norm(sub(x1, x2)) / delta) < 1e-9


# ---------------------------------------------------------------- 可微路径

def test_margin_gap_is_differentiable_in_delta_and_geometry():
    """delta 本身是一个导数通道：d(裕度间隙)/d(delta) 恒为 -1；几何通道走 G3 收敛阶。"""
    A, L = interlocking_pair(nx=4, ny=2, amp=0.25)
    off = (0.008, -0.01, 0.30)
    sep = A.translated(off)
    assert polyhedra_overlap(sep, L, 1e-12) == -1
    _, lab = body_distance(sep, L)
    assert lab is not None and lab[0] in ("VF", "FV", "EE", "VV3")
    sign = 1.0
    if lab[0] == "EE":
        sign = frozen_ee_sign(sep, L, (lab[1][1], lab[1][2]), (lab[2][1], lab[2][2]))
    delta0, amp0 = 0.05, 0.25

    def g_of(theta):
        Ad, Ld = interlocking_pair_generic(nx=4, ny=2, amp=theta[1])
        return val(margin_gap_from_frozen_cover(Ad, Ld, lab, off, theta[0], ee_sign=sign))

    W = 2
    Ad, Ld = interlocking_pair_generic(nx=4, ny=2, amp=Dual.seed(amp0, W, 1), sin_fn=D.sin)
    g = margin_gap_from_frozen_cover(Ad, Ld, lab, off, Dual.seed(delta0, W, 0), ee_sign=sign)
    assert abs(g.v - g_of([delta0, amp0])) < 1e-12
    assert g.e[0] == pytest.approx(-1.0, abs=1e-15)
    rep = convergence_order(g_of, [delta0, amp0], list(g.e),
                            hs=(1e-1, 5e-2, 2.5e-2, 1e-4, 1e-6))
    assert rep["valley_error"] < 1e-9, rep


def test_gate_has_teeth_wrong_delta_sign_is_caught():
    A, B = _small_convex_pair()
    At = A.translated((0.0, 0.0, 1.2))
    d0, lab = body_distance(At, B)
    bad = margin_gap_from_frozen_cover(At, B, lab, (0.0, 0.0, 0.0), -0.05)
    good = margin_gap_from_frozen_cover(At, B, lab, (0.0, 0.0, 0.0), 0.05)
    assert abs(good - (d0 - 0.05)) < 1e-9
    assert abs(bad - (d0 - 0.05)) > 0.09
