"""Pointwise contact gates with independent, explicit polygon geometry.

The small oracles below use analytic inward edge normals and direct rational
twist evaluation; they do not consult entrance cells, clipped covers, or the
production material-cone/Minkowski construction.  Internal monkeypatch mutants
must fail those same semantic assertions, not a source hash or a fake result.
"""

from dataclasses import replace
from fractions import Fraction as Q
from itertools import combinations

import pytest

from eab.kernel2d.assembly import Assembly2, Body2
from eab.kernel2d import contacts as module
from eab.kernel2d.contacts import assemble_contact_set2, constraint_matrix


def body(name, vertices, fixed=False, *, boundary_type=None, dof_mask=(1, 1, 1),
         dof_anchor=None, reference_point=(0, 0)):
    if fixed:
        boundary_type, dof_mask = "FIXED_BODY", (0, 0, 0)
    return Body2.from_vertices(name, vertices, boundary_type=boundary_type, dof_mask=dof_mask,
                               dof_anchor=dof_anchor, reference_point=reference_point)


def assembly(*bodies, pairs=None):
    if pairs is None:
        pairs = tuple(combinations(range(len(bodies)), 2))
    return Assembly2(tuple(bodies), tuple(pairs), "complete")


def square(name="A", x=0, y=0, fixed=False, *, boundary_type=None, dof_mask=(1, 1, 1),
           dof_anchor=None, reference_point=(0, 0)):
    return body(name, [(x, y), (x + 1, y), (x + 1, y + 1), (x, y + 1)], fixed,
                boundary_type=boundary_type, dof_mask=dof_mask,
                dof_anchor=dof_anchor, reference_point=reference_point)


def norm(v):
    size = abs(v[0]) + abs(v[1])
    return (Q(v[0]) / size, Q(v[1]) / size)


def geometry_signature(cs):
    return {(c.a, c.b, c.point, norm(c.normal)) for c in cs.constraints}


def saw_case():
    return assembly(
        body("A", [(-2, 0), (0, 0), (1, 1), (0, 2), (-2, 2)]),
        body("B", [(0, 0), (2, 0), (2, 2), (0, 2), (1, 1)], True),
    )


def assert_two_slope_skeleton(cs):
    assert cs.status == "RESOLVED"
    assert len(cs.segments) == 2
    assert geometry_signature(cs) == {
        (0, 1, (0, 0), (-Q(1, 2), Q(1, 2))),
        (0, 1, (1, 1), (-Q(1, 2), Q(1, 2))),
        (0, 1, (1, 1), (-Q(1, 2), -Q(1, 2))),
        (0, 1, (0, 2), (-Q(1, 2), -Q(1, 2))),
    }, "both nonconvex segments retain both endpoint constraints"
    assert all(p.fp_type == "CONVEX" for p in cs.points)


def test_regression_a_two_segment_saw_keeps_both_segments_and_endpoints():
    assert_two_slope_skeleton(assemble_contact_set2(saw_case()))


def test_regression_b_bare_corner_pair_remains_unresolved():
    from eab.kernel2d.mobility import first_order_free_twists

    cs = assemble_contact_set2(assembly(square(), square("B", 1, 1, True)))
    assert cs.status == "MECHANICAL_UNRESOLVED"
    assert cs.constraints == ()
    assert len(cs.unresolved) == len(cs.reachable_witnesses) == 1
    assert cs.unresolved[0].fp_type == "TRUE_VV"
    assert not cs.reachable_witnesses[0].unreachable
    assert first_order_free_twists(cs.assembly, cs).mathematical_status == "MECHANICAL_UNRESOLVED"


def test_regression_c_corner_disjunction_removed_only_with_twist_certificate():
    cs = assemble_contact_set2(assembly(square(), square("B", 1, 1, True), square("C", 1, 0, True)))
    assert cs.status == "RESOLVED"
    assert len(cs.redundancy_certificates) == 1
    cert = cs.redundancy_certificates[0]
    assert cert.unreachable and cert.twist is None
    assert len(cert.dofs) == 3  # Rotation is included in the actual proof.
    assert all(w >= 0 for w in cert.multipliers)
    for col in zip(*cert.matrix):
        assert sum(w * a for w, a in zip(cert.multipliers, col)) == 0
    assert sum(w * b for w, b in zip(cert.multipliers, cert.rhs)) == 1
    assert any(p.fp_type == "REDUNDANT_PROVED" for p in cs.points)


def assert_flush_normals(cs):
    assert cs.status == "RESOLVED"
    assert len(cs.constraints) == 2, "flush corners have only segment endpoint normals"
    assert {c.point for c in cs.constraints} == {(1, 0), (1, 1)}
    assert {norm(c.normal) for c in cs.constraints} == {(-1, 0)}
    assert len(cs.raw_sources) == 8  # Includes horizontal endpoint associations.


def test_regression_d_flush_corners_do_not_make_endpoint_halfplanes():
    """TIA-G5 L1 prerequisite; the separate exact-limit gate checks 0 and 1/2."""
    assert_flush_normals(assemble_contact_set2(assembly(square(), square("B", 1, 0, True))))


def mixed_case():
    return assembly(square(), body("B", [(0, 0), (0, Q(1, 2)), (-Q(1, 2), Q(1, 2)),
                    (-1, Q(5, 4)), (0, 1), (-Q(1, 4), 2), (-2, 2), (-2, 0)], True))


def assert_mixed_point_cones(cs):
    assert cs.status == "MECHANICAL_UNRESOLVED", "true VV remains unresolved in actual twist space"
    assert len(cs.constraints) == 2
    assert {p.point for p in cs.unresolved} == {(0, 1)}
    G, dofs = constraint_matrix(cs.assembly, cs.constraints)
    assert dofs == ((0, 0), (0, 1), (0, 2))
    twist = (Q(1), Q(1), Q(3, 2))
    assert all(sum(a * b for a, b in zip(row, twist)) >= 0 for row in G)
    velocity = (-Q(1, 2), Q(1))  # v + omega x (0,1)
    assert all(sum(a * b for a, b in zip(n, velocity)) > 0 for n in cs.unresolved[0].forbidden[0])


def test_regression_e_same_pair_edge_plus_true_vv_is_not_pairwise_convex():
    assert_mixed_point_cones(assemble_contact_set2(mixed_case()))


@pytest.mark.parametrize("anchor_x,expected", [(-1, "MECHANICAL_UNRESOLVED"), (1, "RESOLVED")])
def test_true_vv_reachability_uses_actual_mask_and_anchor(anchor_x, expected):
    """With y fixed at the anchor, moving that anchor changes admissible twists.

    At the exceptional point (0,1), penetration needs vx-omega<0 and
    -anchor_x*omega>0. Edge contacts on y in [0,1/2] require vx>=omega/2.
    Thus omega>0 is necessary and the forbidden cone is reachable exactly for
    anchor_x=-1. The load reference remains unchanged in both tests.
    """
    old = mixed_case()
    moving = replace(old.bodies[0], dof_mask=(1, 0, 1), dof_anchor=(Q(anchor_x), Q(0)))
    cs = assemble_contact_set2(assembly(moving, old.bodies[1]))
    assert cs.status == expected
    assert constraint_matrix(cs.assembly, cs.constraints)[1] == ((0, 0), (0, 2))
    if expected == "RESOLVED":
        assert len(cs.redundancy_certificates) == 1
        proof = cs.redundancy_certificates[0]
        assert proof.unreachable
        assert all(w >= 0 for w in proof.multipliers)
        assert all(sum(v * w for v, w in zip(column, proof.multipliers)) == 0 for column in zip(*proof.matrix))
        assert sum(v * w for v, w in zip(proof.rhs, proof.multipliers)) == 1
    else:
        assert len(cs.reachable_witnesses) == 1


def test_integer_body_records_never_round_angular_directions():
    """Exact integer records exercise non-binary direction thirds, not floats."""
    pa = ((-2, 0), (0, 0), (2, 1), (0, 2), (-2, 2))
    pb = ((0, 0), (4, 0), (4, 2), (0, 2), (2, 1))
    direct = assembly(Body2("A", pa, dof_anchor=(0, 0)),
                      Body2("B", pb, boundary_type="FIXED_BODY", dof_mask=(0, 0, 0), dof_anchor=(0, 0)))
    converted = assembly(body("A", pa), body("B", pb, True))
    assert module._ray((2, 1)) == (Q(2, 3), Q(1, 3))
    assert all(isinstance(v, Q) for v in module._ray((2, 1)))
    assert geometry_signature(assemble_contact_set2(direct)) == geometry_signature(assemble_contact_set2(converted))
    for p in assemble_contact_set2(direct).points:
        for d in module._samples(tuple(n for cone in p.forbidden for n in cone)):
            assert all(isinstance(v, Q) for v in d)


def test_regression_f_convex_tip_inside_concave_notch_without_edge_overlap():
    cs = assemble_contact_set2(assembly(
        body("A", [(0, 0), (2, 1), (1, 2)]),
        body("B", [(-2, -2), (2, -2), (2, 0), (0, 0), (0, 2), (-2, 2)], True),
    ))
    assert cs.status == "RESOLVED"
    assert cs.segments == ()
    assert len(cs.points) == 1 and cs.points[0].fp_type == "CONVEX"
    assert {norm(c.normal) for c in cs.constraints} == {(1, 0), (0, 1)}
    assert {c.tangent for c in cs.constraints} == {(2, 0), (0, -2)}


def test_bidirectional_pair_sources_are_preserved_without_double_forces():
    one = assemble_contact_set2(assembly(square(), square("B", 1, 0, True)))
    both = assemble_contact_set2(assembly(square(), square("B", 1, 0, True), pairs=((0, 1), (1, 0))))
    assert geometry_signature(one) == geometry_signature(both)
    assert len(both.constraints) == 2
    assert len(both.raw_sources) == 2 * len(one.raw_sources)
    assert {source[1] for source in both.raw_sources} == {"A", "B"}


def test_sources_use_original_vertex_ids_when_input_ring_is_reversed():
    coords = [(0, 1), (1, 1), (1, 0), (0, 0)]
    A = body("A", coords)
    B = square("B", 1, 0, True)
    cs = assemble_contact_set2(assembly(A, B))
    at_bottom = next(p for p in cs.points if p.point == (1, 0))
    assert any(s[0] == "VE" and s[1:3] == ("A", 2) for s in at_bottom.sources)
    assert all(coords[s[2]] == at_bottom.point for s in at_bottom.sources if s[0] == "VE" and s[1] == "A")


def test_source_body_ids_do_not_become_container_indices_after_body_reordering():
    A, B = square("moving"), square("wall", 1, 0, True)
    original = assemble_contact_set2(assembly(A, B, pairs=((0, 1),)))
    reordered = assemble_contact_set2(assembly(B, A, pairs=((1, 0),)))
    assert original.raw_sources == reordered.raw_sources
    assert {s[1] for s in reordered.raw_sources} == {"moving"}
    assert {s[3] for s in reordered.raw_sources} == {"wall"}
    for cs in (original, reordered):
        assert all(isinstance(c.label[0], str) and isinstance(c.label[1], str) for c in cs.constraints)
        assert all(c.label[3] in ("moving", "wall") for c in cs.constraints)


def test_maximal_collinear_segment_drops_interior_force_point_but_not_sources():
    A = body("A", [(0, 0), (1, 0), (1, Q(1, 2)), (1, 1), (0, 1)])
    cs = assemble_contact_set2(assembly(A, square("B", 1, 0, True)))
    assert len(cs.segments) == 1 and len(cs.constraints) == 2
    assert {p.point for p in cs.points} == {(1, 0), (1, Q(1, 2)), (1, 1)}
    assert {c.point for c in cs.constraints} == {(1, 0), (1, 1)}
    midpoint = next(p for p in cs.points if p.point == (1, Q(1, 2)))
    assert midpoint.fp_type == "CONVEX" and midpoint.boundaries and not midpoint.retained
    assert {norm(n) for n in midpoint.boundaries} == {(-1, 0)}
    assert midpoint.sources
    assert all(p.retained for p in cs.points if p is not midpoint)
    rows, dofs = constraint_matrix(cs.assembly, cs.constraints)
    assert dofs == ((0, 0), (0, 1), (0, 2))
    middle_row = (-Q(1), Q(0), Q(1, 2))
    # This comparison rescales rows for proof only. Production edge vectors
    # remain unnormalized, and the two half-edges need not have unit length.
    same_normal_rows = tuple(tuple(value / abs(row[0]) for value in row) for row in rows)
    assert middle_row == tuple((a + b) / 2 for a, b in zip(*same_normal_rows))


def test_true_vv_retention_flag_does_not_conflate_unresolved_with_redundant():
    bare = assemble_contact_set2(assembly(square(), square("B", 1, 1, True)))
    proved = assemble_contact_set2(assembly(square(), square("B", 1, 1, True), square("C", 1, 0, True)))
    assert all(not p.retained for p in bare.points if p.fp_type == "TRUE_VV")
    assert all(not p.retained for p in proved.points if p.fp_type == "REDUNDANT_PROVED")
    assert bare.unresolved and not proved.unresolved and proved.redundancy_certificates


def test_overlap_rejection_and_outside_noncontribution_are_distinct():
    overlap = assemble_contact_set2(assembly(square(), square("B", Q(1, 2), 0, True)))
    assert overlap.call_status == "OK" and overlap.mathematical_status == "OVERLAP"
    assert overlap.status is None and overlap.constraints == ()
    outside = assemble_contact_set2(assembly(square(), square("B", 2, 0, True)))
    assert outside.status == "RESOLVED" and outside.constraints == outside.raw_sources == ()


def test_constraint_matrix_uses_mask_and_kinematic_anchor_not_load_reference():
    A = square(fixed=True)
    B = square("B", 1, 0, boundary_type="FORCE_CONTROLLED_PLATE", dof_mask=(1, 0, 1),
               dof_anchor=(7, 11), reference_point=(13, -5))
    cs = assemble_contact_set2(assembly(A, B))
    G, dofs = constraint_matrix(cs.assembly, cs.constraints)
    assert dofs == ((1, 0), (1, 2))
    assert set(G) == {(1, 11), (1, 10)}


def test_assembly_does_not_consult_covers_or_entrance_boundary(monkeypatch):
    from eab.kernel2d import covers, global_entrance

    def fail(*args, **kwargs):
        raise AssertionError("the point skeleton must not use covers or entrance cells")

    monkeypatch.setattr(covers, "enumerate_covers", fail)
    monkeypatch.setattr(global_entrance, "global_entrance", fail)
    assert_two_slope_skeleton(assemble_contact_set2(saw_case()))


def test_mutation_missing_nonconvex_interface_point_is_caught(monkeypatch):
    original = module._raw_pair

    def lose_kink(*args, **kwargs):
        out = original(*args, **kwargs)
        out.pop((Q(1), Q(1)), None)
        return out

    monkeypatch.setattr(module, "_raw_pair", lose_kink)
    with pytest.raises(AssertionError, match="both nonconvex segments retain both endpoint constraints"):
        assert_two_slope_skeleton(assemble_contact_set2(saw_case()))


def test_mutation_missing_entire_nonconvex_contact_segment_is_caught(monkeypatch):
    original = module._point_constraints

    def lose_one_slope(*args):
        # Inject the missing-segment defect inside constraint generation at
        # both physical endpoints, before the ContactSet2 object is built.
        return [c for c in original(*args) if c.tangent != (1, 1)]

    monkeypatch.setattr(module, "_point_constraints", lose_one_slope)
    with pytest.raises(AssertionError, match="both nonconvex segments retain both endpoint constraints"):
        assert_two_slope_skeleton(assemble_contact_set2(saw_case()))


def test_mutation_raw_endpoint_association_as_halfplane_is_caught(monkeypatch):
    original = module._point_constraints

    def add_endpoint(point, *args):
        out = original(point, *args)
        if point.point == (1, 0):
            out.append(module.ExactContact2(point.a, point.b, point.point, (Q(1), Q(0)), point.sources, ("injected",)))
        return out

    monkeypatch.setattr(module, "_point_constraints", add_endpoint)
    with pytest.raises(AssertionError, match="flush corners have only segment endpoint normals"):
        assert_flush_normals(assemble_contact_set2(assembly(square(), square("B", 1, 0, True))))


def test_mutation_true_vv_disjunction_replaced_by_and_is_caught(monkeypatch):
    original = module._point_cone

    def force_and(*args):
        kind, normals, forbidden = original(*args)
        if kind == "TRUE_VV":
            return "CONVEX", tuple((-n[0], -n[1]) for n in forbidden[0]), forbidden
        return kind, normals, forbidden

    monkeypatch.setattr(module, "_point_cone", force_and)
    with pytest.raises(AssertionError, match="true VV remains unresolved in actual twist space"):
        assert_mixed_point_cones(assemble_contact_set2(mixed_case()))


def test_mutation_body_pair_translation_convexity_absorbs_true_vv_is_caught(monkeypatch):
    original = module._point_cone

    def use_pair_cone(pa, pb, point):
        kind, normals, forbidden = original(pa, pb, point)
        if kind == "TRUE_VV":
            # In mixed_case the body-pair translation cone is x>=0: the edge
            # already excludes the VV's forbidden x<0,y>0 translations. This
            # false whole-pair replacement loses reachable rotational entry.
            return "CONVEX", ((Q(1), Q(0)),), forbidden
        return kind, normals, forbidden

    monkeypatch.setattr(module, "_point_cone", use_pair_cone)
    with pytest.raises(AssertionError, match="true VV remains unresolved in actual twist space"):
        assert_mixed_point_cones(assemble_contact_set2(mixed_case()))


def test_mutation_translation_only_redundancy_proof_is_caught(monkeypatch):
    original = module._dofs

    def no_rotation(model):
        return tuple(dof for dof in original(model) if dof[1] != 2)

    monkeypatch.setattr(module, "_dofs", no_rotation)
    with pytest.raises(AssertionError, match="true VV remains unresolved in actual twist space"):
        assert_mixed_point_cones(assemble_contact_set2(mixed_case()))


def test_mutation_normalized_generator_is_caught(monkeypatch):
    model = assembly(body("A", [(0, 0), (1, 0), (1, 2), (0, 2)]),
                     body("B", [(1, 0), (2, 0), (2, 2), (1, 2)], True))
    assert {c.tangent for c in assemble_contact_set2(model).constraints} == {(0, 2)}
    original = module._point_constraints

    def scale_to_unit(*args):
        return [replace(c, tangent=norm(c.tangent)) for c in original(*args)]

    monkeypatch.setattr(module, "_point_constraints", scale_to_unit)
    with pytest.raises(AssertionError, match="original unnormalized edge generators"):
        assert {c.tangent for c in assemble_contact_set2(model).constraints} == {(0, 2)}, "original unnormalized edge generators"


def seam_case():
    return assembly(square(), body("B", [(-1, -1), (2, -1), (2, 2), (1, 2),
                    (1, 0), (0, 0), (0, 2), (-1, 2)], True))


def assert_seam_contact(cs):
    assert cs.status == "RESOLVED", "physical CONTACT seam is not overlap"
    assert len(cs.constraints) == 6, "all six seam normal constraints must remain"
    assert len(cs.segments) == 3
    assert cs.pair_states == ((0, 1, 0),)


def test_contact_seam_in_interior_of_closed_entrance_is_not_overlap():
    """Analytic U-shaped holder: free positive-y seam, no local separation."""
    assert_seam_contact(assemble_contact_set2(seam_case()))


def test_mutation_interior_of_closed_entrance_as_overlap_is_caught(monkeypatch):
    from eab.kernel2d.global_entrance import global_entrance

    def wrong_membership(pa, pb):
        return global_entrance(pa, pb).topology((0, 0))

    monkeypatch.setattr(module, "polygons_overlap_exact", wrong_membership)
    with pytest.raises(AssertionError, match="physical CONTACT seam is not overlap"):
        assert_seam_contact(assemble_contact_set2(seam_case()))


def test_mutation_boundary_cover_filter_instead_of_raw_skeleton_is_caught(monkeypatch):
    from eab.kernel2d.global_entrance import global_entrance
    original = module._raw_pair

    def only_exposed_covers(pa, pb, a, b, ids_a=(), ids_b=()):
        # An actual internal filtering defect: only associations whose source
        # has an exposed clipped cover through t=0 survive enumeration.
        g = global_entrance(pa, pb)
        allowed = {piece.label for piece in g.clipped_covers
                   if piece.exposed and module._on((Q(0), Q(0)), piece.start, piece.end)}
        raw = original(pa, pb, a, b, ids_a, ids_b)
        kept = {}
        ia = ids_a or tuple(range(len(pa)))
        ib = ids_b or tuple(range(len(pb)))
        for p, labels in raw.items():
            at = set()
            for source in labels:
                if source[0] == "VE":
                    short = ("VE", ia.index(source[2]), ib.index(source[4][0]))
                else:
                    short = ("EV", ia.index(source[2][0]), ib.index(source[4]))
                if short in allowed:
                    at.add(source)
            if at:
                kept[p] = at
        return kept

    monkeypatch.setattr(module, "_raw_pair", only_exposed_covers)
    with pytest.raises(AssertionError, match="all six seam normal constraints must remain"):
        assert_seam_contact(assemble_contact_set2(seam_case()))


@pytest.mark.parametrize("mu,expected", [(Q(0), Q(0)), (Q(1, 4), Q(1, 2))])
def test_regression_d_flush_corner_exact_limit_integration(mu, expected):
    from eab.adapters.tia2d import g5
    from eab.kernel2d.statics import limit_load_ideal_exact_2d

    model = g5(n=3, height=1, pressure=1, width=1, mu=mu)
    cs = assemble_contact_set2(model)
    assert cs.status == "RESOLVED"
    assert len(cs.constraints) == 8
    assert all(p.fp_type == "CONVEX" for p in cs.points)
    result = limit_load_ideal_exact_2d(model, cs)
    assert result.call_status == "OK"
    assert result.mathematical_status == "OPTIMAL"
    assert result.exact_value == expected


@pytest.mark.parametrize("rotation,reflect,scale,offset", [
    (0, False, Q(1), (0, 0)),
    (1, False, Q(1, 32), (2 ** 10, -2 ** 17)),
    (2, True, Q(64), (-2 ** 17, 2 ** 10)),
    (3, True, Q(1, 8), (2 ** 17, 2 ** 17)),
])
def test_pointwise_contacts_exact_binary_rigid_and_unit_metamorphism(rotation, reflect, scale, offset):
    """Exact signed permutation/scale oracle, independent of local cone code."""
    def vector(v):
        x, y = v
        if reflect:
            x = -x
        for _ in range(rotation):
            x, y = -y, x
        return (x * scale, y * scale)

    old = saw_case()
    transformed = []
    for b in old.bodies:
        poly = [tuple(vector(p)[k] + offset[k] for k in range(2)) for p in b.vertices]
        transformed.append(body(b.body_id, poly, b.boundary_type == "FIXED_BODY"))
    cs = assemble_contact_set2(assembly(*transformed))
    expected = set()
    for c in assemble_contact_set2(old).constraints:
        p = tuple(vector(c.point)[k] + offset[k] for k in range(2))
        expected.add((c.a, c.b, p, norm(vector(c.normal))))
    assert cs.status == "RESOLVED"
    assert geometry_signature(cs) == expected
