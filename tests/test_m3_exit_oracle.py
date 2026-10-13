"""Independent Cartesian global-exit oracle, no production geometry primitive.

The union of two analytic rectangles is an L-shaped entrance set. Its six
boundary segments are listed directly, without triangulation, covers, hulls,
convolution or a global-construction helper. Fractions are the only shared
arithmetic. This finite family certifies neither arbitrary 3D PD nor PD_open.
"""
from fractions import Fraction as F

import pytest

from eab.kernel2d.global_entrance import GlobalEntrance2


@pytest.mark.parametrize("scale,shift", [(F(1, 1000), F(10**5)), (F(1), F(0)), (F(1000), F(-1000))])
def test_global_shortest_exit_matches_independent_l_union_boundary(scale, shift):
    w, h, arm, width, height = F(2, 5), F(1, 3), F(1, 10), F(3), F(4)
    A = [(0, 0), (w, 0), (w, h), (0, h)]
    B = [(0, 0), (width, 0), (width, arm), (arm, arm), (arm, height), (0, height)]
    # A and B undergo the same rigid translation: E is unchanged by shift.
    def body(P):
        return [(scale*x+shift, scale*y-3*shift) for x, y in P]
    model = GlobalEntrance2(body(A), body(B))
    boundary = [(-w, -h), (width, -h), (width, arm), (arm, arm), (arm, height), (-w, height)]
    points = [(F(0), F(0)), (F(1, 20), F(1, 20)), (F(-1, 10), F(2)),
              (F(2), F(-1, 5)), (arm, arm), (width, arm), (F(0), F(3))]
    distinct = set()
    for point in points:
        choices = []
        for a, b in zip(boundary, boundary[1:]+boundary[:1]):
            # Independent coordinate clamping (every segment is axis-aligned).
            q = tuple(max(min(a[k], b[k]), min(max(a[k], b[k]), point[k])) for k in (0, 1))
            square = sum((q[k]-point[k])**2 for k in (0, 1))
            choices.append((square, q))
        expected_square = min(square for square, _ in choices)
        expected_points = {tuple(scale*v for v in p) for square, p in choices if square == expected_square}
        answer = model.shortest_exit(tuple(scale*v for v in point))
        assert answer.squared == scale*scale*expected_square, "global PD_closed differs from analytic L boundary"
        assert answer.exact_point in expected_points, "nearest global exit witness is not analytic minimizer"
        assert model.topology(answer.exact_point) == 0
        distinct.add(answer.squared)
    assert len(distinct) >= 3, "the parameterized products must not collapse to one answer"
