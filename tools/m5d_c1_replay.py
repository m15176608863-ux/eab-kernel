"""Fresh full-history C1 replay; never re-label a frozen prior computation.

Only the 16676 independently detected initially overlapping step/block pairs
enter C1. Its radius is exactly the M5b/M5c full-step vertex tube budget; this
is a conservative static-neighborhood claim at the initial geometry, NOT a
claim that the entire evolving geometry stays in that initial neighborhood.
Each rejected pair remains unproved. Raw per-pair records stay in ignored tmp.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import gzip
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools")]
import m5b_robust_replay as replay
from eab.kernel2d.m5d_exit_certificate import exit_order_certificate
from eab.kernel2d.g0_oracle import overlap
from m5d_c1_oracle import exit_oracle
from m5c_source_binding import runtime_source_hashes, assert_current_sources

EVIDENCE = ROOT / "reports/codex/M5d_evidence"
TMP = EVIDENCE / "tmp"


def sources():
    return runtime_source_hashes(ROOT, __file__)


def reference_counts(label, selected):
    result = Counter()
    for phase in replay.PHASES:
        all_labels = []
        for slot in ("primary", "secondary", "shared_edge"):
            labels = [tuple(row[slot]) for row in selected[phase] if row.get(slot) is not None]
            all_labels.extend(labels)
            prefix = phase+":"+slot
            result[prefix+":total"] += len(labels)
            result[prefix+":match"] += sum(value == label for value in labels)
            result[prefix+":other"] += sum(value != label for value in labels)
            result[prefix+":pair_hit"] += label in labels
        result[phase+":all_slots:pair_hit"] += label in all_labels
        result[phase+":all_slots:pair_miss"] += label not in all_labels
    return result


def run_case(case, directory, source_hashes, input_hashes):
    if sources() != source_hashes or replay.input_hashes() != input_hashes:
        raise AssertionError("C1 worker start binding changed")
    out = Path(directory) / case
    out.mkdir(exist_ok=False)
    frames = defaultdict(list)
    for row in replay.endpoint.iter_inputs(case=case):
        frames[row["step"]].append(row)
    legacy = {row["step"]: row for row in (json.loads(line) for line in
              gzip.decompress((replay.LEGACY / (case+".jsonl.gz")).read_bytes()).decode().splitlines())}
    counts, references, unproved_references = Counter(), Counter(), Counter()
    examples = {}
    started = time.perf_counter()
    raw = out / "pairs.jsonl.gz"
    with gzip.open(raw, "wt", encoding="utf-8", newline="\n") as stream:
        for step, rows in frames.items():
            blocks = {row["block"]: replay.prepare(row) for row in rows}
            ids = sorted(blocks)
            for k, ida in enumerate(ids):
                for idb in ids[k+1:]:
                    a, b = blocks[ida], blocks[idb]
                    counts["all_step_block_pairs"] += 1
                    if overlap(a["start"], b["start"]) != 1:
                        continue
                    counts["initial_overlap_pairs"] += 1
                    result = exit_order_certificate(a["start"], b["start"], a["radius"], b["radius"])
                    reason = result.get("reason", result["status"])
                    counts[reason] += 1
                    selected = {phase: replay.canonical_legacy_rows(
                        [row for row in legacy[step][phase] if row["pair"] == [ida, idb]], rows)
                        for phase in replay.PHASES}
                    packed = dict(case=case, step=step, pair=[ida, idb], result=result,
                                  radius_a=a["radius"], radius_b=b["radius"])
                    if result["status"] == "CERTIFIED_UNIQUE_EXIT":
                        oracle = exit_oracle(a["start"], b["start"])
                        if (not oracle["inside"] or oracle["labels"] != (result["label"],)
                                or oracle["distance2"] != result["distance2"]):
                            raise AssertionError("C1 independent nominal hull oracle mismatch")
                        counts["independent_oracle_checks"] += 1
                        label = replay.global_labels((result["label"],), a, b)[0]
                        refs = reference_counts(label, selected)
                        references.update(refs)
                        packed.update(global_label=label, references=dict(refs))
                    else:
                        for phase in replay.PHASES:
                            for slot in ("primary", "secondary", "shared_edge"):
                                unproved_references[phase+":"+slot+":total"] += sum(
                                    row.get(slot) is not None for row in selected[phase])
                    stream.write(json.dumps(packed, default=str, separators=(",", ":"))+"\n")
                    if reason not in examples:
                        examples[reason] = dict(**packed, a=a["start"], b=b["start"], legacy=selected)
            counts["steps"] += 1
            counts["blocks"] += len(rows)
            if step % 10 == 0 or step == max(frames):
                replay.write_json(out / "progress.json", dict(complete=False, step=step, counts=dict(counts)))
    observed = sources()
    assert_current_sources(ROOT, source_hashes, observed)
    if replay.input_hashes() != input_hashes:
        raise AssertionError("C1 worker input binding changed")
    summary = dict(case=case, complete=True, counts=dict(counts), references=dict(references),
                   unproved_references=dict(unproved_references), examples=examples,
                   raw_sha256=replay.sha(raw), seconds=time.perf_counter()-started)
    replay.write_json(out / "summary.json", summary)
    replay.write_json(out / "progress.json", dict(complete=True, counts=dict(counts)))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    if Path(args.name).name != args.name or args.name in (".", ".."):
        parser.error("fresh single directory name required")
    os.environ["TEMP"] = os.environ["TMP"] = str(TMP)
    out = TMP / args.name
    out.mkdir(parents=True, exist_ok=False)
    expected_sources, expected_inputs = sources(), replay.input_hashes()
    manifest = json.loads((replay.endpoint.INPUTS / "manifest.json").read_text(encoding="utf-8"))
    cases = sorted(manifest["cases"])
    started = time.perf_counter()
    results, counts, refs, unproved = {}, Counter(), Counter(), Counter()
    replay.write_json(out / "progress.json", dict(complete=False, interruption_invalidates=True))
    with ProcessPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(run_case, case, out, expected_sources, expected_inputs) for case in cases]
        for future in as_completed(futures):
            result = future.result()
            results[result["case"]] = result
            counts.update(result["counts"])
            refs.update(result["references"])
            unproved.update(result["unproved_references"])
            replay.write_json(out / "progress.json", dict(complete=False, completed=sorted(results), counts=dict(counts)))
            print(result["case"], result["counts"], flush=True)
    observed = sources()
    assert_current_sources(ROOT, expected_sources, observed)
    if replay.input_hashes() != expected_inputs:
        raise AssertionError("C1 batch input binding changed")
    if tuple(counts[key] for key in ("steps", "blocks", "all_step_block_pairs", "initial_overlap_pairs")) != (1810, 15220, 64010, 16676):
        raise AssertionError("C1 full-history coverage mismatch")
    summary = dict(schema="eab.m5d-c1-replay.v1", complete=True, counts=dict(counts), references=dict(refs),
                   unproved_references=dict(unproved), cases=results, source_hashes=expected_sources,
                   source_hashes_end=observed, input_hashes=expected_inputs,
                   seconds=time.perf_counter()-started, raw_directory=out.relative_to(ROOT).as_posix(),
                   radius_basis="M5b per-block bound + residual + endpoint_parameter at initial geometry",
                   limitations=["Static initial-neighborhood result, not whole-step exit-order persistence",
                                "Unproved pairs do not support any shortest-exit legacy conclusion",
                                "Concave rings, cross-ring parallelism and nominal ties are refused"])
    replay.write_json(out / "summary.json", summary)
    replay.write_json(out / "progress.json", dict(complete=True, counts=dict(counts)))
    if args.publish:
        target = EVIDENCE / "c1_summary.json"
        if target.exists():
            raise ValueError("C1 publication exists; archive it explicitly before fresh publication")
        replay.write_json(target, summary)
        if target.stat().st_size > 1_000_000:
            raise AssertionError("C1 frozen summary exceeds 1 MB")
    print("M5D_C1_REPLAY_COMPLETE", dict(counts), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
