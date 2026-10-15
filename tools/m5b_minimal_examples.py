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
    counts = dict(replay.legacy_counts(result, example["legacy"]))
    return json.loads(json.dumps(dict(result=result, legacy_counts=counts), default=str))


def freeze():
    if TARGET.exists():
        raise ValueError("minimal examples are immutable; never overwrite")
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
    assert replay.source_hashes() == before and replay.input_hashes() == inputs
    replay.write_json(TARGET, dict(complete=True, scope="five independently reexecuted selected examples, not full-run completion",
                      source_hashes=before, input_hashes=inputs, script_sha256=replay.sha(Path(__file__)), examples=examples))


def verify():
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    assert data["complete"] and data["source_hashes"] == replay.source_hashes()
    assert data["script_sha256"] == replay.sha(Path(__file__))
    for example in data["examples"]:
        assert evaluate(example) == example["expected"], (example["case"], example["step"], example["pair"])
    return len(data["examples"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    if args.freeze:
        freeze()
    print("M5B_MINIMAL_EXAMPLES_GREEN", verify())


if __name__ == "__main__":
    main()
