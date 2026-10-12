"""WO-PERF exact equivalence gates; no tolerances, skips, or smaller old grids.

The frozen event reference and uncached candidates are optimization references,
not independent geometric oracles (their arithmetic primitives are shared).
"""
import inspect
import random
from fractions import Fraction as F

import pytest

from eab.kernel3d import exact_sweep as S, interlock as I
from eab.kernel3d.geom3 import Polyhedron, box, tetra
from perf_sweep_reference import reference_events


def _cases():
    rng = random.Random(17291)
    cases = []
    # General positions, exact planar contact, grazing/parallel degeneracy,
    # short scales and large engineering-coordinate offsets.
    for t, scale in ((0, 1), (1000, F(1, 10)), (10**6, F(1, 10**6))):
        for j in range(3):
            sh = tuple(F(rng.randrange(-7, 8), 8) * scale for _ in range(3))
            A = box()
            B = tetra((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)) if j else box()
            def move(P, delta):
                return Polyhedron([tuple(t + scale * F(p[k]) + delta[k] for k in range(3))
                                   for p in P.verts], list(P.faces))
            cases.append((move(A, (0, 0, 0)), move(B, sh)))
        A = box()
        cases.append((move(A, (0, 0, 0)), move(A, (0, 0, scale))))
    for exponent in (0, -8, -30, -300):
        # Non-axis-aligned dyadic tetrahedra, including an almost flat simplex.
        scale = F(10) ** exponent
        verts = [(F(rng.randrange(-16, 17), 8), F(rng.randrange(-16, 17), 8),
                  scale * F(rng.randrange(-16, 17), 8)) for _ in range(4)]
        A = tetra(*verts)
        B = tetra(*[tuple(x + F(1, 16) for x in p) for p in verts])
        cases.append((A, B))
    return cases


@pytest.mark.parametrize('case', range(16))
@pytest.mark.parametrize('direction', ((0, 0, 1), (1, 0, 0), (0, -2, 0), (1, 2, -3), (0, 0, 0)))
def test_static_axis_pruning_matches_unpruned_all_event_values(case, direction):
    A, B = _cases()[case]
    av, bv = tuple(map(S.G.vector, A.verts)), tuple(map(S.G.vector, B.verts))
    args = av, tuple(A.faces), bv, tuple(B.faces), tuple(map(F, direction)), F(0), None
    assert S._events_cached(*args) == reference_events(*args)
    args = args[:-2] + (F(1, 16), F(7, 8))
    assert S._events_cached(*args) == reference_events(*args)


@pytest.mark.parametrize('case', range(14))
def test_candidate_content_cache_matches_uncached_values(case):
    A, B = _cases()[case]
    for off in ((0., 0., 0.), (.23, -.17, .02)):
        for tol, extent in ((0., 0.), (1e-9, 1e-6)):
            want = I._candidates_uncached(A, B, off, tol, extent)
            assert I._candidates(A, B, off, tol, extent) == want
            assert I._candidates(A, B, off, tol, extent) == want


def _assert_cache_does_not_cross_offsets():
    A, B = box(), box().translated((.4, .2, -.7))
    first = I._candidates(A, B, (0., 0., 0.), 1e-9, 1e-9)
    off = (.27, -.13, .11)
    want = I._candidates_uncached(A, B, off, 1e-9, 1e-9)
    assert first != want, 'the two offsets must exercise distinct cached products'
    assert I._candidates(A, B, off, 1e-9, 1e-9) == want, 'offset content must not alias'


def test_candidate_cache_has_teeth_when_signature_omits_offset(monkeypatch):
    I._candidates_cached.cache_clear()
    _assert_cache_does_not_cross_offsets()
    source = inspect.getsource(I._candidates)
    before = 'signature = arguments + (numeric_types, implementations)'
    after = 'signature = arguments[:4] + arguments[5:] + (numeric_types, implementations)'
    assert before in source
    namespace = dict(I.__dict__)
    exec(source.replace(before, after), namespace)
    I._candidates_cached.cache_clear()
    monkeypatch.setattr(I, '_candidates', namespace['_candidates'])
    with pytest.raises(AssertionError, match='offset content must not alias'):
        _assert_cache_does_not_cross_offsets()
    I._candidates_cached.cache_clear()


def test_candidate_cache_mutable_results_and_source_content_are_isolated():
    A, B = box(), box().translated((.4, .2, -.7))
    args = (A, B, (.23, -.17, .02), 1e-9, 1e-9)
    rows, r = I._candidates(*args)
    expected = list(rows)
    rows.clear()
    assert I._candidates(*args) == (expected, r)
    A.verts[0] = tuple(x + .013 for x in A.verts[0])
    assert I._candidates(*args) == I._candidates_uncached(*args)
    A.faces[0] = tuple(reversed(A.faces[0]))
    assert I._candidates(*args) == I._candidates_uncached(*args)


@pytest.mark.parametrize('local', (False, True))
def test_candidate_cache_does_not_hide_a_cover_implementation_mutation(monkeypatch, local):
    A, B = box(), box().translated((.4, .2, -.7))
    args = (A, B, (0., 0., 0.), 1e-9, 1e-9)
    original = I._candidates(*args)
    monkeypatch.setattr(I if local else I._covers, 'ee_cover', lambda *args, **kwargs: None)
    expected = I._candidates_uncached(*args)
    assert expected != original, 'mutation must actually change nominal reports'
    assert I._candidates(*args) == expected


def test_exact_aabb_pruning_keeps_tangent_events_and_detects_strict_bound_mutation(monkeypatch):
    A, B = box(), box().translated((1, 0, -1))
    args = (tuple(map(S.G.vector, A.verts)), tuple(A.faces),
            tuple(map(S.G.vector, B.verts)), tuple(B.faces), (F(0), F(0), F(1)), F(0), None)
    expected = reference_events(*args)
    assert S._events_cached(*args) == expected
    source = inspect.getsource(S._events_cached.__wrapped__)
    source = source.replace('ahi<blo or bhi<alo', 'ahi<=blo or bhi<=alo')
    namespace = dict(S.__dict__)
    exec(source, namespace)
    with pytest.raises(AssertionError, match='tangent events must survive'):
        assert namespace['_events_cached'](*args) == expected, 'tangent events must survive'
