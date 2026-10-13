"""M3 three-dimensional closed/open convex-union and escape gates.

Oracle dependency inventory: geom3.polyhedra_overlap -> exact_geom (independent
surface partition/parity); e5b_wall_oracle -> e5a2_surface_oracle (test-only
triangle SAT/parity). Neither imports global_entrance, cover enumeration, its
SAT slabs, BSP, triangulation or vector primitives. Production geometry is
used only to construct raw test inputs, never the expected answers.
"""
from fractions import Fraction as F
from itertools import combinations
import inspect
import math
import random
import sys
from pathlib import Path
import textwrap

import pytest

from eab.kernel3d import global_entrance as G
from eab.kernel3d import interlock as I
from eab.kernel3d import geom3
from eab.kernel3d import exact_geom
from eab.kernel3d.exact_sweep import translate_exact, surface_events

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from osteomorphic import interlocking_pair
from e5b_wall_oracle import earliest_wall_escape
from test_interlock_exact import _wall


def _prism(profile, half=F(1, 2)):
    profile = tuple(tuple(F(x) for x in p) for p in profile)
    n = len(profile)
    verts = [(x, y, z) for z in (-half, half) for x, y in profile]
    faces = [tuple(range(n-1, -1, -1)), tuple(range(n, 2*n))]
    faces += [(i, (i+1) % n, (i+1) % n+n, i+n) for i in range(n)]
    return geom3.Polyhedron(verts, faces)


def _combine(*parts):
    verts, faces = [], []
    for part in parts:
        first = len(verts)
        verts.extend(part.verts)
        faces.extend(tuple(first+i for i in face) for face in part.faces)
    return geom3.Polyhedron(verts, faces)


def _families():
    little = geom3.box(half=(F(1, 4), F(1, 3), F(1, 5)))
    ell = _prism([(0, 0), (3, 0), (3, 1), (1, 1), (1, 3), (0, 3)])
    pocket = _prism([(0, 0), (3, 0), (3, 3), (2, 3), (2, 1), (1, 1), (1, 3), (0, 3)])
    pin = geom3.box(center=(F(3, 2), F(3, 2), 0), half=(F(1, 2), F(1, 2), F(1, 4)))
    outer, inner = geom3.box(half=(2,)*3), geom3.box(half=(F(1, 2),)*3)
    cavity = _combine(outer, geom3.Polyhedron(inner.verts,
                                             [tuple(reversed(f)) for f in inner.faces]))
    return [('L_prism', little, ell), ('zero_clearance_pin', pin, pocket),
            ('closed_cavity', inner, cavity)]


def _twisted_prism():
    base = ((F(0), F(0)), (F(4), F(0)), (F(1), F(3)))
    cx, cy = F(5, 3), F(1)
    top = [(cx+F(15, 17)*(x-cx)-F(8, 17)*(y-cy),
            cy+F(8, 17)*(x-cx)+F(15, 17)*(y-cy)) for x, y in base]
    vertices = [(x, y, F(0)) for x, y in base]+[(x, y, F(2)) for x, y in top]
    faces = [(0, 2, 1), (3, 4, 5)]
    for i in range(3):
        j = (i+1) % 3
        faces.extend(((i, j, j+3), (i, j+3, i+3)))
    return geom3.Polyhedron(vertices, faces)


def _random_concave(seed):
    rng = random.Random(seed)
    directions = ((1, 0), (F(3, 5), F(4, 5)), (0, 1), (-F(3, 5), F(4, 5)),
                  (-1, 0), (-F(3, 5), -F(4, 5)), (0, -1), (F(3, 5), -F(4, 5)))
    radii = [F(2)+F(rng.randrange(3), 5) if i % 2 == 0 else F(1, 2)+F(rng.randrange(3), 7)
             for i in range(8)]
    return _prism([(r*x, r*y) for r, (x, y) in zip(radii, directions)])


def _raw_shift(P, q):
    return geom3.Polyhedron([tuple(F(p[k])+q[k] for k in range(3)) for p in P.verts], P.faces)


def _assert_states(model, A, B, points):
    for q in points:
        actual = G.GlobalEntrance3D.classify(model, q)
        expected = geom3.polyhedra_overlap(_raw_shift(A, q), B, 0)
        assert actual == expected, ('global3d physical-state zero mismatch', q, actual, expected)


def _cell_probes(model):
    """All convex-pair vertex candidates, support-face centres and true edges.

    This is the lazy convex-union cell probe set, not a claim that an explicit
    3D overlay/strong-completeness boundary mesh has been implemented.
    """
    probes = set()
    for a in model.parts_a:
        for b in model.parts_b:
            vertices = sorted({tuple(y[k]-x[k] for k in range(3))
                               for x in a.vertices for y in b.vertices})
            probes.update(vertices)
            slabs = G._pair_slabs(a, b)
            facets = []
            for n, low, high in slabs:
                for bound in (low, high):
                    face = tuple(p for p in vertices if sum(n[k]*p[k] for k in range(3)) == bound)
                    if len(face) < 3:
                        continue
                    centre = tuple(sum(p[k] for p in face)/len(face) for k in range(3))
                    probes.add(centre)
                    facets.append(set(face))
                    # Exact line endpoints choose a local two-sided probe,
                    # never a floating epsilon or a skipped contact sample.
                    line = G.GlobalEntrance3D.line_sections(model, centre, n)
                    events = [abs(t) for row in line.closed+line.opened for t in row if t]
                    step = min(events)/2 if events else F(1)
                    probes.update(tuple(centre[k]+sign*step*n[k] for k in range(3)) for sign in (-1, 1))
            for p, q in combinations(vertices, 2):
                if sum(p in face and q in face for face in facets) >= 2:
                    probes.add(tuple((p[k]+q[k])/2 for k in range(3)))
    return tuple(sorted(probes))


@pytest.mark.parametrize('name,A,B', _families())
def test_convex_decomposition_covers_nonstar_pocket_and_cavity(name, A, B):
    """Oracle uses only original-surface volume/parity, no global primitives."""
    model = G.global_entrance(A, B)
    assert len(model.parts_b) > 1
    for part in model.parts_b:
        assert exact_geom.point_in_surface(part.interior, B) == 1, 'strict rational part interior'
        assert all(exact_geom.point_in_surface(p, B) >= 0 for p in part.vertices), 'closed part coverage'
    points = [(F(0),)*3, (F(1, 7), F(1, 11), F(1, 13)), (F(4), F(4), F(4)),
              (F(-1, 4), F(1, 2), F(3, 5))]
    _assert_states(model, A, B, points)
    for direction in ((1, 0, 0), (0, 0, 1), (2, -1, 3)):
        line = model.line_sections(direction=direction)
        times = sorted({t for row in line.closed+line.opened for t in row})
        times += [(a+b)/2 for a, b in zip(times, times[1:])]
        points = [tuple(t*component for component in direction) for t in times]
        _assert_states(model, A, B, points)


def test_all_lazy_convex_pair_cell_vertices_edges_faces_and_exact_sides_match_oracle():
    """Every generated probe is counted; zero exclusions and zero tolerances."""
    A = geom3.box(half=(F(1, 4),)*3)
    B = _prism([(0, 0), (2, 0), (2, 1), (1, 1), (1, 2), (0, 2)])
    model = G.global_entrance(A, B)
    points = _cell_probes(model)
    assert len(points) >= 70, 'probe coverage was not silently reduced'
    _assert_states(model, A, B, points)


@pytest.mark.parametrize('seed', [7, 23])
def test_random_concave_and_twisted_prism_have_independent_pointwise_states(seed):
    """Twisted prism exercises Steiner handling, not a claimed Schonhardt proof."""
    A = geom3.box(half=(F(1, 3), F(1, 4), F(1, 5)))
    rng = random.Random(seed)
    for B in (_random_concave(seed), _twisted_prism()):
        model = G.global_entrance(A, B)
        assert len(model.parts_b) > 1
        points = [tuple(F(rng.randrange(-12, 30), 6) for k in range(3)) for j in range(24)]
        _assert_states(model, A, B, points)


def test_zero_clearance_contact_is_not_silently_regularized_to_open_union():
    for name, A, B in _families()[1:]:
        model = G.global_entrance(A, B)
        assert model.classify() == 0, 'physical contact can lie in int E'
        if name == 'closed_cavity':
            for direction in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
                line = model.line_sections(direction=direction)
                assert line.closed == ((F(-5, 2), F(5, 2)),)
                assert line.opened == ((F(-5, 2), F(0)), (F(0), F(5, 2)))
                assert line.first_nonpenetrating(-F(1, 8)) == 0


@pytest.mark.parametrize('scale,shift,rotate', [
    (F(1), F(0), False), (F(1, 1024), F(10**6), True),
    (F(1024), F(-10**5), True), (F(1), F(1000), True)])
def test_global3d_membership_and_ray_sections_are_exactly_covariant(scale, shift, rotate):
    """The reference is direct rational affine algebra, not new SAT geometry."""
    _, A, B = _families()[0]
    def linear(p):
        x, y, z = (F(component) for component in p)
        return ((F(3, 5)*x-F(4, 5)*y)*scale,
                (F(4, 5)*x+F(3, 5)*y)*scale, z*scale) if rotate else tuple(x*scale for x in p)
    def body(P):
        return geom3.Polyhedron([tuple(x+shift for x in linear(p)) for p in P.verts], P.faces)
    base, moved = G.global_entrance(A, B), G.global_entrance(body(A), body(B))
    direction = (F(2), F(-1), F(3))
    origin = (F(1, 5), F(1, 7), F(-1, 11))
    assert moved.line_sections(linear(origin), linear(direction)) == base.line_sections(origin, direction)
    for p in ((0, 0, 0), (F(1, 2), F(1, 2), 0), (4, 5, 6)):
        assert moved.classify(linear(p)) == base.classify(p)


@pytest.mark.parametrize('scale', [F(1, 2**400), F(1), F(2**400)])
def test_global3d_exact_construction_values_match_independent_cartesian_reference(scale):
    A = geom3.box(center=(F(1, 3)*scale, 0, 0), half=(scale, 2*scale, 3*scale))
    B = geom3.box(center=(0, F(1, 7)*scale, 0), half=(2*scale, 3*scale, 4*scale))
    model = G.global_entrance(A, B)
    a = model.parts_a[0]
    assert a.interior == (F(1, 3)*scale, F(0), F(0)), 'independent rational centre'
    assert set(a.vertices) == {(F(1, 3)*scale+x, y, z)
                               for x in (-scale, scale) for y in (-2*scale, 2*scale)
                               for z in (-3*scale, 3*scale)}
    line = model.line_sections()
    assert line.closed == ((-7*scale, 7*scale),)
    assert line.opened == line.closed
    assert line.first_nonpenetrating() == 7*scale


def _legacy_root(A, B, offset):
    """Frozen pre-M3 algorithm for exact Fraction regression (secondary check)."""
    if geom3.polyhedra_overlap(_raw_shift(A, offset), B, 0) != 1:
        return F(0)
    for time in sorted({e.time for e in surface_events(A, B, start=offset) if e.time > 0}):
        displacement = (F(offset[0]), F(offset[1]), F(offset[2])+time)
        if geom3.polyhedra_overlap(_raw_shift(A, displacement), B, 0) != 1:
            return time
    raise AssertionError('legacy surface event set failed')


@pytest.mark.parametrize('family', ['box', 'TIA', 'wall'])
def test_exact_escape_height_and_offset_equal_frozen_pre_m3_values(family):
    if family == 'box':
        A, B, offset = geom3.box(), geom3.box(), (F(1, 7), F(1, 11), F(1, 13))
    elif family == 'TIA':
        A, B = interlocking_pair(nx=3, ny=1, amp=.2)
        offset = (F(1, 5), F(1, 7), F(0))
    else:
        A, B = _wall(16)
        offset = (F(0),)*3
    old = _legacy_root(A, B, offset)
    sol = I.escape_height_covers(A, B, offset)
    assert sol.exact_height == old, 'Fraction-for-Fraction pre-M3 escape root'
    assert sol.exact_offset == (offset[0], offset[1], offset[2]+old), 'exact displacement equality'
    if family == 'wall':
        assert sol.exact_height == earliest_wall_escape(A, B), 'independent wall oracle exact root'


def test_escape_height_has_zero_brute_predicate_calls(monkeypatch):
    A, B = interlocking_pair(nx=3, ny=1, amp=.2)
    calls = []
    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError('M3 escape called a brute intersection predicate')
    monkeypatch.setattr(I, 'polyhedra_overlap', forbidden)
    monkeypatch.setattr(geom3, 'polyhedra_overlap', forbidden)
    monkeypatch.setattr(exact_geom, 'surface_overlap', forbidden)
    I._exact_escape_cached.cache_clear()
    sol = I.escape_height_covers(A, B, (F(2, 7), F(1, 13), 0))
    assert sol.exact_height > 0
    assert calls == [], 'zero brute predicate calls'


def test_global3d_support_domain_errors_are_loud():
    cube = geom3.box()
    with pytest.raises(ValueError, match='closed'):
        G.global_entrance(geom3.Polyhedron(cube.verts, cube.faces[:-1]), cube)
    verts = list(cube.verts)
    verts[0] = (math.inf, 0, 0)
    with pytest.raises(ValueError, match='nonfinite'):
        G.global_entrance(geom3.Polyhedron(verts, cube.faces), cube)
    with pytest.raises(ValueError, match='nonzero'):
        G.global_entrance(cube, cube).line_sections(direction=(0, 0, 0))


def _assert_join_endpoint():
    A = geom3.box(half=(F(1, 2),)*3)
    lower = geom3.box(half=(F(1, 2),)*3)
    upper = geom3.box(center=(0, 0, 2), half=(F(1, 2),)*3)
    B = _combine(lower, upper)
    line = G.global_entrance(A, B).line_sections()
    assert line.classify(1) == 0, 'open interval endpoint must remain physical contact'
    assert line.first_nonpenetrating() == 1, 'first nonpenetrating point is not skipped'


def test_open_interval_endpoint_mutation_is_killed_inside_union(monkeypatch):
    _assert_join_endpoint()
    source = textwrap.dedent(inspect.getsource(G._merge))
    before, after = 'lo < result[-1][1] if strict', 'lo <= result[-1][1] if strict'
    assert source.count(before) == 1
    namespace = dict(vars(G))
    exec(compile(source.replace(before, after), '<M3 endpoint mutation>', 'exec'), namespace)
    monkeypatch.setattr(G, '_merge', namespace['_merge'])
    with pytest.raises(AssertionError, match='endpoint must remain physical contact'):
        _assert_join_endpoint()


def test_omitted_convex_piece_mutation_is_killed_inside_decomposition(monkeypatch):
    name, A, B = _families()[0]
    points = [(F(0), F(2), F(0))]
    _assert_states(G.global_entrance(A, B), A, B, points)
    source = textwrap.dedent(inspect.getsource(G._decompose))
    before, after = 'return parts\n', 'return parts[:-1]\n'
    assert source.count(before) == 1
    namespace = dict(vars(G))
    exec(compile(source.replace(before, after), '<M3 lost-piece mutation>', 'exec'), namespace)
    monkeypatch.setattr(G, '_decompose', namespace['_decompose'])
    with pytest.raises(AssertionError, match='physical-state zero mismatch'):
        _assert_states(G.global_entrance(A, B), A, B, points)


def test_escape_local_event_fallback_mutation_is_killed_at_exact_root(monkeypatch):
    A, B = _wall(16)
    expected = earliest_wall_escape(A, B)
    def check():
        assert I.escape_height_covers(A, B, (0, 0, 0)).exact_height == expected, 'global root not local cover event'
    check()
    source = textwrap.dedent(inspect.getsource(I._exact_escape_cached))
    before = 'state=_nonpenetrating_at(A,B,offset,height)'
    after = 'state=0  # defective local-event fallback'
    assert source.count(before) == 1
    namespace = dict(vars(I))
    exec(compile(source.replace(before, after), '<M3 local-event mutation>', 'exec'), namespace)
    monkeypatch.setattr(I, '_exact_escape_cached', namespace['_exact_escape_cached'])
    with pytest.raises(AssertionError, match='global root not local cover event'):
        check()
