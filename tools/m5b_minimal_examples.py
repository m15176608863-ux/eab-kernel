"""Freshly recompute small real-data examples; default verifies, never refreezes."""
import argparse
import gzip
import json
from pathlib import Path

import m5b_robust_replay as replay

TARGET = replay.EVIDENCE / "robust_minimal_examples.json"
SPECS = (("bb03", 15, (8, 11)), ("bb12", 6, (10, 11)),
         ("bb03", 1, (1, 3)), ("bb03", 1, (2, 3)), ("bb03", 1, (1, 2)))


def evaluate(example):
    a, b = (replay.prepare(row) for row in example["blocks"])
    result = replay.compare_pair(a, b)
    rows = {phase: replay.canonical_legacy_rows(example["legacy"][phase], example["blocks"])
            for phase in replay.PHASES}
    counts = dict(replay.legacy_counts(result, rows))
    return json.loads(json.dumps(dict(result=result, legacy_counts=counts), default=str))


def freeze(*, refresh=False):
    previous = TARGET.read_bytes() if TARGET.exists() else None
    if previous is not None and not refresh:
        raise ValueError("minimal examples are immutable without explicit refresh")
    if refresh:
        backup = replay.ROOT / "reports/codex/M5c_evidence/robust_minimal_examples_r2_before.json"
        if backup.exists():
            raise ValueError("refresh backup already exists")
        if previous is not None:
            backup.write_bytes(previous)
    before, inputs = replay.source_hashes(), replay.input_hashes()
    examples = []
    for case, step, pair in SPECS:
        rows = [row for row in replay.endpoint.iter_inputs(case=case) if row["step"] == step and row["block"] in pair]
        rows.sort(key=lambda row: row["block"])
        legacy = next(json.loads(line) for line in gzip.decompress((replay.LEGACY / (case+".jsonl.gz")).read_bytes()).decode().splitlines()
                      if json.loads(line)["step"] == step)
        example = dict(case=case, step=step, pair=pair, blocks=rows,
                       legacy={phase: [row for row in legacy[phase] if row["pair"] == list(pair)] for phase in replay.PHASES})
        example["expected"] = evaluate(example)
        examples.append(example)
    after = replay.source_hashes()
    replay.assert_current_sources(replay.ROOT, before, after)
    assert replay.input_hashes() == inputs
    if (TARGET.read_bytes() if TARGET.exists() else None) != previous:
        raise AssertionError("minimal target changed during actual recomputation")
    replay.write_json(TARGET, dict(complete=True, scope="five independently reexecuted selected examples, not full-run completion",
                      source_hashes=before, source_hashes_end=after, input_hashes=inputs, script_sha256=replay.sha(Path(__file__)), examples=examples))


def verify():
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    assert data["complete"]
    # Verification may run inside pytest, whose unrelated loaded modules are
    # not replay dependencies. Check every frozen dependency byte instead of
    # comparing the replay closure with that polluted process-wide namespace.
    replay.assert_current_sources(replay.ROOT, data["source_hashes"], data["source_hashes_end"])
    assert data["input_hashes"] == replay.input_hashes()
    assert data["script_sha256"] == replay.sha(Path(__file__))
    for example in data["examples"]:
        assert evaluate(example) == example["expected"], (example["case"], example["step"], example["pair"])
    return len(data["examples"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--refresh", action="store_true", help="backup and actually recompute all selected inputs")
    args = parser.parse_args()
    if args.freeze or args.refresh:
        freeze(refresh=args.refresh)
    print("M5B_MINIMAL_EXAMPLES_GREEN", verify())


if __name__ == "__main__":
    main()
