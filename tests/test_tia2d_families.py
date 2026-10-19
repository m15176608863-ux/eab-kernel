"""TIA-G1/G5 closed-form gates with production contact and exact LP paths.

Reference formulas use elementary force/moment equilibrium, not production
geometry. CONTACT input checks use polygons_overlap_exact (ear/SAT path),
independent of the contact point assembly. Finite cases do not prove a family.
"""
from dataclasses import replace
from fractions import Fraction as Q

import pytest

from eab.adapters.tia2d import (audit_binary64_chain, g1, g1_reference_from_vertices,
                              g1_threshold, g5, g5_closed_form, g5_reference_from_vertices, g5_seed)
from eab.kernel2d.assembly import Body2
from eab.kernel2d.contacts import assemble_contact_set2
from eab.kernel2d.exact import polygons_overlap_exact
from eab.kernel2d.statics import limit_load_ideal_exact_2d
from eab.kernel2d.sensitivity import evaluate_sensitivity2


@pytest.mark.parametrize("n", [3, 5, 7])
@pytest.mark.parametrize("mu", [Q(0), Q(1, 4), Q(1), Q(2)])
def test_g5_production_assembly_matches_sliding_and_hinging(n, mu):
    assembly = g5(n=n, mu=mu)
    contacts = assemble_contact_set2(assembly)
    assert contacts.status == "RESOLVED"
    assert len(contacts.constraints) == 2 * (n + 1)
    result = limit_load_ideal_exact_2d(assembly, contacts)
    assert result.mathematical_status == "OPTIMAL"
    assert result.exact_value == g5_closed_form(n=n, mu=mu)


@pytest.mark.parametrize("mask,expected", [((1, 0, 1), Q(4, 3)), ((1, 1, 0), Q(2, 3))])
def test_g5_claude_approved_boundary_counterexamples(mask, expected):
    assembly = g5(mu=2, dof_mask=mask)
    assert assembly.bodies[-1].dof_anchor == (3, Q(1, 2))
    result = limit_load_ideal_exact_2d(assembly)
    assert result.exact_value == expected != g5_closed_form(mu=2)


@pytest.mark.parametrize("height,pressure,widths", [
    (Q(1, 2), Q(2), (Q(1), Q(1, 2), Q(1))),
    (Q(2), Q(1, 4), (Q(1, 2), Q(2), Q(1, 2))),
])
def test_g5_independent_geometry_load_scales_and_symmetric_unequal_widths(height, pressure, widths):
    assembly = g5(height=height, pressure=pressure, widths=widths, mu=Q(3, 4))
    result = limit_load_ideal_exact_2d(assembly)
    assert result.exact_value == g5_closed_form(height=height, pressure=pressure, widths=widths, mu=Q(3, 4))


@pytest.mark.parametrize("height", [Q(1), Q(3, 2), Q(2)])
@pytest.mark.parametrize("t", [Q(1, 32), Q(1, 4), Q(17, 64)])
def test_g1_koureas_table_range_closed_zero_threshold(height, t):
    assembly = g1(t=t, height=height, mu=0)
    assert g1_threshold(t=t, height=height) == (0, True)
    result = limit_load_ideal_exact_2d(assembly)
    assert result.mathematical_status == "UNBOUNDED"


@pytest.mark.parametrize("height", [Q(1), Q(3, 2), Q(2)])
@pytest.mark.parametrize("orientation", ["koureas", "unreversed", "reverse_i1"])
def test_g1_zero_slope_owner_corrected_open_threshold(height, orientation):
    """Independent force balance: all contact y entries vanish at mu=0."""
    assert g1_threshold(t=0, height=height, orientation=orientation) == (0, False)
    zero = limit_load_ideal_exact_2d(g1(t=0, height=height, orientation=orientation))
    assert zero.mathematical_status == "OPTIMAL" and zero.exact_value == 0
    row = zero.problem.row_labels.index(("block_3", 1))
    assert zero.problem.A[row][:-1] == (Q(0),) * (len(zero.problem.c) - 1)
    assert zero.problem.A[row][-1] == -1
    positive = limit_load_ideal_exact_2d(g1(t=0, height=height, orientation=orientation, mu=Q(1, 1024)))
    assert positive.mathematical_status == "UNBOUNDED"
    assert positive.improving_ray[-1] == 1


@pytest.mark.parametrize("orientation,height,threshold,closed", [
    ("koureas", Q(1, 4), Q(15, 128), True),
    ("unreversed", Q(1), Q(1, 4), False),
    ("reverse_i1", Q(1), Q(1, 4), True),
])
def test_g1_each_orientation_closed_or_open_boundary(orientation, height, threshold, closed):
    assert g1_threshold(orientation=orientation, height=height) == (threshold, closed)
    outcomes = []
    for mu in (threshold - Q(1, 1024), threshold, threshold + Q(1, 1024)):
        result = limit_load_ideal_exact_2d(g1(orientation=orientation, height=height, mu=mu))
        outcomes.append(result.mathematical_status)
        if result.mathematical_status == "OPTIMAL":
            assert result.exact_value == 0
    assert outcomes == ["OPTIMAL", "UNBOUNDED" if closed else "OPTIMAL", "UNBOUNDED"]


def test_shared_input_faces_are_exact_contact_without_extra_overlap():
    for assembly in (g1(t=Q(17, 64), height=Q(3, 2)), g5(n=7)):
        for i, j in assembly.pairs:
            a, b = assembly.bodies[i].vertices, assembly.bodies[j].vertices
            assert polygons_overlap_exact(a, b) == (0 if j == i + 1 else -1)


@pytest.mark.parametrize("orientation", ("koureas", "unreversed", "reverse_i1"))
def test_actual_vertex_g1_reference_uses_measured_height_spacing_and_slopes(orientation):
    model = g1(t=Q(1, 4), height=Q(1, 4), orientation=orientation)
    actual = g1_reference_from_vertices(model)
    assert actual["certified"] is False and actual["source"] == "actual_vertices_closed_form_reference"
    assert (actual["threshold"], actual["attained"]) == g1_threshold(t=Q(1, 4), height=Q(1, 4), orientation=orientation)
    assert actual["height"] == Q(1, 4) and actual["l"] == 2 and actual["t"] == Q(1, 4)
    bodies = tuple(Body2.from_vertices(b.body_id, tuple((x, 2 * y) for x, y in b.vertices),
        reference_point=b.reference_point, dof_anchor=b.dof_anchor, boundary_type=b.boundary_type,
        dof_mask=b.dof_mask, dead=b.dead, live=b.live) for b in model.bodies)
    changed = g1_reference_from_vertices(replace(model, bodies=bodies))
    assert changed["height"] == Q(1, 2) and changed["t"] == Q(1, 8)
    assert (changed["threshold"], changed["attained"]) == g1_threshold(t=Q(1, 8), height=Q(1, 2), orientation=orientation)
    if orientation == "koureas":
        assert actual["tan_theta_minus_gamma"] == actual["threshold"] == Q(15, 128)
        assert changed["threshold"] == 0


def test_actual_vertex_g5_reference_and_mask_applicability_are_explicit():
    model = g5(n=3, height=Q(1, 2), pressure=Q(2), widths=(Q(1), Q(1, 2), Q(1)), mu=Q(3, 4))
    actual = g5_reference_from_vertices(model)
    assert (actual["L"], actual["b"], actual["h"], actual["pressure"]) == (Q(5, 2), Q(1, 2), Q(1, 2), Q(2))
    assert actual["capacity"] == 2 and actual["mode"] == "hinging" and actual["applicable"]
    released = g5_reference_from_vertices(g5(mu=2, dof_mask=(1, 0, 1)))
    assert not released["applicable"] and released["reason"] == "released_plate_mask"
    assert released["capacity"] == 2  # Counterfactual baseline, not released-mask truth.
    with pytest.raises(ValueError, match="central unit"):
        broken = replace(model, bodies=tuple(replace(b, live=(Q(0),) * 3) for b in model.bodies))
        g5_reference_from_vertices(broken)


@pytest.mark.parametrize("model", [g1(t=Q(17, 64), height=Q(3, 2)), g5(n=7),
                                    g1(t=Q(1, 4), height=Q(1, 4))])
def test_binary64_chain_audit_identity_contact_parallel_and_bits(model):
    audit = audit_binary64_chain(model)
    assert audit["binary64_subset"] and audit["rn_identity"] and audit["no_new_concave_vertices"]
    assert all(row[3] for row in audit["pair_states"])
    assert all(old == new for _, _, old, new in audit["face_cross_products"])
    for record in audit["bodies"]:
        assert record["rn_identity"]
        assert all(len(value) == 16 and set(value) <= set("0123456789abcdef") for p in record["xy_bits"] for value in p)
    if len(model.bodies) == 5:
        # Koureas block 2's two incident faces stay EXACTLY parallel after RN.
        assert next(row for row in audit["face_cross_products"] if row[:2] == (0, 1))[2:] == (0, 0)


def test_nonbinary_rational_geometry_is_kept_python_only_not_rounded_into_subset():
    audit = audit_binary64_chain(g1(t=Q(1, 10)))
    assert not audit["binary64_subset"] and not audit["rn_identity"]
    assert audit["reason"] == "python_only_or_exact_contact_audit_failed"


@pytest.mark.parametrize("mu,expected", [(Q(1, 4), {"mu": 2, "P": Q(1, 2), "h": 0}),
                                        (Q(2), {"mu": 0, "P": 2, "h": 2})])
def test_g5_production_contact_mu_pressure_height_sensitivity(mu, expected):
    model = g5(mu=mu)
    contacts = assemble_contact_set2(model)
    assert {c.tangent for c in contacts.constraints} == {(0, 1)}
    result = limit_load_ideal_exact_2d(model, contacts)
    for parameter, slope in expected.items():
        answer = evaluate_sensitivity2(result, g5_seed(result.problem, parameter), parameter=parameter)
        assert answer.method == "mills_freund" and answer.differentiability == "smooth"
        assert answer.left_derivative == answer.right_derivative == slope


def test_g5_production_switch_and_zero_friction_preserve_contract():
    result = limit_load_ideal_exact_2d(g5(mu=1))
    for parameter in ("mu", "h"):
        answer = evaluate_sensitivity2(result, g5_seed(result.problem, parameter), parameter=parameter,
                                       tied_labels=("sliding", "hinging"))
        assert answer.method == "mills_freund" and answer.differentiability == "one_sided"
        assert answer.right_derivative == 0 and answer.left_derivative == 2
        assert answer.tied_labels == ("sliding", "hinging")
    zero = limit_load_ideal_exact_2d(g5(mu=0))
    for parameter in ("mu", "P", "h"):
        answer = evaluate_sensitivity2(zero, g5_seed(zero.problem, parameter), parameter=parameter)
        assert answer.differentiability == "singular" and answer.reason == "possibly_discontinuous"
        assert answer.right_derivative is answer.left_derivative is None and answer.dual_recession_ray


def test_g5_zero_preload_seed_does_not_divide_by_pressure_and_other_masks_refuse():
    zero = limit_load_ideal_exact_2d(g5(pressure=0, mu=Q(1, 4)))
    seed = g5_seed(zero.problem, "P")
    assert seed.db[-1] == 1 and all(v == 0 for v in seed.db[:-1])
    released = limit_load_ideal_exact_2d(g5(dof_mask=(1, 0, 1), mu=2))
    with pytest.raises(ValueError, match="axial plate mask"):
        g5_seed(released.problem, "h")


def test_g5_actual_shared_height_seed_matches_original_matrix_polynomial_derivative():
    """Centered difference is exact for these degree-two matrix entries, not a slope oracle."""
    h, delta = Q(3, 2), Q(1, 32)
    result = limit_load_ideal_exact_2d(g5(height=h, pressure=Q(5, 4), mu=Q(1, 4)))
    left = limit_load_ideal_exact_2d(g5(height=h - delta, pressure=Q(5, 4), mu=Q(1, 4)))
    right = limit_load_ideal_exact_2d(g5(height=h + delta, pressure=Q(5, 4), mu=Q(1, 4)))
    skeleton = lambda p: tuple((c.a, c.b, c.sources) for c in p.contact_set.constraints)
    assert skeleton(left.problem) == skeleton(result.problem) == skeleton(right.problem)
    seed = g5_seed(result.problem, "h")
    assert seed.dA == tuple(tuple((b - a) / (2 * delta) for a, b in zip(l, r))
                            for l, r in zip(left.problem.A, right.problem.A))
    assert seed.db == tuple((b - a) / (2 * delta) for a, b in zip(left.problem.b, right.problem.b))


def test_diagnostic_grid_covers_p0_axes_without_formal_schema_export():
    from tia2d_dataset import case_specs, build_diagnostic
    specs = case_specs()
    assert len(specs) == len({s["case_id"] for s in specs}) == 48
    assert {s["family"] for s in specs} == {"TIA-G1", "TIA-G5"}
    spec = next(s for s in specs if s["case_id"] == "g5_n3_mu1")
    record, certificates = build_diagnostic(spec, critical_steps=2)
    assert record["checks"]["closed_form_match"] and record["checks"]["binary64_subset"]
    assert record["limit"]["value"] == "1/2" and record["critical"]["reason"] == "bounded_on_domain"
    assert all(p["fp_type"] == "CONVEX" for p in record["contact_set"]["points"])
    assert certificates["schema"] == "tia2d.diagnostic-certificates.v1"
    assert certificates["query_limit"]["exact_value"] == "1/2"
    assert all(b["boundary_type"] is not None or b["dof_mask"] == [1, 1, 1] for b in record["assembly"]["bodies"])


def test_binary64_audit_preserves_original_negative_zero_bits():
    model = g5()
    body = model.bodies[1]
    raw = tuple(tuple(-0.0 if value == 0 else value for value in point) for point in body.vertices)
    bodies = list(model.bodies)
    bodies[1] = replace(body, original_vertices=raw)
    audit = audit_binary64_chain(replace(model, bodies=tuple(bodies)))
    assert audit["binary64_subset"]
    bits = audit["bodies"][1]["xy_bits"]
    assert bits[0] == ("8000000000000000", "8000000000000000")


def test_diagnostic_small_run_is_new_bounded_sized_and_references_exact_certificates(tmp_path):
    """Check JSON, CSV and hash references directly, without a formal case exporter."""
    import csv
    import hashlib
    import json
    from tia2d_dataset import run_dataset
    out = tmp_path / "diagnostic_run"
    summary = run_dataset(out, tier="small", critical_steps=2, _output_root=tmp_path)
    assert len(summary["cases"]) == 4 and summary["formal_case_export"] is False
    assert summary["schema"] == "tia2d.diagnostic.v1" and summary["schema_approval"] == "pending"
    assert json.loads((out / "progress.json").read_text(encoding="utf-8"))["status"] == "COMPLETE"
    rendered = (out / "README.md").read_text(encoding="utf-8")
    assert "TIA-G5 有限承载力敏感性" in rendered and "?" not in rendered
    for item in json.loads((out / "manifest.json").read_text(encoding="utf-8")):
        data = (out / item["path"]).read_bytes()
        assert len(data) == item["bytes"] < 1_000_000
        assert hashlib.sha256(data).hexdigest() == item["sha256"]
    rows = list(csv.DictReader((out / "table.csv").open(encoding="utf-8", newline="")))
    sliding = next(r for r in rows if r["case_id"] == "g5_n3_mu1")
    assert (sliding["dmu_left"], sliding["dmu_right"], sliding["dP_right"], sliding["dh_right"]) == ("2/1", "2/1", "1/2", "0/1")
    for record in summary["cases"]:
        ref = record["critical"]["certificate_reference"]
        certificates = json.loads((out / ref["path"]).read_text(encoding="utf-8"))
        assert certificates["case_id"] == record["case_id"] and ref["json_pointer"] == "/critical"
        assert certificates["schema"] != "eab2.case.v1"
    with pytest.raises(ValueError, match="NEW diagnostic"):
        run_dataset(out, tier="small", _output_root=tmp_path)


def test_diagnostic_default_boundary_still_rejects_outside_source_root(tmp_path):
    from tia2d_dataset import ROOT, run_dataset
    out = ROOT.parent / ("outside-diagnostic-" + tmp_path.name)
    assert not out.exists()
    with pytest.raises(ValueError, match="inside this worktree"):
        run_dataset(out, tier="small")
    assert not out.exists()
