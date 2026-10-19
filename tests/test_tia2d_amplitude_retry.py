"""No critical crossing means no certified implicit amplitude slope.

The gates independently substitute exact polynomial coefficients and verify
normal-cone combinations and primal rays using Fraction arithmetic. The L1
guard uses original vertex-edge determinants, not production entrance cells.
"""
from fractions import Fraction as Q

import pytest

from eab.adapters.tia2d import morphology_geometry
from tia2d_amplitude_retry import DELTA, incidence_interval, retry_case


def _poly(coefficients, value):
    return sum(Q(a) * value ** i for i, a in enumerate(coefficients))


def _matrix_vector(matrix, vector):
    return tuple(sum(Q(a) * Q(x) for a, x in zip(row, vector)) for row in matrix)


@pytest.mark.parametrize("family", ("TIA-G2", "TIA-G3", "TIA-G4"))
def test_amplitude_retry_positive_branch_is_not_a_crossing_or_unique_labeled_basis(family):
    case = retry_case(family)
    attempt = case["retry"]
    assert case["exact_threshold"] == "0/1" and case["attained"] is True
    assert case["L1_interval"]["all_signs_constant"]
    assert attempt["reason"] == "domain_boundary_without_crossing_basis"
    assert attempt["zero_components"] == []
    assert attempt["all_basic_components_strictly_positive"]
    assert not attempt["threshold_proof_created"] and not attempt["certified"]
    assert case["retry_sensitivity"]["directional_derivative"] is None
    assert case["production_sensitivity"]["differentiability"] == "unresolved"
    assert all(isinstance(item["seconds"], float) and item["seconds"] >= 0
               for item in case["python_wallclock"].values())
    basis = attempt["branch"]["basis"]
    other = attempt["alternative_labeled_basis"]["basis"]
    problem = case["limit_problem_zero"]
    assert basis != other
    assert [[row[j] for j in basis] for row in problem["A"]] == [[row[j] for j in other] for row in problem["A"]]
    branch = attempt["branch"]
    for value in (-DELTA, Q(0), DELTA):
        denominator = _poly(branch["determinant"], value)
        assert denominator != 0
        basic_values = [_poly(poly, value) / denominator for poly in branch["numerators"]]
        assert all(v > 0 for v in basic_values)
        ray = [Q(0) for _ in problem["c"]]
        for j, v in zip(basis, basic_values):
            ray[j] = v
        ray[branch["entering"]] = Q(1)
        matrix = [[Q(a) + value * (Q(b) - Q(a)) for a, b in zip(row, one)]
                  for row, one in zip(problem["A"], case["limit_problem_one"]["A"])]
        assert _matrix_vector(matrix, ray) == tuple(Q(0) for _ in matrix)
    exact = case["threshold_certificate"]
    assert _matrix_vector(problem["A"], exact["feasible_point"]) == tuple(Q(v) for v in problem["b"])
    assert _matrix_vector(problem["A"], exact["improving_ray"]) == tuple(Q(0) for _ in problem["b"])
    cone = case["first_order"]
    for cert in cone["zero_certificates"]:
        assert all(Q(v) >= 0 for v in cert["multipliers"])
        actual = [sum(Q(w) * Q(row[k]) for w, row in zip(cert["multipliers"], cone["matrix"]))
                  for k in range(len(cone["dofs"]))]
        assert actual == [cert["sign"] if k == cert["coordinate"] else 0 for k in range(len(actual))]


@pytest.mark.parametrize("family", ("TIA-G2", "TIA-G3", "TIA-G4"))
def test_amplitude_retry_zero_control_rejects_changed_skeleton_instead_of_zero_slope(family):
    case = retry_case(family, Q(0))
    assert case["retry"]["reason"] == "L1_skeleton_changes_at_zero_amplitude"
    assert case["retry"]["constraint_counts"][0] < case["retry"]["constraint_counts"][1]
    assert not case["L1_interval"]["all_signs_constant"]
    assert case["retry_sensitivity"]["directional_derivative"] is None
    assert case["production_sensitivity"]["reason"] == "no_valid_direction"


def test_amplitude_retry_L1_interval_checks_continuum_not_just_equal_endpoint_classifications():
    geometry = morphology_geometry("TIA-G2", amplitude=Q(1, 8))
    valid = incidence_interval(geometry, -DELTA, DELTA)
    assert valid["all_signs_constant"]
    assert valid["predicate_count"] > len(valid["grouped_predicates"])
    # The same mechanism must reject an interval reaching the flat geometry.
    invalid = incidence_interval(geometry, -Q(1, 8), DELTA)
    assert not invalid["all_signs_constant"]
    assert any(not item["constant_sign_on_interval"] for item in invalid["grouped_predicates"])
