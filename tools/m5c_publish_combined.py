"""Publish an exact full-history R2 + exhaustive new-contact R3 evidence join.

No solver, certificate or replay module is imported. The historical and fresh
64,010-pair streams are checked record-for-record on exact P1/P2 observations.
All 68 new-contact keys must then join the separately re-solved R2/R3 evidence.
This is NOT another all-pairs P2 solve; it is a bound two-stage evidence join.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
from itertools import combinations, zip_longest
import json
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]
FULL_COVERAGE = (1810, 15220, 64010)
FULL_CASES = 15
NEW_CONTACT_PAIRS = 68
R2_CERTIFIED = 2
EVIDENCE = "reports/codex/M5c_evidence"
BASELINE = EVIDENCE + "/robust_full_m5c_r2_robust_summary_before.json"
FRESH = "reports/codex/M5b_evidence/robust_summary.json"
RESEARCH = EVIDENCE + "/research_summary.json"
DIAGNOSTICS = EVIDENCE + "/research_diagnostics.json"
OUTPUT = EVIDENCE + "/combined_summary.json"
MANIFEST = "reports/codex/M5b_evidence/endpoint_inputs/manifest.json"
SCRIPT = "tools/m5c_publish_combined.py"
CLASSES = {"ROBUST_NO_CONTACT", "ROBUST_SINGLE_FIRST_COVER", "MODEL_SENSITIVE_OR_UNPROVED"}
PHASES = ("raw_df05", "post_df06")
REFERENCE_TOTALS = ("PRIMARY_REFERENCE_TOTAL", "SECONDARY_REFERENCE_TOTAL", "SHARED_EDGE_SLOT_TOTAL")
JOIN_FIELDS = ("case", "step", "pair", "label", "features", "r2_pass", "r3_pass", "certified_union", "legacy_counts")


def require(condition, message):
    if not condition:
        raise ValueError("combined evidence: " + message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def local(root, name):
    path = (root / name).resolve()
    require(path.is_relative_to(root) and path.relative_to(root).as_posix() == name,
            "noncanonical or outside-worktree path: " + name)
    return path


def bind(root, name, bindings, expected=None):
    digest = sha(local(root, name))
    require(expected is None or digest == expected, "hash mismatch: " + name)
    require(name not in bindings or bindings[name] == digest, "input changed during read: " + name)
    bindings[name] = digest
    return local(root, name)


def read(root, name, bindings):
    return json.loads(bind(root, name, bindings).read_text(encoding="utf-8"))


def check_hash_map(root, mapping, bindings):
    require(isinstance(mapping, dict) and bool(mapping), "missing hash map")
    for name, digest in mapping.items():
        bind(root, name, bindings, digest)


def check_sources(root, summary, bindings):
    require(summary.get("source_hashes") == summary.get("source_hashes_end"), "source start/end differ")
    check_hash_map(root, summary.get("source_hashes"), bindings)


def count_map(value):
    require(isinstance(value, dict) and all(type(v) is int and v >= 0 for v in value.values()), "invalid nonnegative count map")
    return Counter(value)



def research_case_counts(value):
    """Normalize only the observed Counter.update(False) zero-count encoding.

    The frozen research schema accidentally serializes an initial false flag
    as JSON false in these three count fields. False is exactly the zero case;
    True, candidate booleans, floats, negatives and unknown fields remain errors.
    The normalized values must still equal independently accumulated exact rows.
    """
    flags = {"r2_pass", "r3_pass", "certified_union"}
    require(isinstance(value, dict) and set(value) == flags | {"candidates"}, "unexpected research case count fields")
    return count_map({name: 0 if name in flags and number is False else number
                      for name, number in value.items()})

def key(row):
    pair = row["pair"]
    require(type(row["step"]) is int and row["step"] > 0
            and isinstance(pair, list) and len(pair) == 2
            and all(type(x) is int for x in pair) and pair[0] < pair[1], "invalid pair key")
    return row["case"], row["step"], tuple(pair)


def iter_rows(path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)


def count_result(result):
    classification, basis = result["classification"], result["comparison_basis"]
    require(classification in CLASSES, "unknown classification")
    require(basis in {"EXPLICIT_TRAJECTORY", "CONSTRUCTED_INITIAL_CONTACT", "CONSTRUCTED_INITIAL_OVERLAP", "CERTIFICATE_DIRECT"}, "unknown comparison basis")
    counts = Counter({"pairs": 1, classification: 1, "comparison_basis:"+basis: 1})
    if basis == "EXPLICIT_TRAJECTORY":
        require(result.get("initial_state") == -1, "explicit trajectory is not initially separated")
        counts["p1_p2_explicit_same" if result["same"] else "p1_p2_explicit_different"] += 1
        counts["explicit_new_contact_pairs"] += result["p1"]["status"] != "no_contact"
    counts["independent_initial_state_evaluations"] += result["oracle_checked"]
    counts["production_initial_state_crosschecks"] += result["production_initial_crosschecked"]
    if classification == "MODEL_SENSITIVE_OR_UNPROVED" and result.get("reason"):
        counts[result["reason"]] += 1
    return counts


def candidate(row):
    return row["result"].get("initial_state") == -1 and row["result"]["p1"]["status"] == "contact"



def check_candidate_references(counts, certified):
    for phase in PHASES:
        total, second, shared = (counts.get(phase+":"+name, 0) for name in REFERENCE_TOTALS)
        require(all(counts.get(phase+":"+name, 0) == 0 for name in (
            "ROBUST_NO_CONTACT_REFERENCE", "ROBUST_NO_CONTACT_SECONDARY_REFERENCE", "ROBUST_NO_CONTACT_SHARED_EDGE_SLOT")),
            "new-contact candidate retains no-contact categories")
        if certified:
            require(all(counts.get(phase+":"+name, 0) == 0 for name in (
                "UNPROVED_REFERENCE", "UNPROVED_SECONDARY_REFERENCE", "UNPROVED_SHARED_EDGE_SLOT")),
                "certified candidate retains unproved categories")
        else:
            require(all(counts.get(phase+":"+name, 0) == 0 for name in (
                "FIRST_COVER_MATCH", "OTHER_REFERENCE", "SECONDARY_FIRST_COVER_MATCH", "SECONDARY_OTHER_REFERENCE",
                "SHARED_EDGE_FIRST_COVER_MATCH", "SHARED_EDGE_OTHER_REFERENCE", "ROBUST_CONTACT_MISSING_PAIR",
                "ROBUST_FIRST_COVER_NOT_SELECTED", "FORMAL_ALL_FIRST_COVER_NOT_SELECTED", "ALL_FIRST_COVER_NOT_SELECTED")),
                "unproved candidate retains certified categories")
        if not certified:
            require((counts.get(phase+":UNPROVED_REFERENCE", 0),
                     counts.get(phase+":UNPROVED_SECONDARY_REFERENCE", 0),
                     counts.get(phase+":UNPROVED_SHARED_EDGE_SLOT", 0)) == (total, second, shared),
                    "unproved candidate reference categories do not conserve row totals")
            continue
        primary_match = counts.get(phase+":FIRST_COVER_MATCH", 0)
        second_match = counts.get(phase+":SECONDARY_FIRST_COVER_MATCH", 0)
        shared_match = counts.get(phase+":SHARED_EDGE_FIRST_COVER_MATCH", 0)
        require((primary_match+counts.get(phase+":OTHER_REFERENCE", 0),
                 second_match+counts.get(phase+":SECONDARY_OTHER_REFERENCE", 0),
                 shared_match+counts.get(phase+":SHARED_EDGE_OTHER_REFERENCE", 0)) == (total, second, shared),
                "certified candidate reference categories do not conserve row totals")
        require((counts.get(phase+":ROBUST_CONTACT_MISSING_PAIR", 0),
                 counts.get(phase+":ROBUST_FIRST_COVER_NOT_SELECTED", 0),
                 counts.get(phase+":FORMAL_ALL_FIRST_COVER_NOT_SELECTED", 0),
                 counts.get(phase+":ALL_FIRST_COVER_NOT_SELECTED", 0))
                == (int(total == 0), int(primary_match == 0),
                    int(primary_match+second_match == 0), int(primary_match+second_match+shared_match == 0)),
                "candidate pair-level reference answers disagree with row-level matches")

def build_combined(root=ROOT, baseline=BASELINE, fresh=FRESH, research=RESEARCH, diagnostics=DIAGNOSTICS, progress=None):
    root = Path(root).resolve()
    started = time.perf_counter()
    bindings = {}
    require(sha(local(root, SCRIPT)) == sha(__file__), "publisher bytes differ from executed script")
    source_start = {SCRIPT: sha(__file__)}
    old, current, studied, compact = (read(root, name, bindings) for name in (baseline, fresh, research, diagnostics))
    require(old.get("complete") and old.get("full_history"), "historical full batch incomplete")
    require(current.get("complete") and current.get("full_history"), "fresh full batch incomplete")
    require(studied.get("complete"), "research batch incomplete")
    require(current.get("source_binding") == "runtime-loaded-repository-closure-start-and-end.v1", "fresh batch lacks runtime closure binding")
    check_sources(root, current, bindings)
    check_sources(root, studied, bindings)
    require({"tools/m5b_robust_replay.py", "tools/m5b_endpoint_replay.py", "tools/m5c_source_binding.py"}
            <= set(current["source_hashes"]), "fresh source closure lacks replay core")
    require(set(current["source_hashes"]) | {"tools/m5c_diagnostics.py", "src/eab/kernel2d/m5c_certificates.py"}
            <= set(studied["source_hashes"]), "research source closure lacks replay dependencies or R3 core")
    require(old["input_hashes"] == current["input_hashes"] == studied["input_hashes"], "replay/research frozen inputs differ")
    check_hash_map(root, current["input_hashes"], bindings)
    manifest = read(root, MANIFEST, bindings)
    require(manifest.get("complete") and len(manifest["cases"]) == FULL_CASES, "manifest case coverage incomplete")
    cases = set(manifest["cases"])
    expected_frames = defaultdict(set)
    for part in manifest["shards"]:
        name = str(Path(MANIFEST).parent.as_posix())+"/"+part["file"]
        require(current["input_hashes"].get(name) == part["sha256"], "endpoint shard is not bound by replay inputs")
        path = bind(root, name, bindings, part["sha256"])
        shard_count = 0
        for block in iter_rows(path):
            identity = block["case"], block["step"]
            require(block["case"] in manifest["cases"] and type(block["step"]) is int
                    and type(block["block"]) is int and block["block"] not in expected_frames[identity],
                    "duplicate or malformed frozen endpoint identity")
            expected_frames[identity].add(block["block"])
            shard_count += 1
        require(shard_count == part["rows"], "frozen endpoint shard row count differs")
    require((len(expected_frames), sum(map(len, expected_frames.values()))) == FULL_COVERAGE[:2],
            "frozen endpoint identity coverage incomplete")
    require(cases == set(old["cases"]) == set(current["cases"]), "old/fresh case coverage differs")
    require(tuple(current["counts"].get(k) for k in ("steps", "blocks", "pairs")) == FULL_COVERAGE, "fresh batch coverage totals incomplete")
    require(tuple(old["counts"].get(k) for k in ("steps", "blocks", "pairs")) == FULL_COVERAGE, "historical batch coverage totals incomplete")
    require((studied["counts"].get("traversed_steps"), studied["counts"].get("traversed_pairs"), studied["counts"].get("recomputed_pairs"))
            == (FULL_COVERAGE[0], FULL_COVERAGE[2], NEW_CONTACT_PAIRS), "research coverage totals incomplete")
    require(len(compact) == NEW_CONTACT_PAIRS, "research compact candidate count differs")
    compact_by_key = {key(row): row for row in compact}
    require(len(compact_by_key) == len(compact), "duplicate compact candidate key")
    exact_path = bind(root, studied["exact_diagnostics_path"], bindings, studied["exact_diagnostics_sha256"])
    exact_by_key = {}
    research_counts, research_refs, research_cases = Counter(), Counter(), defaultdict(Counter)
    for detail in iter_rows(exact_path):
        identity = key(detail)
        require(identity not in exact_by_key and identity in compact_by_key, "exact/compact candidate keys differ")
        small = compact_by_key[identity]
        require(all(detail[field] == small[field] for field in JOIN_FIELDS), "exact/compact candidate values differ")
        require(all(type(detail[field]) is bool for field in ("r2_pass", "r3_pass", "certified_union")), "certificate flags must be booleans")
        require(detail["certified_union"] == (detail["r2_pass"] or detail["r3_pass"]), "union certificate flag inconsistent")
        require(detail["r2_pass"] == any(t["passed"] for t in detail["r2_trials"]), "R2 trials disagree with flag")
        require(detail["r3_pass"] == any(t["passed"] for t in detail["r3_trials"]), "R3 trials disagree with flag")
        require(detail["r3_pass"] == bool(detail["certificate"]) and (not detail["r3_pass"] or len(detail["certificate"]) == 2 and all(detail["certificate"])), "R3 flags lack both production certificates")
        exact_by_key[identity] = {field: detail[field] for field in JOIN_FIELDS}
        for field in ("r2_pass", "r3_pass", "certified_union"):
            research_counts[field] += detail[field]
            research_cases[identity[0]][field] += detail[field]
        research_cases[identity[0]]["candidates"] += 1
        research_refs.update(count_map(detail["legacy_counts"]))
    require(set(exact_by_key) == set(compact_by_key), "missing exact candidate rows")
    require(all(research_counts[k] == studied["counts"][k] for k in research_counts), "research certificate totals disagree with rows")
    require(research_counts["r2_pass"] == R2_CERTIFIED, "research R2 certified baseline differs")
    require(research_refs == count_map(studied["references"]), "research reference totals disagree with rows")
    require(dict(research_cases) == {case: research_case_counts(v) for case, v in studied["by_case"].items()}, "research case totals disagree with rows")
    full_counts, full_refs, full_after_refs, initial_refs = Counter(), Counter(), Counter(), Counter()
    candidate_before_refs, candidate_after_refs = Counter(), Counter()
    by_case, joined, historical_files, all_keys = {}, [], {baseline: bindings[baseline]}, set()
    upgraded, initial_pairs = 0, 0
    for case in sorted(cases):
        old_case, new_case = old["cases"][case], current["cases"][case]
        require(old_case.get("complete") and new_case.get("complete"), "incomplete case: "+case)
        require(new_case["source_hashes"] == new_case["source_hashes_end"] == current["source_hashes"], "worker source closure differs: "+case)
        old_name, new_name = (summary["raw_directory"]+"/"+case+"/pairs.jsonl.gz" for summary in (old, current))
        old_file = bind(root, old_name, bindings, old_case["raw_sha256"])
        new_file = bind(root, new_name, bindings, new_case["raw_sha256"])
        historical_files[old_name] = bindings[old_name]
        counts, refs, after_refs, steps, additions = Counter(), Counter(), Counter(), defaultdict(set), 0
        case_candidates, case_union = 0, 0
        for before, after in zip_longest(iter_rows(old_file), iter_rows(new_file)):
            require(before is not None and after is not None, "old/fresh row counts differ: "+case)
            identity = key(after)
            require(identity == key(before) and identity[0] == case and identity not in all_keys, "old/fresh key/order or uniqueness mismatch")
            all_keys.add(identity)
            steps[identity[1]].add(identity[2])
            for model in ("p1", "p2"):
                require(all(json.dumps(before["result"][model][field], sort_keys=True, separators=(",", ":"))
                            == json.dumps(after["result"][model][field], sort_keys=True, separators=(",", ":"))
                            for field in ("status", "features", "time")), "exact P1/P2 observation mismatch: "+str(identity))
            require(before["result"]["classification"] == after["result"]["classification"], "historical/fresh R2 classification differs")
            require(candidate(before) == candidate(after), "historical/fresh candidate predicate differs")
            result = after["result"]
            counts.update(count_result(result))
            row_refs = count_map(after["legacy_counts"])
            refs.update(row_refs)
            if result["p1"]["status"] == "initial_overlap":
                initial_refs.update(row_refs)
                initial_pairs += 1
            if candidate(after):
                require(identity in exact_by_key, "fresh candidate missing from research")
                detail = exact_by_key[identity]
                require(detail["r2_pass"] == (result["classification"] == "ROBUST_SINGLE_FIRST_COVER"), "candidate R2 flag disagrees with fresh baseline")
                require(detail["features"] == result["p1"]["features"] == result["p2"]["features"], "candidate global features differ")
                case_candidates += 1
                case_union += detail["certified_union"]
                newly = detail["certified_union"] and not detail["r2_pass"]
                if newly:
                    require(result["classification"] == "MODEL_SENSITIVE_OR_UNPROVED"
                            and result.get("reason") == "NO_SUFFICIENT_CERTIFICATE", "R3 upgrade is not from unproved certificate class")
                    additions += 1
                candidate_before_refs.update(row_refs)
                replacement = count_map(detail["legacy_counts"])
                require(all(row_refs.get(phase+":"+name, 0) == replacement.get(phase+":"+name, 0)
                            for phase in PHASES for name in REFERENCE_TOTALS),
                        "candidate physical reference totals differ between R2 and research")
                check_candidate_references(row_refs, detail["r2_pass"])
                check_candidate_references(replacement, detail["certified_union"])
                candidate_after_refs.update(replacement)
                after_refs.update(replacement)
                joined.append(dict(case=case, step=identity[1], pair=list(identity[2]), features=detail["features"],
                                   r2_pass=detail["r2_pass"], r3_pass=detail["r3_pass"], certified_union=detail["certified_union"], newly_certified=bool(newly)))
            else:
                after_refs.update(row_refs)
        require(set(steps) == set(range(1, manifest["cases"][case]["steps"]+1)), "case step coverage incomplete: "+case)
        blocks = 0
        for step, pairs in steps.items():
            vertices = set(v for pair in pairs for v in pair)
            require(vertices == expected_frames.get((case, step)), "pair block IDs differ from frozen endpoint identities")
            require(pairs == set(combinations(sorted(vertices), 2)), "per-step all-pairs coverage incomplete")
            blocks += len(vertices)
        counts.update(steps=len(steps), blocks=blocks)
        require(blocks == manifest["cases"][case]["block_frames"], "case block-frame coverage differs")
        require(tuple(old_case["counts"][name] for name in ("steps", "blocks", "pairs"))
                == tuple(counts[name] for name in ("steps", "blocks", "pairs")), "historical case coverage metadata differs")
        require(counts == count_map(new_case["counts"]), "fresh case counts disagree with raw rows: "+case)
        require(refs == count_map(new_case["references"]), "fresh case references disagree with raw rows: "+case)
        combined_counts = counts.copy()
        combined_counts["ROBUST_SINGLE_FIRST_COVER"] += additions
        combined_counts["MODEL_SENSITIVE_OR_UNPROVED"] -= additions
        combined_counts["NO_SUFFICIENT_CERTIFICATE"] -= additions
        require(all(v >= 0 for v in combined_counts.values()), "classification replacement underflow")
        by_case[case] = dict(r2_counts=dict(counts), combined_counts=dict(combined_counts), candidates=case_candidates,
                            r2_single_cover=counts["ROBUST_SINGLE_FIRST_COVER"], certified_union=case_union,
                            newly_certified=additions, r2_references=dict(refs), combined_references=dict(after_refs))
        full_counts.update(counts)
        full_refs.update(refs)
        full_after_refs.update(after_refs)
        upgraded += additions
        if progress is not None:
            progress(dict(complete=False, joined_cases=len(by_case), compared_pairs=len(all_keys), joined_candidates=len(joined), interruption_invalidates=True))
    require(len(all_keys) == FULL_COVERAGE[2] and len(joined) == NEW_CONTACT_PAIRS, "full pair/candidate coverage incomplete")
    require({key(row) for row in joined} == set(exact_by_key), "fresh/research candidate sets are not equal")
    require(full_counts == count_map(current["counts"]), "fresh global counts disagree with raw rows")
    require(initial_pairs == full_counts["comparison_basis:CONSTRUCTED_INITIAL_OVERLAP"], "initial overlap reference cohort differs from state count")
    require(full_refs == count_map(current["references"]), "fresh global references disagree with raw rows")
    require(studied["inherited_stream_hashes"] == historical_files, "research inherited streams do not match the audited historical batch")
    check_hash_map(root, studied["inherited_stream_hashes"], bindings)
    combined = full_counts.copy()
    combined["ROBUST_SINGLE_FIRST_COVER"] += upgraded
    combined["MODEL_SENSITIVE_OR_UNPROVED"] -= upgraded
    combined["NO_SUFFICIENT_CERTIFICATE"] -= upgraded
    require(combined["ROBUST_SINGLE_FIRST_COVER"] == research_counts["certified_union"], "combined certificate totals inconsistent")
    arithmetic_refs = full_refs.copy()
    arithmetic_refs.subtract(candidate_before_refs)
    arithmetic_refs.update(candidate_after_refs)
    require(arithmetic_refs == full_after_refs and all(v >= 0 for v in full_after_refs.values()), "reference substitution inconsistent")
    require(all(sha(local(root, name)) == value for name, value in bindings.items()), "bound input/source changed during entire join")
    source_end = {SCRIPT: sha(__file__)}
    require(source_end == source_start, "publisher source changed during join")
    return dict(schema="eab.m5c-combined-full-history.v1", complete=True, full_history=True,
                scope="Fresh 1810-step/64010-pair R2 replay exactly matches all historical P1/P2 status/features/time; exhaustive 68-candidate R3 recertification is joined by exact keys. NOT a second all-pairs P2 root solve.",
                counts=dict(combined), r2_baseline_counts=dict(full_counts), newly_certified=upgraded,
                references=dict(full_after_refs), r2_baseline_references=dict(full_refs),
                candidate_references=dict(scope="68 new-contact pairs only", r2=dict(candidate_before_refs), certified_union=dict(candidate_after_refs)),
                initial_overlap_references=dict(scope="All initially penetrated pair records; readable primary/VV/common slots only, NOT shortest-exit matching certificates", pairs=full_counts["comparison_basis:CONSTRUCTED_INITIAL_OVERLAP"], references=dict(initial_refs), certified_exit_pairs=0),
                by_case=by_case, candidate_join=joined, exact_observation_pairs_compared=len(all_keys),
                source_hashes=source_start, source_hashes_end=source_end, input_hashes=bindings,
                source_dependency_contract="All recorded source bytes/current start-end maps checked; research includes every fresh replay source plus R3 core. Actual closure completeness is additionally guarded by the independent A7 import-origin pytest gates.",
                evidence_roles=dict(historical=baseline, fresh_r2=fresh, research=research, compact_diagnostics=diagnostics),
                seconds=time.perf_counter()-started,
                limits=["Only the certified union subset supports first-cover reference conclusions; unproved pairs are not extrapolated",
                        "FORMAL_ALL means primary plus formal VV secondary; ALL additionally includes valid VE common-edge candidate slots",
                        "Positive-radius global shortest-exit ordering remains uncertified for every initially penetrated pair",
                        "R3 is a sufficient research certificate, not independent G6 acceptance"])


def publish(root=ROOT, output=OUTPUT, **kwargs):
    root = Path(root).resolve()
    target = local(root, output)
    require(not target.exists(), "refuse to overwrite existing combined summary")
    result = build_combined(root, **kwargs)
    payload = json.dumps(result, ensure_ascii=False, indent=2)+"\n"
    require(len(payload.encode("utf-8")) < 1_000_000, "published summary exceeds 1 MB")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="") as stream:
        stream.write(payload)
    require(sha(target) == hashlib.sha256(payload.encode("utf-8")).hexdigest(), "published bytes differ")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=OUTPUT)
    parser.add_argument("--name", default="combined_r1", help="fresh progress directory; interrupted joins cannot resume")
    args = parser.parse_args()
    tmp = ROOT / EVIDENCE / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(tmp)
    require(bool(args.name) and args.name not in (".", "..")
            and not any(c in args.name for c in '/\\:\x00<>"|?*') and args.name == args.name.strip(),
            "fresh single portable directory name required")
    directory = (tmp / args.name).resolve()
    require(directory.parent == tmp.resolve(), "progress directory escapes temporary root")
    directory.mkdir(exist_ok=False)
    progress_path = directory / "progress.json"
    def progress(value):
        progress_path.write_text(json.dumps(value, indent=2)+"\n", encoding="utf-8")
    progress(dict(complete=False, interruption_invalidates=True))
    result = publish(output=args.output, progress=progress)
    progress(dict(complete=True, compared_pairs=result["exact_observation_pairs_compared"], newly_certified=result["newly_certified"]))
    print("M5C_COMBINED_COMPLETE", result["counts"])


if __name__ == "__main__":
    main()
