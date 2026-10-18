"""Reexecute two R3 certificates and counts at frozen labels and intervals.

This is a semantic regression against preserved data, not an independent
geometry oracle. The independent analytic R3 oracle remains in
test_m5c_certificates; its construction shares no production primitives.
"""
import json
from pathlib import Path
import sys

import pytest
from mutation_support import replace_module_callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from frozen_evidence import data_path
import m5c_research_examples as examples


def test_fixed_real_r3_subset_reexecutes_certificates_and_counts_at_frozen_label_and_interval():
    data = json.loads(data_path(ROOT, examples.TARGET).read_text(encoding="utf-8"))
    assert [(row["case"], row["step"], row["pair"]) for row in data["examples"]] == [
        ("bb05", 3, [2, 3])]
    # verify() checks both exact certificate fields, mapped frozen labels,
    # legacy counts, live fixture data hashes and historical record consistency.
    # It does not discover the first entrance or independently derive its label.
    assert examples.verify() == len(data["examples"])


def test_fixed_real_r3_subset_kills_an_internal_radius_budget_defect(monkeypatch):
    replace_module_callable(monkeypatch, examples.research.new, "diagnose_single_cover", [(
        'early_separation=early["gap_lower"]-ra-rb',
        'early_separation=early["gap_lower"]-ra',
    )])
    with pytest.raises(AssertionError, match="bb05"):
        test_fixed_real_r3_subset_reexecutes_certificates_and_counts_at_frozen_label_and_interval()
