"""Portable saved geometry witnesses; reproduction, not an independent oracle."""
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from frozen_evidence import data_path
import m4c_reproduce_examples as reproducer


def test_persisted_minimal_examples_recompute_exact_geometry_and_classifications():
    examples = json.loads((data_path(ROOT, "reports/codex/M4c_evidence/minimal_examples.json")).read_text(encoding="utf-8"))
    assert examples
    for name, value in examples.items():
        result = reproducer.reproduce(value)
        assert result["status"] == "PASS", name
        assert value["source_sha256"] and value["terminal_source_sha256"]
