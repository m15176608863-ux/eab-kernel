"""Freeze the first 30 validated snapshot steps and run independent replay CLIs.

This is a declared read-only projection of each full default-horizon capture,
not a claim that its producer ran for 30 steps. Original header/end and whole
source SHA256 are preserved in the manifest. No sibling code is imported.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys

import m4_shadow_replay as replay
from ingest_fixtures import provenance_entry, upsert_provenance

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", type=Path, help="JSON object: bb52 etc -> absolute source JSONL path")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--byte-evidence", type=Path, default=ROOT / "fixtures/m4b_shadow/byte_matrix.json")
    args = parser.parse_args()
    sources = json.loads(args.sources.read_text(encoding="utf-8-sig"))
    byte_evidence = json.loads(args.byte_evidence.read_text(encoding="utf-8")) if args.byte_evidence.exists() else None
    final_runs = {}
    if byte_evidence is not None:
        for row in byte_evidence["cases"]:
            parts = row["case"].split("/")
            case = "bb"+parts[0]+("_db"+parts[1] if len(parts) > 1 else "")
            final_runs[case] = row
            final_path = row["modified"]["shadow"]["shadow"]["path"]
            replay.require(replay.file_hash(sources[case]) == replay.file_hash(final_path), "pilot/final snapshot hash differs")
            sources[case] = final_path
    fixture_root = ROOT / "fixtures/m4b_shadow"
    evidence = ROOT / "reports/codex/M4b_evidence/replay"
    fixture_root.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": "eab.m4b-projection.v1", "steps_per_case": 30,
                "rationale": "30 steps match the shortest FAMILY default horizon (F038/S038), extend M4a tenfold, and bound independent Fraction geometry-audit cost. Byte equivalence still uses the full default horizon; steps after 30 are not replay-audited.",
                "retention": "Only step-start geometry, explicit domain parameters, raw df05 and post df06 Tuple7 tables; no solver outputs or state columns. Lossless deterministic gzip (mtime=0).",
                "cases": {}}
    for case, filename in sources.items():
        source = Path(filename)
        header, frames, end = replay.read_snapshot(source)
        replay.require(len(frames) >= 30, f"{case}: fewer than 30 steps")
        path = fixture_root / f"{case}.jsonl.gz"
        projected = [dict(header, requested_steps=30), *frames[:30],
                     {"kind": "end", "completed_steps": 30, "status": "ok"}]
        content = "".join(json.dumps(row, separators=(",", ":"), allow_nan=False)+"\n" for row in projected).encode()
        path.write_bytes(gzip.compress(content, compresslevel=9, mtime=0))
        manifest["cases"][case] = {"file": path.name, "sha256": replay.file_hash(path), "bytes": path.stat().st_size,
                "source": str(source), "source_sha256": replay.file_hash(source), "source_bytes": source.stat().st_size,
                "source_header": header, "source_end": end, "projection": "prefix steps 1..30; only header.requested_steps and end.completed_steps changed to 30",
                "projected_step_payload_sha256": replay.digest(frames[:30]), "steps": 30,
                "m4a_fixture": case+"_N3"}
        if byte_evidence is not None:
            manifest["cases"][case].update(producer_exe_sha256=byte_evidence["modified_exe_sha256"],
                                           input_sha256=final_runs[case]["inputs"],
                                           byte_evidence_sha256=replay.file_hash(args.byte_evidence))

    def run(item):
        case, entry = item
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        for key in ("BDDA_DETECT", "BDDA_DETECT_SHADOW", "BDDA_SHADOW_PATH"):
            env.pop(key, None)
        out = evidence / case
        command = [sys.executable, "-X", "utf8", str(ROOT / "tools/m4_shadow_replay.py"),
                   str(fixture_root / entry["file"]), "--out", str(out), "--expected-steps", "30",
                   "--m4a-fixture", entry["m4a_fixture"]]
        completed = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8")
        (out / "replay.log").write_text(completed.stdout+completed.stderr, encoding="utf-8")
        result = json.loads((out / "audit.json").read_text(encoding="utf-8"))
        print(case, completed.returncode, result["audit"], flush=True)
        if completed.returncode:
            return case, None
        return case, result

    failures = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for case, result in pool.map(run, manifest["cases"].items()):
            if result is None:
                failures.append(case)
                continue
            entry = manifest["cases"][case]
            entry.update(counts=result["counts"], frames_sha256=replay.digest(result["frames"]),
                         m4a_comparison_audit="EXPLAINED", audit_sha256=replay.file_hash(evidence / case / "audit.json"),
                         m4a_identical_steps=[r["step"] for r in result["m4a_comparison"] if r["identical_classification"]],
                         m4a_changed_keys=sum(len(r["classification_changes"]) for r in result["m4a_comparison"]))
    manifest["audit"] = "RED" if failures else "GREEN"
    manifest["failures"] = failures
    replay.write_json(fixture_root / "manifest.json", manifest)
    entries = [provenance_entry(p.relative_to(ROOT / "fixtures").as_posix(),
               "captured: bdda2 worktree read-only detect shadow; tools/m4b_freeze_replay.py projection and manifest record source/header/end/hash; no solver replacement", str(date.today()))
               for p in sorted(fixture_root.iterdir()) if p.is_file()]
    upsert_provenance(entries)
    return 2 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
