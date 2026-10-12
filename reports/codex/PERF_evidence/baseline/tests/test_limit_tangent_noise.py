"""三维接触的显式切向与法向在舍入内平行时必须报错（G6 第五轮 minor，2026-10-10）。"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eab.limit import _tangents  # noqa: E402

N = tuple(1.0 / math.sqrt(3.0) for _ in range(3))


@pytest.mark.parametrize("tangent", [(1.0, 1.0, 1.0 + 2.0 ** -50), (1.0, 1.0, 1.0 - 2.0 ** -50), (2.0, 2.0, 2.0 + 2.0 ** -49),
                                     (-1e5, -1e5, -1e5 * (1.0 + 2.0 ** -50))])
def test_tangent_parallel_to_the_normal_within_rounding_is_rejected(tangent):
    """修前 (1, 1, 1 + 2⁻⁵⁰) 的投影是舍入垃圾、归一化后 n·t1 = 0.174，内接锥歪斜、α 高估 19%，不报错。"""
    with pytest.raises(ValueError, match="within rounding"):
        _tangents(N, 3, tangent)


@pytest.mark.parametrize("tangent", [(1.0, 0.0, 0.0), (1.0, 1.0, 1.0 + 1e-6), (0.3, -0.2, 5.0)])
def test_a_resolvable_tangent_gives_an_orthonormal_frame(tangent):
    t1, t2 = _tangents(N, 3, tangent)
    for a, b, want in ((t1, t1, 1.0), (t2, t2, 1.0), (t1, N, 0.0), (t2, N, 0.0), (t1, t2, 0.0)):
        assert abs(sum(x * y for x, y in zip(a, b)) - want) <= 1e-12
