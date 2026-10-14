"""Persist complete replay summaries and minimal reproducible four-question examples."""
from __future__ import annotations
import argparse
from collections import Counter
from fractions import Fraction
import gzip
import json
from pathlib import Path
import shutil

import m4c_motion_replay as replay


def bound_terminal_geometry(csv_path, frames, expected_sha256):
    """Never build examples from an endpoint source other than the audited one."""
    replay.require(replay.file_hash(csv_path) == expected_sha256, "example terminal source changed")
    terminal = replay.load_geometry_csv(csv_path, frames)
    replay.require(replay.file_hash(csv_path) == expected_sha256, "example terminal source changed while reading")
    return terminal


def ratio(numerator, denominator):
    return {"numerator": numerator, "denominator": denominator,
            "exact": str(Fraction(numerator, denominator)) if denominator else None,
            "percent_display": round(100*numerator/denominator, 6) if denominator else None}


def reference_metrics(counts):
    """Reference-row denominators; no-contact is not another earlier feature."""
    replay.require(set(counts) <= replay.CATEGORIES and all(type(v) is int and v >= 0 for v in counts.values()),
                   "unknown or invalid summary reference category")
    matches = counts.get("FIRST_COVER_MATCH", 0)
    other = counts.get("OTHER_FEATURE_FIRST", 0)
    incidence = counts.get("FIRST_INCIDENCE_NOT_COVER", 0)
    no_contact = counts.get("NO_CONTACT_IN_STEP", 0)
    contact = matches+other+incidence
    separated = contact+no_contact
    pd_match = counts.get("INITIAL_OVERLAP_PD_MATCH", 0)
    pd_other = counts.get("INITIAL_OVERLAP_PD_OTHER_FEATURE", 0)
    return {"all_reference_rows": sum(counts.values()),
            "separated_rows": separated, "separated_contact_rows": contact,
            "separated_no_contact_rows": no_contact,
            "other_feature_first_rows": other, "first_incidence_not_cover_rows": incidence,
            "first_cover_match_given_contact": ratio(matches, contact),
            "nonfirst_cover_given_contact": ratio(other+incidence, contact),
            "other_feature_first_given_contact": ratio(other, contact),
            "first_incidence_not_cover_given_contact": ratio(incidence, contact),
            "no_contact_given_separated": ratio(no_contact, separated),
            "first_cover_match_all_separated_rows": ratio(matches, separated),
            "pd_cover_match": ratio(pd_match, pd_match+pd_other)}


def legacy_example_categories(phase, legacy):
    """Primary and VV secondary references get distinct example identities."""
    result = [(phase+":"+legacy["category"], "primary")]
    if legacy.get("secondary_category") is not None:
        replay.require(legacy.get("secondary_reference") is not None, "secondary example lacks reference")
        result.append((phase+":secondary:"+legacy["secondary_category"], "secondary"))
    return tuple(result)


def summarize(full, frozen, output):
    full_summary = json.loads((full / "summary.json").read_text(encoding="utf-8"))
    frozen_summary = json.loads((frozen / "summary.json").read_text(encoding="utf-8"))
    for summary, steps in ((full_summary, 1810), (frozen_summary, 450)):
        replay.require(summary["complete"] and summary["steps"] == steps and set(summary["cases"]) == set(replay.CASES),
                       "incomplete batch cannot be persisted as complete evidence")
        replay.require(summary["code_hashes"] == replay.code_hashes(), "replay code changed after final batch")
    examples = {}; ranks = {}; diagnostics = Counter(); missed = []
    for case in replay.CASES:
        audit_path = full / case / "audit.json"
        replay.require(replay.file_hash(audit_path) == full_summary["cases"][case]["audit_sha256"], "audit hash drift")
        source = replay.ROOT / "reports/codex/M4c_evidence/tmp/kinematics_inputs" / case / "shadow.jsonl"
        _, frames, _ = replay.snapshot.read_snapshot(source)
        replay.require(replay.file_hash(source) == full_summary["cases"][case]["input_hashes"]["snapshot"], "example source changed")
        csv_path = source.with_name("geom.csv")
        terminal_hash = full_summary["cases"][case]["input_hashes"]["terminal_source"]
        terminal = bound_terminal_geometry(csv_path, frames, terminal_hash)
        normalized = full / case / "normalized.jsonl.gz"
        replay.require(replay.file_hash(normalized) == full_summary["cases"][case]["normalized_sha256"], "normalized hash drift")
        with gzip.open(normalized, "rt", encoding="utf-8") as stream:
            rows = [json.loads(line) for line in stream]
        replay.require(len(rows) == len(frames), "example replay length mismatch")
        for index, row in enumerate(rows):
            frame = frames[index]
            end = frames[index+1] if index+1 < len(frames) else {**frame, "geometry": terminal}
            sg, eg = replay.snapshot.geometry_from_frame(frame), replay.snapshot.geometry_from_frame(end)
            def choose(name, pair, legacy=None, reference_role=None):
                ba, bb = pair["pair"]
                rank = (len(sg.blocks[ba].poly)+len(sg.blocks[bb].poly), case, row["step"], ba, bb)
                if name in ranks and ranks[name] <= rank:
                    return
                ranks[name] = rank
                previous_geometry = replay.snapshot.geometry_from_frame(frames[index-1]) if index else None
                examples[name] = {"case": case, "step": row["step"], "pair": pair["pair"],
                                  "vertex_ids_A": sg.blocks[ba].vidx, "vertex_ids_B": sg.blocks[bb].vidx,
                                  "A0": sg.blocks[ba].poly, "A1": eg.blocks[ba].poly,
                                  "B0": sg.blocks[bb].poly, "B1": eg.blocks[bb].poly,
                                  "A_previous": None if previous_geometry is None else previous_geometry.blocks[ba].poly,
                                  "B_previous": None if previous_geometry is None else previous_geometry.blocks[bb].poly,
                                  "result": pair, "legacy_row": legacy,
                                  "reference_role": reference_role,
                                  "source_sha256": replay.file_hash(source),
                                  "terminal_source_sha256": terminal_hash,
                                  "reproduce": "motion_first_entrance(A0,B0,A1,B1); for initial overlap shortest_exit_fast(A0,B0)"}
            by_pair = {tuple(p["pair"]): p for p in row["pairs"]}
            for phase in replay.PHASES:
                for legacy in row["phases"][phase]["records"]:
                    pair = by_pair[tuple(legacy["pair"])]
                    for example_name, role in legacy_example_categories(phase, legacy):
                        choose(example_name, pair, legacy, role)
            for pair in row["pairs"]:
                if pair.get("missing_both_legacy_tables"):
                    choose("MISSED_NEW_CONTACT_PAIR", pair)
                    missed.append({"case": case, "step": row["step"], "pair": pair["pair"], "depth_witness": pair["depth_witness"]})
                if pair.get("initial_contact_absent_both_legacy_tables"):
                    choose("INITIAL_CONTACT_ABSENT_BOTH", pair)
                if "translation" in pair:
                    trans = pair["translation"]
                    actual_contact = pair["actual"]["status"] == "contact"
                    any_contact = actual_contact or trans["result"]["status"] == "contact"
                    different = not trans["same_first_cover_set"]
                    diagnostics["actual_new_contact_pairs"] += actual_contact
                    diagnostics["actual_contact_translation_different"] += actual_contact and different
                    diagnostics["actual_or_surrogate_contact_pairs"] += any_contact
                    diagnostics["either_contact_translation_different"] += any_contact and different
                    if different:
                        choose("TRANSLATION_DIFFERENT", pair)
                    if different and actual_contact:
                        choose("TRANSLATION_DIFFERENT_WITH_ACTUAL_CONTACT", pair)
                    if trans["certificate"] == "CERTIFIED_IDENTICAL_TRAJECTORY":
                        choose("TRANSLATION_CERTIFIED_IDENTICAL", pair)
                prediction = pair.get("prediction", {})
                if prediction.get("same_first_cover_set") is False:
                    choose("PREDICTION_DIFFERENT", pair)
        replay.require(replay.file_hash(source) == full_summary["cases"][case]["input_hashes"]["snapshot"],
                       "example source changed during summary")
        replay.require(replay.file_hash(csv_path) == terminal_hash, "example terminal source changed during summary")
    questions = {"scope": "actual-swept-or-legacy candidate pairs; vertex endpoint chord, not continuous rigid rotation",
                 "legacy_primary": {}, "legacy_secondary": {}, "diagnostics": dict(diagnostics),
                 "new_contact_pairs_missing_both": missed}
    for bucket, source_counts in (("legacy_primary", full_summary["counts"]), ("legacy_secondary", full_summary["secondary_counts"])):
        for phase, counts in source_counts.items():
            questions[bucket][phase] = reference_metrics(counts)
    stats = full_summary["stats"]
    questions["translation"] = {
        "descriptive_different_candidate_pairs": ratio(stats.get("translation_descriptive_different_cover", 0),
             stats.get("translation_descriptive_same_cover", 0)+stats.get("translation_descriptive_different_cover", 0)),
        "descriptive_different_given_actual_contact": ratio(diagnostics["actual_contact_translation_different"], diagnostics["actual_new_contact_pairs"]),
        "descriptive_different_given_either_contact": ratio(diagnostics["either_contact_translation_different"], diagnostics["actual_or_surrogate_contact_pairs"]),
        "uncertified": stats.get("translation_uncertified_nontranslation", 0),
        "certified_identical": stats.get("translation_certified_identical_trajectory", 0)}
    output.mkdir(parents=True, exist_ok=True)
    for name, summary in (("full_summary.json", full_summary), ("frozen_summary.json", frozen_summary)):
        replay.write_json(output / name, summary)
    replay.write_json(output / "four_questions.json", questions)
    replay.write_json(output / "minimal_examples.json", examples)
    replay.write_json(output / "replay_artifact_manifest.json", {
        "complete": True, "full_directory": str(full), "frozen_directory": str(frozen),
        "files": {name: replay.file_hash(output / name) for name in
                  ("full_summary.json", "frozen_summary.json", "four_questions.json", "minimal_examples.json")}})
    print("COMPLETE_PERSISTED", len(examples), "examples", len(missed), "missed new-contact pairs")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", type=Path, required=True)
    parser.add_argument("--frozen", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    summarize(args.full, args.frozen, args.out)
