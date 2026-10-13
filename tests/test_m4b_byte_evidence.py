"""Recorded byte hashes are independently compared, never trust a PASS flag.

No geometry oracle is needed: this gate compares strings and integer byte sizes.
The producer executable and source archives remain outside the eab fixtures.
"""
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import m4b_verify_byte_evidence as evidence


def test_frozen_matrix_proves_all_fifteen_cases_three_modes_match_two_preedit_runs():
    matrix = json.loads((ROOT / "fixtures/m4b_shadow/byte_matrix.json").read_text(encoding="utf-8"))
    result = evidence.validate(matrix)
    assert result["steps_per_mode"] == 1810
    assert result["cases"] == 15 and result["modes"] == 3


@pytest.mark.parametrize("defect,message", [
    ("hash", "byte equality"), ("missing_mode", "mode coverage"),
    ("missing_case", "family coverage"), ("short_run", "run identity/horizon"),
    ("step_jump", "shadow step coverage"), ("input", "input bytes changed"),
])
def test_byte_evidence_gate_rejects_corrupted_actual_matrix(defect, message):
    matrix = json.loads((ROOT / "fixtures/m4b_shadow/byte_matrix.json").read_text(encoding="utf-8"))
    evidence.validate(matrix)
    case = matrix["cases"][0]
    if defect == "hash":
        case["modified"]["shadow"]["artifacts"]["state.csv"]["sha256"] = "0" * 64
    elif defect == "missing_mode":
        del case["modified"]["shadow"]
    elif defect == "missing_case":
        matrix["cases"].pop()
    elif defect == "short_run":
        case["modified"]["legacy"]["steps"] -= 1
    elif defect == "step_jump":
        case["modified"]["shadow"]["shadow"]["steps"][1] = 3
    elif defect == "input":
        name = next(iter(case["inputs"]))
        case["modified"]["unset"]["inputs"][name] = "0" * 64
    with pytest.raises(AssertionError, match=message):
        evidence.validate(matrix)
