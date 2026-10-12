"""Independent G2 construction oracle contracts; no production sqrt reference."""
from construction_oracle import scalar_exact
from fractions import Fraction as F
import math

import pytest

import e5a_g2_oracle as O
from eab.kernel3d.geom3 import Polyhedron, box


@pytest.mark.parametrize('exponent', [-600, 600])
def test_g2_oracle_gap_rounds_only_after_exact_squared_distance(exponent):
    s = 2.**exponent
    a = box(half=(s,)*3)
    b = box(center=(3*s, 0, 0), half=(s,)*3)
    gap, _ = O.construction(a, b, ('VV3', ('vertex', 0), ('vertex', 0)), 0.)
    assert gap == 3*s, 'g2-oracle-final-distance-rounding'


def test_g2_oracle_signed_gap_cannot_cancel_exact_small_offset():
    s, t = F(1, 2**100), F(10**8)
    def rotate(p):
        x, y, z = map(F, p)
        return ((3*x-4*y)/5, (4*x+3*y)/5, z)
    source = box()
    b = Polyhedron([rotate(p) for p in source.verts], list(source.faces))
    point = rotate((-1-s, t, 0))
    a = box(center=tuple(v+1 for v in point), half=(F(1),)*3)
    gap, _ = O.construction(a, b, ('VF', ('vertex', 0), ('face', 5)), 0.)
    assert gap == scalar_exact(s), 'g2-oracle-exact-signed-plane-distance'


def test_g2_oracle_early_square_rounding_mutation_is_caught(monkeypatch):
    monkeypatch.setattr(O, '_distance_display', lambda squared: math.sqrt(float(squared)))
    with pytest.raises(AssertionError, match='g2-oracle-final-distance-rounding'):
        test_g2_oracle_gap_rounds_only_after_exact_squared_distance(-600)
