"""暴力相交谓词 `polyhedra_overlap` 漏判薄片交集——审查 C9（major）。

缺陷：每个顶点都落在对方的面平面上、且没有棱严格穿过面内部时（L 块凹槽里咬进一层薄片、
z 范围重合的方块），前三步证人（顶点在内 / 棱穿面 / 各自内点）全空，兜底的 5×5×5 网格 +
60 个随机点撒在 AABB 交集（~2×2×1）里，而真交集只有 ~e×2×1 厚——e ≲ 0.01 就漏，返回 0（相触）。
修法：网格之前加一步"**相触顶点沿内法向和微推**"证人——一个相触顶点沿其关联面外法向之和的
反方向推进一小段，若落在两体严格内部即为证人（只可能修正假阴性，不可能造成假阳性）。

oracle（纪律 A）：L = [0,3]×[0,1]×[0,1] ∪ [0,1]×[0,3]×[0,1]，方块轴对齐 ⇒ 交集体积闭式
（容斥：|B∩R1| + |B∩R2| − |B∩R1∩R2|）；体积 > 0 → 1，闭包相交 → 0，否则 −1。只用算术。
纪律 B：分界（e = 0 恰好填满凹槽 → 0；e < 0 留缝 → −1）、非对称（只咬一面墙、两面咬深不同）、
尺度 ×1e-3 / ×1 / ×1e3 与一般朝向（随机旋转）。

注：计划书写"咬 ~0.05、体积 0.012"——两者不对应：体积 0.012 对应 e = 0.003（4e + e²）；
e = 0.05 旧实现本来就能判出。这里按审查实测的盲区取 e ∈ {0.01, 0.003, 1e-4, 1e-6}。
"""

import math
import random

import pytest

from eab.kernel3d.geom3 import Polyhedron, polyhedra_overlap

L_BASE = [(0.0, 0.0), (3.0, 0.0), (3.0, 1.0), (1.0, 1.0), (1.0, 3.0), (0.0, 3.0)]
R1 = ((0.0, 0.0, 0.0), (3.0, 1.0, 1.0))
R2 = ((0.0, 0.0, 0.0), (1.0, 3.0, 1.0))


def _rotation(seed: int):
    if seed == 0:
        return ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    rng = random.Random(4000 + seed)
    q = [rng.gauss(0.0, 1.0) for _ in range(4)]
    n = math.sqrt(sum(c * c for c in q))
    w, x, y, z = (c / n for c in q)
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


def _place(verts, seed, scale):
    R = _rotation(seed)
    o = (0.0, 0.0, 0.0) if seed == 0 else (1.3 * scale, 0.4 * scale, -2.1 * scale)
    return [tuple(o[i] + scale * (R[i][0] * p[0] + R[i][1] * p[1] + R[i][2] * p[2]) for i in range(3))
            for p in verts]


def _l_block(seed, scale):
    n = len(L_BASE)
    v = [(x, y, 0.0) for x, y in L_BASE] + [(x, y, 1.0) for x, y in L_BASE]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, j + n, i + n))
    return Polyhedron(_place(v, seed, scale), faces)


def _box(lo, hi, seed, scale):
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return Polyhedron(_place(v, seed, scale), f)


def _ov(lo1, hi1, lo2, hi2):
    return [min(hi1[i], hi2[i]) - max(lo1[i], lo2[i]) for i in range(3)]


def _truth(lo, hi):
    """闭式：与 L 的交集体积（容斥）→ 1 / 0 / −1。"""
    def vol(ov):
        return math.prod(max(0.0, d) for d in ov)
    v = vol(_ov(lo, hi, *R1)) + vol(_ov(lo, hi, *R2)) - vol(_ov(lo, hi, (0, 0, 0), (1, 1, 1)))
    if v > 0.0:
        return 1, v
    touch = any(all(d >= 0.0 for d in _ov(lo, hi, *R)) for R in (R1, R2))
    return (0 if touch else -1), 0.0


CASES = [
    # (名称, 凹槽方块 lo, hi)
    ("bite_e0.01", (0.99, 0.99, 0.0), (3.0, 3.0, 1.0)),
    ("bite_e0.003", (0.997, 0.997, 0.0), (3.0, 3.0, 1.0)),
    ("bite_e1e-4", (1 - 1e-4, 1 - 1e-4, 0.0), (3.0, 3.0, 1.0)),
    ("bite_e1e-6", (1 - 1e-6, 1 - 1e-6, 0.0), (3.0, 3.0, 1.0)),
    ("bite_x_only", (0.995, 1.0, 0.0), (3.0, 3.0, 1.0)),        # 只咬 x=1 那面墙
    ("bite_uneven", (0.9995, 0.98, 0.0), (3.4, 2.5, 1.0)),      # 两面咬深不同、方块伸出 L 外
    ("exact_fill", (1.0, 1.0, 0.0), (3.0, 3.0, 1.0)),           # 分界：恰好填满 → 相触
    ("gap", (1.001, 1.002, 0.0), (3.0, 3.0, 1.0)),              # 留缝 → 分离
]


@pytest.mark.parametrize("seed,scale", [(0, 1.0), (0, 1e-3), (0, 1e3), (1, 1.0), (2, 1e3)])
@pytest.mark.parametrize("name,lo,hi", CASES, ids=[c[0] for c in CASES])
def test_thin_notch_bite_is_detected(name, lo, hi, seed, scale):
    want, vol = _truth(lo, hi)
    if name.startswith("bite"):
        assert want == 1 and vol > 0.0
    L = _l_block(seed, scale)
    B = _box(lo, hi, seed, scale)
    tol = 1e-12 * scale
    assert polyhedra_overlap(L, B, tol) == want, (name, vol)
    assert polyhedra_overlap(B, L, tol) == want, (name, vol)


def test_audit_case_volume_is_0_012():
    """审查原例的数值：e = 0.003 ⇒ 交集体积 4e + e² = 0.012009。"""
    want, vol = _truth((0.997, 0.997, 0.0), (3.0, 3.0, 1.0))
    assert want == 1 and abs(vol - 0.012009) < 1e-12
    assert polyhedra_overlap(_l_block(0, 1.0), _box((0.997, 0.997, 0.0), (3.0, 3.0, 1.0), 0, 1.0), 0.0) == 1


# ================================================================ G6 critical 5 / 10：共面交叉（X 形等高板）
#
# 缺陷（G6 2026-09-24，critical 5 + critical 10）：两块等高板 X 形交叉、真实贯入，但
#   · 没有任何顶点在对方体内或体面上（touching=False，微推证人无起点）；
#   · 每条可能穿面的棱都躺在对方的顶/底面平面里（dp = dq = 0），严格穿面判据全部拒绝；
#   · 网格与随机点撒在 AABB 交集里，而真交集是一根细柱——漏掉，返回 −1（分离）。
# margin 层的贯入守卫依赖它，于是 body_distance 报正距离、margin_contacts 返回 []、
# inflated_membership 答 OUTSIDE：C14 的 fail-unsafe 回来了。
#
# oracle（纪律 A）：**分离轴定理**，在本测试里用解析的板中心、板轴与半宽直接写成，
# 不调用 geom3 / covers3 的任何原语：两个有向方块（OBB）的内部相交 ⟺ 15 条候选轴
# （各自 3 条面法向 + 9 条棱方向叉积）上投影区间都**严格**重叠；分离量
#     σ(L) = |(c_B − c_A)·L| − Σ h_A,i |u_A,i·L| − Σ h_B,j |u_B,j·L|      （L 单位化）
# max_L σ < 0 ⟺ 贯入；= 0 ⟺ 相触；> 0 ⟺ 分离。
# 纪律 B：分界（抬起恰一个板厚 → 相触 0；再抬 → −1）、非对称（宽度比、偏心交点、只咬一角）、
# 尺度 ×1e-3 / ×1e3、一般朝向（随机旋转）、工程坐标（平移 1e5）。

from eab.kernel3d.geom3 import point_in_polyhedron  # noqa: E402
from eab.margin import INSIDE, PENETRATING, body_distance, inflated_membership, margin_contacts  # noqa: E402


def _qrot(seed: int):
    if seed == 0:
        return ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    rng = random.Random(5100 + seed)
    q = [rng.gauss(0.0, 1.0) for _ in range(4)]
    n = math.sqrt(sum(c * c for c in q))
    w, x, y, z = (c / n for c in q)
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


class OBB:
    """解析有向方块：中心 c、正交轴 u[0..2]、半宽 h。只用算术。"""

    def __init__(self, c, u, h):
        self.c, self.u, self.h = tuple(c), [tuple(a) for a in u], tuple(h)

    @staticmethod
    def slab(theta: float, c, h):
        ct, st = math.cos(theta), math.sin(theta)
        return OBB(c, [(ct, st, 0.0), (-st, ct, 0.0), (0.0, 0.0, 1.0)], h)

    def moved(self, R, t, s):
        def rv(v):
            return tuple(R[i][0] * v[0] + R[i][1] * v[1] + R[i][2] * v[2] for i in range(3))
        c = rv(self.c)
        return OBB(tuple(t[i] + s * c[i] for i in range(3)), [rv(a) for a in self.u],
                   tuple(s * x for x in self.h))

    def poly(self) -> Polyhedron:
        V = []
        for sx, sy, sz in ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                           (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)):
            V.append(tuple(self.c[i] + sx * self.h[0] * self.u[0][i] + sy * self.h[1] * self.u[1][i]
                           + sz * self.h[2] * self.u[2][i] for i in range(3)))
        f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        return Polyhedron(V, f)


def _sat_sigma(P: OBB, Q: OBB) -> float:
    """max over the SAT axes of the separation σ（>0 分离，<0 贯入，=0 相触）。纯算术。"""
    def dot(a, b):
        return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

    def cross(a, b):
        return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])

    axes = list(P.u) + list(Q.u)
    for a in P.u:
        for b in Q.u:
            c = cross(a, b)
            n = math.sqrt(dot(c, c))
            if n > 1e-9:
                axes.append(tuple(x / n for x in c))
    d = tuple(Q.c[i] - P.c[i] for i in range(3))
    best = -math.inf
    for L in axes:
        rP = sum(P.h[i] * abs(dot(P.u[i], L)) for i in range(3))
        rQ = sum(Q.h[i] * abs(dot(Q.u[i], L)) for i in range(3))
        best = max(best, abs(dot(d, L)) - rP - rQ)
    return best


# (名称, θ_A, 中心_A, 半宽_A, θ_B, 中心_B, 半宽_B)：全部等高（z 半宽相同、z 中心相同）
X_CASES = [
    ("g6_repro", 0.7123231161619232, (-0.08666247398702509, -0.28261190955518073, 0.0), (1.0, 0.1, 0.5),
     2.3208944052154075, (0.0, 0.0, 0.0), (1.0, 0.1, 0.5)),
    ("aspect_3_to_0.1", 0.3, (0.4, -0.2, 0.0), (3.0, 0.1, 0.5), 1.9, (-0.3, 0.1, 0.0), (3.0, 0.1, 0.5)),
    ("width_ratio_1_to_5", 0.2, (0.0, 0.0, 0.0), (2.0, 0.05, 0.5), 1.4, (0.3, 0.2, 0.0), (2.0, 0.25, 0.5)),
    ("thin_0.025", 1.1, (0.0, 0.1, 0.0), (1.5, 0.025, 0.5), -1.1, (0.2, -0.1, 0.0), (1.5, 0.025, 0.5)),
    ("right_angle", 0.0, (0.0, 0.0, 0.0), (2.0, 0.1, 0.5), 0.5 * math.pi, (0.7, 0.0, 0.0), (2.0, 0.1, 0.5)),
    # 只咬一角：B 的端部斜着搭进 A 的一端（交集是一个角上的小楔柱）
    ("corner_bite", 0.0, (0.0, 0.0, 0.0), (1.0, 0.2, 0.5), 0.9,
     (1.0 + 0.6 * math.cos(0.9) - 0.05, 0.6 * math.sin(0.9) - 0.1, 0.0), (0.6, 0.1, 0.5)),
]
PLACEMENTS = [(0, (0.0, 0.0, 0.0), 1.0), (0, (0.0, 0.0, 0.0), 1e-3), (0, (0.0, 0.0, 0.0), 1e3),
              (1, (0.0, 0.0, 0.0), 1.0), (2, (6e4, -8e4, 1e3), 1.0), (3, (1e5, 3e4, -2e4), 1e3)]
PLACEMENT_IDS = [f"R{a}-t{max(abs(c) for c in b):g}-s{c:g}" for a, b, c in PLACEMENTS]


def _x_pair(case, seed, t, s):
    _, ta, ca, ha, tb, cb, hb = case
    R = _qrot(seed)
    return OBB.slab(ta, ca, ha).moved(R, t, s), OBB.slab(tb, cb, hb).moved(R, t, s)


@pytest.mark.parametrize("seed,t,s", PLACEMENTS, ids=PLACEMENT_IDS)
@pytest.mark.parametrize("case", X_CASES, ids=[c[0] for c in X_CASES])
def test_equal_height_x_crossing_is_penetration(case, seed, t, s):
    P, Q = _x_pair(case, seed, t, s)
    sigma = _sat_sigma(P, Q)
    assert sigma < -1e-3 * s, sigma                                   # oracle：真实贯入
    A, B = P.poly(), Q.poly()
    # 前提：审查说的盲区确实是这一类——没有任何顶点严格在对方体内
    assert all(point_in_polyhedron(p, B, 1e-9 * s) != 1 for p in A.verts)
    assert all(point_in_polyhedron(p, A, 1e-9 * s) != 1 for p in B.verts)
    for tol in (0.0, 1e-12 * s, 1e-9 * s):
        assert polyhedra_overlap(A, B, tol) == 1, tol
        assert polyhedra_overlap(B, A, tol) == 1, tol


@pytest.mark.parametrize("seed,t,s", PLACEMENTS, ids=PLACEMENT_IDS)
@pytest.mark.parametrize("case", X_CASES[:2], ids=[c[0] for c in X_CASES[:2]])
def test_x_crossing_lifted_boundaries(case, seed, t, s):
    """分界：B 抬起恰一个板厚（B 底面 = A 顶面，交叉处面面相触）→ 0；再抬 1e-3 → −1。"""
    name, ta, ca, ha, tb, cb, hb = case
    for dz, want in ((2 * ha[2], 0), (2 * ha[2] + 1e-3, -1)):
        lifted = (name, ta, ca, ha, tb, (cb[0], cb[1], cb[2] + dz), hb)
        P, Q = _x_pair(lifted, seed, t, s)
        sigma = _sat_sigma(P, Q)
        assert (sigma > 1e-4 * s) if want == -1 else abs(sigma) < 1e-9 * max(s, 1e-4 * max(abs(c) for c in t)), sigma
        A, B = P.poly(), Q.poly()
        assert polyhedra_overlap(A, B, 1e-9 * s) == want
        assert polyhedra_overlap(B, A, 1e-9 * s) == want


@pytest.mark.parametrize("half_x", [1.0, 2.0, 3.0])
def test_random_equal_height_crossings_match_sat(half_x):
    """G6 独立复核的扫描：y 半宽 0.1、z 半宽 0.5 的等高板随机交叉 40 次（种子 1），
    审查实测漏判 0/5/15（×40）。每一例都按 SAT 判真值（贯入 / 分离），双向断言。"""
    rng = random.Random(1)
    n_pen = 0
    for _ in range(40):
        ta, tb = rng.uniform(0.0, math.pi), rng.uniform(0.0, math.pi)
        ca = (rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), 0.0)
        cb = (rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), 0.0)
        P = OBB.slab(ta, ca, (half_x, 0.1, 0.5))
        Q = OBB.slab(tb, cb, (half_x, 0.1, 0.5))
        sigma = _sat_sigma(P, Q)
        if abs(sigma) < 1e-6:
            continue
        want = 1 if sigma < 0 else -1
        n_pen += want == 1
        A, B = P.poly(), Q.poly()
        assert polyhedra_overlap(A, B, 1e-9) == want, (ta, tb, ca, cb, sigma)
        assert polyhedra_overlap(B, A, 1e-9) == want, (ta, tb, ca, cb, sigma)
    assert n_pen >= 10, n_pen


@pytest.mark.parametrize("seed,s", [(0, 1.0), (0, 1e-3), (0, 1e3), (1, 1.0), (2, 1e-3), (3, 1e3)])
@pytest.mark.parametrize("hw", [0.1, 0.05, 0.025])
def test_margin_layer_answers_violated_on_coplanar_crossing(hw, seed, s):
    """G6 critical 10（margin.py:90；根因在 geom3.polyhedra_overlap，由本组负责，margin.py 不改）：
    等高交叉梁真实贯入时，裕度层三个入口一致地回答"已违约"，两个参数顺序都要。"""
    cb = (0.7 * math.cos(0.7) - 0.9 * math.cos(-0.7), 0.7 * math.sin(0.7) - 0.9 * math.sin(-0.7), 0.0)
    case = ("beams", 0.7, (0.0, 0.0, 0.0), (1.5, hw, 0.5), -0.7, cb, (1.5, hw, 0.5))
    P, Q = _x_pair(case, seed, (0.0, 0.0, 0.0), s)
    assert _sat_sigma(P, Q) < -0.5 * hw * s                         # oracle：贯入
    A, B = P.poly(), Q.poly()
    for X, Y in ((A, B), (B, A)):
        assert body_distance(X, Y) == (0.0, (PENETRATING,))
        ms = margin_contacts(X, Y, delta=0.5 * s)
        assert [m.label for m in ms] == [(PENETRATING,)] and ms[0].closed
        assert inflated_membership(X, Y, delta=0.5 * s) == INSIDE


@pytest.mark.parametrize("frame", ["identity", "shared_rotation", "independent_rotations"])
def test_overlap_is_exact_on_random_convex_pairs_with_coplanar_faces(frame):
    """docstring 的声称"凸体上内部相交 ⟹ 判 1 是精确的"的门：随机有向方块对，中心与半宽取在 0.25 的
    格点上——大量共面 / 共线 / 恰好相触的退化位形（正是采样漏判的那一类）。真值 = SAT（上面的 _sat_sigma）。
    identity：坐标全是二进制有限小数，σ 精确，恰相触（σ = 0）也断言判 0；
    shared_rotation：两块同一旋转（面仍两两平行 / 共面），|σ| < 1e-9 的跳过；
    independent_rotations：一般位置对照。"""
    rng = random.Random({"identity": 11, "shared_rotation": 12, "independent_rotations": 13}[frame])
    grid = [k * 0.25 for k in range(-6, 7)]
    halves = [0.25, 0.5, 0.75, 1.0]
    counts = {1: 0, 0: 0, -1: 0}
    for i in range(150):
        Ra = _qrot(0 if frame == "identity" else 300 + i)
        Rb = Ra if frame != "independent_rotations" else _qrot(600 + i)
        u_a = [tuple(Ra[r][c] for r in range(3)) for c in range(3)]
        u_b = [tuple(Rb[r][c] for r in range(3)) for c in range(3)]
        ca, cb = (tuple(rng.choice(grid) for _ in range(3)) for _ in range(2))
        ha, hb = (tuple(rng.choice(halves) for _ in range(3)) for _ in range(2))
        P = OBB(tuple(sum(Ra[r][k] * ca[k] for k in range(3)) for r in range(3)), u_a, ha)
        Q = OBB(tuple(sum(Ra[r][k] * cb[k] for k in range(3)) for r in range(3)), u_b, hb)
        sigma = _sat_sigma(P, Q)
        if frame == "identity":
            want = 1 if sigma < 0 else (0 if sigma == 0 else -1)
        else:
            if abs(sigma) < 1e-9:
                continue
            want = 1 if sigma < 0 else -1
        counts[want] += 1
        A, B = P.poly(), Q.poly()
        assert polyhedra_overlap(A, B, 1e-9) == want, (frame, i, sigma)
        assert polyhedra_overlap(B, A, 1e-9) == want, (frame, i, sigma)
    assert counts[1] >= 20 and counts[-1] >= 20, counts
    if frame == "identity":
        assert counts[0] >= 5, counts



# ---------------------------------------------------------------- M0.3（G6 第二轮两条 minor）

def _Rq(seed):
    rng = random.Random(seed)
    q = [rng.gauss(0, 1) for _ in range(4)]
    n = math.sqrt(sum(c * c for c in q))
    w, x, y, z = (c / n for c in q)
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


def _rigid(P, R):
    return Polyhedron([tuple(sum(R[i][j] * p[j] for j in range(3)) for i in range(3)) for p in P.verts], list(P.faces))


def _rotz(P, th, c=(0.0, 0.0, 0.0)):
    C, S = math.cos(th), math.sin(th)
    return Polyhedron([(C * x - S * y + c[0], S * x + C * y + c[1], z + c[2]) for x, y, z in P.verts], list(P.faces))


@pytest.mark.parametrize("seed", [0, 8, 13])
def test_rotated_thin_plates_crossing_are_overlapping_at_zero_tolerance(seed):
    """20 × 0.02 × 1 的两块细板 X 形交叉（真实贯入），整体刚体旋转后 tol = 0：旧版的活动面判据只用长度地板，
    薄面在棱-棱交点处的平面距离（法向噪声 × 力臂 ≈ 2.7e-13）超过地板 1.2e-13 被丢，答"接触"。"""
    from eab.kernel3d.geom3 import box
    a, b, o = 1.0683100556795084, 1.2782236262301914, (-1.49930015429593, -1.0462052031617162, 0.0)
    A0 = _rotz(box(half=(10.0, 0.01, 0.5)), a, o)
    B0 = _rotz(box(half=(10.0, 0.01, 0.5)), b)
    assert polyhedra_overlap(A0, B0) == 1
    R = _Rq(seed)
    A, B = _rigid(A0, R), _rigid(B0, R)
    assert polyhedra_overlap(A, B) == 1 and polyhedra_overlap(B, A) == 1


@pytest.mark.parametrize("ov,want", [(1e-10, 1), (1e-11, 1), (1e-13, 0), (1e-14, 0)])
def test_overlap_resolution_is_documented(ov, want):
    """文档写明的有效分辨率 max(tol_eff, 1e-12·diag)：两个单位方块面对面贯入 ov。深于它答 1，浅于它答 0（相触），
    从不答成 −1。"""
    from eab.kernel3d.geom3 import box
    A = box((0.0, 0.0, 0.0), (0.5, 0.5, 0.5))
    B = box((1.0 - ov, 0.0, 0.0), (0.5, 0.5, 0.5))
    assert polyhedra_overlap(A, B) == want
