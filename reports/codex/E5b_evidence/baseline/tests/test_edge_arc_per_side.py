"""棱弧（两相邻面法向张成的楔）判据按**逐侧**允差（G6 第五轮 critical，2026-10-10）。

旧判据 a1 + a2 ≤ w + tol + f1 + f2 是对称和：越过 x 面法向 1.41e-3 rad 的方向，借倒角三角面的噪声 f2 = 2.2e-3 混进楔内，
再按 x 面自己的噪声被判"严格"；local_facets3 多出假严格 EE，membership_convex3 对真相交位形答"分离"（假间隙 +1.9e-3，
所称分辨率 ~1.4e-9 的 1e6 倍），而 G0 因"局部 EE 特征高度 ≤ 4·eps 记说不清"照绿。改为越过 n1 只许 tol + f1、越过 n2 只许 tol + f2。
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from eab.kernel3d.covers3 import local_facets3, membership_convex3  # noqa: E402
from eab.kernel3d.geom3 import Polyhedron, add, box, convex_hull_3d, merge_coplanar, mul, polyhedra_overlap, sub  # noqa: E402
from test_invariance_geom import Motion  # noqa: E402


def _chamfered_on_box(e, yaw=1e-3):
    """单位方块截掉 (1,1,0) 角（三条长 e·√2 的棱），绕竖轴偏航 yaw，叠在单位方块上方 0.1。"""
    pts = [(x, y, z) for x in (0.0, 1.0) for y in (0.0, 1.0) for z in (0.0, 1.0)]
    pts.remove((1.0, 1.0, 0.0))
    pts += [(1 - e, 1.0, 0.0), (1.0, 1 - e, 0.0), (1.0, 1.0, e)]
    A0 = merge_coplanar(convex_hull_3d(pts))
    c, s = math.cos(yaw), math.sin(yaw)
    A0 = Polyhedron([(0.5 + c * (x - 0.5) - s * (y - 0.5), 0.5 + s * (x - 0.5) + c * (y - 0.5), z + 1.1) for x, y, z in A0.verts],
                    list(A0.faces))
    return A0, box(center=(0.5, 0.5, 0.5), half=(0.5, 0.5, 0.5))


@pytest.mark.parametrize("e", (1e-6, 1e-5))
@pytest.mark.parametrize("rot,t", [(0, 0.0), (0, 1e5), (3, 1e5), (7, 1e5), (11, 1e5), (0, 1e6)])
def test_membership_never_says_separated_where_the_bodies_intersect(e, rot, t):
    """从 E 的每个"b_0 − a_i"顶点向差点集质心走 1e-4 … 1.5e-3：谓词答相交（1）处，凸 E 的成员判定不许答 −1。"""
    A0, B0 = _chamfered_on_box(e)
    M = Motion(rot, t, 1.0)
    A, B = M.poly(A0), M.poly(B0)
    F = local_facets3(A, B, 1e-12)
    diffs = [sub(b, a) for a in A.verts for b in B.verts]
    cen = mul([sum(p[i] for p in diffs) for i in range(3)], 1.0 / len(diffs))
    bad = []
    for ia in range(len(A.verts)):
        v = sub(B.verts[0], A.verts[ia])
        for k in (1e-4, 5e-4, 1e-3, 1.5e-3):
            x = add(v, mul(sub(cen, v), k))
            if polyhedra_overlap(A.translated(x), B, 3.5e-12) == 1 and membership_convex3(A, B, x, 1e-7, F) == -1:
                bad.append((ia, k))
    assert not bad, bad
