"""WO-INT1 complete M5a2/M5a revalidation with compare-before-publish.

Reuses the established 450-frame runner, redirecting its candidate manifest to
ignored INT1 tmp. Historical M5a frames and the previous M5a2 normalized output
hashes must agree before replacing the one revalidation manifest/provenance row.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys

import m5a2_revalidate_replay as batch

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/codex/INT1_evidence"


def atomic_bytes(path, raw):
    temporary = path.with_name(path.name + ".writing")
    temporary.write_bytes(raw)
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="se2_revalidation_r1")
    args = parser.parse_args()
    if Path(args.name).name != args.name or args.name in (".", ".."):
        parser.error("fresh single directory name required")
    target = ROOT / "fixtures/m5a2/revalidation.json"
    provenance_path = ROOT / "fixtures/PROVENANCE.json"
    backup = EVIDENCE / (args.name + "_before.json")
    candidate = EVIDENCE / "tmp" / (args.name + "_candidate.json")
    if backup.exists() or candidate.exists():
        parser.error("fresh output name required; interrupted runs cannot be resumed")
    orchestrator_hash = batch.replay.file_hash(Path(__file__))
    before = target.read_bytes()
    old = json.loads(before)
    provenance_before = provenance_path.read_bytes()
    provenance = json.loads(provenance_before)
    backup.write_bytes(before)
    batch.EVIDENCE = EVIDENCE
    batch.MANIFEST = candidate
    sys.argv = ["m5a2_revalidate_replay", "--name", args.name, "--jobs", "4"]
    if batch.main() != 0:
        raise RuntimeError("complete revalidation failed; manifest not published")
    result = json.loads(candidate.read_text(encoding="utf-8"))
    comparisons = {}
    for case in batch.replay.CASES:
        comparisons[case] = {key: result["cases"][case][key] == old["cases"][case][key]
                             for key in ("normalized_sha256", "old_normalized_sha256", "counts", "stats",
                                         "steps", "time_representation_changes", "all_semantic_fields_equal")}
    agreement = all(all(row.values()) for row in comparisons.values())
    batch.replay.write_json(EVIDENCE / (args.name + "_comparison.json"),
        dict(complete=True, all_previous_m5a2_products_identical=agreement, cases=comparisons,
             historical_m5a_comparison="every leaf equal except previously accepted exactly equal time certificates",
             previous_and_current_time_representation_changes_identical=(old["time_representation_changes"] == result["time_representation_changes"])))
    if not agreement or old["time_representation_changes"] != result["time_representation_changes"]:
        raise AssertionError("historical result differs: stop without publishing candidate")
    if target.read_bytes() != before or provenance_path.read_bytes() != provenance_before:
        raise AssertionError("publication target changed during complete replay")
    if batch.replay.file_hash(Path(__file__)) != orchestrator_hash:
        raise AssertionError("orchestrator changed during complete revalidation")
    if batch.replay.code_hashes() != result["code_hashes"]:
        raise AssertionError("source changed before publication")
    result["int1_refresh"] = dict(orchestrator_sha256=orchestrator_hash, previous_manifest=backup.relative_to(ROOT).as_posix(),
        previous_manifest_sha256=batch.replay.file_hash(backup),
        previous_m5a2_all_normalized_hashes_identical=True,
        comparison=(EVIDENCE / (args.name + "_comparison.json")).relative_to(ROOT).as_posix())
    updated = copy.deepcopy(provenance)
    matches = [row for row in updated["entries"] if row["dest"] == "m5a2/revalidation.json"]
    if len(matches) != 1:
        raise AssertionError("exactly one existing M5a2 provenance row required")
    atomic_bytes(target, (json.dumps(result, ensure_ascii=False, indent=2)+"\n").replace("\n", "\r\n").encode("utf-8"))
    matches[0].update(bytes=target.stat().st_size, sha256=batch.replay.file_hash(target),
        source="WO-INT1: tools/int1_revalidate_replay.py using tools/m5a2_revalidate_replay.py; complete 450-frame reexecution; all previous M5a2 normalized hashes identical and historical M5a semantic fields equal; original frozen fixtures unchanged.")
    # Preserve the established one-space indentation, CRLF, and no final newline.
    atomic_bytes(provenance_path, json.dumps(updated, ensure_ascii=False, indent=1).replace("\n", "\r\n").encode("utf-8"))
    untouched = all(a == b for a, b in zip(provenance["entries"], updated["entries"])
                    if a["dest"] != "m5a2/revalidation.json")
    assert untouched and len(provenance["entries"]) == len(updated["entries"])
    batch.replay.write_json(EVIDENCE / (args.name + "_attestation.json"), dict(
        complete=True, audit="GREEN", frames=450, orchestrator_sha256=orchestrator_hash, all_prior_normalized_hashes_equal=True,
        original_m5a_fixture_bytes_unchanged=result["all_historical_fixture_bytes_unchanged"],
        old_provenance_entries_unchanged=untouched, updated_provenance_dest="m5a2/revalidation.json",
        before_provenance_row=next(row for row in provenance["entries"] if row["dest"] == "m5a2/revalidation.json"),
        after_provenance_row=matches[0], code_hashes=result["code_hashes"],
        seconds=result["seconds"], manifest_sha256=batch.replay.file_hash(target)))
    print("INT1_SE2_REVALIDATION_GREEN 450 actual frames; all prior products identical", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
