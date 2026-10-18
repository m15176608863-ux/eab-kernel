"""H1 deliverable size gate, including a no-Git export and a real-file mutation.

Git is read-only when present. Fresh exports fall back to a filesystem inventory
of deliverable roots and the repository's positive .gitignore patterns. Runtime
cache/temp output is not a deliverable; a tracked ignored file still is.
"""
from pathlib import Path

import pytest

from repository_size import LIMIT, assert_deliverable_sizes

ROOT = Path(__file__).resolve().parents[1]


def test_every_tracked_or_deliverable_file_is_at_most_one_megabyte_except_frozen_policy():
    assert_deliverable_sizes(ROOT)


def test_no_git_export_gate_reads_actual_files_and_catches_oversized_candidate(tmp_path):
    source = tmp_path / "src" / "eab" / "size_mutant.py"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"#" * LIMIT)
    assert_deliverable_sizes(tmp_path)
    # Inject into the actual exported source candidate, not into scanner output.
    source.write_bytes(b"#" * (LIMIT + 1))
    with pytest.raises(AssertionError, match="deliverable file exceeds") as caught:
        assert_deliverable_sizes(tmp_path)
    assert "src/eab/size_mutant.py" in str(caught.value)


def test_export_ignores_only_declared_runtime_outputs_and_keeps_other_evidence(tmp_path):
    (tmp_path / ".gitignore").write_text("reports/codex/*/tmp/\n__pycache__/\n", encoding="utf-8")
    ignored = tmp_path / "reports" / "codex" / "H1_evidence" / "tmp" / "runtime.log"
    ignored.parent.mkdir(parents=True)
    ignored.write_bytes(b"x" * (LIMIT + 1))
    assert_deliverable_sizes(tmp_path)
    candidate = ignored.parents[1] / "deliverable.log"
    candidate.write_bytes(b"x" * (LIMIT + 1))
    with pytest.raises(AssertionError, match="deliverable file exceeds") as caught:
        assert_deliverable_sizes(tmp_path)
    assert "deliverable.log" in str(caught.value)
