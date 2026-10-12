"""Equivalent test-oracle acceleration; all original grids/assertions remain.

References are frozen test-only Fraction/Newell/Gram implementations, not any
production predicate or algebra primitive. The accelerated oracle still uses
Gram cone coefficients; it does not reuse production edge-cone logic.
"""
from fractions import Fraction as F
import math
import random
import struct

import pytest

import e5a_cover_oracle as fast
import e5a_escape_oracle as escape
import perf_cover_oracle_reference as slow
import perf_escape_oracle_reference as slow_escape
from eab.kernel3d.geom3 import Polyhedron


FACES = ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
         (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))
SIGNS = ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
         (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1))


def _pair(kind):
    scale = F(1, 1000) if kind == 'small' else F(1000) if kind == 'large' else F(1)
    origin = (10**6, -10**5, 3*10**5) if kind in ('large', 'engineering') else (0, 0, 0)
    rng = random.Random(7531)
    def shape(center):
        result = []
        for i, p in enumerate(SIGNS):
            q = tuple(F(p[k])+center[k] for k in range(3))
            if kind == 'random':
                q = tuple(x+F(rng.randint(-3, 3), 100) for x in q)
            if kind == 'subnormal' and i == 6:
                q = (q[0], q[1], q[2]+F(1, 2**1074))
            if kind != 'axis':
                q = ((3*q[0]-4*q[1])/5, (4*q[0]+3*q[1])/5, q[2])
            result.append(tuple(scale*q[k]+origin[k] for k in range(3)))
        return Polyhedron(result, list(FACES))
    return shape((0, 0, 0)), shape((F(1, 7), F(-2, 9), F(3, 2)))


def test_independent_integer_dot_and_cross_equal_original_fraction_algebra():
    rng = random.Random(20936)
    pairs = []
    for _ in range(120):
        a = tuple(F(rng.randint(-10**9, 10**9), rng.randint(1, 10**5)) for _ in range(3))
        b = tuple(F(rng.randint(-10**9, 10**9), rng.randint(1, 10**5)) for _ in range(3))
        pairs.append((a, b))
    tiny = F(math.ulp(0.))
    pairs += [((F(0),)*3, (F(0),)*3), ((tiny, -tiny, tiny), (tiny, tiny, -tiny)),
              ((F(10**6)+tiny, F(-10**6), F(7)), (F(1), F(1), -tiny)),
              ((F(1), F(2), F(3)), (F(2), F(4), F(6)))]
    for a, b in pairs:
        assert fast.dot(a, b) == slow.dot(a, b)
        assert fast.cross(a, b) == slow.cross(a, b)


def test_independent_oracle_float_fallback_preserves_original_bits():
    rng = random.Random(627)
    for a, b in [((0., -0., math.ulp(0.)), (-0., 0., -math.ulp(0.))),
                 *((tuple(rng.uniform(-1e6, 1e6) for _ in range(3)),
                    tuple(rng.uniform(-1e6, 1e6) for _ in range(3))) for _ in range(50))]:
        assert struct.pack('!d', fast.dot(a, b)) == struct.pack('!d', slow.dot(a, b))
        assert tuple(struct.pack('!d', x) for x in fast.cross(a, b)) == tuple(
            struct.pack('!d', x) for x in slow.cross(a, b))


@pytest.mark.parametrize('kind', ['axis', 'random', 'small', 'large', 'engineering', 'subnormal'])
def test_oracle_vertices_arcs_complete_covers_and_candidates_are_value_identical(kind):
    A, B = _pair(kind)
    for body in (A, B):
        m = fast.model(tuple(body.verts), tuple(body.faces))
        old = slow.model(tuple(body.verts), tuple(body.faces))
        assert m == old
        directions = [(F(0),)*3, (F(1), F(2), F(-3)), *m[2]]
        directions += [tuple(-x for x in d) for d in directions]
        for tol in (0., 1e-9):
            for d in directions:
                for vertex in range(len(body.verts)):
                    assert fast.vertex(m, vertex, d, tol) == slow.vertex(old, vertex, d, tol)
                for edge in m[3]:
                    assert fast.arc(m, edge, d, tol) == slow.arc(old, edge, d, tol)
    for tol in (0., 1e-9):
        assert fast.cover_labels(A, B, tol) == slow.cover_labels(A, B, tol)
    offset = (F(0),)*3
    assert escape.candidates(A, B, offset) == slow_escape.candidates(A, B, offset)
