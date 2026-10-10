"""近竖直墙面的盖不许给逃逸高度（G6 第五轮 critical，2026-10-10）。

U 形槽里的键贴着两侧竖墙、底面压进槽底 0.2。墙面盖的 n_z 在工程坐标下是 ~1e-11 的纯舍入；旧判据按绝对阈值 1e-12
把它当"朝上"，z = −gap/n_z 是垃圾高度，又在接受高度的并列组里按枚举序胜出，报 0.99 / 0.58 / 0.35（真值 0.2）。
修：n_z 必须超过盖法向自身的方向噪声（面法向噪声 / EE 候选的 (n_A + n_B)/sinθ）；height 取谓词接受的候选高度。
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eab.kernel3d.geom3 import Polyhedron, box  # noqa: E402
from eab.kernel3d.interlock import (escape_height_brute, escape_height_covers, escape_height_from_frozen_cover,  # noqa: E402
                                    frozen_ee_sign)

U_PROF = [(-2, -1), (2, -1), (2, 1), (1, 1), (1, 0), (-1, 0), (-1, 1), (-2, 1)]   # 槽底 z = 0（|x| < 1），竖墙 x = ±1 到 z = 1
DIR = (0.6, -0.48, 0.64)


def _prism_xz(prof, y0, y1):
    n = len(prof)
    v = [(float(x), float(y0), float(z)) for x, z in prof] + [(float(x), float(y1), float(z)) for x, z in prof]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    P = Polyhedron(v, faces)
    return P if P.volume() > 0 else Polyhedron(v, [tuple(reversed(f)) for f in faces])


def _key():
    A0 = box(center=(0.0, 0.0, 0.3), half=(1.0, 0.5, 0.5))                   # 贴两墙、压进槽底 0.2
    return Polyhedron([(-p[0], p[1], p[2]) for p in A0.verts], [tuple(reversed(f)) for f in A0.faces])   # 顶点 0 在 x = +1 侧


def _place(P, th, t, rng, ulps):
    """绕 z 转 th、平移到 |t|，每个坐标再加 ±ulps 个 ulp 的独立舍入（DDA 更新或导出的顶点就是这样）。"""
    c, s = math.cos(th), math.sin(th)
    return Polyhedron([tuple(x + rng.randint(-ulps, ulps) * math.ulp(x) for x in
                             (c * p[0] - s * p[1] + t * DIR[0], s * p[0] + c * p[1] + t * DIR[1], p[2] + t * DIR[2]))
                       for p in P.verts], list(P.faces))


@pytest.mark.parametrize("t,ulps", [(1e5, 4), (1e4, 1), (1e3, 4), (0.0, 0)])
def test_vertical_walls_do_not_hijack_the_escape_height(t, ulps):
    L0, Am = _prism_xz(U_PROF, -1.0, 1.0), _key()
    for seed in range(20):
        rng = random.Random(seed)
        A, L = _place(Am, 0.7, t, rng, ulps), _place(L0, 0.7, t, rng, ulps)
        sol = escape_height_covers(A, L, (0.0, 0.0, 0.0))
        assert abs(sol.height - 0.2) <= 1e-6, (seed, sol.height, sol.cover_label)
        lab = sol.cover_label
        assert lab[0] in ("VF", "FV", "EE")
        # 胜出盖必须是真正决定高度的那个：它的冻结闭式也给 0.2（墙面盖胜出时冻结闭式是 −gap/n_z 的垃圾，导数无意义）
        sg = frozen_ee_sign(A, L, (lab[1][1], lab[1][2]), (lab[2][1], lab[2][2])) if lab[0] == "EE" else 1.0
        zf = float(escape_height_from_frozen_cover(A, L, lab, (0.0, 0.0, 0.0), ee_sign=sg))
        assert abs(zf - 0.2) <= 1e-6, (seed, lab, zf)
        if seed < 3:
            assert abs(sol.height - escape_height_brute(A, L, (0.0, 0.0, 0.0), hi=2.0)) <= 1e-6
