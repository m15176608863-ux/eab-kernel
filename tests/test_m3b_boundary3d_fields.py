"""Independent all-field Cartesian reference for the public 3D boundary APIs.

Oracle imports: Fraction, itertools.product, math.lcm only.  Its geometric
operations below are test-owned and call no boundary/global/cover primitive.
The fixture is two non-symmetric boxes under an exact quaternion SO(3) map.
The public global_entrance path is used, including its triangle-diagonal SAT
planes. This is every-field coverage of this box branch, not arbitrary BSP or
clipping-Steiner topology coverage. Polygon rings are compared modulo cyclic
ordering, with orientation checked separately; no bytewise ordering claim.
"""
from fractions import Fraction as F
from itertools import product
from math import lcm
import random

import pytest

from eab.kernel3d import boundary as B
from eab.kernel3d import global_entrance as G
from eab.kernel3d.geom3 import Polyhedron


FACES = ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
         (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))
FACE_AXES = ((2, -1), (2, 1), (1, -1), (0, 1), (1, 1), (0, -1))
ALO, AHI = (0, 0, 0), (2, 3, 5)
BLO, BHI = (7, -4, 13), (11, 2, 21)


def _minus(a, b):
    return tuple(a[k]-b[k] for k in range(3))


def _scalar(a, b):
    return sum(a[k]*b[k] for k in range(3))


def _wedge(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def _canonical(vector):
    first = next((x for x in vector if x), None)
    if first is None:
        return None
    ratios = tuple(F(x)/first for x in vector)
    multiplier = lcm(*(x.denominator for x in ratios))
    return tuple(int(x*multiplier) for x in ratios)


def _rotation(point, quaternion):
    w, x, y, z = quaternion
    denominator = w*w+x*x+y*y+z*z
    matrix = ((w*w+x*x-y*y-z*z, 2*(x*y-w*z), 2*(x*z+w*y)),
              (2*(x*y+w*z), w*w-x*x+y*y-z*z, 2*(y*z-w*x)),
              (2*(x*z-w*y), 2*(y*z+w*x), w*w-x*x-y*y+z*z))
    return tuple(sum(F(matrix[k][j], denominator)*point[j] for j in range(3)) for k in range(3))


def _corners(low, high):
    x, y, z = low
    X, Y, Z = high
    return tuple(tuple(F(v) for v in p) for p in
                 ((x, y, z), (X, y, z), (X, Y, z), (x, Y, z),
                  (x, y, Z), (X, y, Z), (X, Y, Z), (x, Y, Z)))


def _transform(point, scale, shift, quaternion):
    rotated = _rotation(point, quaternion)
    return tuple(scale*rotated[k]+shift[k] for k in range(3))


def _mean(points):
    return tuple(sum(p[k] for p in points)/len(points) for k in range(3))


def _source_edges():
    return tuple(sorted({tuple(sorted((i, j))) for face in FACES for i, j in zip(face, face[1:]+face[:1])}))


def _reference_planes(av, bv, quaternion):
    # Every strictly convex four-vertex face is split by the declared first
    # ear into (last, first, second) and (second, third, last). These explicit
    # fixture triangles, not any SUT face/hull/part output, generate SAT edges.
    triangles = tuple(tri for a, b, c, d in FACES for tri in ((d, a, b), (b, c, d)))
    edges = tuple(sorted({tuple(sorted((i, j))) for tri in triangles for i, j in zip(tri, tri[1:]+tri[:1])}))
    aa = tuple(_minus(av[j], av[i]) for i, j in edges)
    bb = tuple(_minus(bv[j], bv[i]) for i, j in edges)
    axes = {_canonical(_rotation(tuple(F(k == axis) for k in range(3)), quaternion)) for axis in range(3)}
    axes.update(_canonical(_wedge(a, b)) for a in aa for b in bb)
    axes.discard(None)
    rows = []
    for axis in sorted(axes):
        a = [_scalar(axis, p) for p in av]
        b = [_scalar(axis, p) for p in bv]
        rows.extend(((axis, min(b)-max(a)), (axis, max(b)-min(a))))
    return tuple(sorted(set(rows)))


def _expected_local(av, bv, scale, quaternion):
    rows = []
    for vertices, other, low, high, kind in ((av, bv, BLO, BHI, 'VF'), (bv, av, ALO, AHI, 'FV')):
        for fi, face in enumerate(FACES):
            axis, sign = FACE_AXES[fi]
            perpendicular = tuple(k for k in range(3) if k != axis)
            magnitude = F(2)*scale*scale*(high[perpendicular[0]]-low[perpendicular[0]])*(high[perpendicular[1]]-low[perpendicular[1]])
            normal = _rotation(tuple(magnitude*sign if k == axis else F(0) for k in range(3)), quaternion)
            minimum = min(_scalar(normal, p) for p in vertices)
            a, b, c, d = face
            for vi, vertex in enumerate(vertices):
                if _scalar(normal, vertex) != minimum:
                    continue
                label = (kind, ('vertex', vi), ('face', fi)) if kind == 'VF' else (kind, ('face', fi), ('vertex', vi))
                outward = normal if kind == 'VF' else tuple(-v for v in normal)
                for indices in ((d, a, b), (b, c, d)):
                    points = tuple(_minus(other[i], vertex) if kind == 'VF' else _minus(vertex, other[i]) for i in indices)
                    rows.append((label, tuple(sorted(points)), outward))
    for ea in _source_edges():
        for eb in _source_edges():
            normal = _wedge(_minus(bv[eb[1]], bv[eb[0]]), _minus(av[ea[1]], av[ea[0]]))
            if not any(normal):
                continue
            for outward in (normal, tuple(-x for x in normal)):
                lower = min(_scalar(outward, p) for p in av)
                upper = max(_scalar(outward, p) for p in bv)
                if (all(_scalar(outward, av[i]) == lower for i in ea)
                        and all(_scalar(outward, bv[j]) == upper for j in eb)):
                    polygon = tuple(sorted(_minus(bv[j], av[i]) for i in ea for j in eb))
                    rows.append((('EE', ('edge', *ea), ('edge', *eb)), polygon, outward))
                    break
    return tuple(sorted(rows))


def _assert_orientation(polygon, expected_normal):
    # A test-owned area vector also checks orientation, not only vertex sets.
    origin = polygon[0]
    area = tuple(sum(_wedge(_minus(polygon[i], origin), _minus(polygon[i+1], origin))[k]
                     for i in range(1, len(polygon)-1)) for k in range(3))
    assert _scalar(area, expected_normal) > 0, 'all-field independent ring orientation'


@pytest.mark.parametrize('exponent', [-400, 0, 400])
@pytest.mark.parametrize('translation', [0, 10**3, 10**5, 10**6])
def test_all_boundary_fields_have_independent_cartesian_values(exponent, translation):
    rng = random.Random(3109+translation)
    quaternion = tuple(rng.randrange(1, 8) for _ in range(4))
    while any(value == 0 for axis in range(3) for value in
              _rotation(tuple(F(k == axis) for k in range(3)), quaternion)):
        quaternion = tuple(rng.randrange(1, 8) for _ in range(4))
    scale = F(2)**exponent
    # The common shift has exactly the requested Euclidean magnitude, using
    # the 3-4-12-13 Pythagorean triple; origins remain mutually asymmetric.
    ta = (F(3*translation, 13), F(4*translation, 13), F(12*translation, 13))
    tb = tuple(ta[k]+(5, 7, -11)[k] for k in range(3))
    assert _scalar(ta, ta) == translation*translation
    delta = _minus(tb, ta)
    av = tuple(_transform(p, scale, ta, quaternion) for p in _corners(ALO, AHI))
    bv = tuple(_transform(p, scale, tb, quaternion) for p in _corners(BLO, BHI))
    A, C = Polyhedron(list(av), list(FACES)), Polyhedron(list(bv), list(FACES))
    model = G.global_entrance(A, C)
    boundary = B.explicit_boundary(model)
    assert boundary.model is model
    assert (boundary.candidate_facets, boundary.arranged_patches) == (6, 6)
    assert len(boundary.patches) == len(boundary.arrangement) == 6
    planes = _reference_planes(av, bv, quaternion)
    assert boundary.planes == planes, 'independent complete planes including triangle-diagonal redundancy'

    low = tuple(F(BLO[k]-AHI[k]) for k in range(3))
    high = tuple(F(BHI[k]-ALO[k]) for k in range(3))
    corners = tuple(_transform(p, scale, delta, quaternion) for p in _corners(low, high))
    expected = {}
    for fi, indices in enumerate(FACES):
        polygon = tuple(corners[i] for i in indices)
        axis, sign = FACE_AXES[fi]
        direction = _rotation(tuple(F(k == axis) for k in range(3)), quaternion)
        normal = _canonical(direction)
        outward = normal if sign*_scalar(normal, direction) > 0 else tuple(-x for x in normal)
        centre = _mean(polygon)
        times = [abs((h-_scalar(n, centre))/_scalar(n, normal))
                 for n, h in planes if _scalar(n, normal) and h != _scalar(n, centre)]
        step = min(times)/2
        sides = tuple(tuple(centre[k]+s*step*normal[k] for k in range(3)) for s in (-1, 1))
        # Inward along canonical n iff outward.n is negative.
        states = (1, -1) if _scalar(outward, normal) > 0 else (-1, 1)
        expected[tuple(sorted(polygon))] = (normal, outward, sides, states)
    assert {tuple(sorted(p.polygon)) for p in boundary.patches} == set(expected)
    assert {tuple(sorted(p.polygon)) for p in boundary.arrangement} == set(expected)
    for collection, exposed in ((boundary.patches, True), (boundary.arrangement, False)):
        for patch in collection:
            canonical, outward, sides, states = expected[tuple(sorted(patch.polygon))]
            expected_normal = outward if exposed else canonical
            assert patch.normal == expected_normal, 'independent exact patch/arrangement normal'
            assert patch.side_points == sides, 'independent exact canonical-plane side points'
            assert patch.side_states == states, 'independent closed box side labels'
            assert patch.sources == ((0, 0),), 'independent convex-pair provenance'
            _assert_orientation(patch.polygon, expected_normal)

    expected_probes = {'vertex': set(corners), 'edge': set(), 'face': set(), 'side': set()}
    for indices in FACES:
        polygon = tuple(corners[i] for i in indices)
        expected_probes['face'].add(_mean(polygon))
        expected_probes['edge'].update(_mean((a, b)) for a, b in zip(polygon, polygon[1:]+polygon[:1]))
        expected_probes['side'].update(expected[tuple(sorted(polygon))][2])
    assert boundary.probes() == {name: tuple(sorted(points)) for name, points in expected_probes.items()}, 'independent every probe coordinate'

    local = B.local_cover_candidates(A, C)
    expected_local = _expected_local(av, bv, scale, quaternion)
    actual = tuple(sorted((p.label, tuple(sorted(p.polygon)), p.normal) for p in local))
    assert actual == expected_local, 'independent every local VF/FV/EE label coordinate normal'
    for patch in local:
        _assert_orientation(patch.polygon, patch.normal)
    clipped = B.clip_local_covers(boundary, local)
    expected_clipped = []
    for label, polygon, normal in expected_local:
        canonical = _canonical(normal)
        outward = canonical if _scalar(canonical, normal) > 0 else tuple(-x for x in canonical)
        expected_clipped.append((label, polygon, outward))
    assert tuple(sorted((p.label, tuple(sorted(p.polygon)), p.normal) for p in clipped)) == tuple(sorted(expected_clipped)), 'independent every clipped local field'
    for patch in clipped:
        _assert_orientation(patch.polygon, patch.normal)

    point = tuple((low[k]+high[k])/2+F(k+1, 17) for k in range(3))
    query = _transform(point, scale, delta, quaternion)
    candidates = [((bound-point[k])**2*scale*scale,
                   _transform(tuple(bound if j == k else point[j] for j in range(3)), scale, delta, quaternion))
                  for k in range(3) for bound in (low[k], high[k])]
    minimum = min(square for square, point in candidates)
    distance = boundary.shortest_exit(query)
    assert distance.squared == minimum
    assert distance.tied_exact_points == tuple(sorted(p for square, p in candidates if square == minimum)), 'independent full optimal witness set'
