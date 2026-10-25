"""SE(2) path covariance under independent exact coordinate constructions.

These are metamorphic checks, not independent root oracles. The similarity
and reflection maps below use their own component formula; motion centers
and translations are transformed along with both bodies. Polygon input
indices are also permuted, and all returned labels must follow that mapping.
"""
from fractions import Fraction as F
from random import Random

import pytest

from eab.kernel2d.se2 import SE2Motion
from eab.kernel2d.se2_paths import se2_first_penetration


def _linear(point, scale, q, mirror):
    x, y = F(point[0]), F(point[1])
    scale, q = F(scale), F(q)
    if mirror:
        x = -x
    den = 1+q*q
    return (scale*((1-q*q)*x-2*q*y)/den,
            scale*(2*q*x+(1-q*q)*y)/den)


def _point(point, scale, q, shift, mirror):
    linear = _linear(point, scale, q, mirror)
    return tuple(linear[k]+F(shift[k]) for k in (0, 1))


def _motion(motion: SE2Motion, scale: F, q: F, shift: tuple[F, F], mirror: bool):
    return SE2Motion(-motion.u1 if mirror else motion.u1,
                     _linear(motion.translation, scale, q, mirror),
                     _point(motion.center, scale, q, shift, mirror))


def _mapped_label(label, a_order, b_order):
    tag, i, j = label
    # Orders are cyclic shifts, so an edge and its start vertex share a map.
    mapped_i = next(index for index, value in enumerate(a_order) if value == i)
    mapped_j = next(index for index, value in enumerate(b_order) if value == j)
    return tag, mapped_i, mapped_j


def _same_time(a, b):
    if a is None or b is None:
        return a is b
    if getattr(a, "rational", None) is not None:
        return b == a.rational
    if getattr(b, "rational", None) is not None:
        return a == b.rational
    return a == b


@pytest.mark.parametrize("magnitude,scale", [
    (0, F(1)), (1000, F(1)), (100000, F(1)),
    (100000, F(1, 10**8)), (1000, F(10000)),
])
@pytest.mark.parametrize("mirror", [False, True])
def test_exact_rigid_similarity_and_mirror_covariance(magnitude, scale, mirror):
    a = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    b = ((F(6, 5), -3), (3, -3), (3, 3), (F(6, 5), 3))
    ma, mb = SE2Motion(1), SE2Motion()
    reference = se2_first_penetration(a, b, ma, mb)
    rng = Random(71053)
    products = set()
    for _ in range(3):
        q = F(rng.randrange(-13, 14), rng.randrange(2, 12))
        shift = (F(magnitude)+F(7, 3), -F(magnitude)+F(11, 7))
        aa = tuple(_point(p, scale, q, shift, mirror) for p in a)
        bb = tuple(_point(p, scale, q, shift, mirror) for p in b)
        a_order, b_order = (2, 3, 0, 1), (1, 2, 3, 0)
        got = se2_first_penetration(tuple(aa[i] for i in a_order),
                                    tuple(bb[i] for i in b_order),
                                    _motion(ma, scale, q, shift, mirror),
                                    _motion(mb, scale, q, shift, mirror))
        assert (got.status, got.initial_state, got.end_state, got.immediate, got.touches_end) == (
            reference.status, reference.initial_state, reference.end_state,
            reference.immediate, reference.touches_end), "state covariance"
        assert _same_time(got.exact_time, reference.exact_time), "exact time covariance"
        assert set(got.incidences) == {_mapped_label(label, a_order, b_order)
                                       for label in reference.incidences}, "incidence identity permutation"
        assert set(got.features) == {_mapped_label(label, a_order, b_order)
                                     for label in reference.features}, "cover identity permutation"
        products.add(aa)
    assert len(products) == 3, "the three rational rotations must produce distinct geometry"


def test_covariance_moves_both_nonzero_motion_centers():
    a = ((0, 0), (2, 0), (1, 1))
    b = ((2, -1), (4, -1), (4, 2), (2, 2))
    ma = SE2Motion(F(2, 5), (F(5, 7), F(-1, 3)), (F(-3, 2), F(4, 3)))
    mb = SE2Motion(F(-1, 4), (F(-1, 6), F(2, 7)), (F(7, 3), F(-5, 2)))
    reference = se2_first_penetration(a, b, ma, mb)
    scale, q, shift = F(3, 11), F(-3, 7), (F(100000), F(-99997))
    for mirror in (False, True):
        got = se2_first_penetration(
            tuple(_point(p, scale, q, shift, mirror) for p in a),
            tuple(_point(p, scale, q, shift, mirror) for p in b),
            _motion(ma, scale, q, shift, mirror), _motion(mb, scale, q, shift, mirror))
        assert (got.status, got.initial_state, got.end_state, got.immediate, got.touches_end) == (
            reference.status, reference.initial_state, reference.end_state,
            reference.immediate, reference.touches_end)
        assert _same_time(got.exact_time, reference.exact_time)
        assert got.incidences == reference.incidences and got.features == reference.features
