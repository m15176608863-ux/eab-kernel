"""M3b independent gates for the exact labelled coarsening and weak covers.

Oracle: g0_oracle (imports only eab.oracle_construction, Fraction, math.lcm),
using original polygon integer winding and intersections. It imports no hull,
triangulation, cell index, clipping, or subdivision primitive from the SUT.
Geometry inputs and probe coordinates may be shared, never the adjudicator.
"""
from fractions import Fraction as F
import inspect
from pathlib import Path
import sys
import textwrap

import pytest

from eab.kernel2d import g0_oracle as oracle
from eab.kernel2d import global_entrance as module
from eab.kernel2d.global_entrance import GlobalEntrance2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))


SQUARE = ((0, 0), (1, 0), (1, 1), (0, 1))
L = ((0, 0), (3, 0), (3, 1), (1, 1), (1, 3), (0, 3))
FLAT = ((0, 0), (F(1, 3), 0), (1, 0), (1, 1), (0, 1))
POCKET = ((0, 0), (6, 0), (6, 2), (5, 2), (5, 1), (1, 1), (1, 5), (5, 5), (5, 4), (6, 4), (6, 6), (0, 6))
PLUG = ((1, 1), (5, 1), (5, 5), (1, 5))


def _check_every_stratum(g: GlobalEntrance2):
    sub = g.subdivision
    count = 0
    for cells in (sub.vertices, sub.edges, sub.faces):
        for cell in cells:
            expected = oracle.overlap(oracle.translate(g.A, cell.sample), g.B)
            assert cell.state == expected == g.membership(cell.sample), "complete subdivision stored body label mismatch"
            count += 1
    for edge in sub.edges:
        for p in g.side_probes(*edge.vertices):
            moved = oracle.translate(g.A, p)
            expected = oracle.overlap(moved, g.B)
            topo = (0 if oracle.boundary_has_exterior(moved, g.B) else 1) if expected == 0 else expected
            assert (g.membership(p), g.topology(p)) == (expected, topo), "exact side probe mismatch"
            count += 1
    assert len(sub.vertices)-len(sub.edges)+len(sub.faces) == 1, "subdivision is not a complete rectangle partition"
    assert count == len(sub.vertices)+3*len(sub.edges)+len(sub.faces)
    return count


@pytest.mark.parametrize("A,B", [(FLAT, L), (SQUARE, SQUARE), (PLUG, POCKET)], ids=["flat_L", "nonstrict", "isolated_contact"])
def test_contact_skeleton_subdivision_checks_every_stratum(A, B):
    g = GlobalEntrance2(A, B, merge_convex=True, compact_subdivision=True)
    assert _check_every_stratum(g) > 20


def test_contact_skeleton_preserves_an_isolated_tight_contact():
    g = GlobalEntrance2(PLUG, POCKET, merge_convex=True, compact_subdivision=True)
    assert oracle.overlap(g.A, g.B) == g.membership((0, 0)) == 0
    assert g.topology((0, 0)) == 1
    for p in ((F(1, 100), 0), (F(-1, 100), 0), (0, F(1, 100)), (0, F(-1, 100))):
        assert oracle.overlap(oracle.translate(g.A, p), g.B) == g.membership(p) == 1
    assert any(c.sample == (0, 0) and c.state == 0 for c in g.subdivision.vertices), "isolated contact vertex was regularized away"
    assert not any(oracle.on_segment((0, 0), a, b) for a, b in g._contact_edges), "fixture must exercise isolated-point branch"


@pytest.mark.parametrize("exponent", [-400, 0, 400])
@pytest.mark.parametrize("kind", ["isolated_point", "collinear_seam"])
def test_compact_side_probes_stay_in_adjacent_open_faces_before_every_event(exponent, kind):
    """Independent winding/determinant oracle; no SUT clipping/intersection helper.

    Both cases previously landed exactly on a state-0 point rather than in an
    adjacent open face. Three scales, large independent translation, and a
    quarter turn exercise the real endpoint/isolated-point defect.
    """
    if kind == "isolated_point":
        A, B = PLUG, POCKET[:-1]+((F(10, 3), 6),)+POCKET[-1:]
    else:
        A = ((0, F(1, 2)), (1, F(1, 2)), (1, F(3, 2)), (0, F(3, 2)))
        B = ((-1, -1), (2, -1), (2, 2), (1, 2), (1, 0), (0, 0), (0, 2), (-1, 2))
        A, B = [tuple((-y, x) for x, y in body) for body in (A, B)]
    scale = F(2)**exponent
    A = tuple((scale*x+100000, scale*y-3000) for x, y in A)
    B = tuple((scale*x-2000, scale*y+4000) for x, y in B)
    g = GlobalEntrance2(A, B, merge_convex=True, compact_subdivision=True)
    _assert_adjacent_open_face_probes(g)


def _assert_adjacent_open_face_probes(g: GlobalEntrance2):
    sub = g.subdivision
    box = tuple((min(c.sample[k] for c in sub.vertices), max(c.sample[k] for c in sub.vertices)) for k in (0, 1))
    for edge in sub.edges:
        middle = edge.sample
        neighbors = [face for face in sub.faces if any(oracle.on_segment(middle, a, b)
                     for a, b in zip(face.vertices, face.vertices[1:]+face.vertices[:1]))]
        for point in g.side_probes(*edge.vertices):
            inside_neighbor = any(all(oracle.turn(a, b, point) > 0 for a, b in
                                  zip(face.vertices, face.vertices[1:]+face.vertices[:1])) for face in neighbors)
            a, b = edge.vertices
            outside_box = any((a[k] == b[k] == lo and point[k] < lo) or
                              (a[k] == b[k] == hi and point[k] > hi) for k, (lo, hi) in enumerate(box))
            assert inside_neighbor or outside_box, "compact side probe left its adjacent open face"
            assert g.membership(point) == oracle.overlap(oracle.translate(g.A, point), g.B)
            # A direct exact ray/segment test: no later subdivision event may
            # lie on the closed segment from this edge midpoint to the probe.
            dx, dy = point[0]-middle[0], point[1]-middle[1]
            for other in sub.edges:
                a, b = other.vertices
                ex, ey = b[0]-a[0], b[1]-a[1]
                determinant = dx*ey-dy*ex
                if determinant:
                    ax, ay = a[0]-middle[0], a[1]-middle[1]
                    t, u = (ax*ey-ay*ex)/determinant, (ax*dy-ay*dx)/determinant
                    assert not (0 < t <= 1 and 0 <= u <= 1), "compact side probe crossed a subdivision event"


def _assert_weak_cover(g):
    local = [(piece.start, piece.end) for piece in g.clipped_covers if piece.exposed]
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
            assert lo <= end, "nonstrict local weak cover leaves a boundary gap"
            end = max(end, hi)
        assert end == 1, "nonstrict local weak cover omits boundary"


@pytest.mark.parametrize("A,B", [(FLAT, SQUARE), (FLAT, L), (PLUG, POCKET)])
def test_nonstrict_flat_collinear_local_covers_weakly_cover_boundary(A, B):
    g = GlobalEntrance2(A, B)
    _assert_weak_cover(g)
    for a, b in g.boundary:
        p = ((a[0]+b[0])/2, (a[1]+b[1])/2)
        moved = oracle.translate(g.A, p)
        assert oracle.overlap(moved, g.B) == 0 and oracle.boundary_has_exterior(moved, g.B)
    if A == FLAT and B == SQUARE:
        assert any(p.label == ("VE", 1, 2) and p.exposed for p in g.clipped_covers), "flat vertex's nonstrict outward ray must remain valid"


def test_certified_convex_merge_refuses_a_nonconvex_union():
    g = GlobalEntrance2(SQUARE, L, merge_convex=True)
    assert len(g.parts_a) == 1 and len(g.parts_b) == 2
    # Independent analytic point in the removed corner of the convex hull.
    p = (F(3, 2), F(3, 2))
    assert oracle.overlap(oracle.translate(g.A, p), g.B) == -1
    assert g.membership(p) == -1, "nonconvex union must not be filled by convex merging"


def test_spatial_index_never_omits_an_exact_contact_candidate():
    g = GlobalEntrance2(SQUARE, L, merge_convex=True)
    for p in ((-1, -1), (3, 0), (0, 3), (F(3, 2), F(3, 2)), (0, 0)):
        assert g.membership(p) == oracle.overlap(oracle.translate(g.A, p), g.B), "spatial index omitted a contributing cell"


def test_sweep_partition_matches_unpruned_all_pairs_including_collinear():
    segments = [((0, 0), (6, 0)), ((2, 0), (8, 0)), ((3, -2), (3, 2)),
                ((0, -1), (6, 1)), ((6, 0), (6, 3)), ((10, 0), (10, 2))]
    segments = [tuple(oracle.points(s)) for s in segments]
    expected = set()
    for a, b in segments:
        points = {a, b}
        for c, d in segments:
            # Independent segment-line formula expressed through oracle turns.
            ca, cb = oracle.turn(c, d, a), oracle.turn(c, d, b)
            if ca != cb:
                t = ca/(ca-cb)
                p = tuple(a[k]+t*(b[k]-a[k]) for k in (0, 1))
                if oracle.on_segment(p, a, b) and oracle.on_segment(p, c, d):
                    points.add(p)
            else:
                points.update(p for p in (c, d) if oracle.on_segment(p, a, b))
        ordered = sorted(points)
        expected.update(zip(ordered, ordered[1:]))
    assert set(module._split_segments(segments)) == expected


@pytest.mark.parametrize("exponent,shift,rotation", [(-400, 0, 0), (0, 10**3, 1), (400, 10**5, 2)])
def test_compact_constructions_three_tiers_with_independent_rigid_motion(exponent, shift, rotation):
    s = F(2)**exponent
    def rotate(p):
        return p if rotation == 0 else ((-p[1], p[0]) if rotation == 1 else ((3*p[0]-4*p[1])/F(5), (4*p[0]+3*p[1])/F(5)))
    def body(P, x, y):
        return tuple((s*rotate(p)[0]+x, s*rotate(p)[1]+y) for p in P)
    g = GlobalEntrance2(body(SQUARE, shift, -shift), body(L, -2*shift, 3*shift), merge_convex=True, compact_subdivision=True)
    # Exact every-value original-piece coverage: disjoint ear pieces merge into
    # one square and two rectangles; all output coordinates must be original.
    assert len(g.parts_a) == 1 and len(g.parts_b) == 2
    assert set(g.parts_a[0]) == set(body(SQUARE, shift, -shift))
    assert set(p for part in g.parts_b for p in part) <= set(body(L, -2*shift, 3*shift))
    assert _check_every_stratum(g) > 20
    base = GlobalEntrance2(SQUARE, L, merge_convex=True)
    for p in ((-1, -1), (0, 0), (3, 0), (F(3, 2), F(3, 2))):
        x = (s*rotate(p)[0]-3*shift, s*rotate(p)[1]+4*shift)
        assert (g.membership(x), g.topology(x)) == (base.membership(p), base.topology(p))


@pytest.mark.parametrize("exponent", [-400, 0, 400])
def test_every_compact_subdivision_coordinate_has_an_independent_rectangle_value(exponent):
    """Direct Cartesian difference, no production geometry in expected values."""
    s = F(2)**exponent
    tx, ty = F(13, 7), F(-29, 11)
    A = tuple((s*x, s*y) for x, y in SQUARE)
    B = tuple((s*x+tx, s*y+ty) for x, y in ((0, 0), (2, 0), (2, 3), (0, 3)))
    g = GlobalEntrance2(A, B, merge_convex=True, compact_subdivision=True)
    x0, x1, y0, y1 = tx-s, tx+2*s, ty-s, ty+3*s
    ring = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
    sub = g.subdivision
    assert g.parts_a == (A,) and g.parts_b == (B,)
    # Full raw contact arrangement retains collinear state-0 event vertices:
    # these are legitimate extra subdivisions on the rectangle's four sides.
    xevents = (tx-s, tx, tx+s, tx+2*s)
    yevents = (ty-s, ty, ty+2*s, ty+3*s)
    expected_vertices = {(x, y) for x in xevents for y in (y0, y1)}
    expected_vertices.update((x, y) for x in (x0, x1) for y in yevents)
    assert {c.sample for c in sub.vertices} == expected_vertices
    expected_faces = [((left, y0), (right, y0), (right, y1), (left, y1)) for left, right in zip(xevents, xevents[1:])]
    assert [c.vertices for c in sub.faces] == expected_faces
    for cell in sub.vertices+sub.edges+sub.faces:
        assert cell.sample == tuple(sum(v[k] for v in cell.vertices)/len(cell.vertices) for k in (0, 1))
        x, y = cell.sample
        assert cell.state == (1 if x0 < x < x1 and y0 < y < y1 else 0)
        for x, y in cell.vertices:
            assert x0 <= x <= x1 and y0 <= y <= y1
    assert set(g.cells[0]) == set(ring)
    expected_planes = ((0, 1, -y0), (-1, 0, x1), (0, -1, y1), (1, 0, -x0))
    box, rows = g._indexed_cells[0]
    assert box == ((x0, x1), (y0, y1))
    assert tuple(tuple(F(v, max(abs(a), abs(b))) for v in (a, b, c)) for a, b, c in rows) == expected_planes
    for edge in sub.edges:
        a, b = edge.vertices
        middle = tuple((a[k]+b[k])/2 for k in (0, 1))
        direction = (a[1]-b[1], b[0]-a[0])
        step = F(1)
        for nx, ny, c in expected_planes+tuple((1, 0, -x) for x in xevents):
            height = nx*middle[0]+ny*middle[1]+c
            slope = nx*direction[0]+ny*direction[1]
            if height and slope:
                step = min(step, abs(height/slope)/2)
        expected = tuple(tuple(middle[k]+sign*step*direction[k] for k in (0, 1)) for sign in (1, -1))
        assert g.side_probes(*edge.vertices) == expected


@pytest.mark.parametrize("pair", [(3, 8), (4, 9), (7, 8)])
def test_bb52_representative_complete_subdivisions(pair):
    from bb52_g0 import load_blocks
    blocks, _ = load_blocks(1)
    g = GlobalEntrance2(blocks[pair[0]]["poly"], blocks[pair[1]]["poly"], merge_convex=True, compact_subdivision=True)
    assert _check_every_stratum(g) > 20


@pytest.mark.parametrize("kind", ["nonconvex_merge", "index_candidate_loss", "strict_only_local_cover", "drop_isolated_contact", "compact_probe_event_loss"])
def test_internal_semantic_mutants_fail_without_source_hash_tripwires(monkeypatch, kind):
    """Patch executed source inside the SUT; no source-hash gate is called."""
    def mutate(target, name, old, new):
        value = getattr(target, name)
        source = textwrap.dedent(inspect.getsource(value))
        assert old in source
        namespace = dict(module.__dict__)
        exec(compile(source.replace(old, new, 1), "<M3b semantic mutant>", "exec"), namespace)
        monkeypatch.setattr(target, name, namespace[name])
    if kind == "nonconvex_merge":
        mutate(module, "_merge_convex_parts", "if _area2(hull) == _area2(a)+_area2(b):", "if True:")
        g = GlobalEntrance2(SQUARE, L, merge_convex=True)
        with pytest.raises(AssertionError, match="nonconvex union"):
            assert g.membership((F(3, 2), F(3, 2))) == -1, "nonconvex union must not be filled by convex merging"
    elif kind == "index_candidate_loss":
        mutate(GlobalEntrance2, "_candidate_cells", "in self._indexed_cells", "in self._indexed_cells[1:]")
        with pytest.raises(AssertionError, match="spatial index omitted"):
            test_spatial_index_never_omits_an_exact_contact_candidate()
    elif kind == "strict_only_local_cover":
        source = textwrap.dedent(inspect.getsource(GlobalEntrance2.clipped_covers.fget))
        source = source.replace(" >= 0:", " > 0:")
        namespace = dict(module.__dict__)
        exec(compile(source, "<M3b strict local-cover mutant>", "exec"), namespace)
        monkeypatch.setattr(GlobalEntrance2, "clipped_covers", namespace["clipped_covers"])
        with pytest.raises(AssertionError, match="nonstrict local weak cover"):
            _assert_weak_cover(GlobalEntrance2(FLAT, SQUARE))
    elif kind == "drop_isolated_contact":
        mutate(GlobalEntrance2, "_contact_subdivision", "contact_points = {p for e in arranged for p in e if self.membership(p) == 0}",
               "contact_points = {p for e in contacts for p in e}")
        with pytest.raises(AssertionError, match="isolated contact vertex"):
            test_contact_skeleton_preserves_an_isolated_tight_contact()
    else:
        mutate(GlobalEntrance2, "side_probes", "for p, q in probe_edges:", "for p, q in self._contact_edges:")
        with pytest.raises(AssertionError, match="compact side probe left its adjacent open face"):
            test_compact_side_probes_stay_in_adjacent_open_faces_before_every_event(0, "isolated_point")
