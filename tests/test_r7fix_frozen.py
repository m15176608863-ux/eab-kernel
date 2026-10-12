"""Same-family construction scan: independent exact midpoint certificates."""
from fractions import Fraction as F
import math
import pytest
from eab.dual import Dual
from eab.kernel3d.geom3 import Polyhedron
from eab.kernel3d.frozen import frozen_normal


@pytest.mark.parametrize("with_dual", [False, True])
@pytest.mark.parametrize("sign", [-1, 1])
def test_frozen_unit_component_rounds_after_final_normalization(with_dual, sign):
    q = F(math.ulp(0.0))
    z = sign * 249 * q / 100
    # Explicit exact norm; the tiny squared component lies between midpoints
    # for output 2q (not q). No production geometry is used by this oracle.
    nn = 2 + z*z
    assert (F(3,2)*q)**2 < z*z/nn < (F(5,2)*q)**2
    x = Dual(1., (0.,)) if with_dual else 1.
    A = Polyhedron([(x, 1., z)], [])
    B = Polyhedron([(0., 0., 0.)], [])
    n = frozen_normal(A, B, ("VV3", ("V",0), ("V",0)))
    value = n[2].v if with_dual else n[2]
    assert value == sign * float(2*q), "final normalized component was rounded twice"


def test_frozen_unit_derivative_rounds_after_exact_normalization():
    q = F(math.ulp(0.0))
    t = F(3,2) * q * F(math.sqrt(3))
    assert (q/2)**2 < t*t/3 < (F(3,2)*q)**2
    A = Polyhedron([(Dual(1., (t,)), Dual(1., (-t/2,)), Dual(1., (-t/2,)))], [])
    B = Polyhedron([(0., 0., 0.)], [])
    n = frozen_normal(A, B, ("VV3", ("V",0), ("V",0)))
    assert n[0].e == (float(q),), "rounded norm changed derivative midpoint decision"
