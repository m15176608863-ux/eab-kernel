"""Minimal downstream adaptation; the escape semantics remain an E5b task."""
from fractions import Fraction as F
import math
from types import SimpleNamespace

from eab.kernel3d.geom3 import Polyhedron, cross, norm
from eab.kernel3d.interlock import _normal_noise


def test_normal_noise_handles_exact_cross_hidden_by_unit_vector_rounding():
    """Independent rational edge differences, not production cone primitives."""
    A = Polyhedron([(-0.5499999999999999, -0.5, 1.7321660590032764),
                    (-0.14999999999999997, -0.5, 1.3910452200557695)], [])
    B = Polyhedron([(-0.6, 0.5, 0.7321660590032764),
                    (-0.19999999999999996, 0.5, 0.3910452200557694)], [])
    edge = (0, 1)
    assert norm(cross(B.edge_dir(edge), A.edge_dir(edge))) == 0
    u = tuple(F(b) - F(a) for a, b in zip(A.verts[0], A.verts[1]))
    v = tuple(F(b) - F(a) for a, b in zip(B.verts[0], B.verts[1]))
    n = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
    sine_squared = sum(x*x for x in n) / (sum(x*x for x in u)*sum(x*x for x in v))
    assert sine_squared > 0
    expected = (A.edge_noise(edge)+B.edge_noise(edge))/math.sqrt(float(sine_squared))
    cover = SimpleNamespace(label=lambda: ('EE', ('edge', 0, 1), ('edge', 0, 1)))
    actual = _normal_noise(A, B, cover)
    assert math.isfinite(actual) and actual > 1
    assert math.isclose(actual, expected, rel_tol=2e-15)
