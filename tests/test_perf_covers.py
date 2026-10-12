"""Integer minimum-simplex optimization versus the unoptimized Fraction path.

Oracle primitives: test-local componentwise Fraction dot/cross/affine projection
and signed tetrahedral volumes. No production geometry/vector primitive is used.
Besides the point, the entire support tuple and its order must match exactly.
"""
from fractions import Fraction as F
from itertools import combinations
import inspect
import random

import pytest

from eab.kernel3d import covers3


def _dot(a, b):
    return sum((x * y for x, y in zip(a, b)), F(0))


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def _segment(a, b):
    d = _sub(b, a)
    dd = _dot(d, d)
    t = max(F(0), min(F(1), -_dot(a, d)/dd)) if dd else F(0)
    return tuple(x + t*y for x, y in zip(a, d))


def _triangle(a, b, c):
    n = _cross(_sub(b, a), _sub(c, a))
    nn = _dot(n, n)
    if nn:
        p = tuple(x*_dot(a, n)/nn for x in n)
        if all(_dot(_cross(_sub(u, p), _sub(v, p)), n) >= 0
               for u, v in ((b, c), (c, a), (a, b))):
            return p
    candidates = (_segment(a, b), _segment(b, c), _segment(c, a))
    return min((_dot(x, x), index, x) for index, x in enumerate(candidates))[2]


def _tetra(a, b, c, d):
    def volume(p, q, r, s):
        return _dot(_sub(q, p), _cross(_sub(r, p), _sub(s, p)))
    v = volume(a, b, c, d)
    z = (F(0),)*3
    return bool(v) and all(x*v >= 0 for x in (
        volume(z, b, c, d), volume(a, z, c, d), volume(a, b, z, d), volume(a, b, c, z)))


def _reference_simplex(points):
    best = min((_dot(x, x), index, x) for index, x in enumerate(points))[2]
    support = (best,)
    best2 = _dot(best, best)
    for subset in combinations(points, 2):
        p = _segment(*subset)
        d2 = _dot(p, p)
        if d2 < best2:
            best, best2, support = p, d2, subset
    for subset in combinations(points, 3):
        p = _triangle(*subset)
        d2 = _dot(p, p)
        if d2 < best2:
            best, best2, support = p, d2, subset
    for subset in combinations(points, 4):
        if _tetra(*subset):
            return (F(0),)*3, subset
    return best, support


def _reference_hull(points):
    point = min((_dot(x, x), index, x) for index, x in enumerate(points))[2]
    support = (point,)
    while True:
        q = min((_dot(x, point), index, x) for index, x in enumerate(points))[2]
        if _dot(q, point) >= _dot(point, point):
            return point
        previous = _dot(point, point)
        point, support = _reference_simplex((*support, q))
        assert _dot(point, point) < previous


def _samples(kind, scale, offset, count=24):
    rng = random.Random(721891)
    for index in range(count):
        # Rationalize the actual binary inputs after the engineering translation.
        pts = [tuple(F(offset + scale*rng.uniform(-2, 2)) for _ in range(3))
               for _ in range(1 + index % 5)]
        if kind == "duplicate":
            pts[-1] = pts[0]
        elif kind == "coplanar":
            pts = [(*p[:2], F(offset)) for p in pts]
        elif kind == "collinear":
            pts = [(p[0], F(2)*p[0]+F(offset), F(3)*p[0]-F(offset)) for p in pts]
        elif kind == "mixed_denominators":
            pts = [tuple(p[k]/(3, 7, 11)[k] for k in range(3)) for p in pts]
        yield tuple(pts)


@pytest.mark.parametrize("scale,offset", [(1.0, 0.0), (1e-6, 1e6), (1e3, -1e5), (1e-150, 0.0)])
@pytest.mark.parametrize("kind", ["random", "duplicate", "coplanar", "collinear", "mixed_denominators"])
def test_integer_simplex_matches_fraction_reference(kind, scale, offset):
    """Independent oracle specified in module docstring; compares point AND support."""
    for points in _samples(kind, scale, offset):
        assert covers3._qclosest_simplex(points) == _reference_simplex(points), "simplex exact point/support mismatch"


@pytest.mark.parametrize("scale,offset", [(1.0, 0.0), (1e-6, 1e6), (1e3, -1e5)])
@pytest.mark.parametrize("kind", ["random", "duplicate", "coplanar", "collinear", "mixed_denominators"])
def test_integer_simplex_hull_matches_fraction_reference(kind, scale, offset):
    for points in _samples(kind, scale, offset, count=12):
        assert covers3._qclosest_hull.__wrapped__(points) == _reference_hull(points)


@pytest.mark.parametrize("points", [
    [(F(1), F(0), F(0)), (F(1), F(1), F(0)), (F(1), F(-1), F(0))],
    [(F(0), F(0), F(0)), (F(1), F(0), F(0)), (F(0), F(1), F(0)), (F(0), F(0), F(1))],
    [(F(1, 10**400), F(0), F(0)), (F(0), F(1, 10**400), F(0)), (F(0), F(0), F(1, 10**400))],
    [(F(1, 2**1074), F(0), F(0)), (F(-1, 2**1074), F(0), F(0))],
    [(F(10**400), F(0), F(0)), (F(0), F(10**400), F(0)), (F(0), F(0), F(10**400))],
])
def test_integer_simplex_exact_extremes_and_support_ties(points):
    assert covers3._qclosest_simplex(points) == _reference_simplex(points), "simplex exact point/support mismatch"


def test_integer_simplex_support_tie_gate_has_internal_teeth(monkeypatch):
    source = inspect.getsource(covers3._qclosest_simplex)
    mutant = source.replace("< best_num * denominator2:", "<= best_num * denominator2:")
    assert mutant != source
    namespace = dict(vars(covers3))
    exec(compile(mutant, "<PERF-simplex-tie-mutant>", "exec"), namespace)
    monkeypatch.setattr(covers3, "_qclosest_simplex", namespace["_qclosest_simplex"])
    points = [(F(1), F(0), F(0)), (F(1), F(1), F(0)), (F(1), F(-1), F(0))]
    with pytest.raises(AssertionError, match="simplex exact point/support mismatch"):
        test_integer_simplex_exact_extremes_and_support_ties(points)


def test_integer_simplex_rescaling_gate_has_internal_teeth(monkeypatch):
    source = inspect.getsource(covers3._qclosest_simplex)
    mutant = source.replace("Fraction(c, den * scale)", "Fraction(c, den)")
    assert mutant != source
    namespace = dict(vars(covers3))
    exec(compile(mutant, "<PERF-simplex-scale-mutant>", "exec"), namespace)
    monkeypatch.setattr(covers3, "_qclosest_simplex", namespace["_qclosest_simplex"])
    points = [(F(1, 3), F(0), F(0)), (F(0), F(1, 3), F(0)), (F(0), F(0), F(1, 3))]
    with pytest.raises(AssertionError, match="simplex exact point/support mismatch"):
        test_integer_simplex_exact_extremes_and_support_ties(points)
