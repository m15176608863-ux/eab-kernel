"""Local penetration-thickness contract, with independent product-set oracles.

Oracle primitives: Fraction scalar arithmetic, coordinate bounds in a supplied
orthonormal frame, Cartesian products and squared norms. None calls production
normals, predicates, triangulation, covers, hulls, distance, SAT or star centres.
For these boxes, all transformed vertices are checked against all eight product
corners, so interval intersection is a complete solid oracle, not an AABB guess.
"""
from fractions import Fraction as F
import inspect
from itertools import product

import pytest

import eab.margin as M
from eab.kernel3d import exact_sweep as S
from eab.kernel3d.geom3 import Polyhedron


IDENTITY = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
ROTATION = ((F(3, 5), -F(4, 5), 0),
            (F(4, 5), F(3, 5), 0), (0, 0, 1))
FACES = ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
         (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))


def _box(half=(1, 1, 1), center=(0, 0, 0)):
    signs = ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
             (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1))
    return Polyhedron([tuple(F(center[k]) + s[k]*F(half[k]) for k in range(3))
                       for s in signs], list(FACES))


def _pose(P, frame=IDENTITY, scale=F(1), origin=(0, 0, 0)):
    return Polyhedron([tuple(F(origin[k]) + scale*sum(frame[k][j]*F(p[j])
                         for j in range(3)) for k in range(3)) for p in P.verts], P.faces)


def _intervals(P, frame=IDENTITY, origin=(0, 0, 0)):
    points = [tuple(sum(F(frame[k][j])*(F(p[k])-F(origin[k])) for k in range(3))
                    for j in range(3)) for p in P.verts]
    intervals = tuple((min(p[k] for p in points), max(p[k] for p in points)) for k in range(3))
    assert set(points) == set(product(*intervals)), "oracle requires an exact product solid"
    return intervals


def _state(A, B, frame=IDENTITY, origin=(0, 0, 0)):
    a, b = _intervals(A, frame, origin), _intervals(B, frame, origin)
    widths = [min(x[1], y[1])-max(x[0], y[0]) for x, y in zip(a, b)]
    return -1 if min(widths) < 0 else 0 if min(widths) == 0 else 1


def _assert_axis_certificate(axis, sign, scale=F(1), origin=(0, 0, 0)):
    w = scale/4
    A = _pose(_box(), scale=scale, origin=origin)
    B = _pose(_box(center=tuple(-sign*F(7, 4) if k == axis else 0 for k in range(3))),
              scale=scale, origin=origin)
    assert _state(A, B) == 1
    rows = S.contact_models(A, B, w)
    assert M.inflated_membership(A, B, delta=0, contact_window=w) == M.ON_BOUNDARY, "axis-public-report"
    accepted = [name for name, a, b in rows if _state(a, b) <= 0]
    # A single direction is necessary here: cores and the other five all overlap.
    assert accepted == [f"shift_{axis}_{sign}"], "all-six-axis-certificates"
    ca = next(a for name, a, _ in rows if name == accepted[0])
    displacement = tuple(F(ca.verts[0][k])-F(A.verts[0][k]) for k in range(3))
    assert sum(x*x for x in displacement) == w*w
    assert _state(ca, B) == 0, "axis translation independently separates interiors"
    # For aligned boxes the closest face of B-A is at exactly w, independently.
    ai, bi = _intervals(A), _intervals(B)
    exact_pd = min(min(x[1]-y[0], y[1]-x[0]) for x, y in zip(ai, bi))
    assert exact_pd == w


@pytest.mark.parametrize("axis,sign", product(range(3), (-1, 1)))
@pytest.mark.parametrize("scale,origin", [(F(1, 16), (0, 0, 0)),
                                         (F(1), (5, -3, 2)),
                                         (F(64), (10**6, -10**6, 10**5))])
def test_each_of_six_axis_certificates_proves_pd_at_most_window(axis, sign, scale, origin):
    """Independent oracle: exact interval products and a measured axis vector."""
    _assert_axis_certificate(axis, sign, scale, origin)


def _bilateral(overlap, w):
    A = _box(half=(1, F(1, 16), F(1, 16)))
    left = _box(half=(F(1, 2)+overlap/2, 1, 1), center=(-F(3, 2)+overlap/2, 0, 0))
    right = _box(half=(F(1, 2)+overlap/2, 1, 1), center=(F(3, 2)-overlap/2, 0, 0))
    B = Polyhedron([*left.verts, *right.verts],
                   [*left.faces, *(tuple(i+8 for i in face) for face in right.faces)])
    return A, B, left, right


def test_shell_certificate_contains_every_overlap_region_but_does_not_bound_pd():
    """Independent oracle: two interval overlaps and convex norm vertex maxima.

    Once all core coordinates are one homothetic factor, every radial boundary
    point is a face convex combination. Its removed-segment squared norm is
    bounded by the largest vertex value; thus this checks a continuum, not rays
    sampled at a few contact points. Core disjointness puts both overlap regions
    in the closed shell. No production star/point/overlap primitive is the oracle.
    """
    w = F(1, 64)
    A, B, left, right = _bilateral(3*w/4, w)
    rows = S.contact_models(A, B, w)
    assert "core_B" not in {name for name, _, _ in rows}
    core = next(a for name, a, _ in rows if name == "core_A")
    a_intervals, c_intervals = _intervals(A), _intervals(core)
    factor = F(core.verts[0][0])/F(A.verts[0][0])
    assert 0 < factor < 1
    assert all(tuple(F(x)*factor for x in a) == tuple(c) for a, c in zip(A.verts, core.verts))
    longest_shell_segment2 = max(sum((F(a[k])-F(c[k]))**2 for k in range(3))
                                for a, c in zip(A.verts, core.verts))
    assert longest_shell_segment2 <= w*w, "radial-shell-thickness-at-most-window"
    for wall in (left, right):
        assert _state(A, wall) == 1
        assert _state(core, wall) == -1
        wi = _intervals(wall)
        intersection = tuple((max(a[0], b[0]), min(a[1], b[1])) for a, b in zip(a_intervals, wi))
        assert all(lo < hi for lo, hi in intersection)
        # The complete interval overlap misses the core, not only its vertices.
        assert any(hi < c[0] or lo > c[1] for (lo, hi), c in zip(intersection, c_intervals))
    for name, a, _ in rows:
        if name != "core_A":
            assert any(_state(a, wall) == 1 for wall in (left, right))
    assert M.inflated_membership(A, B, delta=0, contact_window=w) == M.ON_BOUNDARY
    # Any displacement of norm <= 1 has each component <= 1: transverse
    # intervals still overlap both walls (half sums = 17/16), while escaping
    # one x-overlap moves into the other. A transverse lift 17/16 separates.
    collision_intervals = []
    for wall in (left, right):
        wi = _intervals(wall)
        forbidden = tuple((b[0]-a[1], b[1]-a[0]) for a, b in zip(a_intervals, wi))
        assert all(lo < -1 < 1 < hi for lo, hi in forbidden[1:])
        collision_intervals.append(forbidden[0])
    (ll, lh), (rl, rh) = collision_intervals
    assert ll < -1 and rh > 1 and rl < lh
    assert w < 1, "shell acceptance is compatible with PD greater than 1"


def _oblique_pair(frame):
    w, penetration = F(1, 4), F(9, 40)
    A = _pose(_box(half=(1, 4, 4)), frame)
    B = _pose(_box(half=(1, 4, 4), center=(2-penetration, 0, 0)), frame)
    return A, B, w, penetration


def test_shorter_oblique_escape_can_be_missed_so_penetrating_does_not_mean_pd_exceeds_w():
    """Independent oracle: rational orthogonal coordinates and exact box PD."""
    A, B, w, penetration = _oblique_pair(ROTATION)
    assert _state(A, B, ROTATION) == 1
    assert penetration < w
    # The following displacement is oblique in world axes, length exactly PD.
    shift = tuple(-penetration*ROTATION[k][0] for k in range(3))
    escaped = Polyhedron([tuple(F(p[k])+shift[k] for k in range(3)) for p in A.verts], A.faces)
    assert sum(x*x for x in shift) == penetration**2 < w*w
    assert _state(escaped, B, ROTATION) == 0
    ai, bi = _intervals(A, ROTATION), _intervals(B, ROTATION)
    assert min(min(x[1]-y[0], y[1]-x[0]) for x, y in zip(ai, bi)) == penetration
    assert all(_state(a, b, ROTATION) == 1 for _, a, b in S.contact_models(A, B, w))
    assert M.inflated_membership(A, B, delta=0, contact_window=w) == M.INSIDE, "oblique-escape-missed"
    assert M.body_distance(A, B, contact_window=w) == (0, (M.PENETRATING,))


def test_six_axis_coordinate_dependence_means_rotation_invariance_is_not_guaranteed():
    """Same exact pose rotated by a rational isometry; both reports are honest."""
    # R^T R = I is checked rather than treating rounded trigonometry as rotation.
    assert tuple(tuple(sum(ROTATION[k][i]*ROTATION[k][j] for k in range(3))
                       for j in range(3)) for i in range(3)) == IDENTITY
    statuses = []
    for frame in (IDENTITY, ROTATION):
        A, B, w, pd = _oblique_pair(frame)
        models = S.contact_models(A, B, w)
        votes = {name: _state(a, b, frame) for name, a, b in models}
        assert votes['core_A'] == votes['core_B'] == 1
        if frame == IDENTITY:
            assert votes['shift_0_-1'] == -1
            assert pd < w  # independent certificate supporting reported contact
        else:
            assert all(v == 1 for v in votes.values())
        statuses.append(M.inflated_membership(A, B, delta=0, contact_window=w))
    assert statuses == [M.ON_BOUNDARY, M.INSIDE], "coordinate-dependent-rotation-counterexample"


def test_local_shell_rotation_invariance_is_not_guaranteed_either():
    """Independent two-wall interval oracle isolates the L1 shell limitation."""
    w = F(1, 64)
    A0, B0, left0, right0 = _bilateral(3*w/4, w)
    statuses = []
    for frame in (IDENTITY, ROTATION):
        A, B, left, right = (_pose(p, frame) for p in (A0, B0, left0, right0))
        rows = S.contact_models(A, B, w)
        accepted = []
        for name, a, _ in rows:
            if all(_state(a, wall, frame) <= 0 for wall in (left, right)):
                accepted.append(name)
        assert accepted == (['core_A'] if frame == IDENTITY else [])
        statuses.append(M.inflated_membership(A, B, delta=0, contact_window=w))
    # No rigid shift certifies either case, and physical PD is unchanged: only
    # the coordinate-dependent L1 upper bound used for radial thickness differs.
    assert statuses == [M.ON_BOUNDARY, M.INSIDE], "radial-l1-rotation-counterexample"


def _assert_thick_bilateral_overlap_rejected():
    w = F(1, 64)
    A, B, left, right = _bilateral(3*w/2, w)
    # A contact on the centre x-ray already penetrates 1.5w. Both independent
    # overlap components survive every permitted shift and the <=w shell.
    assert max(p[0] for p in left.verts) == -1+3*w/2
    assert min(p[0] for p in right.verts) == 1-3*w/2
    assert M.inflated_membership(A, B, delta=0, contact_window=w) == M.INSIDE, "reject-thicker-than-w-shell"


def test_shell_thicker_than_window_is_not_accepted():
    _assert_thick_bilateral_overlap_rejected()


def _mutant(function, source):
    namespace = dict(S.__dict__)
    exec(compile(source, '<PERF window internal mutation>', 'exec'), namespace)
    return namespace[function.__name__]


def test_shell_window_doubling_mutation_is_caught_by_public_rejection(monkeypatch):
    original = inspect.getsource(S.star_core)
    changed = original.replace('alpha=min(w/radius,F(1,2))', 'alpha=min(2*w/radius,F(1,2))')
    assert changed != original
    monkeypatch.setattr(S, 'star_core', _mutant(S.star_core, changed))
    monkeypatch.setattr(M, '_resolved', M._resolve)
    with pytest.raises(AssertionError, match='reject-thicker-than-w-shell'):
        _assert_thick_bilateral_overlap_rejected()


def test_five_axis_mutation_is_caught_by_the_missing_direction_gate(monkeypatch):
    original = inspect.getsource(S.contact_models)
    anchor = "choices.append((f'shift_{axis}_{sign}',translate_exact(A,offset),B))"
    changed = original.replace(anchor, "\n            if (axis,sign)!=(2,1):\n                " + anchor)
    assert changed != original
    monkeypatch.setattr(S, 'contact_models', _mutant(S.contact_models, changed))
    monkeypatch.setattr(M, '_resolved', M._resolve)
    with pytest.raises(AssertionError, match='axis-public-report'):
        _assert_axis_certificate(2, 1)
