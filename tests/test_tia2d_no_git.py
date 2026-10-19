"""No checkout is a supported provenance state, not a numerical failure."""
from pathlib import Path
import subprocess

import pytest

import tia2d_provenance as provenance
from tia2d_run_gates import source_names
import frozen_evidence


@pytest.mark.parametrize("failure", [FileNotFoundError(), subprocess.CalledProcessError(128, "git")])
def test_optional_git_records_null_and_explicit_reason(monkeypatch, tmp_path, failure):
    def unavailable(*args, **kwargs):
        raise failure
    monkeypatch.setattr(provenance.subprocess, "check_output", unavailable)
    assert provenance.git_provenance(tmp_path) == dict(git_commit=None, git_commit_reason="no_git_checkout")
    (tmp_path / "src").mkdir()
    (tmp_path / "src/example.py").write_text("pass\n", encoding="utf-8")
    (tmp_path / "reports/codex/T1a_evidence/tmp").mkdir(parents=True)
    (tmp_path / "reports/codex/T1a_evidence/tmp/ignored.txt").write_text("cache", encoding="utf-8")
    assert source_names(tmp_path) == ["src/example.py"]


def test_byte_export_does_not_borrow_parent_checkout_provenance(monkeypatch, tmp_path):
    monkeypatch.setattr(provenance.subprocess, "check_output", lambda *a, **kw: str(tmp_path.parent))
    assert provenance.git_provenance(tmp_path)["git_commit"] is None


def test_frozen_evidence_resolver_prefers_fixture_then_live_then_archive(monkeypatch, tmp_path):
    root, external = tmp_path / "source", tmp_path / "archive"
    relative = Path("reports/codex/T1a_evidence/data.json")
    monkeypatch.setattr(frozen_evidence, "ARCHIVE_ROOT", external)
    archived = external / relative
    archived.parent.mkdir(parents=True)
    archived.write_text("archive", encoding="utf-8")
    assert frozen_evidence.data_path(root, relative) == archived
    live = root / relative
    live.parent.mkdir(parents=True)
    live.write_text("live", encoding="utf-8")
    assert frozen_evidence.data_path(root, relative) == live
    fixture = root / "fixtures/frozen/codex/T1a_evidence/data.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text("fixture", encoding="utf-8")
    assert frozen_evidence.data_path(root, relative) == fixture
