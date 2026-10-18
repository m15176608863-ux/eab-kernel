"""Frozen data integrity is independent of the current implementation bytes."""
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from frozen_evidence import assert_data_entry


def test_frozen_data_hashes_are_preserved_without_current_source_pins():
    manifest = json.loads((ROOT / "fixtures/frozen/PROVENANCE.json").read_text(encoding="utf-8"))
    assert manifest["schema"] == "h1-frozen-data-provenance-v1"
    rows = manifest["files"]
    assert len(rows) == len({row["path"] for row in rows}) == 137
    for row in rows:
        assert_data_entry(ROOT, row)
        assert row["producing_git_commit"] == "unknown"
        assert row["tool_version"] == "unknown (no explicit historical producer version recorded)"
        assert len(row["accepted_git_commit"]) == 40
        assert set(row["accepted_git_commit"]) <= set("0123456789abcdef")


def test_frozen_data_integrity_rejects_an_actual_same_size_input_edit(tmp_path):
    path = tmp_path / "data.json"
    path.write_bytes(b'{"state":0}\n')
    row = dict(path="data.json", bytes=path.stat().st_size,
               sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    assert_data_entry(tmp_path, row)
    path.write_bytes(b'{"state":1}\n')
    with pytest.raises(AssertionError, match="H1 frozen data SHA256 changed"):
        assert_data_entry(tmp_path, row)
