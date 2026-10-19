"""M3 independent gates: integer winding/intersections, not construction geometry.

Primary oracle imports only g0_oracle (Fraction, math.lcm, oracle_construction).
It shares no hull, ear decomposition, cover, arrangement or geometry primitive
with global_entrance. Test data construction uses plain rational coordinates.
Large full-family/bb52 replay lives in the M3 evidence script, not skipped tests.
"""
from fractions import Fraction as F
import ast
import inspect
import random
import textwrap

import pytest

from eab.kernel2d import g0_oracle as oracle
from eab.kernel2d import global_entrance as module
from eab.kernel2d.global_entrance import GlobalEntrance2, global_entrance
from eab.numeric_domain import ConstructionDomainError
from eab.oracle_construction import scalar_exact, sqrt_exact


SQUARE = [(0, 0), (1, 0), (1, 1), (0, 1)]
THIN_L = [(0, 0), (3, 0), (3, F(1, 10)), (F(1, 10), F(1, 10)), (F(1, 10), 3), (0, 3)]
CHANNEL = [(0, 0), (3, 0), (3, 1), (1, 1), (1, F(9, 5)), (3, F(9, 5)), (3, F(14, 5)), (0, F(14, 5))]
WEDGE = [(0, 0), (F(3, 5), F(1, 5)), (F(1, 5), F(3, 4))]
U = [(-1, -1), (2, -1), (2, 2), (1, 2), (1, 0), (0, 0), (0, 2), (-1, 2)]
PIN = [(0, F(1, 2)), (1, F(1, 2)), (1, F(3, 2)), (0, F(3, 2))]
POCKET = [(0, 0), (6, 0), (6, 2), (5, 2), (5, 1), (1, 1), (1, 5), (5, 5), (5, 4), (6, 4), (6, 6), (0, 6)]
INTERLOCK = [(0, 0), (4, 0), (4, 1), (3, 1), (3, 2), (2, 2), (2, 1), (1, 1), (1, 2), (0, 2)]


def _families():
    return [
        ("thin_L", [(0, 0), (F(1, 2), 0), (F(1, 2), F(1, 20)), (0, F(1, 20))], THIN_L),
        ("slot_wedge", WEDGE, CHANNEL),
        ("interlock_section", [(0, 0), (F(1, 2), 0), (F(1, 2), F(1, 2)), (0, F(1, 2))], INTERLOCK),
        ("tight_fit", PIN, U),
        ("pocket_hole", [(F(5, 2)*x, F(5, 2)*y) for x, y in SQUARE], POCKET),
        ("collinear", [(0, 0), (F(1, 2), 0), (1, 0), (1, 1), (0, 1)], THIN_L),
    ]


def _oracle_state(A, B, x):
    return oracle.overlap(oracle.translate(A, x), B)


def _oracle_topology(A, B, x):
    moved = oracle.translate(A, x)
    state = oracle.overlap(moved, B)
    return (0 if oracle.boundary_has_exterior(moved, oracle.points(B)) else 1) if state == 0 else state


def _assert_states(g: GlobalEntrance2, probes):
    for p in probes:
        assert g.membership(p) == _oracle_state(g.A, g.B, p), ("body label mismatch", p)
        assert g.topology(p) == _oracle_topology(g.A, g.B, p), ("topological label mismatch", p)


@pytest.mark.parametrize("name,A,B", _families(), ids=[x[0] for x in _families()])
def test_global_body_and_topology_match_independent_oracle_without_skip(name, A, B):
    g = GlobalEntrance2(A, B)
    probes = {p for cell in g.cells for p in cell}
    for piece in g.clipped_covers:
        probes.update((piece.start, piece.end, ((piece.start[0]+piece.end[0])/2, (piece.start[1]+piece.end[1])/2)))
        probes.update(piece.side_points)
    probes.update((F(x, 4), F(y, 4)) for x in (-8, -1, 0, 1, 5, 12, 25) for y in (-8, -1, 0, 1, 5, 12, 25))
    _assert_states(g, sorted(probes))
    assert {-1, 0, 1} <= {g.membership(p) for p in probes}


@pytest.mark.parametrize("A,B", [(SQUARE, THIN_L), (PIN, U)], ids=["L", "tight"])
def test_subdivision_has_all_dimensions_and_exact_oracle_labels(A, B):
    g = GlobalEntrance2(A, B)
    subdivision = g.subdivision
    assert subdivision.vertices and subdivision.edges and subdivision.faces
    for cells in (subdivision.vertices, subdivision.edges, subdivision.faces):
        for cell in cells:
            assert cell.state == _oracle_state(A, B, cell.sample), "subdivision label mismatch"
    for edge in subdivision.edges:
        _assert_states(g, g.side_probes(*edge.vertices))
    # A true planar subdivision, not just overlapping convex cells: Euler for
    # connected rectangle closure, all boundary subdivisions explicitly split.
    assert len(subdivision.vertices)-len(subdivision.edges)+len(subdivision.faces) == 1


@pytest.mark.parametrize("name,A,B", _families(), ids=[x[0] for x in _families()])
def test_clipped_covers_are_exactly_boundary_and_cover_oracle_ray_exits(name, A, B):
    g = GlobalEntrance2(A, B)
    hidden = exposed = 0
    for piece in g.clipped_covers:
        p = ((piece.start[0]+piece.end[0])/2, (piece.start[1]+piece.end[1])/2)
        truth = _oracle_topology(A, B, p)
        assert (truth == 0) == piece.exposed, "cover clipping exposure mismatch"
        side = tuple(_oracle_state(A, B, q) for q in piece.side_points)
        assert side == piece.side_states, "cover side label mismatch"
        if piece.exposed:
            exposed += 1
            assert _oracle_state(A, B, p) == 0, "exposed cover must be contact"
            assert (side[0] == -1) != (side[1] == -1), "exposed cover must separate E and exterior"
        else:
            hidden += 1
            assert truth == 1, "hidden cover must be interior E"
    assert hidden and exposed
    origins = [(0, 0), (F(1, 4), F(1, 4)), (F(3, 4), F(3, 4))]
    origin = next(p for p in origins if _oracle_topology(A, B, p) == 1)
    for direction in [(1, 0), (0, 1), (-1, 0), (0, -1), (2, 3), (-3, 2), (5, -1), (-1, -3)]:
        time = oracle.ray_exit(oracle.translate(A, origin), oracle.points(B), direction)
        p = origin[0]+time*direction[0], origin[1]+time*direction[1]
        assert any(oracle.on_segment(p, a, b) for a, b in g.boundary), "oracle ray exit missed by production boundary"


def test_global_shortest_exit_distinguishes_tight_contact_seam():
    g = GlobalEntrance2(PIN, U)
    assert g.membership((0, 0)) == 0 and g.topology((0, 0)) == 1
    # Independent Cartesian union: E=[-2,2] x [-5/2,3/2].
    got = g.shortest_exit((0, 0))
    assert got.squared == F(9, 4), "global exit cannot return the local zero-gap seam"
    assert got.exact_point == (0, F(3, 2))
    assert g.distance_to_e((0, 0)).squared == 0
    for x in [(F(1, 3), F(1, 5)), (-1, 1), (1, -1)]:
        want = min((x[0]+2)**2, (2-x[0])**2, (x[1]+F(5, 2))**2, (F(3, 2)-x[1])**2)
        assert g.shortest_exit(x).squared == want


def test_shortest_exit_tied_minimizer_set_not_lex_representative_is_covariant():
    square = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    def rotate(p):
        return -p[1], p[0]
    first = GlobalEntrance2(square, square).shortest_exit((0, 0))
    other = GlobalEntrance2(list(map(rotate, square)), list(map(rotate, square))).shortest_exit((0, 0))
    assert first.squared == other.squared == 4
    assert set(first.tied_exact_points) == {(-2, 0), (2, 0), (0, -2), (0, 2)}
    assert set(map(rotate, first.tied_exact_points)) == set(other.tied_exact_points)
    assert first.exact_point == other.exact_point == (-2, 0)
    assert rotate(first.exact_point) != other.exact_point


@pytest.mark.parametrize("name,A,B", _families(), ids=[x[0] for x in _families()])
def test_local_clipping_covers_the_independently_built_cell_boundary(name, A, B):
    g = GlobalEntrance2(A, B)
    local = [(p.start, p.end) for p in g.clipped_covers if p.exposed]
    # Exact interval cover along each global segment, not a midpoint-only
    # assertion: union the local parameter intervals and require all [0,1].
    for a, b in g.boundary:
        axis = 0 if a[0] != b[0] else 1
        intervals = []
        for p, q in local:
            if oracle.turn(a, b, p) == oracle.turn(a, b, q) == 0:
                lo, hi = sorted(((p[axis]-a[axis])/(b[axis]-a[axis]), (q[axis]-a[axis])/(b[axis]-a[axis])))
                if hi >= 0 and lo <= 1:
                    intervals.append((max(F(0), lo), min(F(1), hi)))
        end = F(0)
        for lo, hi in sorted(intervals):
            assert lo <= end, "local clips leave a gap on global boundary"
            end = max(end, hi)
        assert end == 1, "local clips omit global boundary"


def test_global_entrance_can_have_a_bounded_hole():
    A = [(F(5, 2)*x, F(5, 2)*y) for x, y in SQUARE]
    g = GlobalEntrance2(A, POCKET)
    point = (F(3, 2), F(3, 2))
    assert g.membership(point) == -1
    # Four independently chosen axis barriers bound this free pocket.
    for point in [(0, F(3, 2)), (3, F(3, 2)), (F(3, 2), 0), (F(3, 2), 3)]:
        assert _oracle_state(A, POCKET, point) == g.membership(point) == 1


def test_distance_to_e_matches_independent_features():
    g = GlobalEntrance2(WEDGE, CHANNEL)
    for x in [(-3, -4), (4, F(1, 3)), (F(3, 2), F(11, 10)), (0, 0)]:
        state = _oracle_state(WEDGE, CHANNEL, x)
        expected = F(0)
        if state < 0:
            moved = oracle.translate(WEDGE, x)
            expected = min(oracle.segment_square(p, a, b)[0]
                           for P, Q in ((moved, oracle.points(CHANNEL)), (oracle.points(CHANNEL), moved))
                           for p in P for a, b in zip(Q, Q[1:]+Q[:1]))
        assert g.distance_to_e(x).squared == expected, "global distance differs from independent boundary features"


def _ray_oracle(A, B, x, d):
    events = {F(0)}
    for P, Q, direction in ((oracle.translate(A, x), oracle.points(B), d), (oracle.points(B), oracle.translate(A, x), (-d[0], -d[1]))):
        for p in P:
            for a, b in zip(Q, Q[1:]+Q[:1]):
                h = oracle.turn(a, b, p)
                slope = (b[0]-a[0])*direction[1]-(b[1]-a[1])*direction[0]
                if slope:
                    events.add(-h/slope)
                elif not h:
                    for k in (0, 1):
                        if direction[k]:
                            events.update((q[k]-p[k])/direction[k] for q in (a, b))
    return next((t for t in sorted(events) if t >= 0 and _oracle_state(A, B, (x[0]+t*d[0], x[1]+t*d[1])) >= 0), None)


@pytest.mark.parametrize("x,d", [((-5, 0), (1, 0)), ((5, 3), (-2, -1)), ((1, 5), (0, -1)), ((1, 1), (1, 0)), ((9, 9), (1, 1))])
def test_global_first_entrance_is_complete_without_body_predicates(x, d, monkeypatch):
    want = _ray_oracle(WEDGE, CHANNEL, x, d)
    def forbidden(*args, **kwargs):
        raise AssertionError("production called body oracle")
    from eab.kernel2d import exact, geom
    monkeypatch.setattr(exact, "polygons_overlap_exact", forbidden)
    monkeypatch.setattr(geom, "polygons_overlap", forbidden)
    monkeypatch.setattr(oracle, "overlap", forbidden)
    got = GlobalEntrance2(WEDGE, CHANNEL).first_entrance(x, d)
    assert (None if got is None else got.exact_time) == want, "global first entrance mismatch"


def test_existing_concave_membership_and_first_entrance_call_brute_zero_times(monkeypatch):
    from eab.kernel2d import exact, geom, entrance, covers
    calls = []
    def forbidden(*args, **kwargs):
        calls.append(1)
        raise AssertionError("production called brute intersection")
    monkeypatch.setattr(exact, "polygons_overlap_exact", forbidden)
    monkeypatch.setattr(geom, "polygons_overlap", forbidden)
    monkeypatch.setattr(entrance, "polygons_overlap_exact", forbidden)
    assert covers.membership_convex(PIN, U, (0, 0)) == 1
    got = entrance.first_entrance(WEDGE, CHANNEL, (-5, 0), (1, 0))
    assert got.kind == "entrance" and got.t_exact == F(22, 5)
    assert len(calls) == 0


@pytest.mark.parametrize("exponent", [-400, 0, 397])
def test_public_constructions_three_tiers_and_exact_motion_covariance(exponent):
    scale = F(2)**exponent
    # Exact rational rotation (3/5,4/5), independent translations of A and B.
    def rotate(p):
        return (3*p[0]-4*p[1])/F(5), (4*p[0]+3*p[1])/F(5)
    ta, tb = (10**6, -3*10**5), (-4*10**5, 7*10**5)
    def body(P, t):
        return [(scale*(rotate(p)[0]+t[0]), scale*(rotate(p)[1]+t[1])) for p in P]
    def config(p):
        return scale*(rotate(p)[0]+tb[0]-ta[0]), scale*(rotate(p)[1]+tb[1]-ta[1])
    original, moved = GlobalEntrance2(PIN, U), GlobalEntrance2(body(PIN, ta), body(U, tb))
    for p in [(0, 0), (F(1, 3), 1), (2, 0), (3, 0)]:
        assert moved.membership(config(p)) == original.membership(p)
        assert moved.topology(config(p)) == original.topology(p)
    exact = moved.shortest_exit(config((0, 0)))
    assert exact.squared == scale*scale*F(9, 4)
    assert exact.exact_point == config((0, F(3, 2)))
    assert exact.distance == sqrt_exact(exact.squared)
    assert exact.point == tuple(scalar_exact(v) for v in exact.exact_point)
    hit = moved.first_entrance(config((3, 0)), tuple(-scale*v for v in rotate((1, 0))))
    assert hit.exact_time == 1 and hit.time == scalar_exact(F(1))
    assert hit.point == tuple(scalar_exact(v) for v in config((2, 0)))
    # Match every clipped segment after motion, with orientation-free endpoints.
    before = {tuple(sorted((config(p.start), config(p.end)))) for p in original.clipped_covers if p.exposed}
    after = {tuple(sorted((p.start, p.end))) for p in moved.clipped_covers if p.exposed}
    assert before == after


@pytest.mark.parametrize("shift,scale,rotation", [(0, F(1, 1000), 0), (10**3, F(1), 1), (10**5, F(1000), 2)])
def test_public_api_rigid_motion_with_independently_varied_translation_scale(shift, scale, rotation):
    def rotate(p):
        if rotation == 0:
            return p
        if rotation == 1:
            return -p[1], p[0]
        return (3*p[0]-4*p[1])/F(5), (4*p[0]+3*p[1])/F(5)
    def body(P, tx, ty):
        return [(scale*rotate(p)[0]+tx, scale*rotate(p)[1]+ty) for p in P]
    def config(p):
        return scale*rotate(p)[0]-3*shift, scale*rotate(p)[1]+4*shift
    a, b = body(PIN, shift, -shift), body(U, -2*shift, 3*shift)
    base, moved = GlobalEntrance2(PIN, U), GlobalEntrance2(a, b)
    for p in [(0, 0), (2, 0), (3, 0)]:
        assert moved.membership(config(p)) == base.membership(p)
        assert moved.topology(config(p)) == base.topology(p)
    assert moved.distance_to_e(config((3, 0))).squared == scale*scale
    assert moved.shortest_exit(config((0, 0))).squared == scale*scale*F(9, 4)
    assert moved.shortest_exit(config((0, 0))).exact_point == config((0, F(3, 2)))
    direction = tuple(-scale*x for x in rotate((1, 0)))
    assert moved.first_entrance(config((3, 0)), direction).exact_time == 1
    assert {tuple(sorted((config(a), config(b)))) for a, b in base.boundary} == set(moved.boundary)
    # Vertical subdivision is orientation-dependent; its semantic labels, not
    # the artificial vertical edges, must be covariant under rotation.
    for cell in (*moved.subdivision.vertices, *moved.subdivision.edges, *moved.subdivision.faces):
        assert cell.state == _oracle_state(a, b, cell.sample)


@pytest.mark.parametrize("exponent", [-400, 0, 397])
def test_every_exact_construction_field_matches_an_analytic_hexagon(exponent):
    """Independent hand-derived difference of two right triangles, every field.

    Reference halfplanes: -2<=x<=3, -1<=y<=2, x+2y+2>=0,
    2x+3y<=6. No production hull/triangulator/clip/subdivision helper is used.
    """
    s = F(2)**exponent
    def point(p):
        return s*p[0], s*p[1]
    A, B = [(0, 0), (2, 0), (0, 1)], [(0, 0), (3, 0), (0, 2)]
    g = GlobalEntrance2(list(map(point, A)), list(map(point, B)))
    hexagon = [(-2, 0), (0, -1), (3, -1), (3, 0), (0, 2), (-2, 2)]
    assert g.A == tuple(map(point, A)) and g.B == tuple(map(point, B))
    assert g.parts_a == (tuple(map(point, A)),) and g.parts_b == (tuple(map(point, B)),)
    assert g.cells == (tuple(map(point, hexagon)),)
    segments = {tuple(sorted((point(a), point(b)))) for a, b in zip(hexagon, hexagon[1:]+hexagon[:1])}
    assert set(g.cell_edges) == set(g.boundary) == segments
    planes = [(1, 0, 2), (-1, 0, 3), (0, 1, 1), (0, -1, 2), (1, 2, 2), (-2, -3, 6)]
    def state(p):
        x, y = p[0]/s, p[1]/s
        signs = [nx*x+ny*y+c for nx, ny, c in planes]
        return -1 if min(signs) < 0 else (0 if min(signs) == 0 else 1)
    labelled = [(('VE', 0, 1), (3, 0), (0, 2)), (('EV', 0, 2), (0, 2), (-2, 2)),
                (('EV', 1, 0), (-2, 0), (0, -1)), (('VE', 1, 2), (-2, 2), (-2, 0)),
                (('VE', 2, 0), (0, -1), (3, -1)), (('EV', 2, 1), (3, -1), (3, 0))]
    assert len(g.clipped_covers) == len(labelled)
    for piece, (label, a, b) in zip(g.clipped_covers, labelled):
        assert (piece.label, piece.start, piece.end, piece.exposed, piece.body_state) == (label, point(a), point(b), True, 0)
        x, y = F(a[0]+b[0], 2), F(a[1]+b[1], 2)
        dx, dy = a[1]-b[1], b[0]-a[0]
        step = F(1)
        for nx, ny, c in planes:
            h, slope = nx*x+ny*y+c, nx*dx+ny*dy
            if h and slope:
                step = min(step, abs(h/slope)/2)
        expected = point((x+step*dx, y+step*dy)), point((x-step*dx, y-step*dy))
        assert piece.side_points == g.side_probes(point(a), point(b)) == expected
        assert piece.side_states == tuple(state(p) for p in expected)
    subdivision = g.subdivision
    vertices = [(-2, -1), (-2, 0), (-2, 2), (0, -1), (0, 2), (3, -1), (3, 0), (3, 2)]
    assert {cell.sample for cell in subdivision.vertices} == set(map(point, vertices))
    faces = [([(-2, 0), (0, -1), (0, 2), (-2, 2)], (-1, F(3, 4)), 1),
             ([(0, -1), (3, -1), (3, 0), (0, 2)], (F(3, 2), 0), 1),
             ([(-2, -1), (0, -1), (-2, 0)], (-1, F(-3, 4)), -1),
             ([(3, 2), (3, 0), (0, 2)], (F(3, 2), F(3, 2)), -1)]
    assert [(cell.vertices, cell.sample, cell.state) for cell in subdivision.faces] == [
        (tuple(map(point, ring)), point(sample), label) for ring, sample, label in faces]
    expected_edges = {tuple(sorted((point(a), point(b)))) for ring, _, _ in faces for a, b in zip(ring, ring[1:]+ring[:1])}
    assert {cell.vertices for cell in subdivision.edges} == expected_edges
    for cell in subdivision.vertices+subdivision.edges:
        assert cell.sample == tuple(sum(p[k] for p in cell.vertices)/len(cell.vertices) for k in (0, 1))
        assert cell.state == state(cell.sample)
    assert subdivision.exterior_state == -1
    assert g.ray_intervals(point((-4, 0)), point((1, 0))) == ((F(2), F(7)),)
    assert g.ray_intervals(point((-4, 0)), point((1, 0)), strict=True) == ((F(2), F(7)),)
    hit = g.first_entrance(point((-4, 0)), point((1, 0)))
    assert (hit.exact_time, hit.exact_point, hit.time, hit.point) == (F(2), point((-2, 0)), scalar_exact(F(2)), tuple(scalar_exact(v) for v in point((-2, 0))))
    for result, square, target in [(g.distance_to_e(point((-4, 0))), 4*s*s, point((-2, 0))),
                                   (g.shortest_exit((0, 0)), F(4, 5)*s*s, point((F(-2, 5), F(-4, 5))))]:
        assert (result.squared, result.exact_point) == (square, target)
        assert result.tied_exact_points == (target,)
        assert result.distance == sqrt_exact(square) and result.point == tuple(scalar_exact(v) for v in target)


@pytest.mark.parametrize("scale", [F(1, 1000), F(1), F(1000)])
def test_random_star_body_labels_at_three_distinct_scales(scale):
    rng = random.Random(20261013)
    rays = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
    polygons = []
    for _ in range(2):
        polygons.append([(scale*r*x, scale*r*y) for i, (x, y) in enumerate(rays)
                         for r in [F(rng.randrange(2, 5), 1 if i % 2 == 0 else 5)]])
    g = GlobalEntrance2(*polygons)
    probes = {p for cell in g.cells for p in cell}
    probes.update((scale*F(rng.randrange(-30, 31), 5), scale*F(rng.randrange(-30, 31), 5)) for _ in range(40))
    _assert_states(g, probes)
    assert max(abs(x) for p in g.A for x in p) == 4*scale


def test_global_input_domain_rejects_invalid_and_display_range():
    with pytest.raises(ValueError, match="simple"):
        GlobalEntrance2([(0, 0), (2, 2), (0, 2), (2, 0)], SQUARE)
    with pytest.raises(ValueError, match="zero-length"):
        GlobalEntrance2([(0, 0), (1, 0), (1, 0), (0, 1)], SQUARE)
    with pytest.raises(ValueError, match="nonfinite"):
        GlobalEntrance2([(0, 0), (float("inf"), 0), (0, 1)], SQUARE)
    for scale in (F(2)**-2000, F(2)**2000):
        g = GlobalEntrance2([(scale*x, scale*y) for x, y in PIN], [(scale*x, scale*y) for x, y in U])
        result = g.shortest_exit((0, 0))
        assert result.squared == scale*scale*F(9, 4)
        with pytest.raises(ConstructionDomainError):
            _ = result.distance


def test_primary_oracle_imports_no_global_cover_or_geometry_primitive():
    tree = ast.parse(inspect.getsource(oracle))
    imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert imports == ["eab.oracle_construction", "fractions", "math"]
    assert not any(isinstance(node, ast.Import) for node in ast.walk(tree))


@pytest.mark.parametrize("kind", ["label_inversion", "missing_piece", "open_endpoint", "label_propagation", "local_exit", "remove_clipping"])
def test_internal_mutants_fail_the_expected_assertion(monkeypatch, kind):
    def mutated_method(name, old, new):
        original = getattr(GlobalEntrance2, name)
        if isinstance(original, property):
            original = original.fget
        source = textwrap.dedent(inspect.getsource(original))
        assert old in source
        namespace = dict(module.__dict__)
        exec(compile(source.replace(old, new, 1), "<M3 internal mutant>", "exec"), namespace)
        return namespace[name]
    if kind == "label_inversion":
        monkeypatch.setattr(GlobalEntrance2, "membership", mutated_method("membership", "return 1", "return -1"))
        with pytest.raises(AssertionError, match="body label mismatch"):
            _assert_states(GlobalEntrance2(SQUARE, THIN_L), [(0, 0)])
    elif kind == "missing_piece":
        monkeypatch.setattr(GlobalEntrance2, "__init__", mutated_method("__init__", "for pa in self.parts_a for pb in self.parts_b)", "for pa in self.parts_a for pb in self.parts_b[:1])"))
        with pytest.raises(AssertionError, match="body label mismatch"):
            _assert_states(GlobalEntrance2(SQUARE, THIN_L), [(0, 2)])
    elif kind == "open_endpoint":
        monkeypatch.setattr(GlobalEntrance2, "ray_intervals", mutated_method("ray_intervals", "low < high if strict else low <= high", "low < high"))
        g = GlobalEntrance2(SQUARE, SQUARE)
        with pytest.raises(AssertionError, match="isolated closed contact"):
            assert g.first_entrance((-2, 0), (1, 1)) is not None, "isolated closed contact"
    elif kind == "label_propagation":
        monkeypatch.setattr(GlobalEntrance2, "topology", mutated_method("topology", "if state != 0:", "if state >= -1:"))
        with pytest.raises(AssertionError, match="topological label mismatch"):
            _assert_states(GlobalEntrance2(PIN, U), [(0, 0)])
    elif kind == "local_exit":
        monkeypatch.setattr(GlobalEntrance2, "_nearest_boundary", mutated_method(
            "_nearest_boundary", "for a, b in self.boundary:",
            "for a, b in ((p.start, p.end) for p in self.clipped_covers):"))
        with pytest.raises(AssertionError, match="global exit cannot return the local zero-gap seam"):
            test_global_shortest_exit_distinguishes_tight_contact_seam()
    else:
        monkeypatch.setattr(GlobalEntrance2, "clipped_covers", mutated_method("clipped_covers",
            "exposed = (states[0] >= 0) != (states[1] >= 0)", "exposed = True"))
        with pytest.raises(AssertionError, match="cover clipping exposure mismatch"):
            test_clipped_covers_are_exactly_boundary_and_cover_oracle_ray_exits("tight", PIN, U)
