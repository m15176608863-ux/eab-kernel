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
