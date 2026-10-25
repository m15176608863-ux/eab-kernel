"""Metamorphic-input oracles use affine identities, not production solvers."""
import copy
from fractions import Fraction as Q
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from eab2_c3l3_diff import rebuilt_problem
from eab2_c3l4_diff import rebuilt_seed
import eab2_c3l4_meta as meta
from eab2_c3l4_meta import (CASES, Transform, anchor_direction, cases, formal_cases,
                          g1_tilt_from_original_edges, theta_direction,
                          shared_edge_direction, transformed_contacts, transformed_model, transformed_query,
                          transformed_label)


def test_public_meta_additive_branch_schema_keeps_frozen_slopes_and_categories(monkeypatch):
    sources = list(formal_cases(set(CASES)))
    before = copy.deepcopy(sources)
    monkeypatch.setattr(meta, "formal_cases", lambda selection: iter(sources))
    outputs = list(cases())
    assert sources == before
    assert len(outputs) == 64
    assert sum(len(case["queries"]) for case in outputs) == 163
    for case in outputs:
        for query in case["queries"]:
            assert "branch_certificate" in query["result"]
            assert query["result"]["branch_certificate"] is None
    # Identity queries preserve every old oracle field, not just selected
    # derivatives. Anchor/propagation channels have separate existing gates.
    for source in sources:
        if source["case_id"] == "regression_f_convex_in_notch":
            continue
        target = "critical" if source["case_id"].startswith("g1_") else "limit"
        old = [query for _, query in source["queries"] if meta.target_kind(query) == target]
        identity = next(case for case in outputs if case["case_id"] == source["case_id"] + "/identity")
        for original, changed in zip(old, identity["queries"]):
            assert changed["result"] == dict(original["result"], branch_certificate=None)


def test_public_meta_inputs_keep_exact_binary64_and_original_ids():
    outputs = list(cases())
    assert len(outputs) == 64
    assert sum(len(c["queries"]) for c in outputs) == 163
    assert {c["source_case"] for c in outputs} == set(CASES)
    for case in outputs:
        # The builder asserts every coordinate/frame/load transports exactly.
        model, jet = case["model"], case["queries"][0]["geometry_seed"]
        assert jet["vertex_ids"] == [[b.body_id, i] for b in sorted(model.bodies, key=lambda b: b.body_id)
                                     for i in range(len(b.original_vertices))]
        if case["case_id"].endswith("/theta_chain"):
            expected = "theta"
        elif case.get("propagation_only"):
            expected = "shared_edge_affine"
        elif case["source_case"] == "g5_rotation_free_mid":
            expected = "mu"
        else:
            expected = "anchor_frame"
        assert case["queries"][-1]["result"]["parameter"] == expected


def test_public_meta_length_chain_rule_not_same_numeric_jet():
    source = next(formal_cases({"g1_slender"}))
    query = next(q for _, q in source["queries"] if q["result"]["parameter"] == "h")
    transform = Transform("units", length_unit=Q(8))
    changed = transformed_query(query, transform)
    assert Q(changed["result"]["right_derivative"]) == Q(-17, 256)
    assert changed["geometry_seed"]["vertices"] == query["geometry_seed"]["vertices"]
    assert changed["seed"] is None


def test_public_meta_reference_reparameterization_preserves_raw_lp_and_jet():
    source = next(formal_cases({"g5_n3_mu1"}))
    transform = Transform("reference", reference_offset=(Q(17, 8), Q(-29, 16)))
    model = transformed_model(source["model"], transform)
    contacts = transformed_contacts(source["contacts"], transform)
    p = rebuilt_problem(source["model"], source["contacts"], source["model"].mu)
    changed = rebuilt_problem(model, contacts, model.mu)
    assert all(p[key] == changed[key] for key in ("A", "b", "c"))
    for _, query in source["queries"]:
        original = rebuilt_seed(source["model"], source["contacts"], model.mu, query["geometry_seed"])
        moved = rebuilt_seed(model, contacts, model.mu, transformed_query(query, transform)["geometry_seed"])
        assert original == moved


def test_public_meta_anchor_channel_has_real_matrix_and_live_derivatives():
    source = next(formal_cases({"g5_n3_mu1"}))
    query = anchor_direction(source["queries"][0][1])
    seed = rebuilt_seed(source["model"], source["contacts"], source["model"].mu, query["geometry_seed"])
    assert any(value for row in seed["dA"] for value in row)
    assert any(row[-1] for row in seed["dA"])
    assert query["result"]["right_derivative"] == query["result"]["left_derivative"] == "0/1"


def test_public_theta_chain_shared_geometry_reconstructs_scaled_raw_seed():
    for source in formal_cases({"g1_slender", "g1_unreversed_t1"}):
        query = next(q for _, q in source["queries"] if q["result"]["parameter"] == "t")
        tilt = g1_tilt_from_original_edges(source["model"], source["contacts"])
        factor = 1 + tilt * tilt
        theta = theta_direction(query, tilt)
        mu = Q(source["bases"]["critical"]["result"]["exact_threshold"])
        original = rebuilt_seed(source["model"], source["contacts"], mu, query["geometry_seed"])
        changed = rebuilt_seed(source["model"], source["contacts"], mu, theta["geometry_seed"])
        assert changed["dA"] == tuple(tuple(factor * value for value in row) for row in original["dA"])
        assert changed["db"] == tuple(factor * value for value in original["db"])
        assert changed["dc"] == tuple(factor * value for value in original["dc"])
        assert changed["parameter"] == "theta"
        assert Q(theta["result"]["right_derivative"]) == factor * Q(query["result"]["right_derivative"])
        if source["case_id"] == "g1_slender":
            assert tilt == Q(1, 4)
            assert theta["result"]["right_derivative"] == "255/256"


def test_public_theta_chain_scales_nonzero_load_anchor_and_mu_channels_too():
    # A transport-only probe makes normally zero G1 load/anchor/mu channels
    # nonzero, so a vertices-only multiplication cannot pass this gate.
    source = next(formal_cases({"g1_slender"}))
    query = next(q for _, q in source["queries"] if q["result"]["parameter"] == "t")
    import copy
    query = copy.deepcopy(query)
    jet = query["geometry_seed"]
    for name, width in (("dead", 3), ("live", 3), ("dof_anchor", 2)):
        jet[name][0][0] = [str(Q(k + 1, 2 * k + 3)) for k in range(width)]
    jet["mu"] = ["-2/7"]
    factor = Q(17, 16)
    changed = theta_direction(query, Q(1, 4))["geometry_seed"]
    for name in ("vertices", "dead", "live", "dof_anchor"):
        assert [[[Q(value) for value in row] for row in channel] for channel in changed[name]] == [
            [[factor * Q(value) for value in row] for row in channel] for channel in jet[name]]
    assert Q(changed["mu"][0]) == factor * Q(jet["mu"][0])


@pytest.mark.parametrize("transform,point,force", (
    (Transform("reflect_x", cosine=Q(-1), orientation=-1), (-2, 3), (-5, -7)),
    (Transform("reflect_y", orientation=-1), (2, -3), (5, 7)),
    (Transform("swap_xy", cosine=Q(0), sine=Q(1), orientation=-1), (3, 2), (-7, 5)),
))
def test_improper_meta_changes_torque_sign_and_preserves_force_geometry_pairing(transform, point, force):
    assert transform.point((2, 3)) == point
    assert transform.wrench((5, -7, 11)) == force + (-11,)
    # Pseudovector determinant is indispensable even when rotation is free.
    assert transform.wrench((0, 0, 11))[2] == -11
    source = next(formal_cases({"g5_rotation_free_mid"}))
    model = transformed_model(source["model"], transform)
    original_plate, plate = source["model"].bodies[-1], model.bodies[-1]
    assert original_plate.dof_mask == (1, 0, 1)
    assert plate.dof_mask == ((0, 1, 1) if transform.name == "swap_xy" else (1, 0, 1))
    contacts = transformed_contacts(source["contacts"], transform)
    for old, new in zip(source["contacts"]["constraints"], contacts["constraints"]):
        assert new["label"][4] == list(reversed(old["label"][4]))
        tangent = tuple(map(Q, old["tangent"]))
        assert tuple(map(Q, new["tangent"])) == tuple(-v for v in transform.rotate(tangent))
        label = [old["label"], 1]
        assert transformed_label(label, transform) == [new["label"], -1]
    # Original input IDs survive CW normalization; only CCW edge direction changes.
    assert all(new.original_vertices == tuple(transform.point(p) for p in old.original_vertices)
               for old, new in zip(source["model"].bodies, model.bodies))


def test_regression_f_shared_b_edge_jet_has_hand_computed_nonzero_tangent_derivative():
    source = next(formal_cases({"regression_f_convex_in_notch"}))
    query = shared_edge_direction(source["queries"][0][1], source["model"])
    seed = rebuilt_seed(source["model"], source["contacts"], 0, query["geometry_seed"])
    # Both source edges belong to b. With T=-edge and affine H, dN=(-dTy,dTx).
    assert seed["dA"] == (
        (Q(-1, 8), Q(-1, 8), Q(-1, 4), Q(-1, 4), Q(0)),
        (Q(1, 4), Q(1, 4), Q(-1, 8), Q(-1, 8), Q(0)),
        (Q(1, 4), Q(1, 4), Q(3, 8), Q(3, 8), Q(0)),
    )
    assert query["result"]["differentiability"] == "unresolved"
    assert query["result"]["right_derivative"] is None
    assert all(c["label"][3] == "B" for c in source["contacts"]["constraints"])


def test_meta_anchor_offset_exposes_nonzero_lever_arm_times_force_jet():
    source = next(formal_cases({"regression_f_convex_in_notch"}))
    query = shared_edge_direction(source["queries"][0][1], source["model"])
    shift = Transform("offset", anchor_offset=(Q(7, 8), Q(-5, 16)))
    moved = transformed_model(source["model"], shift)
    old = rebuilt_seed(source["model"], source["contacts"], 0, query["geometry_seed"])
    new = rebuilt_seed(moved, transformed_contacts(source["contacts"], shift), 0, query["geometry_seed"])
    # Changing anchor by a gives dM' = dM - ax*dFy + ay*dFx.
    assert new["dA"][2] == tuple(m - Q(7, 8)*fy - Q(5, 16)*fx for fx, fy, m in zip(*old["dA"]))
    assert new["dA"][2] != old["dA"][2]


def test_partially_constrained_rotation_does_not_get_fake_anchor_gauge_invariance():
    selected = [c for c in cases() if c["source_case"] == "g5_rotation_free_mid"]
    assert len(selected) == 8
    assert all(not c["case_id"].endswith("anchor_only") for c in selected)
    assert all(len(c["queries"]) == 1 for c in selected)
