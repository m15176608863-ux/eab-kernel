"""Exact bool optimization: independent nonnegative barycentric feasibility.

Oracle solves the five coordinate/sum equalities by its own Fraction row
reduction and enumerates basic feasible supports. It imports no production
normal, orientation, intersection, distance or SAT primitive. Comparison to
the old intersection-point path is additional equivalence evidence only.
"""
from fractions import Fraction as F
from itertools import combinations
import inspect
import random

import pytest

from eab.kernel3d import exact_geom as E


def _feasible(first, second):
    a, b = [tuple(tuple((F(_r12_item) for _r12_item in p)) for p in tri) for tri in (first, second)]
    rows = [[a[j][i] for j in range(3)] + [-b[j][i] for j in range(3)] for i in range(3)]
    rows += [[F(1)]*3+[F(0)]*3, [F(0)]*3+[F(1)]*3]
    rhs = [F(0)]*3+[F(1), F(1)]
    for size in range(1, 6):
        for subset in combinations(range(6), size):
            matrix = [[row[j] for j in subset]+[v] for row, v in zip(rows, rhs)]
            rank = 0
            for col in range(size):
                pivot = next((i for i in range(rank, 5) if matrix[i][col]), None)
                if pivot is None:
                    break
                matrix[rank], matrix[pivot] = matrix[pivot], matrix[rank]
                d = matrix[rank][col]
                matrix[rank] = [x/d for x in matrix[rank]]
                for i in range(5):
                    if i != rank:
                        c = matrix[i][col]
                        matrix[i] = [x-c*y for x, y in zip(matrix[i], matrix[rank])]
                rank += 1
            if rank == size and all(not row[-1] for row in matrix[rank:]) and all(matrix[i][-1] >= 0 for i in range(rank)):
                return True
    return False


def _pairs():
    rng = random.Random(51200)
    def make():
        while True:
            tri = tuple(tuple(F(rng.randrange(-9,10),rng.randrange(1,12)) for _ in range(3)) for _ in range(3))
            # Generator-only rejection; never determines an expected answer.
            if any(E.cross(E.sub(tri[1],tri[0]),E.sub(tri[2],tri[0]))):
                return tri
    for _ in range(1200):
        yield make(), make()
    raw = [((0,0,0),(2,0,0),(0,2,0)), ((F(1,2),F(1,2),0),(F(3,2),F(1,2),0),(F(1,2),F(3,2),0)),
           ((2,0,0),(3,0,0),(2,2,0)), ((0,0,0),(1,0,1),(0,1,1)),
           ((0,0,F(1,10**9)),(2,0,F(1,10**9)),(0,2,F(1,10**9)))]
    for scale, offset in ((F(1),F(0)),(F(1,10**6),F(10**6)),(F(1000),F(-10**5)),(F(1,10**150),F(0))):
        ts = [tuple(tuple(offset+scale*c for c in p) for p in tri) for tri in raw]
        for a in ts:
            for b in ts:
                yield a,b


def test_boolean_intersection_matches_all_1300_original_pairs():
    pairs = list(_pairs())
    assert len(pairs) == len(set(pairs)) == 1300
    states = set()
    for a,b in pairs:
        want = bool(E.triangle_intersection(a,b))
        got = E._triangles_intersect_prepared(E._triangle_data(a),E._triangle_data(b))
        assert got == want
        states.add(got)
    assert states == {False,True}


def test_boolean_intersection_matches_independent_rational_feasibility():
    pairs = list(_pairs())
    for a,b in pairs[:32]+pairs[1200:]:
        assert E._triangles_intersect_prepared(E._triangle_data(a),E._triangle_data(b)) == _feasible(a,b)


def _endpoint_check():
    a=tuple((E.vector(_r12_item) for _r12_item in ((0,0,0),(2,0,0),(0,2,0))))
    b=tuple((E.vector(_r12_item) for _r12_item in ((2,0,0),(2,0,1),(3,0,1))))
    assert _feasible(a,b)
    assert E._triangles_near([(0,a)],[(0,b)],F(0)), 'closed endpoint lost'


@pytest.mark.parametrize('needle,replacement',[
    ('max(lo,left) <= min(hi,right)','max(lo,left) < min(hi,right)'),
    ('min(da) > 0 or max(da) < 0','min(da) >= 0 or max(da) <= 0'),
])
def test_boolean_internal_boundary_mutations_are_killed(monkeypatch,needle,replacement):
    _endpoint_check()
    source=inspect.getsource(E._triangles_intersect_prepared)
    assert source.count(needle)==1
    namespace=dict(E.__dict__)
    exec(compile(source.replace(needle,replacement),'<triangle-boolean-mutant>','exec'),namespace)
    monkeypatch.setattr(E,'_triangles_intersect_prepared',namespace['_triangles_intersect_prepared'])
    with pytest.raises(AssertionError,match='closed endpoint lost'):
        _endpoint_check()
