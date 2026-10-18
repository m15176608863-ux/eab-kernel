"""Shi 2015 section 4.5 in displacement form, pointwise against an oracle.

The independent oracle is g0_oracle's integer winding/segment intersection:
no production hull, decomposition, arrangement, membership, or boundary
primitive computes expected states. Topology uses the oracle's independent
angular-sector exterior test. Metamorphism alone is not the oracle.
The production API uses displacement coordinates: E(B,A) = -E(A,B).
This finite probe gate is not a separate test of reference-point bookkeeping.
"""
from fractions import Fraction as F

import pytest

from eab.kernel2d import g0_oracle as independent
from eab.kernel2d.global_entrance import GlobalEntrance2


@pytest.mark.parametrize("scale", (F(1, 1000), F(1), F(1000)))
@pytest.mark.parametrize("translation", ((0, 0), (1000, -1700), (100000, -230000), (1000000, -3100000)))
@pytest.mark.parametrize("rotation", ((F(1), F(0)), (F(3, 5), F(4, 5))))
def test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance(scale, translation, rotation):
    # The notch and notch-contact probes distinguish this L from its hull.
    a = ((0, 0), (3, 0), (3, 1), (1, 1), (1, 3), (0, 3))
    b = ((F(7, 2), -1), (5, -1), (F(19, 4), F(1, 2)), (F(7, 2), 1))
    cosine, sine = rotation

    def direction(point):
        x, y = point
        return scale*(cosine*x-sine*y), scale*(sine*x+cosine*y)

    def transformed(point):
        x, y = direction(point)
        return x+translation[0], y+translation[1]

    probes = ((F(-4), 0), (0, 0), (F(1, 2), 0), (F(3, 2), 0), (3, 0),
              (F(7, 2), -1), (5, 0), (7, 0), (4, 2), (4, -3),
              (2, F(-11, 5)), (F(5, 2), -2))
    pin = ((0, F(1, 2)), (1, F(1, 2)), (1, F(3, 2)), (0, F(3, 2)))
    channel = ((-1, -1), (2, -1), (2, 2), (1, 2), (1, 0), (0, 0), (0, 2), (-1, 2))
    families = ((a, b, probes, {(2, F(-11, 5)): (-1, -1), (F(5, 2), -2): (0, 0)}),
                (pin, channel, ((0, 0), (F(1, 10), 0), (3, 0), (0, F(3, 2))),
                 {(0, 0): (0, 1)}))
    for first, second, samples, prescribed in families:
        first, second = tuple(map(transformed, first)), tuple(map(transformed, second))
        truth = []
        for sample in samples:
            displacement = direction(sample)
            moved = independent.translate(first, displacement)
            state = independent.overlap(moved, second)
            topology = (0 if independent.boundary_has_exterior(moved, second) else 1) if state == 0 else state
            if sample in prescribed:
                assert (state, topology) == prescribed[sample], "independent notch/seam witness must be load-bearing"
            truth.append((displacement, state, topology))
        assert {row[1] for row in truth} == {-1, 0, 1}
        # The oracle always receives the CCW originals. Only production gets
        # reversed rings: expected orientation must not depend on SUT _ring.
        for clockwise_a, clockwise_b in ((False, False), (True, False), (False, True), (True, True)):
            aa = tuple(reversed(first)) if clockwise_a else first
            bb = tuple(reversed(second)) if clockwise_b else second
            try:
                forward, reverse = GlobalEntrance2(aa, bb), GlobalEntrance2(bb, aa)
            except ArithmeticError as error:
                raise AssertionError("valid clockwise rings must retain the displacement contract") from error
            for displacement, state, topology in truth:
                reflected = tuple(-v for v in displacement)
                assert forward.membership(displacement) == state, "forward E state disagrees with independent overlap oracle"
                assert reverse.membership(reflected) == state, "reflected E state disagrees with independent overlap oracle"
                assert forward.topology(displacement) == topology, "forward E topology disagrees with independent exterior oracle"
                assert reverse.topology(reflected) == topology, "reflected E topology disagrees with independent exterior oracle"


def test_of_test_symmetry_parameter_cells_produce_distinct_geometries():
    """Test-of-test: parameter diversity only; not an additional production gate."""
    products = set()
    for scale in (F(1, 1000), F(1), F(1000)):
        for tx, ty in ((0, 0), (1000, -1700), (100000, -230000), (1000000, -3100000)):
            for cosine, sine in ((F(1), F(0)), (F(3, 5), F(4, 5))):
                products.add(tuple((scale*(cosine*x-sine*y)+tx, scale*(sine*x+cosine*y)+ty)
                                   for x, y in ((0, 0), (3, 0), (1, 1))))
    assert len(products) == 24
