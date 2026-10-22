"""C3-L1 wire/checker unit gates; no DLL is optionalized or silently skipped.

The mathematical expected side uses frozen canonical rational records and
independent Fraction equations, not C++ geometry or optimization helpers.
Production DLL differential is a mandatory separate CLI gate.
"""
from collections import Counter
import copy
from fractions import Fraction as Q
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / "tools").is_dir():
    ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src/eab").is_dir())
sys.path.insert(0, str(ROOT / "tools"))
from eab2_c3l1_diff import (compare, differences, formal_cases, metamorphic_cases, rational,
                          read_json, t1b_cases, verify_lp, geometry_constraint_rows, geometry_dofs,
                          geometry_normalized_lp, mat, python_query, vec, verify_optimum, wire)


@pytest.mark.parametrize("raw", ["2/4", "-0/1", "01/2", "1/-2", "1/0", "1.0", 1, True])
def test_c3l1_rational_reader_rejects_noncanonical_wire(raw):
    with pytest.raises(ValueError):
        rational(raw)


@pytest.mark.parametrize("raw", [b'{"a":1,"a":2}', b'{"x":NaN}', b'\xef\xbb\xbf{}'])
def test_c3l1_json_reader_rejects_ambiguous_wire(raw):
    with pytest.raises(ValueError):
        read_json(raw)


def test_c3l1_optimal_and_unbounded_certificate_equations():
    problem = dict(A=[["1/1", "-1/1"]], b=["1/1"], c=["1/1", "0/1"])
    verify_lp(problem, dict(status="optimal", objective="1/1", x=["1/1", "0/1"], y=["1/1"]))
    problem["maximize"] = True
    result = dict(status="unbounded", objective=None, x=["1/1", "0/1"], ray=["1/1", "1/1"])
    verify_lp(problem, result)
    result["x"] = ["0/1", "0/1"]
    with pytest.raises(ValueError, match="feasible point"):
        verify_lp(problem, result)


def test_c3l1_farkas_strictness_and_column_equations():
    problem = dict(A=[["1/1"], ["1/1"]], b=["1/1", "2/1"], c=["0/1"])
    verify_lp(problem, dict(status="infeasible", y=["-1/1", "1/1"]))
    with pytest.raises(ValueError, match="strict positive"):
        verify_lp(problem, dict(status="infeasible", y=["0/1", "0/1"]))
    with pytest.raises(ValueError, match="columns"):
        verify_lp(problem, dict(status="infeasible", y=["1/1", "1/1"]))


def test_c3l1_all_six_named_regressions_keep_pointwise_contract():
    names = {"regression_" + n for n in ("a_saw", "b_bare_vv", "c_redundant_vv", "d_flush_mu0", "d_flush_mu025", "e_mixed_vv_edge", "f_convex_in_notch")}
    cases = {name: (assembly, queries) for name, assembly, queries in formal_cases(selection=names)}
    assert set(cases) == names
    results = {name: next(r for _, q, r in queries if q["kind"] == "assembly") for name, (_, queries) in cases.items()}
    a = results["regression_a_saw"]
    assert len(a["constraints"]) == 4
    assert len(next(p for p in a["points"] if p["point"] == ["1/1", "1/1"])["boundaries"]) == 2
    b = results["regression_b_bare_vv"]
    assert b["mathematical_status"] == "MECHANICAL_UNRESOLVED" and not b["constraints"]
    c = results["regression_c_redundant_vv"]
    assert c["mathematical_status"] == "RESOLVED" and len(c["redundancy_certificates"]) == 1
    assert any(p["fp_type"] == "REDUNDANT_PROVED" for p in c["points"])
    for name in ("regression_d_flush_mu0", "regression_d_flush_mu025"):
        d = results[name]
        assert len(d["constraints"]) == 8 and all(p["fp_type"] == "CONVEX" for p in d["points"])
        assert all(p["boundaries"] == [["-1/1", "0/1"]] for p in d["points"])
    e = results["regression_e_mixed_vv_edge"]
    assert e["mathematical_status"] == "MECHANICAL_UNRESOLVED" and len(e["constraints"]) == 2
    f = results["regression_f_convex_in_notch"]
    assert len(f["constraints"]) == 2 and f["points"][0]["fp_type"] == "CONVEX"
    for assembly, queries in cases.values():
        for _, q, r in queries:
            assert not compare(q["kind"], r, r, assembly=assembly)["semantic_differences"]


def test_c3l1_checker_distinguishes_order_nonunique_and_semantic_fields():
    _, assembly, queries = next(formal_cases(selection={"regression_c_redundant_vv"}))
    expected = queries[0][2]
    actual = copy.deepcopy(expected)
    actual["constraints"].reverse()
    assert compare("assembly", expected, actual, assembly=assembly)["strict_field_differences"] == []
    actual["reason"] = "incorrect reason"
    assert compare("assembly", expected, actual, assembly=assembly)["semantic_differences"]
    actual = copy.deepcopy(expected)
    actual["redundancy_certificates"][0]["multipliers"] = ["0/1"] * len(actual["redundancy_certificates"][0]["multipliers"])
    with pytest.raises(ValueError, match="Farkas normalization"):
        compare("assembly", expected, actual, assembly=assembly)
    assert differences({"field": None}, {})[0]["actual"] == "<missing>"
    _, assembly, bare = next(formal_cases(selection={"regression_b_bare_vv"}))
    expected = bare[0][2]
    actual = copy.deepcopy(expected)
    actual["reachable_witnesses"][0]["twist"] = ["2/1", "2/1", "0/1"]
    checked = compare("assembly", expected, actual, assembly=assembly)
    assert checked["strict_field_differences"] and not checked["semantic_differences"]



def test_c3l1_exact_transform_grid_includes_reflection_asymmetry_and_large_translation():
    cases = list(metamorphic_cases())
    assert len(cases) == 36
    assert sum(len(q) for _, _, q in cases) == 126
    assert any(abs(b.dof_anchor[0]) >= 100000 for _, a, _ in cases for b in a.bodies)
    counts = Counter(q["kind"] for _, _, queries in cases for _, q, _ in queries)
    assert counts == {"assembly": 36, "first_order": 36, "lock": 54}


def test_c3l1_t1b_frozen_l1_projection_has_36_lossless_inputs():
    from eab.construction import scalar_rational

    cases = list(t1b_cases())
    assert len(cases) == 36
    for _, assembly, queries in cases:
        assert all(Q(scalar_rational(x)) == x for b in assembly.bodies for p in b.vertices for x in p)
        assert [q["kind"] for _, q, _ in queries] == ["assembly", "first_order"]


def test_c3l1_c1_compact_contact_layers_match_raw_skeleton():
    from eab2_c1_exact import GlobalEntrance2, python_export, verify_contact_layers
    square = ((0, 0), (1, 0), (1, 1), (0, 1))
    adjacent = ((1, 0), (2, 0), (2, 1), (1, 1))
    exported = python_export(GlobalEntrance2(square, adjacent, merge_convex=True, compact_subdivision=True))
    verify_contact_layers(exported)


def test_c3l1_c1_reader_rejects_exterior_state_and_missing_contact_edge():
    """Parser self-check only: malformed wire is not a production mutation."""
    from eab2_c1_exact import GlobalEntrance2, python_export, verify_contact_layers
    square = ((0, 0), (1, 0), (1, 1), (0, 1))
    adjacent = ((1, 0), (2, 0), (2, 1), (1, 1))
    original = python_export(GlobalEntrance2(square, adjacent, merge_convex=True, compact_subdivision=True))
    bad = copy.deepcopy(original)
    bad["subdivision"]["exterior_state"] = 0
    with pytest.raises(AssertionError, match="exterior_state"):
        verify_contact_layers(bad)
    bad = copy.deepcopy(original)
    edges = bad["subdivision"]["edges"]
    contact = next(i for i, edge in enumerate(edges) if edge["body_state"] == 0)
    del edges[contact]
    with pytest.raises(AssertionError, match="CONTACT"):
        verify_contact_layers(bad)


def test_c3l1_abi_statuses_do_not_flatten_unresolved_or_overlap_to_value():
    from eab2_c3l1_abi import mathematical_status
    states = {None: 0, "OVERLAP": 4, "UNPROVED": 2, "MECHANICAL_UNRESOLVED": 7,
              "INFEASIBLE": 5, "UNBOUNDED": 6, "optimal": 1, "ZERO_CONE": 1,
              "NONZERO_CONE": 1, "RESOLVED": 1, "NOT_CONTACT": 1,
              "REMOVABLE_TRANSLATION": 1, "NOT_SEPARABLE_TRANSLATION": 1}
    for state, code in states.items():
        assert mathematical_status(state) == code
    with pytest.raises(ValueError, match="unknown mathematical status"):
        mathematical_status("MISSING_CAPABILITY_IS_NOT_FALSE")


def _asymmetric_kinematic_case(*, cage=False):
    from eab.kernel2d.assembly import Assembly2, Body2

    def box(x, y):
        return ((x, y), (x + 2, y), (x + 2, y + 2), (x, y + 2))

    moving = Body2.from_vertices("moving", box(13, 19), reference_point=(100, -100),
                                 dof_anchor=(12, 18), dof_mask=(1, 1, 1) if cage else (1, 0, 1))
    if cage:
        bodies = (moving,) + tuple(Body2.from_vertices("wall_" + str(i), box(x, y),
            boundary_type="FIXED_BODY", dof_mask=(0, 0, 0), reference_point=(31, -7))
            for i, (x, y) in enumerate(((11, 19), (15, 19), (13, 17), (13, 21))))
    else:
        bodies = (moving, Body2.from_vertices("plate", box(15, 19), reference_point=(-7, 9),
            boundary_type="FORCE_CONTROLLED_PLATE", dof_anchor=(18, 23), dof_mask=(0, 1, 1)))
    pairs = tuple((a, b) for a in range(len(bodies)) for b in range(a + 1, len(bodies)))
    return Assembly2(bodies, pairs, "complete")


def test_c3l1_geometry_matrix_uses_actual_asymmetric_anchor_masks_and_action_reaction():
    """Explicit columns are an independent edge/anchor hand construction."""
    from dataclasses import replace

    assembly = _asymmetric_kinematic_case()
    contacts = python_query(assembly, {"kind": "assembly"})
    assert geometry_dofs(assembly) == ((0, 0), (0, 2), (1, 1), (1, 2))
    rows = geometry_constraint_rows(assembly, wire(contacts.constraints))
    assert rows == ((-2, 2, 0, 8), (-2, 6, 0, 4))
    result = wire(python_query(assembly, {"kind": "first_order"}, contacts))
    assert not compare("first_order", result, result, assembly=assembly, contacts=contacts)["semantic_differences"]
    # A load-reference change alone must not alter the actual kinematics.
    shifted = replace(assembly, bodies=tuple(replace(b, reference_point=(Q(-117), Q(203)))
                                            for b in assembly.bodies))
    assert geometry_constraint_rows(shifted, wire(contacts.constraints)) == rows


@pytest.mark.parametrize("cage", [False, True], ids=["normalized_nonzero", "normalized_zero_combinations"])
def test_c3l1_geometry_rejects_internally_wrong_anchor_with_self_consistent_certificates(monkeypatch, cage):
    """Inject inside the referee row builder, not into a completed export.

    The mutated kernel supplies internally valid matrices AND LP/zero-cone
    certificates about the wrong load reference. Even matching expected/actual
    exports must fail against the independently reconstructed actual anchor.
    """
    from dataclasses import replace
    import eab.kernel2d.contacts as contact_module

    assembly = _asymmetric_kinematic_case(cage=cage)
    original = contact_module._velocity_row

    def wrong_reference(model, a, b, point, normal, dofs):
        changed = replace(model, bodies=tuple(replace(body, dof_anchor=body.reference_point)
                                               for body in model.bodies))
        return original(changed, a, b, point, normal, dofs)

    monkeypatch.setattr(contact_module, "_velocity_row", wrong_reference)
    contacts = python_query(assembly, {"kind": "assembly"})
    result = wire(python_query(assembly, {"kind": "first_order"}, contacts))
    assert result["mathematical_status"] == ("ZERO_CONE" if cage else "NONZERO_CONE")
    assert bool(result["zero_certificates"]) is cage
    proof = result["normalization_certificate"]
    verify_optimum(mat(proof["matrix"]), vec(proof["rhs"]), vec(proof["objective"]),
                   vec(proof["exact_x"]), vec(proof["exact_y"]), rational(result["normalized_value"]))
    with pytest.raises(ValueError, match="geometry first-order matrix"):
        compare("first_order", result, result, assembly=assembly, contacts=contacts)


@pytest.mark.parametrize("case_name", ["regression_c_redundant_vv", "regression_b_bare_vv"])
def test_c3l1_geometry_rejects_internal_forged_vv_normals_and_corresponding_matrix(monkeypatch, case_name):
    """The producer mutates point geometry before generating a valid proof.

    Doubling the forbidden normals preserves reachability but changes the
    recorded geometry and every associated matrix/certificate consistently;
    both comparison sides are forged, so only the raw-input geometry check wins.
    """
    import eab.kernel2d.contacts as contact_module

    _, assembly, _ = next(formal_cases(selection={case_name}))
    original = contact_module._point_cone

    def doubled_forbidden(pa, pb, point):
        kind, normals, cones = original(pa, pb, point)
        return kind, normals, tuple(tuple(tuple(2 * v for v in n) for n in cone) for cone in cones)

    monkeypatch.setattr(contact_module, "_point_cone", doubled_forbidden)
    contacts = python_query(assembly, {"kind": "assembly"})
    result = wire(contacts)
    assert result["redundancy_certificates"] or result["reachable_witnesses"]
    with pytest.raises(ValueError, match="geometry VV forbidden normals"):
        compare("assembly", result, result, assembly=assembly, contacts=contacts)


def test_c3l1_geometry_rejects_internal_forged_tangent_even_with_matching_exports(monkeypatch):
    from dataclasses import replace
    import eab.kernel2d.contacts as contact_module

    assembly = _asymmetric_kinematic_case()
    original = contact_module._point_constraints

    def wrong_tangent(*args, **kwargs):
        return [replace(c, tangent=tuple(2 * v for v in c.tangent)) for c in original(*args, **kwargs)]

    monkeypatch.setattr(contact_module, "_point_constraints", wrong_tangent)
    contacts = python_query(assembly, {"kind": "assembly"})
    result = wire(python_query(assembly, {"kind": "first_order"}, contacts))
    assert result["normalization_certificate"] is not None
    with pytest.raises(ValueError, match="geometry tangent must equal labelled edge"):
        compare("first_order", result, result, assembly=assembly, contacts=contacts)


def test_c3l1_geometry_normalized_and_zero_equations_are_anchored_to_reconstructed_rows():
    assembly = _asymmetric_kinematic_case(cage=True)
    contacts = python_query(assembly, {"kind": "assembly"})
    result = wire(python_query(assembly, {"kind": "first_order"}, contacts))
    assert result["mathematical_status"] == "ZERO_CONE"
    G = geometry_constraint_rows(assembly, wire(contacts.constraints))
    A, rhs, objective = geometry_normalized_lp(G, len(geometry_dofs(assembly)))
    proof = result["normalization_certificate"]
    assert (mat(proof["matrix"]), vec(proof["rhs"]), vec(proof["objective"])) == (A, rhs, objective)
    assert not compare("first_order", result, result, assembly=assembly, contacts=contacts)["semantic_differences"]
    # These are malformed-wire checks, separate from the internal mutations above.
    bad = copy.deepcopy(result)
    bad["normalization_certificate"]["rhs"][-1] = "2/1"
    with pytest.raises(ValueError, match="geometry normalized rhs"):
        compare("first_order", bad, bad, assembly=assembly, contacts=contacts)
    bad = copy.deepcopy(result)
    bad["zero_certificates"][0]["multipliers"] = ["0/1"] * len(G)
    with pytest.raises(ValueError, match="zero-cone combination"):
        compare("first_order", bad, bad, assembly=assembly, contacts=contacts)
