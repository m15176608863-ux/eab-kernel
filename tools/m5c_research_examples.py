"""Freeze/reexecute smallest R3 real-data examples, with both model certificates."""
from frozen_evidence import data_path
import argparse
import gzip
import json
from fractions import Fraction as F

import m5c_diagnostics as research

TARGET = research.EVIDENCE / "research_minimal_examples.json"


def _plain(value):
    return json.loads(json.dumps(value, default=str))


def _evaluate(example):
    a, b = (research.replay.prepare(row) for row in example["blocks"])
    bracket = tuple(F(x) for x in example["bracket"])
    label = tuple(example["label"])
    certificates = [research.new.single_cover_certificate(a[key], b[key], label, bracket,
                                                           a["radius"], b["radius"])
                    for key in ("paths1", "paths2")]
    assert all(certificates), "minimal real-data example no longer certified"
    features = research.replay.global_labels((label,), a, b)
    result = dict(classification="ROBUST_SINGLE_FIRST_COVER", p1=dict(features=features))
    return _plain(dict(certificates=certificates, features=features,
                       legacy_counts=research.replay.legacy_counts(result, example["legacy"])))


def freeze():
    if TARGET.exists():
        raise ValueError("refuse to overwrite frozen minimal examples")
    source_path = research.EVIDENCE / "research_summary.json"
    summary = json.loads(source_path.read_text(encoding="utf-8"))
    assert summary["complete"]
    raw = research.ROOT / summary["exact_diagnostics_path"]
    assert research._sha(raw) == summary["exact_diagnostics_sha256"]
    sources, inputs = research._sources(), research.replay.input_hashes()
    inherited = {p.relative_to(research.ROOT).as_posix(): research._sha(p) for p in (source_path, raw)}
    with gzip.open(raw, "rt", encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream]
    rows.sort(key=lambda row: (sum(len(block["start"]) for block in row["blocks"]), row["case"], row["step"], row["pair"]))
    predicates = {
        "new_certificate": lambda row: row["r3_pass"] and not row["r2_pass"],
        "primary_miss": lambda row: row["r3_pass"] and row["legacy_counts"].get("raw_df05:ROBUST_FIRST_COVER_NOT_SELECTED", 0),
        "formal_all_miss": lambda row: row["r3_pass"] and row["legacy_counts"].get("raw_df05:FORMAL_ALL_FIRST_COVER_NOT_SELECTED", 0),
        "all_slots_miss": lambda row: row["r3_pass"] and row["legacy_counts"].get("raw_df05:ALL_FIRST_COVER_NOT_SELECTED", 0),
        "missing_pair": lambda row: row["r3_pass"] and row["legacy_counts"].get("raw_df05:ROBUST_CONTACT_MISSING_PAIR", 0),
    }
    selected, absent = {}, []
    for name, predicate in predicates.items():
        row = next((row for row in rows if predicate(row)), None)
        if row is None:
            absent.append(name)
            continue
        key = row["case"], row["step"], tuple(row["pair"])
        if key not in selected:
            selected[key] = dict(case=row["case"], step=row["step"], pair=row["pair"],
                                 label=row["label"], blocks=row["blocks"], legacy=row["legacy"],
                                 bracket=row["certificate"][0]["bracket"], purposes=[])
        selected[key]["purposes"].append(name)
    examples = list(selected.values())
    assert examples
    for example in examples:
        example["expected"] = _evaluate(example)
    after = research._sources()
    assert sources == after and inputs == research.replay.input_hashes()
    assert inherited == {name: research._sha(research.ROOT / name) for name in inherited}
    research._write(TARGET, dict(complete=True, source_hashes=sources, source_hashes_end=after,
                                input_hashes=inputs, inherited_hashes=inherited, examples=examples,
                                absent_purposes=absent, selection="minimum total vertices, then case/step/pair, per question"))
    assert TARGET.stat().st_size < 1_000_000


def verify(target=None):
    # Default reads immutable regression data; a new producer passes its exact output.
    source = data_path(research.ROOT, TARGET) if target is None else target
    data = json.loads(source.read_text(encoding="utf-8"))
    assert data["complete"] and data["source_hashes"] == data["source_hashes_end"]
    # H1: recorded historical source bytes are not compared to current code.
    assert data["input_hashes"] == {name.replace("fixtures/frozen/", "reports/", 1): digest
                                    for name, digest in research.replay.input_hashes().items()}
    # The 5 MB historical diagnostic stream remains archive provenance, not
    # a dependency of this self-contained selected-input replay.
    for example in data["examples"]:
        assert _evaluate(example) == example["expected"], (example["case"], example["step"], example["pair"])
    return len(data["examples"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    if args.freeze:
        freeze()
    print("M5C_RESEARCH_MINIMAL_EXAMPLES_GREEN", verify(TARGET if args.freeze else None), flush=True)
