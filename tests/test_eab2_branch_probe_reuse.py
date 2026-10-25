"""Hand-polynomial oracle for the original C++ reuse-fragment JSON driver."""
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from eab2_branch_probe_reuse import verify_reused_basis_records


def test_cpp_reused_basis_json_gate_rejects_a_probe_negative_acceptance():
    records = [dict(epsilon=epsilon, eta="1/4", denominator=[[0, 0, "1/1"]],
                    numerator=[[0, 0, "1/1"], [1, 0, "-32/1"]], k_feasible=True, accepted=accepted)
               for epsilon, accepted in (("1/64", True), ("1/16", False))]
    verify_reused_basis_records(records)
    bad = copy.deepcopy(records)
    bad[1]["accepted"] = True
    with pytest.raises(AssertionError, match="reused probe-negative basis must be skipped"):
        verify_reused_basis_records(bad)
