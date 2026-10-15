"""M3b exact construction, embedded-input and acceleration contracts.

Independent oracle imports: fractions.Fraction, itertools.combinations/product.
The numerical oracle uses its own determinant/Cramer halfspace enumeration;
no production normal, triangulator, clipper, BSP, SAT, or hull is its oracle.
geom3 and test_m3_global3d helpers supply raw inputs only. Analytic orthogonal
unions decide candidate/merge probes; legacy replay is secondary corroboration.
"""
from fractions import Fraction as F
from itertools import combinations, product
import inspect
import textwrap

import pytest

from eab.kernel3d import global_entrance as G
from eab.kernel3d import geom3
from test_m3_global3d import _combine, _prism, _twisted_prism


@pytest.fixture(autouse=True)
def _clear_mutation_caches():
    yield
    G._decompose.cache_clear()
    G._line_sections.cache_clear()


def _det(rows):
    a, b, c = rows
    return (a[0]*(b[1]*c[2]-b[2]*c[1])-
            a[1]*(b[0]*c[2]-b[2]*c[0])+
            a[2]*(b[0]*c[1]-b[1]*c[0]))


def _planes(body):
    """Only triangular input is admitted to this independent audit oracle."""
    result = []
    for face in body.faces:
        assert len(face) == 3
        a, b, c = [body.verts[i] for i in face]
        u = [b[k]-a[k] for k in range(3)]
        v = [c[k]-a[k] for k in range(3)]
        n = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
        result.append((n, sum(n[k]*a[k] for k in range(3))))
    for k in range(3):
        n = tuple(F(j == k) for j in range(3))
        result += [(n, min(p[k] for p in body.verts)), (n, max(p[k] for p in body.verts))]
    return result


def _vertices_by_cramer(constraints, planes=None):
    result = set()
    for rows in combinations(planes if planes is not None else constraints, 3):
        matrix = [row[0] for row in rows]
        determinant = _det(matrix)
        if not determinant:
            continue
        point = tuple(_det([tuple(row[1] if j == k else row[0][j] for j in range(3))
                            for row in rows])/determinant for k in range(3))
        if all(sum(n[k]*point[k] for k in range(3)) <= bound for n, bound in constraints):
            result.add(point)
    return result


def _audit_part(part, source_planes):
    constraints = []
    for face in part.faces:
        matches = [(n, h) for n, h in source_planes
                   if all(sum(n[k]*p[k] for k in range(3)) == h for p in face)]
        assert matches, 'every BSP facet lies on an original or bounding plane'
        n, h = matches[0]
        if sum(n[k]*part.interior[k] for k in range(3)) > h:
            n, h = tuple(-x for x in n), -h
        constraints.append((n, h))
        # Every ordered face has outward orientation, not merely the same set.
        turns = [_det((tuple(b[k]-a[k] for k in range(3)),
                       tuple(p[k]-a[k] for k in range(3)), n))
                 for a, b in zip(face, face[1:]+face[:1]) for p in face]
        assert min(turns) >= 0 and max(turns) > 0, 'ordered BSP face orientation and convex cycle'
    extreme = _vertices_by_cramer(constraints)
    candidates = _vertices_by_cramer(constraints, source_planes)
    assert extreme <= set(part.vertices), 'all independent halfspace extreme points are represented'
    assert set(part.vertices) <= candidates, 'all Steiner coordinates match independent Cramer vertices'
    # Merging retains non-extreme collinear subdivision points. Their exact
    # coordinates are independently certified too, not silently discarded.
    assert part.interior == tuple(sum(p[k] for p in part.vertices)/len(part.vertices) for k in range(3))
    assert all(isinstance(x, F) for p in part.vertices for x in p)


@pytest.mark.parametrize('scale', [F(1, 2**400), F(1), F(2**400)])
def test_both_parts_and_ordered_face_subsets_have_three_scale_exact_references(scale):
    bodies = [geom3.box(center=tuple(q*scale for q in centre), half=tuple(q*scale for q in half))
              for centre, half in (((F(1, 3), -2, F(3, 7)), (1, 2, 3)),
                                   ((-3, F(1, 7), F(5, 11)), (2, 3, 4)))]
    model = G.global_entrance(*bodies)
    for parts, body in zip((model.parts_a, model.parts_b), bodies):
        assert len(parts) == 1
        part = parts[0]
        expected_faces = tuple(tuple(body.verts[i] for i in tri)
                               for p, q, r, s in body.faces for tri in ((s, p, q), (q, r, s)))
        assert part.vertices == tuple(sorted(body.verts)), 'parts_a and parts_b exact vertices'
        assert part.faces == expected_faces, 'every ordered face subset is exact'
        expected_centre = tuple(sum(p[k] for p in body.verts)/8 for k in range(3))
        assert part.interior == expected_centre, 'both exact centres'
    assert model.parts_a != model.parts_b, 'parameter outputs must be distinct'


@pytest.mark.parametrize('scale', [F(1, 2**400), F(1), F(2**400)])
def test_general_bsp_steiner_values_match_independent_cramer_at_three_scales(scale):
    raw = _twisted_prism()
    body = geom3.Polyhedron([tuple(q*scale for q in p) for p in raw.verts], raw.faces)
    parts = G.convex_decomposition(body)
    assert len(parts) > 1
    new_points = set().union(*(set(p.vertices) for p in parts))-set(body.verts)
    assert new_points, 'this is a Steiner construction, not source-vertex selection'
    reference = _planes(body)
    for part in parts:
        _audit_part(part, reference)


@pytest.mark.parametrize('scale', [F(1, 2**400), F(1), F(2**400)])
def test_general_plane_clip_both_sides_have_independent_exact_vertices(scale):
    body = geom3.box(half=(scale,)*3)
    cell = G.convex_decomposition(body)[0]
    n, h = (F(3), F(5), F(7)), F(2, 3)*scale
    minus, plus = G._split_cell(cell, n, h)
    planes = [(tuple(F(j == k) for j in range(3)), sign*scale)
              for k in range(3) for sign in (-1, 1)]+[(n, h)]
    # The convex fast path retains source triangles, so their face diagonals
    # create extra collinear cut points. Add their independent edge planes.
    for face in cell.faces:
        for a, b in zip(face, face[1:]+face[:1]):
            for axis in range(3):
                edge = tuple(b[k]-a[k] for k in range(3))
                basis = tuple(F(k == axis) for k in range(3))
                normal = (edge[1]*basis[2]-edge[2]*basis[1],
                          edge[2]*basis[0]-edge[0]*basis[2], edge[0]*basis[1]-edge[1]*basis[0])
                if any(normal):
                    row = (normal, sum(normal[k]*a[k] for k in range(3)))
                    if row not in planes:
                        planes.append(row)
    _audit_part(minus, planes)
    _audit_part(plus, planes)
    assert set(minus.vertices) != set(plus.vertices)


def _invalid_inputs():
    cube = geom3.box(half=(F(1),)*3)
    inverted = geom3.box(center=(4, 0, 0), half=(F(1, 3),)*3)
    inverted = geom3.Polyhedron(inverted.verts, [tuple(reversed(f)) for f in inverted.faces])
    # Two disjoint combinatorial spheres crossing geometrically, while total
    # volume stays strictly positive: the historical volume check accepted it.
    crossed = _combine(cube, geom3.box(center=(F(3, 2), F(1, 3), F(1, 5))))
    coplanar = _combine(cube, geom3.box(center=(2, F(1, 3), F(1, 5))))
    zero = geom3.Polyhedron([(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)],
                           [(0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)])
    raw_pinched = _combine(cube, geom3.box(center=(2, 2, 2)))
    welded = tuple(dict.fromkeys(raw_pinched.verts))
    pinched = geom3.Polyhedron(welded, [tuple(welded.index(raw_pinched.verts[i]) for i in face)
                                      for face in raw_pinched.faces])
    return [('nonmanifold_edge', geom3.Polyhedron(cube.verts, cube.faces[:-1])),
            ('inconsistent_face', geom3.Polyhedron(cube.verts, [tuple(reversed(cube.faces[0]))]+list(cube.faces[1:]))),
            ('crossed_shells', crossed), ('coplanar_overlap', coplanar),
            ('pinched_vertex_with_manifold_edges', pinched),
            ('inverted_shell_hidden_by_total_volume', _combine(cube, inverted)),
            ('zero_volume', zero)]


@pytest.mark.parametrize('name,body', _invalid_inputs())
def test_invalid_surfaces_are_rejected_exactly(name, body):
    with pytest.raises(ValueError, match='global3d'):
        G.convex_decomposition(body)


def test_unused_vertex_buffer_is_not_an_isolated_surface_piece_or_bbox_input():
    body = _prism([(0, 0), (3, 0), (3, 1), (1, 1), (1, 3), (0, 3)])
    far = (F(10**20), F(-10**30), F(10**40))
    buffered = geom3.Polyhedron([far]+list(body.verts)+[far],
                                [tuple(i+1 for i in face) for face in body.faces])
    reference = G.convex_decomposition(body)
    assert G.convex_decomposition(buffered) == reference, 'unused coordinates cannot alter BSP or part values'
    a = geom3.box(half=(F(1, 4),)*3)
    plain, extra = G.global_entrance(a, body), G.global_entrance(a, buffered)
    assert extra.line_sections(direction=(2, -1, 3)) == plain.line_sections(direction=(2, -1, 3))
    assert extra.classify((F(3, 2), F(3, 2), 0)) == plain.classify((F(3, 2), F(3, 2), 0)) == -1


@pytest.mark.parametrize('scale,shift', [(F(1, 2**400), F(0)),
                                        (F(1), F(10**6)), (F(2**400), F(10**5))])
def test_exact_embedded_rejection_is_rigid_motion_and_unit_covariant(scale, shift):
    body = dict(_invalid_inputs())['crossed_shells']
    moved = geom3.Polyhedron([((F(3, 5)*p[0]-F(4, 5)*p[1])*scale+shift,
                              (F(4, 5)*p[0]+F(3, 5)*p[1])*scale-2*shift,
                              F(p[2])*scale+3*shift) for p in body.verts], body.faces)
    with pytest.raises(ValueError, match='self-intersecting'):
        G.convex_decomposition(moved)


def test_spatial_pruning_handles_nonaxial_lines_without_dropping_tangencies(monkeypatch):
    a = geom3.box(half=(F(1, 2),)*3)
    b = geom3.box(center=(3, 3, 0), half=(F(1, 2),)*3)
    model = G.global_entrance(a, b)
    def forbidden(*args):
        raise AssertionError('disjoint Cartesian parameter intervals must prune before feature SAT')
    monkeypatch.setattr(G, '_pair_slabs', forbidden)
    line = model.line_sections(direction=(1, -1, 0))
    assert line.closed == line.opened == ()
    monkeypatch.undo()
    b = geom3.box(center=(3, 1, 0), half=(F(1, 2),)*3)
    line = G.global_entrance(a, b).line_sections(direction=(1, 0, 0))
    assert line.closed == ((F(2), F(4)),), 'closed AABB tangency cannot be pruned'
    assert line.opened == (), 'stationary tangency is not penetration'


def _mutate(monkeypatch, function, before, after):
    source = textwrap.dedent(inspect.getsource(function))
    assert source.count(before) == 1, 'mutation site must be unambiguous'
    namespace = dict(vars(G))
    exec(compile(source.replace(before, after), '<M3b internal semantic mutation>', 'exec'), namespace)
    monkeypatch.setattr(G, function.__name__, namespace[function.__name__])
    G._decompose.cache_clear()
    G._line_sections.cache_clear()


def _crossing_assertion():
    body = dict(_invalid_inputs())['coplanar_overlap']
    try:
        G.convex_decomposition(body)
    except ValueError as error:
        assert 'self-intersecting' in str(error), 'precise embedded-intersection rejection'
    else:
        raise AssertionError('overlapping coplanar shells must be rejected before decomposition')


def test_self_intersection_detection_mutation_dies_at_semantic_assertion(monkeypatch):
    _crossing_assertion()
    _mutate(monkeypatch, G._validate_embedded,
            'meeting = _triangle_meeting(a, b)', 'meeting = set()')
    # This defect really admits an invalid surface: the coplanar overlap has
    # zero shared volume, so the downstream volume certificate cannot save it.
    with pytest.raises(AssertionError, match='overlapping coplanar shells must be rejected'):
        _crossing_assertion()


def _candidate_assertion():
    a = geom3.box(half=(F(1, 2),)*3)
    b = _combine(geom3.box(half=(F(1, 2),)*3),
                 geom3.box(center=(0, 0, 3), half=(F(1, 2),)*3))
    line = G.global_entrance(a, b).line_sections()
    assert line.closed == ((F(-1), F(1)), (F(2), F(4))), 'all exact box candidates are retained'


def test_spatial_candidate_omission_mutation_dies_at_interval_assertion(monkeypatch):
    _candidate_assertion()
    _mutate(monkeypatch, G._line_candidate, 'return True', 'return b.interior[2] < 2')
    with pytest.raises(AssertionError, match='all exact box candidates are retained'):
        _candidate_assertion()


def test_certified_merge_never_fills_the_missing_quadrant():
    a = geom3.box(half=(F(1, 4),)*3)
    b = _prism([(0, 0), (3, 0), (3, 1), (1, 1), (1, 3), (0, 3)])
    model = G.global_entrance(a, b)
    assert len(model.parts_b) > 1, 'nonconvex union must not be convexified'
    assert model.classify((F(3, 2), F(3, 2), 0)) == -1, 'missing quadrant remains exterior'


def test_nonconvex_merge_mutation_is_stopped_by_independent_geometric_assertion(monkeypatch):
    # Two genuine full-facet neighbours. Their apex-to-apex midpoint lies
    # outside the common base, so the union is nonconvex. This enters the real
    # shared-facet candidate branch; it is not output replacement after merge.
    base = ((F(0),)*3, (F(2), F(0), F(0)), (F(0), F(2), F(0)))
    parts = tuple(G.convex_decomposition(geom3.tetra(*base, apex))[0]
                  for apex in ((F(0), F(0), F(1)), (F(4), F(4), F(-1))))
    def check():
        merged = G._merge_parts(parts)
        model = G.GlobalEntrance3D(G.convex_decomposition(geom3.box(half=(F(1, 16),)*3)), merged)
        # Entire probe box violates x+y+2z<=2 of the upper tetrahedron and
        # x+y+6z<=2 of the lower one, independently of tested geometry.
        assert model.classify((F(2), F(2), 0)) == -1, 'full-facet nonconvex merge filled independently excluded region'
    check()
    before = ('                if any(_dot(n, _sub(p, q)) > 0 for n, q in planes for p in vertices):\n'
              '                    continue\n'
              '                parts[i] = _part(faces)')
    _mutate(monkeypatch, G._merge_parts, before, '                parts[i] = _box_part(vertices)')
    with pytest.raises(AssertionError, match='full-facet nonconvex merge filled independently excluded region'):
        check()
