"""Independent exact-time sensitivity recount; standard library only.

Saved canonical minimal-polynomial/rational certificates are compared as
exact serialized values, never via the rounded time_display field. Two
no-contact results both have null time and therefore contribute no difference.
"""
import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
TEMPORARY = ROOT / "reports/codex/M4c_evidence/tmp/review_summary"
TEMPORARY.mkdir(exist_ok=True)
os.environ["TEMP"] = os.environ["TMP"] = str(TEMPORARY)


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rate(numerator, denominator):
    return {"numerator": numerator, "denominator": denominator,
            "exact": str(Fraction(numerator, denominator)) if denominator else None,
            "percent_display": 100*numerator/denominator if denominator else None}


def run(full, output):
    start = time.perf_counter()
    summary_path = full / "summary.json"
    summary_hash = file_hash(summary_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["complete"] is True and summary["steps"] == 1810 and len(summary["cases"]) == 15
    counts = {scope: Counter() for scope in ("all_evaluated_candidates", "given_actual_contact", "given_either_contact")}
    diagnostics = Counter()
    witnesses = {}
    normalized_hashes = {}
    steps = 0
    for case, case_data in summary["cases"].items():
        path = full / case / "normalized.jsonl.gz"
        observed_hash = file_hash(path)
        assert observed_hash == case_data["normalized_sha256"]
        normalized_hashes[case] = observed_hash
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            rows = [json.loads(line) for line in stream]
        assert len(rows) == case_data["steps"]
        for row in rows:
            steps += 1
            for pair in row["pairs"]:
                if "translation" not in pair:
                    continue
                assert pair["initial_state"] == -1
                actual = pair["actual"]
                translation = pair["translation"]
                surrogate = translation["result"]
                actual_contact = actual["status"] == "contact"
                surrogate_contact = surrogate["status"] == "contact"
                assert (actual["time"] is not None) == actual_contact
                assert (surrogate["time"] is not None) == surrogate_contact
                time_difference = actual["time"] != surrogate["time"]
                assert translation["same_time"] == (not time_difference), "stored same_time differs from exact certificates"
                cover_difference = (actual["status"] != surrogate["status"] or actual["features"] != surrogate["features"])
                assert translation["same_first_cover_set"] == (not cover_difference)
                any_difference = time_difference or cover_difference
                scopes = ["all_evaluated_candidates"]
                if actual_contact:
                    scopes.append("given_actual_contact")
                if actual_contact or surrogate_contact:
                    scopes.append("given_either_contact")
                for scope in scopes:
                    count = counts[scope]
                    count["denominator"] += 1
                    count["exact_time_difference"] += time_difference
                    count["status_or_cover_difference"] += cover_difference
                    count["status_cover_or_time_difference"] += any_difference
                    count["same_status_cover_but_different_exact_time"] += time_difference and not cover_difference
                diagnostics["both_no_contact"] += not actual_contact and not surrogate_contact
                diagnostics["both_contact"] += actual_contact and surrogate_contact
                diagnostics["only_one_contact"] += actual_contact != surrogate_contact
                diagnostics["stored_same_time_checks"] += 1
                if not actual_contact and not surrogate_contact:
                    assert not time_difference and not any_difference
                names = []
                if time_difference and not cover_difference:
                    names.append("same_status_cover_but_different_exact_time")
                if actual_contact and surrogate_contact and time_difference:
                    names.append("both_contact_different_exact_time")
                if actual_contact != surrogate_contact:
                    names.append("one_contact_other_no_contact")
                identity = (case, row["step"], tuple(pair["pair"]))
                for name in names:
                    old = witnesses.get(name)
                    if old is None or identity < (old["case"], old["step"], tuple(old["pair"])):
                        witnesses[name] = {"case": case, "step": row["step"], "pair": pair["pair"],
                                           "actual": actual, "translation": translation,
                                           "normalized_sha256": observed_hash,
                                           "reproduce": "Compare actual.time and translation.result.time canonical exact certificates; check translation.same_time"}
    assert steps == 1810
    assert counts["all_evaluated_candidates"]["denominator"] == 17603
    assert counts["given_actual_contact"]["denominator"] == 68
    assert counts["given_either_contact"]["denominator"] == 838
    assert file_hash(summary_path) == summary_hash
    metrics = {}
    for scope, count in counts.items():
        denominator = count["denominator"]
        metrics[scope] = {name: rate(count[name], denominator) for name in
                          ("exact_time_difference", "status_or_cover_difference", "status_cover_or_time_difference",
                           "same_status_cover_but_different_exact_time")}
    result = {"complete": True, "steps": steps, "cases": 15,
              "scope": "Initial-separated actual-swept-or-legacy candidates only; exact saved canonical certificates, not time_display",
              "no_contact_policy": "Two null times contribute zero difference; one null and one contact time differ",
              "metrics": metrics, "diagnostics": dict(diagnostics),
              "minimum_identity_witnesses": witnesses,
              "minimum_identity_order": "lexicographic case,step,pair; not geometric minimization",
              "full_summary_sha256": summary_hash, "normalized_sha256": normalized_hashes,
              "script_sha256": file_hash(Path(__file__)), "seconds": time.perf_counter()-start,
              "independence": "stdlib only; no replay, summarizer or geometry API imports"}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"complete": True, "metrics": metrics, "diagnostics": dict(diagnostics), "seconds": result["seconds"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.full, args.out)
