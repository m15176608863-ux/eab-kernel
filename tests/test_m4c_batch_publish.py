"""Batch publication accepts a relative workspace output path.

No geometry oracle is used: subprocess computation is stubbed to isolate the
driver's final artifact-path publication, which previously failed after all
children had completed successfully.
"""
import json
from pathlib import Path
from types import SimpleNamespace
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import m4c_run_replays as batch


def test_frozen_relative_output_path_publishes_expected_fixture(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(batch, "ROOT", tmp_path)
    monkeypatch.setattr(batch.replay, "CASES", ("probe",))
    monkeypatch.setattr(batch.replay, "code_hashes", lambda: {"source": "0" * 64})
    (tmp_path / "fixtures/m4c_motion").mkdir(parents=True)
    phases = {phase: {} for phase in batch.replay.PHASES}
    audit = {"steps": 30, "counts": phases, "secondary_counts": phases, "stats": {}, "seconds": 0,
             "input_hashes": {}, "frame_sha256": ["1" * 64] * 30,
             "frames_sha256": "2" * 64, "normalized_sha256": "3" * 64}

    def child(command, **kwargs):
        directory = Path(command[command.index("--out") + 1])
        directory.mkdir(parents=True)
        (directory / "audit.json").write_text(json.dumps(audit), encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(batch.subprocess, "run", child)
    monkeypatch.setattr(batch, "validate_case_files", lambda *args: audit)
    assert batch.run_batch("frozen", Path("relative-output"), 1) == 0
    expected = json.loads((tmp_path / "fixtures/m4c_motion/expected.json").read_text(encoding="utf-8"))
    assert expected["cases"]["probe"]["normalized_file"] == "relative-output/probe/normalized.jsonl.gz"
    summary = json.loads((tmp_path / "relative-output/summary.json").read_text(encoding="utf-8"))
    assert summary["complete"] is True and summary["steps"] == 30
