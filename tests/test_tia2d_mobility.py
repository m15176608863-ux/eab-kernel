"""First-order gates with exact determinant and elementary velocity oracles.

The DD oracle enumerates n-1 active-row intersections by explicit cofactors;
it does not use the production elimination, DD adjacency or LP path. Geometry
fixtures use hand-known straight endpoints. All conclusions are first-order:
zero implies immobility, nonzero does not certify a finite rigid motion.
"""
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction as F
from itertools import combinations
import math
import random

import pytest

from eab.kernel2d.assembly import Assembly2, Body2
from eab.kernel2d.contacts import assemble_contact_set2
from eab.kernel2d.mobility import first_order_free_twists, _double_description
from eab.oracle_construction import scalar_exact


SQUARE = ((0, 0), (1, 0), (1, 1), (0, 1))
LEFT = ((-1, 0), (0, 0), (0, 1), (-1, 1))
RIGHT = ((1, 0), (2, 0), (2, 1), (1, 1))
BOTTOM = ((0, -1), (1, -1), (1, 0), (0, 0))
TOP = ((0, 1), (1, 1), (1, 2), (0, 2))
ORIGIN = (F(3, 8), F(-5, 8))


def _assembly(moving=SQUARE, fixed=(), *, mask=(1, 1, 1), anchor=ORIGIN, mu=0):
    bodies = [Body2.from_vertices("moving", moving, reference_point=ORIGIN,
                                 dof_mask=mask, dof_anchor=anchor)]
    bodies += [Body2.from_vertices(str(i), ring, reference_point=ORIGIN,
                                  boundary_type="FIXED_BODY", dof_mask=(0, 0, 0))
               for i, ring in enumerate(fixed)]
    return Assembly2(tuple(bodies), tuple(combinations(range(len(bodies)), 2)), "complete", mu=F(mu))


def _normalize(v):
    length = sum(abs(x) for x in v)
    return tuple(F(x) / length for x in v)


def _determinant(matrix):
    """Independent expanded determinant polynomial, dimensions zero to three."""
    if not matrix:
        return F(1)
    if len(matrix) == 1:
        return F(matrix[0][0])
    if len(matrix) == 2:
        return F(matrix[0][0]) * matrix[1][1] - F(matrix[0][1]) * matrix[1][0]
    if len(matrix) == 3:
        a, b, c = matrix
        return (F(a[0]) * (b[1] * c[2] - b[2] * c[1])
                - F(a[1]) * (b[0] * c[2] - b[2] * c[0])
                + F(a[2]) * (b[0] * c[1] - b[1] * c[0]))
    raise ValueError("tiny determinant oracle supports dimensions through three")


def _cofactor_rays(rows, size):
    """Complete pointed cone oracle; caller supplies a full-rank row set."""
    rays = set()
    for active in combinations(rows, size - 1):
        v = tuple((-1) ** j * _determinant(
            [list(row[:j] + row[j + 1:]) for row in active]) for j in range(size))
        if not any(v):
            continue
        for sign in (-1, 1):
            candidate = tuple(sign * x for x in v)
            if all(sum(x * y for x, y in zip(row, candidate)) >= 0 for row in rows):
                rays.add(_normalize(candidate))
    return rays


def _verify_certificates(result):
    assert result.call_status == "OK"
    G, size = result.matrix, len(result.dofs)
    proof = result.normalization_certificate
    assert proof is not None
    assert all(v >= 0 for v in proof.exact_x)
    assert all(sum(a * b for a, b in zip(row, proof.exact_x)) == rhs
               for row, rhs in zip(proof.matrix, proof.rhs))
    assert all(sum(proof.matrix[i][j] * proof.exact_y[i] for i in range(len(proof.rhs))) >= cost
               for j, cost in enumerate(proof.objective))
    assert sum(c * x for c, x in zip(proof.objective, proof.exact_x)) == result.normalized_value
    assert sum(b * y for b, y in zip(proof.rhs, proof.exact_y)) == result.normalized_value
    assert all(sum(g * v for g, v in zip(row, ray)) >= 0 for row in G for ray in result.generators)
    assert all(sum(g * v for g, v in zip(row, line)) == 0 for row in G for line in result.lineality)
    for line in result.lineality:
        assert line in result.generators and tuple(-v for v in line) in result.generators
    if result.cone_is_zero:
        assert result.status == "ZERO_CONE" and not result.generators
        assert result.exact_rank == size and result.normalized_value == 0
        assert len(result.zero_certificates) == 2 * size
        assert {(p.coordinate, p.sign) for p in result.zero_certificates} == {
            (k, sign) for k in range(size) for sign in (-1, 1)}
        for p in result.zero_certificates:
            assert len(p.multipliers) == len(G) and all(v >= 0 for v in p.multipliers)
            assert tuple(sum(row[k] * w for row, w in zip(G, p.multipliers))
                         for k in range(size)) == tuple(p.sign * (k == p.coordinate) for k in range(size))
    else:
        assert result.status == "NONZERO_CONE" and result.generators and not result.zero_certificates


def test_first_order_cage_zero_has_full_rank_normalized_lp_and_both_sign_certificates():
    assembly = _assembly(fixed=(LEFT, RIGHT, TOP, BOTTOM))
    contacts = assemble_contact_set2(assembly)
    result = first_order_free_twists(assembly, contacts)
    assert result.contact_set is contacts and result.cone_is_zero is True
    _verify_certificates(result)
    with pytest.raises(FrozenInstanceError):
        result.cone_is_zero = False


def test_first_order_rank_deficient_seam_is_not_zero_despite_normalized_zero():
    assembly = _assembly(fixed=(LEFT, RIGHT))
    result = first_order_free_twists(assembly)
    assert result.cone_is_zero is False, "zero normalized objective cannot see a free line"
    assert result.exact_rank == 2 and result.normalized_value == 0
    assert set(result.generators) == {(0, 1, 0), (0, -1, 0)}
    assert result.interpretation == "锥 = {0} 推出不可动；锥非零推不出可动"
    _verify_certificates(result)


def test_first_order_empty_contact_has_all_three_bidirectional_twists():
    result = first_order_free_twists(_assembly())
    assert result.cone_is_zero is False and result.exact_rank == 0 and result.normalized_value == 0
    assert len(result.lineality) == 3 and len(result.generators) == 6
    _verify_certificates(result)


def test_first_order_one_plane_has_quotient_rays_and_free_translation():
    result = first_order_free_twists(_assembly(fixed=(BOTTOM,)))
    assert result.cone_is_zero is False and result.normalized_value == 1
    assert len(result.rays) == 2 and len(result.lineality) == 1
    assert set(result.lineality) <= {(1, 0, 0), (-1, 0, 0)}
    _verify_certificates(result)


def test_first_order_all_fixed_is_zero_in_zero_dimensional_coordinate_space():
    assembly = _assembly(fixed=(LEFT,))
    bodies = tuple(replace(body, boundary_type="FIXED_BODY", dof_mask=(0, 0, 0)) for body in assembly.bodies)
    result = first_order_free_twists(replace(assembly, bodies=bodies))
    assert result.cone_is_zero is True and result.dofs == result.zero_certificates == ()
    _verify_certificates(result)


def test_first_order_bare_corner_both_apis_remain_mechanical_unresolved():
    diagonal = ((1, 1), (2, 1), (2, 2), (1, 2))
    assembly = _assembly(fixed=(diagonal,))
    contacts = assemble_contact_set2(assembly)
    result = first_order_free_twists(assembly, contacts)
    assert contacts.status == result.status == "MECHANICAL_UNRESOLVED"
    assert result.cone_is_zero is result.normalized_value is result.normalization_certificate is None
    assert result.display_status == "NOT_APPLICABLE"
    assert result.dofs == ((0, 0), (0, 1), (0, 2))
    assert result.matrix is result.rays is result.lineality is result.generators is result.zero_certificates is None


def test_first_order_redundant_corner_keeps_actual_twist_proof_and_then_resolves():
    diagonal = ((1, 1), (2, 1), (2, 2), (1, 2))
    assembly = _assembly(fixed=(diagonal, RIGHT))
    contacts = assemble_contact_set2(assembly)
    assert contacts.status == "RESOLVED" and contacts.redundancy_certificates
    assert all(len(c.dofs) == 3 for c in contacts.redundancy_certificates)
    result = first_order_free_twists(assembly, contacts)
    _verify_certificates(result)


def test_first_order_actual_plate_mask_and_anchor_are_not_load_reference():
    assembly = _assembly(fixed=(LEFT,), mask=(1, 0, 1), anchor=(0, F(1, 2)))
    bodies = (replace(assembly.bodies[0], boundary_type="FORCE_CONTROLLED_PLATE"), *assembly.bodies[1:])
    assembly = replace(assembly, bodies=bodies)
    result = first_order_free_twists(assembly)
    assert result.dofs == ((0, 0), (0, 2))
    assert set(result.matrix) == {(1, F(1, 2)), (1, F(-1, 2))}
    assert set(result.rays) == {(F(1, 3), F(2, 3)), (F(1, 3), F(-2, 3))}
    assert result.lineality == () and result.cone_is_zero is False
    _verify_certificates(result)


def test_first_order_never_adds_friction_or_dilation():
    results = [first_order_free_twists(_assembly(fixed=(LEFT, RIGHT), mu=mu))
               for mu in (F(0), F(1, 4), F(8))]
    assert all(r.matrix == results[0].matrix and r.generators == results[0].generators for r in results)
    assert all(r.cone_is_zero is False for r in results)


def test_first_order_invalid_incomplete_overlap_do_not_become_false():
    assembly = _assembly()
    contacts = assemble_contact_set2(assembly)
    wrong = first_order_free_twists(replace(assembly, mu=F(1)), contacts)
    assert wrong.call_status == "INVALID_INPUT" and wrong.cone_is_zero is None
    unknown = first_order_free_twists(replace(assembly, completeness="completeness_unknown"))
    assert unknown.status == "UNPROVED" and unknown.cone_is_zero is None
    overlap = ((F(1, 2), 0), (F(3, 2), 0), (F(3, 2), 1), (F(1, 2), 1))
    rejected = first_order_free_twists(_assembly(fixed=(overlap,)))
    assert rejected.call_status == "OK" and rejected.status == "OVERLAP" and rejected.cone_is_zero is None
    assert first_order_free_twists(None).call_status == "INVALID_INPUT"


@pytest.mark.parametrize("rows,size,expected_rays,expected_lines", [
    ((), 2, set(), 2),
    (((1, 0),), 2, {(1, 0)}, 1),
    (((-1, 0),), 2, {(-1, 0)}, 1),
    (((1, 0), (-1, 0)), 2, set(), 1),
    (((1, 0), (0, 1)), 2, {(1, 0), (0, 1)}, 0),
    (((1, 0), (-1, 0), (0, 1)), 2, {(0, 1)}, 0),
    (((1, 0), (-1, 0), (0, 1), (0, -1)), 2, set(), 0),
    (((1, 1), (1, -1)), 2, {(F(1, 2), F(1, 2)), (F(1, 2), F(-1, 2))}, 0),
])
def test_double_description_hand_cones_preserve_lineality_and_ray_sign(rows, size, expected_rays, expected_lines):
    rays, lines = _double_description(rows, size)
    assert set(rays) == expected_rays and len(lines) == expected_lines
    assert all(sum(F(x) * y for x, y in zip(row, line)) == 0 for row in rows for line in lines)


@pytest.mark.parametrize("size", (2, 3, 4))
def test_double_description_matches_independent_cofactor_oracle(size):
    rng = random.Random(20261019 + size)
    products = set()
    for _ in range(8):
        # Unit-coordinate rows guarantee full rank, without production rank.
        rows = tuple(tuple(F(int(i == j)) for j in range(size)) for i in range(size))
        rows += tuple(tuple(F(rng.randrange(-3, 4)) for _ in range(size)) for _ in range(size + 1))
        expected = _cofactor_rays(rows, size)
        rays, lines = _double_description(rows, size)
        assert not lines and set(rays) == expected
        products.add(tuple(sorted(rays)))
        # Redundant/scaled/reversed order rows must not invent or lose a ray.
        changed = tuple(reversed(rows)) + tuple(tuple(8 * x for x in row) for row in rows[:2])
        other, lines = _double_description(changed, size)
        assert not lines and set(other) == expected
    assert len(products) > 1, "parameterized DD oracle must exercise distinct cones"


def _saw():
    return _assembly(((-2, 0), (0, 0), (1, 1), (0, 2), (-2, 2)),
                     (((0, 0), (2, 0), (2, 2), (0, 2), (1, 1)),))


@pytest.mark.parametrize("turn,reflect,shift,scale", [
    (0, False, (0, 0), F(1)),
    (1, False, (2 ** 10, -2 ** 17), F(1, 8)),
    (2, True, (-2 ** 17, 2 ** 10), F(4)),
    (3, True, (2 ** 17, 2 ** 17), F(1, 2 ** 20)),
])
def test_first_order_exact_rotation_reflection_large_shift_and_units(turn, reflect, shift, scale):
    def vector(p):
        x, y = p
        if reflect:
            x = -x
        for _ in range(turn):
            x, y = -y, x
        return scale * x, scale * y
    def point(p):
        x, y = vector(p)
        return x + shift[0], y + shift[1]
    old = _saw()
    before = first_order_free_twists(old)
    assert before.lineality == ()
    bodies = tuple(Body2.from_vertices(b.body_id, tuple(point(p) for p in b.vertices),
        reference_point=point(b.reference_point), boundary_type=b.boundary_type,
        dof_mask=b.dof_mask, dof_anchor=point(b.dof_anchor)) for b in old.bodies)
    model = replace(old, bodies=bodies)
    result = first_order_free_twists(model)
    expected = set()
    for vx, vy, omega in before.rays:
        tx, ty = vector((vx, vy))
        expected.add(_normalize((tx, ty, -omega if reflect else omega)))
    assert result.cone_is_zero == before.cone_is_zero and set(result.rays) == expected
    _verify_certificates(result)


def test_first_order_random_rn_geometry_matches_actual_endpoint_velocity_oracle():
    rng = random.Random(190610)
    model = _saw()
    for shift in (0, 2 ** 10, 2 ** 17):
        angle = rng.uniform(-math.pi, math.pi)
        co, si = F(math.cos(angle)), F(math.sin(angle))
        def point(p):
            return (scalar_exact(co * p[0] - si * p[1] + shift),
                    scalar_exact(si * p[0] + co * p[1] - shift))
        shared = {p: point(p) for b in model.bodies for p in b.vertices}
        bodies = tuple(Body2.from_vertices(b.body_id, tuple(shared[p] for p in b.vertices),
            reference_point=point(b.reference_point), boundary_type=b.boundary_type,
            dof_mask=b.dof_mask, dof_anchor=point(b.dof_anchor)) for b in model.bodies)
        current = replace(model, bodies=bodies)
        contacts = assemble_contact_set2(current)
        result = first_order_free_twists(current, contacts)
        # Rebuild normal rows from the actual two shared A edges, not ContactSet2.
        A = bodies[0].vertices
        ox, oy = bodies[0].dof_anchor
        rows = []
        for a, b in ((A[1], A[2]), (A[2], A[3])):
            nx, ny = a[1] - b[1], b[0] - a[0]
            rows.extend((nx, ny, (p[0] - ox) * ny - (p[1] - oy) * nx) for p in (a, b))
        assert set(result.matrix) == set(rows)
        assert not result.lineality and set(result.rays) == _cofactor_rays(tuple(rows), 3)
        _verify_certificates(result)
