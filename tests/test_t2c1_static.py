"""No new static admission is allowed for this work order.

This is an admission-count check, not a declaration that the untrusted tools
have passed raw closed-subset analysis or a proof of numerical safety.
"""
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_t2c1_static_admission_count_is_zero():
    policy = json.loads((ROOT / "tools/exact_construction_policy.json").read_text(encoding="utf-8"))
    admissions = [row for row in policy["waivers"]
                  if row["path"].startswith(("tools/t2c_", "tests/test_t2c1_"))]
    assert len(admissions) == 0, ("T2c1 must add zero static admissions", admissions)


@pytest.mark.parametrize("path", ["tools/t2c_probe.py", "tests/test_t2c1_probe.py"])
def test_t2c1_internal_policy_input_admission_is_rejected(monkeypatch, path):
    # Inject at the policy parser consumed by the count gate, not its output.
    policy = dict(waivers=[dict(path=path, rule="closed-rounded-construction")])
    monkeypatch.setattr(json, "loads", lambda text: policy)
    with pytest.raises(AssertionError, match="T2c1 must add zero static admissions"):
        test_t2c1_static_admission_count_is_zero()
