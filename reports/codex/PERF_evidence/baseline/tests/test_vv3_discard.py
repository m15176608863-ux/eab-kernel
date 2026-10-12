"""VV3 的"是不是 E 的顶点"只按舍入噪声丢弃，不按调用方角容差（G6 第五轮 minor，2026-10-10）。"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eab.kernel3d.geom3 import Polyhedron, box, brute_feature_distance  # noqa: E402
from eab.margin import body_distance  # noqa: E402


@pytest.mark.parametrize("psi", (1e-11, 1e-10, 1e-9, 3e-9))
def test_corner_to_corner_pair_with_a_thin_cone_wedge_is_measured(psi):
    """A = 单位方块（半宽 1）偏航 psi，其 (−x, +y, −z) 角放在 B 的 (+, +, +) 角外 (0.1, psi·0.05, 0.1)：两角的分离方向落在只有
    psi 宽的锥交楔里（锥裕度 5e-12 … 1.5e-9，噪声 2.2e-14）。旧判据把调用方 tol = 1e-9 当丢弃阈值，psi ≤ 1e-9 时这对 VV3 被丢，
    裕度层自校验抛"漏了最近对"。"""
    B = box()
    g = 0.1
    cs, sn = math.cos(psi), math.sin(psi)
    rc = (cs * -1.0 - sn * 1.0, sn * -1.0 + cs * 1.0, -1.0)
    corner = (1.0 + g, 1.0 + psi * g / 2, 1.0 + g)
    c = tuple(corner[i] - rc[i] for i in range(3))
    A = Polyhedron([(c[0] + cs * x - sn * y, c[1] + sn * x + cs * y, c[2] + z) for x, y, z in box().verts], list(box().faces))
    d, lab = body_distance(A, B)
    assert abs(d - brute_feature_distance(A, B)) <= 1e-12
    assert lab is not None and lab[0] in ("VV3", "EE", "VE3", "EV3"), lab     # 角点处同距的盖按枚举序裁决
