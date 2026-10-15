"""WO-INT1: complete M4c replay, deep comparison, then atomic summary refresh.

Reuses the validated M3c orchestration; prior M3c and M5a lineage is preserved.
Interrupted batches are invalid and require a fresh name. No historical frames
are overwritten. All temporary files remain in INT1 evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import gzip
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import m4c_motion_replay as replay
import m4c_run_replays as batch

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/codex/INT1_evidence"


def atomic_json(path, value):
    temporary = path.with_name(path.name + ".writing")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="motion_refresh_r1")
    args = parser.parse_args()
    if Path(args.name).name != args.name or args.name in (".", ".."):
        parser.error("one new directory name required")
    out = EVIDENCE / "tmp" / args.name
    out.mkdir(parents=True, exist_ok=False)
    target = ROOT / "reports/codex/M4c_evidence/frozen_summary.json"
    backup = EVIDENCE / (args.name + "_before.json")
    if backup.exists():
        raise ValueError("refuse to overwrite rollback anchor")
    shutil.copyfile(target, backup)
    initial = replay.code_hashes()
    orchestration = {name: replay.file_hash(ROOT / name) for name in (
        "tools/int1_refresh_motion.py", "tools/m4c_run_replays.py")}
    expected_path = ROOT / "fixtures/m4c_motion/expected.json"
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    fixture_paths = [expected_path, *(ROOT / row["normalized_file"] for row in expected["cases"].values())]
    fixture_hashes = {p.relative_to(ROOT).as_posix(): replay.file_hash(p) for p in fixture_paths}
    previous_summary = json.loads(target.read_text(encoding="utf-8"))
    before = replay.file_hash(target)
    start = time.perf_counter()
    env = dict(os.environ, TEMP=str(EVIDENCE / "tmp"), TMP=str(EVIDENCE / "tmp"),
               PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1", PYTHONUNBUFFERED="1")
    progress = EVIDENCE / (args.name + "_progress.json")
    replay.write_json(progress, dict(complete=False, started=True, source_hashes=initial, completed=[]))

    def run(case):
        command = [sys.executable, "-X", "utf8", str(ROOT / "tools/m4c_motion_replay.py"),
            str(ROOT / "fixtures/m4b_shadow" / (case + ".jsonl.gz")),
            "--endpoint-file", str(ROOT / "fixtures/m4c_motion/endpoints.json"),
            "--case", case, "--pd-edge-limit", "0", "--out", str(out / case)]
        with (out / (case + ".log")).open("wb") as stream:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=3600)
        return case, result.returncode, command

    completed = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(run, case) for case in replay.CASES]):
            case, code, command = future.result()
            completed[case] = dict(exit_code=code, command=command)
            replay.write_json(progress, dict(complete=False, completed=completed, source_hashes=initial))
            print(case, code, flush=True)
    counts = {p: Counter() for p in replay.PHASES}
    secondary = {p: Counter() for p in replay.PHASES}
    stats = Counter()
    summaries = {}
    compared = 0
    for case in replay.CASES:
        result = batch.validate_case_files(out, case, "frozen", initial, completed[case]["exit_code"])
        old = expected["cases"][case]
        for field in ("steps", "counts", "secondary_counts", "stats", "input_hashes", "frame_sha256", "frames_sha256"):
            assert result[field] == old[field], (case, field, "450-frame refresh must preserve frozen semantics")
        with gzip.open(out / case / "normalized.jsonl.gz", "rt", encoding="utf-8") as stream:
            new_frames = [json.loads(s) for s in stream]
        with gzip.open(ROOT / old["normalized_file"], "rt", encoding="utf-8") as stream:
            old_frames = [json.loads(s) for s in stream]
        assert new_frames == old_frames and len(new_frames) == 30, (case, "full normalized frame values")
        compared += len(new_frames)
        summaries[case] = {k: result[k] for k in ("steps", "counts", "secondary_counts", "stats", "seconds", "input_hashes", "frames_sha256", "normalized_sha256")}
        summaries[case]["audit_sha256"] = replay.file_hash(out / case / "audit.json")
        for phase in replay.PHASES:
            counts[phase].update(result["counts"][phase])
            secondary[phase].update(result["secondary_counts"][phase])
        stats.update(result["stats"])
    assert compared == 450 and replay.code_hashes() == initial
    assert orchestration == {name: replay.file_hash(ROOT / name) for name in orchestration}, "orchestration changed during replay"
    assert all(replay.file_hash(ROOT / name) == value for name, value in fixture_hashes.items()), "frozen expected fixtures changed during replay"
    assert replay.file_hash(target) == before, "summary changed while replay ran"
    summary = dict(schema="eab.m4c-batch.v1", audit="GREEN", complete=True, mode="frozen",
        cases=summaries, steps=compared, code_hashes=initial,
        counts={p: dict(sorted(v.items())) for p, v in counts.items()},
        secondary_counts={p: dict(sorted(v.items())) for p, v in secondary.items()},
        stats=dict(sorted(stats.items())), wall_seconds=time.perf_counter()-start, jobs=4,
        int1_refresh=dict(orchestration_hashes=orchestration, reason="Integrated M3/M5 source; complete recomputation and all frame values compared, not hash-only rebinding.",
            original_summary=backup.relative_to(ROOT).as_posix(), raw_directory=out.relative_to(ROOT).as_posix(),
            attestation="reports/codex/INT1_evidence/" + args.name + "_attestation.json"))
    for key in ("m3c_refresh", "m5a_revalidation"):
        summary[key] = previous_summary[key]
    replay.write_json(out / "summary.json", summary)
    atomic_json(target, summary)
    replay.write_json(EVIDENCE / (args.name + "_attestation.json"), dict(status="GREEN", complete=True,
        cases=15, frames=compared, full_frame_values_equal=True, source_unchanged=True,
        source_hashes=initial, orchestration_hashes=orchestration, before_summary_sha256=before, after_summary_sha256=replay.file_hash(target),
        actual_replay_summary_sha256=replay.file_hash(out / "summary.json"), raw_directory=str(out),
        seconds=summary["wall_seconds"], expected_fixture_unchanged=True,
        expected_fixture_hashes_before_and_after=fixture_hashes))
    replay.write_json(progress, dict(complete=True, frames=compared, status="GREEN"))
    print("INT1_MOTION_REFRESH_GREEN 450 actual frames, full values identical")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
