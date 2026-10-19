"""Pre-implementation contract diagnostics, not a gate for the new APIs.

The static columns are hand-assembled from four vertical interfaces, not
from covers, GlobalEntrance2 or assemble_contact_set2. Exact primal/dual
equalities prove each queried optimum; they do not verify the missing L1
geometry, profile applicability, or production sensitivity implementation.
"""
from fractions import Fraction as Q

import pytest

from tia2d_contract_probe import problem, solve_and_verify, zero_friction_recession


@pytest.mark.parametrize("mu,mask,expected", [
    (Q(0), (1, 0, 0), Q(0)),
    (Q(1, 4), (1, 0, 0), Q(1, 2)),
    (Q(1), (1, 0, 0), Q(2)),
    (Q(2), (1, 0, 0), Q(2)),
    (Q(2), (1, 1, 0), Q(2, 3)),
    (Q(2), (1, 0, 1), Q(1, 3)),
])
@pytest.mark.parametrize("origin", [(Q(5, 8), Q(-3, 8)), (Q(7, 4), Q(9, 8))])
def test_hand_assembled_optima_and_noncentral_reference(mu, mask, expected, origin):
    result = solve_and_verify(problem(mu, mask, origin))
    assert result["value"] == expected


def test_mu_zero_has_an_explicit_nonzero_dual_optimal_face_recession():
    model = problem(Q(0))
    witness = zero_friction_recession(model)
    assert witness["A_transpose_q"] == [Q(0)] * 16 + [Q(1)]
    assert witness["b_dot_q"] == 0
    assert witness["design_directional_derivative"] is None


def test_released_rotation_requires_an_explicit_constraint_anchor():
    global_anchor = solve_and_verify(problem(Q(2), (1, 0, 1)))
    plate_anchor = solve_and_verify(problem(Q(2), (1, 0, 1), plate_anchor=(Q(3), Q(1, 2))))
    assert global_anchor["value"] == Q(1, 3)
    assert plate_anchor["value"] == Q(4, 3)
