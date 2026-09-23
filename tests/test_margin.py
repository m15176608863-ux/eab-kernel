"""L2 裕度层的门：四条定理各有一道，外加牙。"""

import functools
import math
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from osteomorphic import interlocking_pair, interlocking_pair_generic  # noqa: E402

from eab import dual as D  # noqa: E402
from eab.dual import Dual, convergence_order, val  # noqa: E402
from eab.kernel3d.covers3 import cone_relint_direction, vertex_cone_contains  # noqa: E402
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


def test_theorem_two_gate_has_teeth_shrinking_the_nearest_point_is_caught(monkeypatch):
    """定理二那道门的牙（reports/margin_layer.md 记为"把 E 的最近点缩 1% → 全部样本被抓"，此前无测试）：
    把凸 oracle 的最近点缩 1%，同一采样下每一个分离样本的 |d_config − d_body| 检验都必须失败。"""
    import eab.margin as M
    true_nearest = M.nearest_point_on_convex_entrance
    monkeypatch.setattr(M, "nearest_point_on_convex_entrance",
                        lambda E, x: tuple(0.99 * c for c in true_nearest(E, x)))
    A, B = _small_convex_pair()
    E = entrance_block_convex(A, B)
    rng = random.Random(0)
    n = caught = 0
    for _ in range(60):
        x = (rng.uniform(-2.2, 2.2), rng.uniform(-2.2, 2.2), rng.uniform(-2.2, 2.2))
        At = A.translated(x)
        if polyhedra_overlap(At, B, 1e-12) != -1:
            continue
        n += 1
        d_body, _ = body_distance(At, B)
        caught += abs(distance_to_convex_entrance(E, x) - d_body) >= 1e-9
    assert n > 40 and caught == n, (n, caught)


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

# 探针点集是确定性的；真实法向带备忘（每次 inflated_normal ~11 ms，全部探针点 ~400 个）
_TRUE_INFLATED_NORMAL = inflated_normal
_TRUE_MEMO: dict = {}


def _true_normal(E, x):
    if x not in _TRUE_MEMO:
        _TRUE_MEMO[x] = _TRUE_INFLATED_NORMAL(E, x)
    return _TRUE_MEMO[x]


def _lipschitz_probe_points(E, delta):
    """(局部差商点对, 闭环相邻点对)。全部点都在 {dist ≥ δ}（局部点对的第二点可内移 h）。

    · 随机基点 12 个：δ ≤ dist ≤ 3δ；
    · E 顶点基点：v + δ·d，d = 该顶点法锥的相对内部方向（非极点的共线/共面凸包点法锥退化，跳过）
      ——法向变化最快的位置，理论商恰为 1/δ；
    · 每个基点 6 个随机方向，步长 h = 1e-3·δ（局部差商，不再被点对间距稀释）；
    · 三个坐标平面上、以 E 顶点均值为心、半径 rmax + δ 的闭环（dist ≥ δ 由三角不等式保证），
      相邻点间距 ≤ 0.15：Lipschitz 场沿闭环不许有跳变（局部差商看不见的"局部反号"类错误在这里现形）。
    """
    rng = random.Random(11)
    bases = []
    while len(bases) < 12:
        x = (rng.uniform(-2.5, 2.5), rng.uniform(-2.5, 2.5), rng.uniform(-2.5, 2.5))
        if delta <= distance_to_convex_entrance(E, x) <= 3.0 * delta:
            bases.append(x)
    n_vertex = 0
    for vi, v in enumerate(E.verts):
        d = cone_relint_direction(E.vertex_edge_dirs(vi))
        if d is None:
            continue
        assert vertex_cone_contains(E, vi, d, 1e-9) == 1
        bases.append(tuple(v[k] + delta * d[k] for k in range(3)))
        n_vertex += 1
    assert n_vertex >= 10, n_vertex
    h = 1e-3 * delta
    local = []
    for x in bases:
        for _ in range(6):
            e = unit((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1)))
            local.append((x, tuple(x[k] + h * e[k] for k in range(3))))
    c = tuple(sum(v[k] for v in E.verts) / len(E.verts) for k in range(3))
    R = max(norm(sub(v, c)) for v in E.verts) + delta
    m = int(math.ceil(2.0 * math.pi * R / 0.15))
    loops = []
    for u, w in ((0, 1), (1, 2), (2, 0)):
        ring = []
        for i in range(m):
            p = list(c)
            p[u] += R * math.cos(2.0 * math.pi * i / m)
            p[w] += R * math.sin(2.0 * math.pi * i / m)
            ring.append(tuple(p))
        loops += [(ring[i], ring[(i + 1) % m]) for i in range(m)]
    return local, loops


def _lipschitz_worst(normal_fn, E, pairs):
    worst = 0.0
    for x, y in pairs:
        worst = max(worst, norm(sub(normal_fn(E, x), normal_fn(E, y))) / norm(sub(x, y)))
    return worst


def _legacy_global_pairs(E, delta):
    """审查前那道门的 66 个全局点对，构造原样保留（rng = Random(11)，12 个 δ ≤ dist ≤ 3δ 的随机点两两配对）。

    它检的是**非局部**点对上的 Lipschitz 上界，局部差商与闭环都不覆盖这部分，所以并入上界判据、不删。
    对任何单位向量场它单独无牙（最小间距 > δ，见 test_inflated_normal_is_lipschitz 里对此的断言）；
    它抓得住的是非单位的区域性错误（test_lipschitz_gate_global_pairs_have_their_own_teeth）。
    单位向量类错误的牙在局部差商 + 下界 + 闭环。
    """
    rng = random.Random(11)
    pts = []
    while len(pts) < 12:
        x = (rng.uniform(-2.5, 2.5), rng.uniform(-2.5, 2.5), rng.uniform(-2.5, 2.5))
        d = distance_to_convex_entrance(E, x)
        if delta <= d <= 3.0 * delta:
            pts.append(x)
    pairs = []
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            if norm(sub(pts[i], pts[j])) > 0:
                pairs.append((pts[i], pts[j]))
    return pairs


@functools.lru_cache(maxsize=None)
def _lipschitz_setup(delta):
    A, B = _small_convex_pair()
    E = entrance_block_convex(A, B)
    return (E,) + _lipschitz_probe_points(E, delta) + (_legacy_global_pairs(E, delta),)


def _lipschitz_verdict(normal_fn, delta=0.25):
    """定理四的双边门。

    上界（Lipschitz，常数 2/δ，容差 1e-9 与原门相同）查**全部**点对：局部差商 ∪ 闭环 ∪ 原门 66 个全局点对；
    紧性下界（≥ 0.9/δ，顶点处真实值 = 1/δ）只看局部 ∪ 闭环——把全局点对并进下界只会让下界更松，故不并。
    返回 ((局部∪闭环最坏商, 全局点对最坏商), 是否通过)。
    """
    E, local, loops, glob = _lipschitz_setup(delta)
    w_local = max(_lipschitz_worst(normal_fn, E, local), _lipschitz_worst(normal_fn, E, loops))
    w_global = _lipschitz_worst(normal_fn, E, glob)
    ok = max(w_local, w_global) <= 2.0 / delta + 1e-9 and w_local >= 0.9 / delta
    return (w_local, w_global), ok


def test_inflated_normal_is_lipschitz():
    """凸集投影非扩张 => 膨胀法向 Lipschitz，常数 <= 2/delta；且在 E 顶点处**紧**（商 >= 0.9/delta）。

    旧门（12 个点两两求商）对单位向量场单独无牙：点对最小间距 0.42 ≫ δ，任何单位向量函数的商都 ≤ 2/0.42 ≈ 4.81 < 8
    （下面第一组断言把这句钉死）。它的 66 个点对与 1e-9 容差**原样保留**在上界判据里；
    牙来自新增的局部差商 + 顶点基点 + 闭环扫描 + 紧性下界，见下一条测试。
    oracle（纪律 A）：判据的两条界来自定理（投影非扩张 ⇒ ≤ 2/δ；顶点法锥内 n 以 1/dist 转动 ⇒
    顶点基点处 = 1/δ），不来自任何实现。共用：随机基点的筛选用了 distance_to_convex_entrance
    （与被测 inflated_normal 同一个最近点例程）——它只决定"在哪儿探"，不参与判据；
    顶点基点与闭环点的位置由法锥方向与三角不等式构造，不经过最近点例程。
    """
    delta = 0.25
    _, _, _, glob = _lipschitz_setup(delta)
    assert len(glob) == 66
    dmin = min(norm(sub(x, y)) for x, y in glob)
    assert 2.0 / dmin < 4.82 < 2.0 / delta, dmin          # 旧门单独无牙的原因（任何单位向量场都过）
    fn = _true_normal if inflated_normal is _TRUE_INFLATED_NORMAL else inflated_normal
    (w_local, w_global), ok = _lipschitz_verdict(fn, delta)
    assert w_global <= 2.0 / delta + 1e-9, w_global       # 原门断言，原样
    assert w_local <= 2.0 / delta + 1e-9, w_local
    assert w_local >= 0.9 / delta, w_local
    assert ok


def test_lipschitz_gate_has_teeth():
    """门要有牙：审查列出的四种错误实现必须全部被双边门抓住。

    随机单位向量（上界破）、常向量（紧性下界破）、径向 unit(x)（下界破）、
    x[0] > 0 处法向反号（局部差商看不见，闭环扫描上跳变 2/0.15 ≫ 2/δ）。
    """
    rng = random.Random(99)
    mutants = {
        "random": lambda E, x: unit((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))),
        "constant": lambda E, x: (1.0, 0.0, 0.0),
        "radial": lambda E, x: unit(x),
        "local_flip": lambda E, x: (tuple(-c for c in _true_normal(E, x)) if x[0] > 0.0
                                    else _true_normal(E, x)),
    }
    for name, fn in mutants.items():
        worst, ok = _lipschitz_verdict(fn)
        assert not ok, f"错误实现 {name} 没被抓住：(局部∪闭环, 全局) worst = {worst}"


def test_lipschitz_gate_global_pairs_have_their_own_teeth():
    """原门的 66 个全局点对不是摆设（把"局部差商与闭环不覆盖非局部点对"这句钉死）：

    在最近一对全局点的一端 p0 的 1e-3 球内给法向加常向量 (10,0,0)（区域性的归一化失误）。
    以 p0 为起点的局部差商两点同在球内（h = 2.5e-4）、偏移相同；其余探针点与闭环离 p0 都 > 0.1（实测 ≥ 0.33）
    ⇒ 局部 ∪ 闭环的最坏商与真实实现逐位相同、落在 [0.9/δ, 2/δ] 内；只有全局点对看得见跳变（≥ 8/0.42 ≈ 19 > 2/δ）。
    """
    delta = 0.25
    E, local, loops, glob = _lipschitz_setup(delta)
    p0 = min(glob, key=lambda xy: norm(sub(xy[0], xy[1])))[0]
    assert min(norm(sub(q, p0)) for pr in loops for q in pr) > 0.1
    assert min(norm(sub(q, p0)) for pr in local if pr[0] != p0 for q in pr) > 0.1

    def bump(E, x):
        n = _true_normal(E, x)
        return (n[0] + 10.0, n[1], n[2]) if norm(sub(x, p0)) < 1e-3 else n

    (w_local, w_global), ok = _lipschitz_verdict(bump, delta)
    (w_true, _), _ = _lipschitz_verdict(_true_normal, delta)
    assert w_local == w_true and 0.9 / delta <= w_local <= 2.0 / delta, (w_local, w_true)   # 局部 ∪ 闭环看不见
    assert w_global > 2.0 / delta and not ok, w_global         # 全局点对抓住


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
    # 原断言原样保留（不放松）：这个手选偏移落在 VF/FV 并列集上（8 个等距盖全是 VF/FV）。
    # 它描述的是本测试的输入，不是冻结路径的能力边界——VE3/EV3 已有分支，
    # 全部种类（含 VE3/EV3）的批量门见 tests/test_frozen_lowdim.py。
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
