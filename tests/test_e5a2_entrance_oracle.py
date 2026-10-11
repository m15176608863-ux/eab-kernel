"""Independent ray oracle self-check: analytic asymmetric boxes, no geometry API."""
from fractions import Fraction as F
from itertools import product
import pytest

from e5a2_entrance_oracle import convex_overlap, convex_ray_interval


@pytest.mark.parametrize("scale,origin", [(F(1, 1024), 0), (F(1), 10**6), (F(1024), -10**6)])
def test_exact_continuous_sat_ray_oracle_has_closed_form_endpoints(scale, origin):
    a = [(origin+scale*x, -origin+scale*y, origin+scale*z)
         for x, y, z in product((-1, 1), (-2, 2), (-3, 3))]
    b = [(origin+scale*x, -origin+scale*y, origin+scale*z)
         for x, y, z in product((3, 5), (-1, 1), (-1, 1))]
    assert convex_overlap(a, b) == -1
    interval = convex_ray_interval(a, b, (0, 0, 0), (2*scale, 0, 0), 10)
    assert interval == (F(1), F(3))
    assert convex_ray_interval(a, b, (0, 0, 0), (-2*scale, 0, 0), 10) is None
    for t, want in ((F(0), -1), (F(1), 0), (F(2), 1), (F(3), 0), (F(4), -1)):
        moved = [(x+2*scale*t, y, z) for x, y, z in a]
        assert convex_overlap(moved, b) == want
