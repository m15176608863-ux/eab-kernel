"""Shi's entrance-block reflection identity, with explicit reference points.

The independent oracle is g0_oracle's integer winding/segment intersection:
no production hull, decomposition, arrangement, membership, or boundary
primitive computes expected states. Metamorphism alone is not the oracle.
The production API uses displacement coordinates (B-A); reference positions
are restored explicitly before testing E(A,B)=-E(B,A)+(a0+b0).
"""
from fractions import Fraction as F

import pytest

from eab.kernel2d import g0_oracle as independent
from eab.kernel2d.global_entrance import GlobalEntrance2


@pytest.mark.parametrize("scale", (F(1, 1000), F(1), F(1000)))
@pytest.mark.parametrize("translation", ((0, 0), (1000, -1700), (100000, -230000), (1000000, -3100000)))
@pytest.mark.parametrize("rotation", ((F(1), F(0)), (F(3, 5), F(4, 5))))
def test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance(scale, translation, rotation):
    # Nonconvex A and asymmetric convex B; both references lie in the bodies.
    a = ((0, 0), (3, 0), (3, 1), (1, 1), (1, 3), (0, 3))
    b = ((F(7, 2), -1), (5, -1), (F(19, 4), F(1, 2)), (F(7, 2), 1))
    a0, b0 = (F(1, 4), F(1, 3)), (4, 0)
    cosine, sine = rotation

    def transformed(point):
        x, y = point
        return (scale*(cosine*x-sine*y)+translation[0],
                scale*(sine*x+cosine*y)+translation[1])

    a, b = tuple(map(transformed, a)), tuple(map(transformed, b))
    a0, b0 = transformed(a0), transformed(b0)
    forward, reverse = GlobalEntrance2(a, b), GlobalEntrance2(b, a)
    # Independent fixed probe family includes separation, contact and overlap;
    # no SUT-generated sample is needed to make any of the three occur.
    probes = ((F(-4), 0), (0, 0), (F(1, 2), 0), (F(3, 2), 0), (3, 0),
              (F(7, 2), -1), (5, 0), (7, 0), (4, 2), (4, -3))
    observed = set()
    for x, y in probes:
        displacement = (scale*(cosine*x-sine*y), scale*(sine*x+cosine*y))
        reference_position = (a0[0]+displacement[0], a0[1]+displacement[1])
        reflected_position = (a0[0]+b0[0]-reference_position[0],
                              a0[1]+b0[1]-reference_position[1])
        reverse_displacement = (reflected_position[0]-b0[0], reflected_position[1]-b0[1])
        assert reverse_displacement == tuple(-v for v in displacement)
        expected = independent.overlap(independent.translate(a, displacement), b)
        observed.add(expected)
        assert forward.membership(displacement) == expected, "forward E state disagrees with independent overlap oracle"
        assert reverse.membership(reverse_displacement) == expected, "reflected E state disagrees with independent overlap oracle"
        # E membership includes contact seams; topology is a separate label.
        assert forward.topology(displacement) == reverse.topology(reverse_displacement), "reflected E topological state differs"
    assert observed == {-1, 0, 1}


def test_symmetry_parameter_cells_produce_distinct_reference_geometries():
    products = set()
    for scale in (F(1, 1000), F(1), F(1000)):
        for tx, ty in ((0, 0), (1000, -1700), (100000, -230000), (1000000, -3100000)):
            for cosine, sine in ((F(1), F(0)), (F(3, 5), F(4, 5))):
                products.add(tuple((scale*(cosine*x-sine*y)+tx, scale*(sine*x+cosine*y)+ty)
                                   for x, y in ((0, 0), (3, 0), (1, 1))))
    assert len(products) == 24
