"""WO-M4c-fix: reproducible domain/secondary-reference and historical byte audits.

Only local copied inputs are consumed; no sibling process or source is executed.
Domain validation deliberately calls the production domain contract, not an
independent geometric oracle. Historical integrity scans never repair/delete bytes.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import time

import m4c_motion_replay as replay
from m4c_run_replays import INPUTS, FULL_STEPS

ROOT = replay.ROOT
EVIDENCE = ROOT / "reports/codex/M4c_evidence"


def domain_audit(output):
    started = time.perf_counter()
    historical = json.loads((EVIDENCE / "full_summary.json").read_text(encoding="utf-8"))
    cases = {}
    for case in replay.CASES:
        source, endpoint = INPUTS / case / "shadow.jsonl", INPUTS / case / "geom.csv"
        hashes = {"snapshot": replay.file_hash(source), "terminal_source": replay.file_hash(endpoint)}
        replay.require(hashes == historical["cases"][case]["input_hashes"], "historical input identity")
        _, frames, _ = replay.snapshot.read_snapshot(source)
        terminal = replay.load_geometry_csv(endpoint, frames)
        geometries = replay.paired_geometries(frames, terminal)
        replay.require(len(frames) == FULL_STEPS[case], "full case frame count")
        counts = Counter(steps=len(frames))
        rejected = []
        secondary_differences = []
        for frame, sg, eg in geometries:
            bad = {}
            blocks = sorted(sg.blocks)
            counts["step_blocks"] += len(blocks)
            for block in blocks:
                try:
                    replay.motion._validated_motion(replay._exact_poly(sg.blocks[block].poly),
                                                    replay._exact_poly(eg.blocks[block].poly))
                except ValueError as exc:
                    bad[block] = str(exc)
            pairs = [(a, b) for i, a in enumerate(blocks) for b in blocks[i+1:]]
            counts["all_step_block_pairs"] += len(pairs)
            for a, b in pairs:
                if a in bad or b in bad:
                    rejected.append({"step": frame["step"], "pair": [a, b], "invalid_blocks": bad})
            for phase in replay.PHASES:
                for index, row in enumerate(frame[phase], 1):
                    old = row[0] == 1 and all(row[k] for k in (4, 5, 6))
                    new = row[0] == 1 and row[4] > 0
                    counts[phase + "_secondary_old"] += old
                    counts[phase + "_secondary_new"] += new
                    if old != new:
                        secondary_differences.append({"step": frame["step"], "phase": phase,
                                                      "index": index, "tuple7": row})
        replay.require(hashes == {"snapshot": replay.file_hash(source), "terminal_source": replay.file_hash(endpoint)},
                       "input changed during audit")
        cases[case] = {"counts": dict(counts), "input_hashes": hashes,
                       "domain_rejected_step_block_pairs": rejected,
                       "secondary_rule_differences": secondary_differences}
        print(case, dict(counts), flush=True)
    totals = Counter()
    for row in cases.values():
        totals.update(row["counts"])
    rejected_count = sum(len(r["domain_rejected_step_block_pairs"]) for r in cases.values())
    # No rejected pair implies no rejection *after* an existing first contact;
    # nonzero rejections would need a separate prefix-contact computation.
    result = {"schema": "eab.m4c-fix.domain-audit.v1", "complete": True,
              "domain_policy": "whole-step conservative refusal; out-of-domain is not no-contact",
              "method": "validate every block over [0,1], including swept-box-excluded pairs",
              "totals": dict(totals), "cases": cases,
              "domain_rejected_step_block_pairs": rejected_count,
              "post_contact_only_domain_rejected_step_block_pairs": 0 if rejected_count == 0 else None,
              "secondary_rule_differences": sum(len(r["secondary_rule_differences"]) for r in cases.values()),
              "code_hashes": replay.code_hashes(), "seconds": time.perf_counter()-started}
    replay.write_json(output, result)
    return 0


def history_audit(output):
    names = subprocess.check_output(["git", "ls-files", "-z", "reports/codex/M4c_evidence"], cwd=ROOT).decode().split("\0")
    invalid = []
    for name in filter(None, names):
        path = ROOT / name
        data = path.read_bytes()
        reason = "ALL_NUL" if data and not data.strip(b"\0") else None
        if path.suffix == ".gz":
            try:
                with gzip.open(path, "rb") as stream:
                    while stream.read(1024*1024):
                        pass
            except (EOFError, OSError) as exc:
                reason = type(exc).__name__ + ": " + str(exc)
        if reason:
            invalid.append({"path": path.relative_to(EVIDENCE).as_posix(), "reason": reason,
                            "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    replay.write_json(output, {"schema": "eab.m4c-fix.history-integrity.v1",
                              "scope": "git ls-files reports/codex/M4c_evidence; read-only bytes",
                              "tracked_files_scanned": len(list(filter(None, names))), "invalid_files": invalid})
    print("HISTORY_INVALID_FILES", len(invalid))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("domain", "history"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    output = args.out.resolve()
    if not output.is_relative_to(EVIDENCE) or output.exists():
        parser.error("output must be a new file inside M4c_evidence")
    raise SystemExit((domain_audit if args.mode == "domain" else history_audit)(output))
