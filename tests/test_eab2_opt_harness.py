"""LP differential-checker gates: plain Fraction algebra, no DLL and no skip.

These exercise the Python checker with constructed valid and invalid witnesses,
not a substitute for production-source mutation gates or the 745-model DLL run.
"""
import copy
from dataclasses import replace
from fractions import Fraction

import pytest

from eab2_opt_diff import case, exact_vector, require, verify


def _result(status, x, y, objective, ray=(), basis=(0,), auxiliary_solves=0, maximize=False):
    return dict(status=status, sense="max" if maximize else "min", x=list(x), y=list(y),
                objective=objective, ray=list(ray), basis=list(basis), auxiliary_solves=auxiliary_solves,
                pivots=0, max_stored_integer_bits=8)


def test_opt_checker_accepts_nonunique_optima_but_not_false_equal_objectives():
    model = case("unit", "nonunique", [[1, 1]], [1], [1, 1])
    expected = _result("optimal", ["1/1", "0/1"], ["1/1"], "1/1")
    verify(model, expected)
    alternative = copy.deepcopy(expected)
    alternative["x"] = ["0/1", "1/1"]
    alternative["basis"] = [1]
    verify(model, alternative)
    alternative["x"] = ["1/1", "1/1"]
    with pytest.raises(AssertionError, match="feasible point"):
        verify(model, alternative)


@pytest.mark.parametrize("field,value", [
    ("objective", "2/1"), ("y", ["0/1"]), ("y", ["2/1"]), ("x", ["1/1"]),
    ("basis", []), ("basis", [3]), ("basis", [True]), ("status", "OPTIMAL"),
    ("ray", ["0/1", "0/1"]), ("pivots", True), ("pivots", -1),
])
def test_opt_checker_rejects_optimal_field_corruption(field, value):
    model = case("unit", "optimum", [[1, 1]], [1], [1, 1])
    result = _result("optimal", ["1/1", "0/1"], ["1/1"], "1/1")
    result[field] = value
    with pytest.raises(AssertionError):
        verify(model, result)


def test_opt_checker_checks_dual_inequality_not_only_equal_objectives():
    # x2 is feasible with value2 and b*y=2, but x1 has smaller cost1.
    model = case("unit", "suboptimal", [[1, 1]], [1], [1, 2])
    false = _result("optimal", ["0/1", "1/1"], ["2/1"], "2/1", basis=(1,))
    with pytest.raises(AssertionError, match="dual column"):
        verify(model, false)
    model = replace(model, maximize=True)
    false["sense"] = "max"
    verify(model, false)


@pytest.mark.parametrize("A,b,c", [([[1]], [1], [1, 0]), ([[1, 0]], [], [1, 0]), ([], [1], [1, 0])])
def test_opt_checker_rejects_malformed_original_model_dimensions(A, b, c):
    model = case("unit", "malformed", A, b, c)
    result = _result("optimal", ["1/1", "0/1"], ["1/1"], "1/1")
    with pytest.raises(AssertionError, match="original LP dimensions"):
        verify(model, result)


def test_opt_checker_requires_nonzero_rhs_feasible_point_for_unbounded():
    model = case("unit", "unbounded", [[1, -1]], [3], [-2, 0])
    result = _result("unbounded", ["3/1", "0/1"], [], None,
                     ray=["1/2", "1/2"], auxiliary_solves=2)
    verify(model, result)
    result["x"] = ["0/1", "0/1"]
    with pytest.raises(AssertionError, match="feasible point"):
        verify(model, result)


@pytest.mark.parametrize("ray", [["0/1", "0/1"], ["1/1", "1/1"], ["1/2", "0/1"], ["-1/2", "-1/2"]])
def test_opt_checker_requires_normalized_nonnegative_improving_kernel_ray(ray):
    model = case("unit", "unbounded", [[1, -1]], [3], [-2, 0])
    result = _result("unbounded", ["3/1", "0/1"], [], None, ray=ray, auxiliary_solves=2)
    with pytest.raises(AssertionError):
        verify(model, result)


def test_opt_checker_maximization_maps_improving_ray_sign():
    model = case("unit", "max", [[1, -1]], [3], [2, 0], True)
    result = _result("unbounded", ["3/1", "0/1"], [], None,
                     ray=["1/2", "1/2"], auxiliary_solves=2, maximize=True)
    verify(model, result)
    result["sense"] = "min"
    with pytest.raises(AssertionError, match="sense"):
        verify(model, result)


@pytest.mark.parametrize("y", [["0/1", "0/1"], ["1/1", "1/1"], ["1/1", "-1/1"]])
def test_opt_checker_farkas_requires_strict_rhs_and_all_columns(y):
    model = case("unit", "infeasible", [[1], [1]], [1, 2], [0])
    valid = _result("infeasible", [], ["-1/1", "1/1"], None, basis=(0, 2))
    verify(model, valid)
    valid["y"] = y
    with pytest.raises(AssertionError):
        verify(model, valid)


@pytest.mark.parametrize("values", [["2/4"], ["-0/1"], ["01/1"], ["1/-2"], [1], [True], ("1/1",)])
def test_opt_checker_requires_canonical_json_rational_arrays(values):
    with pytest.raises((AssertionError, ValueError)):
        exact_vector(values)
    assert exact_vector(["-3/4", "0/1"]) == [Fraction(-3, 4), Fraction(0)]


def test_opt_checker_gate_does_not_depend_on_python_assert_statement():
    with pytest.raises(AssertionError, match="semantic failure"):
        require(False, "semantic failure")
