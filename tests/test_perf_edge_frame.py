"""Exact integer wedge payload versus independent Fraction arithmetic.

Oracle primitives are local Fraction vector formulas and literal face-ring
traversal/Newell sums. No production edge traversal, normal, cone, sign, cache,
or geometry predicate is called by the reference. Production Polyhedron is
only an input container. The full -1/0/1 result, not acceptance alone, is tested.
"""
from construction_oracle import scalar_exact
from fractions import Fraction as F
import inspect
import random

import pytest

from eab.kernel3d import covers3 as C
from eab.kernel3d.geom3 import Polyhedron


VERTS = [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
         (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]
FACES = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
         (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def _v(v):
    return tuple(F(component) for component in v)


def _sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def _dot(a, b):
    return sum((x*y for x, y in zip(a, b)), F(0))


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def _normal(P, fi):
    face = P.faces[fi]
    origin = _v(P.verts[face[0]])
    total = (F(0),)*3
    for i, j in zip(face, face[1:]+face[:1]):
        term = _cross(_sub(_v(P.verts[i]), origin), _sub(_v(P.verts[j]), origin))
        total = tuple(x+y for x, y in zip(total, term))
    return total


def _frame(P, edge):
    target = tuple(sorted(edge))
    traversals = [(fi, a, b) for fi, face in enumerate(P.faces)
                  for a, b in zip(face, face[1:]+face[:1]) if tuple(sorted((a, b))) == target]
    if len(traversals) != 2:
        return None
    (f1, a, b), (f2, _, _) = traversals
    t = _sub(_v(P.verts[b]), _v(P.verts[a]))
    if not any(t):
        raise ValueError("zero-length edge")
    return t, _normal(P, f1), _normal(P, f2)


def _outside(value, a, b, tol):
    if value <= 0:
        return False
    return tol <= 0 or value*value > F(tol)**2 * _dot(a, a) * _dot(b, b)


def _reference_edge_state(P, edge, direction, tol=0):
    frame = _frame(P, edge)
    if frame is None:
        return -1
    t, n1, n2 = frame
    if _dot(_cross(n1, n2), t) <= 0:
        return -1
    direction = _v(direction)
    axial = _dot(direction, t)
    if _outside(abs(axial), direction, t, tol):
        return -1
    h1, h2 = _cross(t, n1), _cross(n2, t)
    s1, s2 = _dot(h1, direction), _dot(h2, direction)
    if _outside(-s1, h1, direction, tol) or _outside(-s2, h2, direction, tol):
        return -1
    return 1 if s1 > 0 and s2 > 0 and axial == 0 else 0


def _body(kind, scale, offset, rounded):
    vertices = [_v(p) for p in VERTS]
    faces = list(FACES)
    if kind in ("skew", "folded"):
        skewed = []
        for x, y, z in vertices:
            x += F(2, 7)*y
            y -= F(1, 5)*z
            z += F(3, 11)*x
            skewed.append((x, y, z))
        vertices = skewed
    if kind == "folded":
        x, y, z = vertices[6]
        vertices[6] = (x, y, z-F(5, 2))
    elif kind == "flat_seam":
        faces = [(face[0], face[1], face[2]) for face in FACES] + [
            (face[0], face[2], face[3]) for face in FACES]
    elif kind == "open":
        faces = faces[:-1]
    elif kind == "reversed":
        faces = [tuple(reversed(face)) for face in faces]
    vertices = [tuple(scale*x+(j+1)*offset for j, x in enumerate(p)) for p in vertices]
    if rounded:
        vertices = [tuple(scalar_exact(component) for component in p) for p in vertices]
    return Polyhedron(vertices, faces)


def _production_outcome(P, edge, direction, tol):
    try:
        return C._qedge_contains(P, edge, direction, tol)
    except ValueError as error:
        assert "zero-length edge" in str(error)
        return "zero-length edge"


def _reference_outcome(P, edge, direction, tol):
    try:
        return _reference_edge_state(P, edge, direction, tol)
    except ValueError as error:
        assert "zero-length edge" in str(error)
        return "zero-length edge"


def _queries(P):
    rng = random.Random(491792)
    edges = sorted({tuple(sorted((a, b))) for face in P.faces for a, b in zip(face, face[1:]+face[:1])})
    # New comparison grid only: no pre-existing grid is removed or changed.
    selected = list(dict.fromkeys((edges[0], edges[len(edges)//2], edges[-1])))
    for edge in selected:
        directions = [(F(0),)*3]
        directions += [tuple(F(rng.randrange(-9, 10), rng.choice((1, 3, 7))) for _ in range(3))
                       for _ in range(7)]
        try:
            frame = _frame(P, edge)
        except ValueError:
            frame = None
        if frame is not None:
            t, n1, n2 = frame
            directions += [n1, n2, tuple(x+y for x, y in zip(n1, n2)),
                           tuple(x+y+F(1, 2**80)*z for x, y, z in zip(n1, n2, t))]
        for direction in directions:
            for tol in (F(-1, 7), F(0), F(1, 10**12), F(1, 4)):
                yield edge, direction, tol


@pytest.mark.parametrize("kind", ["axis", "skew", "folded", "flat_seam", "open", "reversed"])
@pytest.mark.parametrize("scale,offset", [(F(1), F(0)), (F(1, 10**8), F(10**6)),
                                         (F(1000), F(-10**5)), (F(1, 2**1074), F(0))])
@pytest.mark.parametrize("rounded", [False, True])
def test_integer_edge_frame_matches_fraction_reference(kind, scale, offset, rounded):
    P = _body(kind, scale, offset, rounded)
    for edge, direction, tol in _queries(P):
        got = _production_outcome(P, edge, direction, tol)
        expected = _reference_outcome(P, edge, direction, tol)
        assert got == expected, ("exact edge state", kind, scale, offset, rounded, edge, direction, tol)


def test_integer_edge_frame_closed_window_and_direction_sign_have_analytic_oracle():
    """Oracle: cube edge x=z=1 has normal wedge x,z>=0 and zero y."""
    P = Polyhedron([_v(p) for p in VERTS], list(FACES))
    edge = (5, 6)
    cases = [
        ((1, 0, 1), F(0), 1), ((1, 0, 0), F(0), 0), ((-1, 0, 1), F(0), -1),
        ((1, 0, -F(1, 100)), F(1, 50), 0),
        ((4, 3, 0), F(3, 5), 0), ((4, 3, 0), F(3, 5)-F(1, 2**80), -1),
        ((4, 0, -3), F(3, 5), 0), ((4, 0, -3), F(3, 5)-F(1, 2**80), -1),
        ((1, F(1, 2**1074), 1), F(0), -1),
        ((1, F(1, 2**1074), 1), F(1, 2**1074), 0),
        ((0, 0, 0), F(-1), 0), ((1, 0, 1), F(-1), 1),
    ]
    results = []
    for direction, tol, expected in cases:
        got = C._qedge_contains(P, edge, _v(direction), tol)
        assert got == expected, "analytic edge direction/window state"
        results.append(got)
    assert set(results) == {-1, 0, 1}


def test_integer_edge_frame_reuses_only_current_geometry_and_topology():
    P = _body("axis", F(1), F(0), False)
    states = []
    for kind in ("axis", "skew", "folded", "reversed", "axis"):
        replacement = _body(kind, F(1), F(10**6), False)
        P.verts[:] = replacement.verts
        P.faces[:] = replacement.faces
        for edge, direction, tol in _queries(P):
            got = C._qedge_contains(P, edge, direction, tol)
            assert got == _reference_edge_state(P, edge, direction, tol), "current edge frame contents"
            states.append(got)
    assert set(states) == {-1, 0, 1}


def test_integer_edge_direction_sign_mutation_has_teeth(monkeypatch):
    source = inspect.getsource(C._qedge_contains)
    needle = "d = _integer_ray(d)"
    assert source.count(needle) == 1
    namespace = dict(vars(C))
    exec(compile(source.replace(needle, "d = _integer_ray(tuple(abs(c) for c in d))"),
                 "<PERF-edge-sign-mutant>", "exec"), namespace)
    monkeypatch.setattr(C, "_qedge_contains", namespace["_qedge_contains"])
    with pytest.raises(AssertionError, match="analytic edge direction/window state"):
        test_integer_edge_frame_closed_window_and_direction_sign_have_analytic_oracle()


def test_integer_edge_anisotropic_rescaling_mutation_has_teeth(monkeypatch):
    source = inspect.getsource(C._integer_ray)
    needle = "c.numerator * (den // c.denominator)"
    assert source.count(needle) == 1
    namespace = dict(vars(C))
    exec(compile(source.replace(needle, "c.numerator"), "<PERF-edge-denominator-mutant>", "exec"), namespace)
    C._qedge_frame_cached.cache_clear()
    monkeypatch.setattr(C, "_integer_ray", namespace["_integer_ray"])
    try:
        with pytest.raises(AssertionError, match="analytic edge direction/window state"):
            test_integer_edge_frame_closed_window_and_direction_sign_have_analytic_oracle()
    finally:
        C._qedge_frame_cached.cache_clear()
