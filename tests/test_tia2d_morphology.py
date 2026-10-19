"""Fixed-table morphology gates, not smooth-interface convergence evidence.

Independent oracles are direct affine vertex derivatives, rational matrix
differences on an unchanged contact skeleton, and polygon overlap predicates.
No threshold difference quotient is accepted as a certified derivative.
"""
from fractions import Fraction as Q

import pytest

from eab.adapters.tia2d import morphology_geometry, morphology_seed, morphology_table
from eab.kernel2d.contacts import assemble_contact_set2
from eab.kernel2d.exact import polygons_overlap_exact
from eab.kernel2d.lock import translation_lock_certificate
from eab.kernel2d.statics import build_limit_problem2
from tia2d_morphology import diagnose, summary_row
from test_tia2d_lock import _assert_sector_oracle


@pytest.mark.parametrize("family,segments", [("TIA-G2", 2), ("TIA-G3", 8), ("TIA-G4", 8)])
def test_morphology_fixed_binary_table_shared_contacts_and_exact_seeds(family, segments):
    geometry = morphology_geometry(family, amplitude=Q(1, 8), wavelength=Q(1, 2))
    assembly = geometry.assembly
    assert len(geometry.table) == segments + 1
    assert geometry.frame == ((0, -1), (1, 0))
    assert assembly.bodies[0].boundary_type == assembly.bodies[-1].boundary_type == "FIXED_BODY"
    assert all(body.dead == (0, 0, 0) for body in assembly.bodies)
    for i, j in assembly.pairs:
        assert polygons_overlap_exact(assembly.bodies[i].vertices, assembly.bodies[j].vertices) == (0 if j == i + 1 else -1)
    for k, face in enumerate(geometry.interfaces, 1):
        for p, (u, s) in zip(face, geometry.table):
            assert tuple(Q(v) for v in p) == (-5 + 2 * k - geometry.amplitude * s, geometry.wavelength * u)
            left = assembly.bodies[k - 1].original_vertices
            right = assembly.bodies[k].original_vertices
            assert any(v is p for v in left) and any(v is p for v in right)
    for parameter in ("amplitude", "wavelength"):
        contacts = assemble_contact_set2(assembly)
        problem = build_limit_problem2(assembly, contacts, Q(1, 4))
        seed = morphology_seed(problem, geometry, parameter)
        delta = Q(1, 1024)
        other = morphology_geometry(family,
            amplitude=geometry.amplitude + (delta if parameter == "amplitude" else 0),
            wavelength=geometry.wavelength + (delta if parameter == "wavelength" else 0))
        changed = assemble_contact_set2(other.assembly)
        # Stable feature IDs exclude the moving point coordinates in labels.
        labels = tuple((c.label[0], c.label[1], c.label[3], c.label[4]) for c in contacts.constraints)
        changed_labels = tuple((c.label[0], c.label[1], c.label[3], c.label[4]) for c in changed.constraints)
        assert labels == changed_labels
        probe = build_limit_problem2(other.assembly, changed, Q(1, 4))
        # Cross terms can make the moment quadratic. A centered rational
        # difference is exact for this affine-vertex/affine-edge family.
        before = morphology_geometry(family,
            amplitude=geometry.amplitude - (delta if parameter == "amplitude" else 0),
            wavelength=geometry.wavelength - (delta if parameter == "wavelength" else 0))
        prior_contacts = assemble_contact_set2(before.assembly)
        prior_labels = tuple((c.label[0], c.label[1], c.label[3], c.label[4]) for c in prior_contacts.constraints)
        assert labels == prior_labels
        prior = build_limit_problem2(before.assembly, prior_contacts, Q(1, 4))
        assert tuple(tuple((b - a) / (2 * delta) for a, b in zip(low, high))
                     for low, high in zip(prior.A, probe.A)) == seed.dA
        assert not any(seed.db) and not any(seed.dc)
        assert all(row[-1] == 0 for row in seed.dA)


def test_morphology_table_shapes_and_input_guards_are_not_runtime_trigonometry():
    circle = morphology_table("TIA-G3")
    assert tuple(s for _, s in circle) == tuple(s for _, s in reversed(circle))
    assert morphology_table("TIA-G4")[1] == (Q(1, 8), Q(181, 256))
    for family in ("TIA-G2", "TIA-G3", "TIA-G4"):
        with pytest.raises(ValueError, match="identity rounding"):
            morphology_geometry(family, amplitude=Q(1, 10))
        with pytest.raises(ValueError):
            morphology_geometry(family, amplitude=1)


@pytest.mark.slow
@pytest.mark.parametrize("family", ("TIA-G2", "TIA-G3", "TIA-G4"))
def test_morphology_sector_oracle_uses_input_incident_edges_not_product_cells(family):
    """Independent input-edge rays plus ear/SAT classifications at exact r."""
    assembly = morphology_geometry(family, amplitude=Q(1, 8), wavelength=Q(1, 2)).assembly
    moving = assembly.bodies[2].vertices
    fixed = tuple(body.vertices for i, body in enumerate(assembly.bodies) if i != 2)
    certificate = translation_lock_certificate(moving, fixed)
    _assert_sector_oracle(moving, fixed, certificate)


@pytest.mark.slow
@pytest.mark.parametrize("family", ("TIA-G2", "TIA-G3", "TIA-G4"))
@pytest.mark.parametrize("amplitude", (Q(0), Q(1, 16), Q(1, 8), Q(1, 4)))
@pytest.mark.parametrize("wavelength", (Q(1, 2), Q(1), Q(2)))
def test_morphology_scan_each_parameter_cell_reports_only_measured_claims(family, amplitude, wavelength):
    case = diagnose(family, amplitude, wavelength)
    row = summary_row(case)
    assert not case["case_v1_export"]
    assert case["input_audit"]["lossless_binary64"]
    assert case["contact_status"] == "RESOLVED"
    assert set(case["fp_type_counts"]) == {"CONVEX"}
    assert case["critical"]["call_status"] == "OK"
    assert case["amplitude_threshold_sensitivity"]["directional_derivative"] is None
    assert row["derivative_status"] in ("unresolved", "unsupported", "singular")
    assert all(x["seconds"] >= 0 for x in case["python_wallclock"].values())
    if amplitude:
        assert row["first_order_multi"] == "ZERO_CONE"
        assert row["first_order_single"] == ["ZERO_CONE"] * 3
        assert row["lock_refinements"] == ["TRANSLATION_IMMOBILE"] * 3
        assert row["exact_threshold"] == "0/1" and row["attained"] is True
    else:
        assert row["first_order_multi"] == "NONZERO_CONE"
        assert row["lock_refinements"] == ["SEAM_SLIDING"] * 3
