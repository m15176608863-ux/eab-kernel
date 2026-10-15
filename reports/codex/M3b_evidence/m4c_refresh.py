"""Rerun all M4c frozen frames before renewing its M3b source binding.

The production CLI is unmodified. This wrapper never calls run_batch (which
writes fixtures); comparisons use stdlib JSON/gzip/hashlib, no geometry helpers.
Incomplete runs are not reusable and never replace the source-bound summary.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "reports/codex/M3b_evidence"
OUT = EVIDENCE / "tmp/m4c_frozen_refresh_r2"
SUMMARY = ROOT / "reports/codex/M4c_evidence/frozen_summary.json"
sys.path.insert(0, str(ROOT / "tools"))
import m4c_motion_replay as replay
import m4c_run_replays as batch


def hash_file(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    temp = OUT / "temp"
    temp.mkdir()
    started = time.perf_counter()
    old_bytes = SUMMARY.read_bytes()
    old = json.loads(old_bytes)
    backup = EVIDENCE / "m4c_frozen_summary_before_r2.json"
    assert not backup.exists(), "do not overwrite historical source-bound summary"
    backup.write_bytes(old_bytes)
    expected_path = ROOT / "fixtures/m4c_motion/expected.json"
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    sources = {name: hash_file(ROOT / name) for name in replay.REPLAY_SOURCE_FILES}
    fixtures = {p.relative_to(ROOT).as_posix(): hash_file(p) for p in (ROOT / "fixtures").rglob("*") if p.is_file()}
    binding = dict(driver_sha256=hash_file(Path(__file__)), batch_driver_sha256=hash_file(ROOT / "tools/m4c_run_replays.py"),
                   source_before=sources, fixture_before=fixtures, old_summary_sha256=hash_file(backup),
                   expected_sha256=hash_file(expected_path), TEMP=str(temp), TMP=str(temp))
    write(OUT / "start.json", binding)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", TEMP=str(temp), TMP=str(temp))
    completed = {}

    def run(case):
        command = [sys.executable, "-X", "utf8", str(ROOT / "tools/m4c_motion_replay.py"),
                   str(ROOT / "fixtures/m4b_shadow" / (case+".jsonl.gz")), "--endpoint-file",
                   str(ROOT / "fixtures/m4c_motion/endpoints.json"), "--case", case,
                   "--pd-edge-limit", "0", "--out", str(OUT / case)]
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, encoding="utf-8", errors="replace")
        (OUT / (case+".log")).write_text(result.stdout+result.stderr, encoding="utf-8")
        return case, dict(returncode=result.returncode, command=command)

    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(run, case) for case in replay.CASES]):
            case, row = future.result()
            completed[case] = row
            write(OUT / "progress.json", dict(complete=False, completed=completed, source_before=sources))
            print(case, row["returncode"], flush=True)
    assert set(completed) == set(replay.CASES) == set(expected["cases"]) == set(old["cases"])
    assert all(r["returncode"] == 0 for r in completed.values()), "every replay child must complete"
    comparisons, cases = [], {}
    counts = {p: Counter() for p in replay.PHASES}
    secondary = {p: Counter() for p in replay.PHASES}
    stats = Counter()
    for case in replay.CASES:
        current = batch.validate_case_files(OUT, case, "frozen", sources, completed[case]["returncode"])
        reference = expected["cases"][case]
        original_path = ROOT / reference["normalized_file"]
        fresh_path = OUT / case / "normalized.jsonl.gz"
        assert hash_file(original_path) == reference["normalized_sha256"]
        with gzip.open(original_path, "rt", encoding="utf-8") as stream:
            original = [json.loads(line) for line in stream]
        with gzip.open(fresh_path, "rt", encoding="utf-8") as stream:
            fresh = [json.loads(line) for line in stream]
        assert len(original) == len(fresh) == current["steps"] == reference["steps"] == 30
        assert [r["step"] for r in fresh] == list(range(1, 31))
        for index in range(30):
            assert fresh[index] == original[index], (case, index+1, "full normalized frame differs")
            assert digest(fresh[index]) == reference["frame_sha256"][index] == current["frame_sha256"][index]
        assert hash_file(fresh_path) == hash_file(original_path), (case, "normalized gzip bytes differ")
        for field in ("steps", "counts", "secondary_counts", "stats", "input_hashes", "frames_sha256", "normalized_sha256"):
            assert current[field] == reference[field] == old["cases"][case][field], (case, field)
        assert current["frame_sha256"] == reference["frame_sha256"]
        assert not current["stats"].get("pd_not_evaluated_resource_pairs", 0)
        cases[case] = {k: current[k] for k in ("steps", "counts", "secondary_counts", "stats", "seconds", "input_hashes", "frames_sha256", "normalized_sha256")}
        cases[case]["audit_sha256"] = hash_file(OUT / case / "audit.json")
        comparisons.append(dict(case=case, frames=30, equal_frames=30, gzip_bytes_equal=True,
                                frame_hashes_equal=True, normalized_sha256=hash_file(fresh_path),
                                new_audit_sha256=cases[case]["audit_sha256"]))
        for phase in replay.PHASES:
            counts[phase].update(current["counts"][phase])
            secondary[phase].update(current["secondary_counts"][phase])
        stats.update(current["stats"])
    after = {name: hash_file(ROOT / name) for name in replay.REPLAY_SOURCE_FILES}
    fixtures_after = {p.relative_to(ROOT).as_posix(): hash_file(p) for p in (ROOT / "fixtures").rglob("*") if p.is_file()}
    assert sources == after, "source drift invalidates entire run"
    assert fixtures == fixtures_after, "fixtures must not change"
    assert SUMMARY.read_bytes() == old_bytes, "summary changed concurrently"
    new = dict(old, cases=cases, code_hashes=after, wall_seconds=time.perf_counter()-started, jobs=4)
    assert {p: dict(counts[p]) for p in replay.PHASES} == old["counts"]
    assert {p: dict(secondary[p]) for p in replay.PHASES} == old["secondary_counts"]
    assert dict(stats) == old["stats"]
    new["m3b_refresh"] = dict(reason="M3b changed the 2D global-entrance and exact-construction source closure; real 450-frame rerun required before source rebinding.",
                              original_summary="reports/codex/M3b_evidence/m4c_frozen_summary_before_r2.json",
                              raw_directory=OUT.relative_to(ROOT).as_posix(),
                              attestation="reports/codex/M3b_evidence/m4c_refresh_attestation.json")
    write(OUT / "summary.json", new)
    attestation = dict(status="COMPLETE", complete=True, invocations=1, resume_or_splice=False,
                       frames=450, equal_frames=sum(r["equal_frames"] for r in comparisons),
                       cases=comparisons, mismatches=0, skipped=0, all_gzip_bytes_equal=True,
                       source_before=sources, source_after=after, fixture_count=len(fixtures),
                       fixtures_unchanged=fixtures == fixtures_after, fixture_manifest_digest=digest(fixtures),
                       old_summary_sha256=hash_file(backup), new_summary_sha256=hash_file(OUT / "summary.json"),
                       raw_directory=OUT.relative_to(ROOT).as_posix(), wall_seconds=new["wall_seconds"],
                       driver_sha256=binding["driver_sha256"], batch_driver_sha256=binding["batch_driver_sha256"],
                       reason=new["m3b_refresh"]["reason"], independent_comparator_imports=["json", "gzip", "hashlib"],
                       limitations="Exact historical semantic regression, not a new independent geometry oracle; original M4c ledger oracle remains unchanged.")
    write(EVIDENCE / "m4c_refresh_attestation.json", attestation)
    SUMMARY.write_bytes((OUT / "summary.json").read_bytes())
    write(OUT / "progress.json", dict(complete=True, frames=450, source_before=sources, source_after=after,
                                      summary_sha256=hash_file(SUMMARY), fixture_unchanged=True))
    print("M4C_M3B_REFRESH_COMPLETE 450 equal_frames; fixtures unchanged; seconds", new["wall_seconds"], flush=True)


if __name__ == "__main__":
    main()
