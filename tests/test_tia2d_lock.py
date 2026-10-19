"""Independent exact local-sector oracle for translation certificates.

The oracle constructs critical directions directly from incident input edges,
not GlobalEntrance2 cells, arrangements, covers or entrance_membership_exact.
Its point classification is polygons_overlap_exact: an independent exact ear
decomposition in geom plus triangle SAT. Production lock classification instead
uses global_entrance's own decomposition, product hulls and tangent halfplanes.
The oracle and production share Fraction arithmetic but no geometric path.
"""
from dataclasses import FrozenInstanceError
from fractions import Fraction as F
import inspect
import math
import random

import pytest

from eab.kernel2d import lock as module
from eab.kernel2d.exact import polygons_overlap_exact
from eab.kernel2d.lock import translation_lock_certificate
from eab.oracle_construction import scalar_exact


SQUARE = ((0, 0), (1, 0), (1, 1), (0, 1))
LEFT = ((-1, 0), (0, 0), (0, 1), (-1, 1))
RIGHT = ((1, 0), (2, 0), (2, 1), (1, 1))
BOTTOM = ((0, -1), (1, -1), (1, 0), (0, 0))
TOP = ((0, 1), (1, 1), (1, 2), (0, 2))


def _oracle_rays(A, neighbors):
    """Input-edge determinant oracle; no production cells or angle helpers."""
    points = [[(F(x), F(y)) for x, y in p] for p in (A, *neighbors)]
    directions = {(F(1), F(0)), (F(0), F(1)), (F(-1), F(0)), (F(0), F(-1))}
    for index, ring in enumerate(points):
        other_points = [p for j, other in enumerate(points) if j != index
                        and (index == 0 or j == 0) for p in other]
        for a, b in zip(ring, ring[1:] + ring[:1]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            if any(dx * (p[1] - a[1]) == dy * (p[0] - a[0])
                   and min(a[0], b[0]) <= p[0] <= max(a[0], b[0])
                   and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])
                   for p in other_points):
                size = abs(dx) + abs(dy)
                ray = dx / size, dy / size
                directions.update((ray, (-ray[0], -ray[1])))
    # Insertion order uses only independent quadrant and determinant arithmetic.
    ordered = []
    for ray in sorted(directions):
        angle_half = 0 if ray[1] > 0 or (ray[1] == 0 and ray[0] > 0) else 1
        index = 0
        while index < len(ordered):
            old = ordered[index]
            old_half = 0 if old[1] > 0 or (old[1] == 0 and old[0] > 0) else 1
            if angle_half < old_half or (angle_half == old_half
                                       and ray[0] * old[1] - ray[1] * old[0] > 0):
                break
            index += 1
        ordered.insert(index, ray)
    result = set(ordered)
    for a, b in zip(ordered, ordered[1:] + ordered[:1]):
        direction = a[0] + b[0], a[1] + b[1]
        if a[0] * b[1] - a[1] * b[0] <= 0:
            direction = -a[1], a[0]
        size = abs(direction[0]) + abs(direction[1])
        result.add((direction[0] / size, direction[1] / size))
    return result


def _certificate_state(certificate, direction):
    """Locate one angular record independently, not by reusing local cones."""
    dx, dy = direction
    found = []
    for arc in certificate.arcs:
        ax, ay = arc.start
        bx, by = arc.end
        ca, cb = ax * dy - ay * dx, dx * by - dy * bx
        if arc.kind == "RAY":
            inside = ca == 0 and ax * dx + ay * dy > 0
        else:
            inside = ca > 0 and cb > 0
        if inside:
            found.append(arc.state)
    assert len(found) == 1, "angular coverage must include each ray exactly once"
    return found[0]


def _assert_sector_oracle(A, neighbors, certificate):
    assert certificate.call_status == "OK" and certificate.radius > 0
    rays = _oracle_rays(A, neighbors)
    rays.update(arc.sample for arc in certificate.arcs)
    for direction in rays:
        x = tuple(certificate.radius * v for v in direction)
        states = [polygons_overlap_exact(A, other, x) for other in neighbors]
        truth = "PENETRATING" if 1 in states else "CONTACT" if 0 in states else "SEPARATING"
        assert _certificate_state(certificate, direction) == truth, "exact sector oracle mismatch"
    assert len(certificate.arcs) % 2 == 0
    for ray, arc in zip(certificate.arcs[::2], certificate.arcs[1::2]):
        assert ray.kind == "RAY" and arc.kind == "OPEN_ARC" and ray.start == arc.start
    assert certificate.arcs[-1].end == certificate.arcs[0].start


def _koureas_block2():
    """TIA-G1 block 2: exact binary slope, two parallel shared interfaces."""
    t, height = F(1, 4), F(3, 2)
    def interface(center):
        return ((center + t * height / 2, F(0)),
                (center - t * height / 2, height))
    left, right = interface(F(-3)), interface(F(-1))
    moving = (left[0], right[0], right[1], left[1])
    a = ((F(-5), F(0)), left[0], left[1], (F(-5), height))
    b = (right[0], (F(1), F(0)), (F(1), height), right[1])
    return moving, (a, b)


def _concave_seam():
    """A finite square pin in a concave U; E has a non-overlap inner seam."""
    moving = ((0, F(1, 2)), (1, F(1, 2)), (1, F(3, 2)), (0, F(3, 2)))
    fixed = ((-1, -1), (2, -1), (2, 2), (1, 2), (1, 0), (0, 0), (0, 2), (-1, 2))
    return moving, (fixed,)


@pytest.mark.parametrize("A,neighbors,status,refinement", [
    (SQUARE, (), "NOT_CONTACT", None),
    (SQUARE, (((3, 0), (4, 0), (4, 1), (3, 1)),), "NOT_CONTACT", None),
    (SQUARE, (LEFT,), "REMOVABLE_TRANSLATION", None),
    (SQUARE, (LEFT, RIGHT), "NOT_SEPARABLE_TRANSLATION", "SEAM_SLIDING"),
    (SQUARE, (LEFT, RIGHT, TOP, BOTTOM), "NOT_SEPARABLE_TRANSLATION", "TRANSLATION_IMMOBILE"),
    (*_concave_seam(), "NOT_SEPARABLE_TRANSLATION", "SEAM_SLIDING"),
])
def test_lock_all_states_and_refinements(A, neighbors, status, refinement):
    certificate = translation_lock_certificate(A, neighbors)
    assert certificate.status == certificate.mathematical_status == status
    assert certificate.refinement == refinement
    assert (certificate.separation_ray is not None) == (status == "REMOVABLE_TRANSLATION")
    assert (certificate.seam_ray is not None) == (refinement == "SEAM_SLIDING")
    _assert_sector_oracle(A, neighbors, certificate)


def test_lock_pair_alias_and_immutable_fields():
    single = translation_lock_certificate(SQUARE, LEFT)
    multiple = translation_lock_certificate(SQUARE, (LEFT,))
    assert single == multiple
    assert isinstance(single.radius, F)
    with pytest.raises(FrozenInstanceError):
        single.status = "UNPROVED"


def test_lock_overlap_is_successful_refusal_not_one_of_four_states():
    inside = ((F(1, 4), F(1, 4)), (F(3, 4), F(1, 4)),
              (F(3, 4), F(3, 4)), (F(1, 4), F(3, 4)))
    certificate = translation_lock_certificate(SQUARE, (LEFT, inside))
    assert certificate.call_status == "OK" and certificate.mathematical_status == "OVERLAP"
    assert certificate.status is certificate.refinement is certificate.radius is None
    assert certificate.reason == "overlap_initial_state"
    assert not certificate.arcs and not certificate.contact_sources


@pytest.mark.parametrize("A,neighbors", [
    (((0, 0), (float("nan"), 0), (0, 1)), (LEFT,)),
    (((0, 0), (float("inf"), 0), (0, 1)), (LEFT,)),
    (((0, 0), (True, 0), (0, 1)), (LEFT,)),
    (((0, 0), (1, 0), (2, 0)), (LEFT,)),
    (((0, 0), (1, 1), (0, 1), (1, 0)), (LEFT,)),
    (SQUARE, (((0, 0), (1, 0)),)),
])
def test_lock_rejects_invalid_geometry_without_false_mathematical_status(A, neighbors):
    certificate = translation_lock_certificate(A, neighbors)
    assert certificate.call_status == "INVALID_INPUT"
    assert certificate.status is certificate.mathematical_status is None
    assert certificate.radius is None and certificate.reason


@pytest.mark.parametrize("A,neighbors", [
    _koureas_block2(), _concave_seam(),
    (SQUARE, (((1, 1), (2, 1), (2, 2), (1, 2)),)),
    (SQUARE, (LEFT, RIGHT, TOP, BOTTOM)),
])
def test_lock_independent_sector_oracle(A, neighbors):
    _assert_sector_oracle(A, neighbors, translation_lock_certificate(A, neighbors))


def test_lock_koureas_pairs_removable_combined_seam_not_immobile():
    moving, fixed = _koureas_block2()
    for neighbor in fixed:
        assert translation_lock_certificate(moving, neighbor).status == "REMOVABLE_TRANSLATION"
    result = translation_lock_certificate(moving, fixed)
    assert result.status == "NOT_SEPARABLE_TRANSLATION"
    assert result.refinement == "SEAM_SLIDING"
    assert result.seam_ray[0] + F(1, 4) * result.seam_ray[1] == 0
    _assert_sector_oracle(moving, fixed, result)


@pytest.mark.parametrize("count", (3, 5, 7))
def test_lock_tia_g5_each_inner_rectangle_is_seam_sliding(count):
    """TIA-G5: with the other bodies held fixed, no inner block is immobile."""
    blocks = [((i, 0), (i + 1, 0), (i + 1, 1), (i, 1)) for i in range(count)]
    for i in range(1, count - 1):
        neighbors = (blocks[i - 1], blocks[i + 1])
        result = translation_lock_certificate(blocks[i], neighbors)
        assert result.status == "NOT_SEPARABLE_TRANSLATION" and result.refinement == "SEAM_SLIDING"
        assert result.seam_ray[0] == 0
        _assert_sector_oracle(blocks[i], neighbors, result)


def test_lock_radius_is_strict_and_excludes_outside_neighbors():
    gap = F(1, 1024)
    close = ((1 + gap, 0), (2 + gap, 0), (2 + gap, 1), (1 + gap, 1))
    result = translation_lock_certificate(SQUARE, (LEFT, close))
    assert result.pair_states == (0, -1)
    assert {source.neighbor_index for source in result.contact_sources} == {0}
    assert result.radius < gap
    for bound in result.radius_bounds:
        assert result.radius ** 2 < bound.squared_distance
        # Independent clamped projection, not the production distance helper.
        ax, ay = bound.start
        dx, dy = bound.end[0] - ax, bound.end[1] - ay
        u = max(F(0), min(F(1), -(ax * dx + ay * dy) / (dx * dx + dy * dy)))
        assert bound.squared_distance == (ax + u * dx) ** 2 + (ay + u * dy) ** 2
    assert {bound.neighbor_index for bound in result.radius_bounds} == {0, 1}
    _assert_sector_oracle(SQUARE, (LEFT, close), result)


def test_lock_contact_sources_keep_endpoint_associations_without_cover_filter():
    result = translation_lock_certificate(SQUARE, RIGHT)
    expected = {("VE", 1, 0), ("VE", 1, 3), ("VE", 2, 2), ("VE", 2, 3),
                ("EV", 0, 0), ("EV", 1, 0), ("EV", 1, 3), ("EV", 2, 3)}
    assert {source.label for source in result.contact_sources} == expected
    assert {source.point for source in result.contact_sources} == {(1, 0), (1, 1)}


def test_lock_local_cells_and_blocking_features_are_exact_certificates():
    result = translation_lock_certificate(SQUARE, (LEFT, RIGHT, TOP, BOTTOM))
    cells = {(cell.neighbor_index, cell.cell_index): cell for cell in result.local_cells}
    for cell in cells.values():
        assert cell.active_edges
        for a, b in cell.active_edges:
            assert a[0] * b[1] == a[1] * b[0]
            assert min(a[0], b[0]) <= 0 <= max(a[0], b[0])
            assert min(a[1], b[1]) <= 0 <= max(a[1], b[1])
    for arc in result.arcs:
        assert arc.state == "PENETRATING" and arc.blockers
        for blocker in arc.blockers:
            for a, b in cells[blocker].active_edges:
                assert (b[0] - a[0]) * arc.sample[1] - (b[1] - a[1]) * arc.sample[0] > 0


@pytest.mark.parametrize("turn,reflect,shift,scale", [
    (0, False, 0, F(1)), (1, False, 2 ** 10, F(1, 8)),
    (2, True, 2 ** 17, F(4)), (3, True, 2 ** 10, F(1, 2)),
    (1, False, 2 ** 17, F(1, 2 ** 20)),
])
def test_lock_exact_rigid_and_unit_covariance(turn, reflect, shift, scale):
    A, neighbors = _koureas_block2()
    def transform(poly):
        out = []
        for x, y in poly:
            x, y = F(x), F(y)
            if reflect:
                x = -x
            for _ in range(turn):
                x, y = -y, x
            out.append((scale * x + shift, scale * y - 3 * shift))
        return out
    moved = transform(A)
    fixed = tuple(transform(p) for p in neighbors)
    result = translation_lock_certificate(moved, fixed)
    assert result.status == "NOT_SEPARABLE_TRANSLATION" and result.refinement == "SEAM_SLIDING"
    _assert_sector_oracle(moved, fixed, result)


def test_lock_random_rotation_rechecks_actual_binary64_not_old_classification():
    rng = random.Random(20261019)
    A, neighbors = _koureas_block2()
    for _ in range(3):
        angle = rng.uniform(-math.pi, math.pi)
        co, si = math.cos(angle), math.sin(angle)
        # Shared vertex conversion is done once and reused by all incident rings.
        points = {p: (scalar_exact(F(co) * p[0] - F(si) * p[1] + 1024),
                      scalar_exact(F(si) * p[0] + F(co) * p[1] - 2048))
                  for p in {p for poly in (A, *neighbors) for p in poly}}
        moved = tuple(points[p] for p in A)
        fixed = tuple(tuple(points[p] for p in poly) for poly in neighbors)
        result = translation_lock_certificate(moved, fixed)
        # These rings share complete edges even if two parallel faces lose exact parallelism.
        assert result.call_status == "OK" and result.mathematical_status != "OVERLAP"
        _assert_sector_oracle(moved, fixed, result)


def test_lock_oracle_source_does_not_reuse_production_geometry():
    source = inspect.getsource(_oracle_rays) + inspect.getsource(_assert_sector_oracle)
    for forbidden in ("global_entrance", "entrance_membership_exact", "local_cells", "clipped_covers"):
        assert forbidden not in source
    assert "polygons_overlap_exact" in source


def test_lock_internal_int_e_as_overlap_mutant_fails_seam_guard(monkeypatch):
    source = inspect.getsource(module._classify)
    old = "if all(value > 0 for value in signs):"
    assert source.count(old) == 1
    scope = dict(module.__dict__)
    exec(source.replace(old, "if all(value >= 0 for value in signs):"), scope)
    # Replace the actual production predicate, not a fabricated final result.
    monkeypatch.setattr(module, "_classify", scope["_classify"])
    with pytest.raises(AssertionError, match="contact seam is not strict overlap"):
        result = translation_lock_certificate(SQUARE, (LEFT, RIGHT))
        assert result.refinement == "SEAM_SLIDING", "contact seam is not strict overlap"


def test_lock_internal_missing_neighbor_cell_mutant_fails_combined_guard(monkeypatch):
    real = module._local_data
    def omit_one_side(pairs):
        cells, bounds = real(pairs)
        return tuple(cell for cell in cells if cell.neighbor_index != 1), bounds
    monkeypatch.setattr(module, "_local_data", omit_one_side)
    with pytest.raises(AssertionError, match="combined constraints must cover both sides"):
        result = translation_lock_certificate(SQUARE, (LEFT, RIGHT))
        assert result.status == "NOT_SEPARABLE_TRANSLATION", "combined constraints must cover both sides"
