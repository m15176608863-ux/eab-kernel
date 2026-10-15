"""Independent literal ledger tests for the full-history evidence join.

Oracle imports only stdlib containers/JSON/hash/gzip; no replay, solver,
certificate, geometry, or count_result primitive generates the expected ledger.
Tiny fixtures replace only corpus-size constants; production values are pinned
by a separate literal gate. Semantic corruptions repair their enclosing file
hashes so the intended join/coverage assertion, not a stale hash, must reject.
"""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import m5c_publish_combined as combined


def test_combined_publisher_requires_the_actual_full_history_size():
    assert combined.FULL_COVERAGE == (1810, 15220, 64010)
    assert combined.FULL_CASES == 15 and combined.NEW_CONTACT_PAIRS == 68 and combined.R2_CERTIFIED == 2


@pytest.mark.parametrize("defect,reason", (
    (None, None),
    ("fresh_incomplete", "fresh full batch incomplete"),
    ("research_incomplete", "research batch incomplete"),
    ("missing_case", "case coverage differs"),
    ("truncated_gzip", "hash mismatch"),
    ("old_time", "exact P1/P2 observation mismatch"),
    ("old_features", "exact P1/P2 observation mismatch"),
    ("old_missing_row", "row counts differ"),
    ("duplicate_fresh_pair", "key/order or uniqueness mismatch"),
    ("research_missing_candidate", "compact candidate count differs"),
    ("candidate_feature", "candidate global features differ"),
    ("candidate_duplicate", "duplicate compact candidate key"),
    ("research_wrong_sources", "hash mismatch"),
    ("source_end_mismatch", "source start/end differ"),
    ("fresh_reference_total", "fresh case references disagree"),
    ("missing_exact_candidate", "missing exact candidate rows"),
    ("inherited_stream", "inherited streams do not match"),
    ("runtime_input_change", "bound input/source changed during entire join"),
    ("reference_mass", "candidate physical reference totals differ"),
    ("certified_unproved_residue", "certified candidate retains unproved categories"),
    ("unproved_certified_residue", "unproved candidate retains certified categories"),
    ("research_core_missing", "research source closure lacks replay dependencies or R3 core"),
    ("false_positive_counter", "research case totals disagree with rows"),
    ("invented_block", "pair block IDs differ from frozen endpoint identities"),
    ("overwrite", "refuse to overwrite"),
))
def test_combined_join_rejects_incomplete_or_inconsistent_evidence_without_publishing(tmp_path, monkeypatch, defect, reason):
    monkeypatch.setattr(combined, "FULL_COVERAGE", (2, 6, 6))
    monkeypatch.setattr(combined, "FULL_CASES", 1)
    monkeypatch.setattr(combined, "NEW_CONTACT_PAIRS", 2)
    monkeypatch.setattr(combined, "R2_CERTIFIED", 1)

    def write(name, value, compressed=False):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if compressed:
            payload = "".join(json.dumps(row)+"\n" for row in value).encode()
            path.write_bytes(gzip.compress(payload, mtime=0))
        else:
            path.write_text(json.dumps(value), encoding="utf-8")
        return hashlib.sha256(path.read_bytes()).hexdigest()

    source = tmp_path / combined.SCRIPT
    source.parent.mkdir(parents=True)
    source.write_bytes(Path(combined.__file__).read_bytes())
    kernel = "src/eab/frozen_join_fixture.py"
    kernel_path = tmp_path / kernel
    kernel_path.parent.mkdir(parents=True)
    kernel_path.write_bytes(b"fixture = 1\n")
    sources = {kernel: hashlib.sha256(kernel_path.read_bytes()).hexdigest()}
    for name in ("tools/m5b_robust_replay.py", "tools/m5b_endpoint_replay.py", "tools/m5c_source_binding.py",
                 "tools/m5c_diagnostics.py", "src/eab/kernel2d/m5c_certificates.py"):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"source_fixture = 1\n")
        sources[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    endpoint_name = str(Path(combined.MANIFEST).parent.as_posix())+"/unit.jsonl.gz"
    endpoint_rows = [dict(case="unit", step=step, block=block) for step in (1, 2) for block in (1, 2, 3)]
    endpoint_hash = write(endpoint_name, endpoint_rows, True)
    manifest = {"complete": True, "cases": {"unit": {"steps": 2, "block_frames": 6}},
                "shards": [dict(file="unit.jsonl.gz", rows=6, sha256=endpoint_hash)]}
    inputs = {combined.MANIFEST: write(combined.MANIFEST, manifest), endpoint_name: endpoint_hash}
    rows = []
    phases = ("raw_df05", "post_df06")
    pairs = ((1, 2), (1, 3), (2, 3), (1, 2), (1, 3), (2, 3))
    for index, pair in enumerate(pairs):
        status = "contact" if index < 2 else "initial_overlap" if index == 2 else "no_contact"
        features = [["VE", 1, 2, 3]] if index == 0 else [["VE", 3, 1, 2]] if index == 1 else []
        observation = dict(status=status, features=features, time={"exact": "1/2"} if index < 2 else None)
        classification = "ROBUST_SINGLE_FIRST_COVER" if index == 0 else "MODEL_SENSITIVE_OR_UNPROVED" if index < 3 else "ROBUST_NO_CONTACT"
        result = dict(classification=classification, same=True, p1=observation, p2=copy.deepcopy(observation),
                      comparison_basis="EXPLICIT_TRAJECTORY" if index < 2 else "CONSTRUCTED_INITIAL_OVERLAP" if index == 2 else "CERTIFICATE_DIRECT",
                      oracle_checked=index < 3, production_initial_crosschecked=index < 2)
        if index < 3:
            result["initial_state"] = -1 if index < 2 else 1
        if index in (1, 2):
            result["reason"] = "NO_SUFFICIENT_CERTIFICATE" if index == 1 else "INITIAL_EXIT_ORDER_UNCERTIFIED"
        counts = {}
        for phase in phases:
            counts[phase+":PRIMARY_REFERENCE_TOTAL"] = 1
            counts[phase+":SECONDARY_REFERENCE_TOTAL"] = 0
            counts[phase+":SHARED_EDGE_SLOT_TOTAL"] = int(index == 1)
            counts[phase+(":FIRST_COVER_MATCH" if index == 0 else ":UNPROVED_REFERENCE" if index < 3 else ":ROBUST_NO_CONTACT_REFERENCE")] = 1
            if index == 1:
                counts[phase+":UNPROVED_SHARED_EDGE_SLOT"] = 1
        rows.append(dict(case="unit", step=1 if index < 3 else 2, pair=list(pair), result=result, legacy_counts=counts))
    refs = {}
    for row in rows:
        for name, value in row["legacy_counts"].items():
            refs[name] = refs.get(name, 0)+value
    counts = {"pairs": 6, "steps": 2, "blocks": 6, "ROBUST_SINGLE_FIRST_COVER": 1,
              "MODEL_SENSITIVE_OR_UNPROVED": 2, "ROBUST_NO_CONTACT": 3,
              "comparison_basis:EXPLICIT_TRAJECTORY": 2, "comparison_basis:CONSTRUCTED_INITIAL_OVERLAP": 1,
              "comparison_basis:CERTIFICATE_DIRECT": 3, "p1_p2_explicit_same": 2, "explicit_new_contact_pairs": 2,
              "independent_initial_state_evaluations": 3, "production_initial_state_crosschecks": 2,
              "INITIAL_EXIT_ORDER_UNCERTIFIED": 1, "NO_SUFFICIENT_CERTIFICATE": 1}
    old_raw, new_raw = "reports/old/unit/pairs.jsonl.gz", "reports/new/unit/pairs.jsonl.gz"
    case = dict(complete=True, counts=counts, references=refs, source_hashes=sources, source_hashes_end=sources)
    old_case = dict(case, raw_sha256=write(old_raw, rows, True))
    new_case = dict(case, raw_sha256=write(new_raw, rows, True))
    old = dict(complete=True, full_history=True, counts=counts, references=refs, cases={"unit": old_case},
               input_hashes=inputs, raw_directory="reports/old")
    fresh = dict(complete=True, full_history=True, counts=counts, references=refs, cases={"unit": new_case},
                 input_hashes=inputs, raw_directory="reports/new", source_hashes=sources, source_hashes_end=sources,
                 source_binding="runtime-loaded-repository-closure-start-and-end.v1")
    write(combined.BASELINE, old)
    write(combined.FRESH, fresh)
    details = []
    for index in (0, 1):
        references = copy.deepcopy(rows[index]["legacy_counts"])
        if index == 1:
            for phase in phases:
                del references[phase+":UNPROVED_REFERENCE"]
                del references[phase+":UNPROVED_SHARED_EDGE_SLOT"]
                references[phase+":OTHER_REFERENCE"] = 1
                references[phase+":SHARED_EDGE_FIRST_COVER_MATCH"] = 1
                references[phase+":ROBUST_FIRST_COVER_NOT_SELECTED"] = 1
                references[phase+":FORMAL_ALL_FIRST_COVER_NOT_SELECTED"] = 1
        details.append(dict(case="unit", step=1, pair=rows[index]["pair"], label=["VE", index, 0],
                            features=rows[index]["result"]["p1"]["features"], r2_pass=index == 0,
                            r3_pass=index == 1, certified_union=True, legacy_counts=references,
                            r2_trials=[dict(passed=index == 0)], r3_trials=[dict(passed=index == 1)],
                            certificate=[{"proof": "P1"}, {"proof": "P2"}] if index == 1 else None))
    compact = [{field: row[field] for field in combined.JOIN_FIELDS} for row in details]
    research_refs = {}
    for row in details:
        for name, value in row["legacy_counts"].items():
            research_refs[name] = research_refs.get(name, 0)+value
    exact_name = "reports/research/exact_diagnostics.jsonl.gz"
    research = dict(complete=True, counts=dict(traversed_steps=2, traversed_pairs=6, recomputed_pairs=2,
                                              r2_pass=1, r3_pass=1, certified_union=2), references=research_refs,
                    by_case={"unit": dict(candidates=2, r2_pass=1, r3_pass=1, certified_union=2)},
                    source_hashes=sources, source_hashes_end=sources, input_hashes=inputs,
                    exact_diagnostics_path=exact_name, exact_diagnostics_sha256=write(exact_name, details, True),
                    inherited_stream_hashes={combined.BASELINE: hashlib.sha256((tmp_path/combined.BASELINE).read_bytes()).hexdigest(),
                                             old_raw: old_case["raw_sha256"]})
    if defect == "fresh_incomplete":
        fresh["complete"] = False
    elif defect == "research_incomplete":
        research["complete"] = False
    elif defect == "missing_case":
        fresh["cases"] = {}
    elif defect == "truncated_gzip":
        (tmp_path/new_raw).write_bytes(b"bad truncated gzip")
    elif defect in ("old_time", "old_features", "old_missing_row"):
        changed = copy.deepcopy(rows)
        if defect == "old_time":
            changed[0]["result"]["p2"]["time"] = {"exact": "2/3"}
        elif defect == "old_features":
            changed[0]["result"]["p1"]["features"] = [["VE", 9, 8, 7]]
        else:
            changed.pop()
        old["cases"]["unit"]["raw_sha256"] = write(old_raw, changed, True)
        write(combined.BASELINE, old)
    elif defect == "duplicate_fresh_pair":
        changed = copy.deepcopy(rows)
        changed[1] = copy.deepcopy(changed[0])
        fresh["cases"]["unit"]["raw_sha256"] = write(new_raw, changed, True)
    elif defect == "research_missing_candidate":
        compact.pop()
    elif defect == "candidate_feature":
        details[1]["features"] = [["VE", 9, 8, 7]]
        compact[1]["features"] = [["VE", 9, 8, 7]]
        research["exact_diagnostics_sha256"] = write(exact_name, details, True)
    elif defect == "candidate_duplicate":
        compact[1] = copy.deepcopy(compact[0])
    elif defect == "research_wrong_sources":
        kernel_path.write_bytes(b"fixture = 2\n")
    elif defect == "source_end_mismatch":
        research["source_hashes_end"] = {}
    elif defect == "fresh_reference_total":
        fresh["cases"]["unit"]["references"] = dict(refs)
        fresh["cases"]["unit"]["references"]["raw_df05:FIRST_COVER_MATCH"] += 1
    elif defect == "missing_exact_candidate":
        research["exact_diagnostics_sha256"] = write(exact_name, details[:1], True)
    elif defect == "inherited_stream":
        research["inherited_stream_hashes"] = {combined.BASELINE: "0"*64}
    if defect == "certified_unproved_residue":
        details[1]["legacy_counts"]["raw_df05:UNPROVED_REFERENCE"] = 1
        research["references"]["raw_df05:UNPROVED_REFERENCE"] = 1
        research["exact_diagnostics_sha256"] = write(exact_name, details, True)
    elif defect == "unproved_certified_residue":
        changed = copy.deepcopy(rows)
        changed[1]["legacy_counts"]["raw_df05:FIRST_COVER_MATCH"] = 1
        fresh["cases"]["unit"]["raw_sha256"] = write(new_raw, changed, True)
    elif defect == "research_core_missing":
        research["source_hashes"] = {kernel: sources[kernel]}
        research["source_hashes_end"] = {kernel: sources[kernel]}
    elif defect == "false_positive_counter":
        research["by_case"]["unit"]["r2_pass"] = False
    elif defect == "reference_mass":
        for suffix in (":PRIMARY_REFERENCE_TOTAL", ":OTHER_REFERENCE"):
            details[1]["legacy_counts"]["raw_df05"+suffix] += 1
            research["references"]["raw_df05"+suffix] += 1
        research["exact_diagnostics_sha256"] = write(exact_name, details, True)
    elif defect == "invented_block":
        changed = copy.deepcopy(rows)
        for row in changed:
            row["pair"] = [4 if block == 3 else block for block in row["pair"]]
        for exact, small in zip(details, compact):
            exact["pair"] = [4 if block == 3 else block for block in exact["pair"]]
            small["pair"] = exact["pair"]
        old["cases"]["unit"]["raw_sha256"] = write(old_raw, changed, True)
        fresh["cases"]["unit"]["raw_sha256"] = write(new_raw, changed, True)
        write(combined.BASELINE, old)
        research["exact_diagnostics_sha256"] = write(exact_name, details, True)
    write(combined.FRESH, fresh)
    write(combined.RESEARCH, research)
    write(combined.DIAGNOSTICS, compact)
    callback = None
    if defect == "runtime_input_change":
        def callback(progress):
            kernel_path.write_bytes(b"fixture = 3\n")
    if defect == "overwrite":
        output = tmp_path/combined.OUTPUT
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"preserve accepted bytes")
    if defect is not None:
        with pytest.raises(ValueError, match=reason):
            combined.publish(tmp_path, progress=callback)
        if defect == "overwrite":
            assert (tmp_path/combined.OUTPUT).read_bytes() == b"preserve accepted bytes"
        else:
            assert not (tmp_path/combined.OUTPUT).exists(), "invalid evidence cannot leave a published complete artifact"
    else:
        result = combined.publish(tmp_path)
        assert result["complete"] and result["exact_observation_pairs_compared"] == 6
        assert result["newly_certified"] == 1
        assert result["counts"]["ROBUST_SINGLE_FIRST_COVER"] == 2
        assert result["counts"]["MODEL_SENSITIVE_OR_UNPROVED"] == 1
        assert result["counts"]["ROBUST_NO_CONTACT"] == 3
        assert result["initial_overlap_references"]["pairs"] == 1
        assert result["initial_overlap_references"]["certified_exit_pairs"] == 0
        for phase in phases:
            assert result["references"][phase+":PRIMARY_REFERENCE_TOTAL"] == 6
            assert result["references"][phase+":UNPROVED_REFERENCE"] == 1
            assert result["references"][phase+":SHARED_EDGE_FIRST_COVER_MATCH"] == 1
            assert result["initial_overlap_references"]["references"][phase+":PRIMARY_REFERENCE_TOTAL"] == 1
        assert result["source_hashes"] == result["source_hashes_end"]
        assert "NOT a second all-pairs P2 root solve" in result["scope"]
        assert json.loads((tmp_path/combined.OUTPUT).read_text()) == result



def test_frozen_combined_summary_has_complete_cohorts_current_sources_and_bound_upstream_summaries():
    """Distributed artifact gate, not a hidden all-history replay.

    Large raw gzip equality is checked by the rerunnable publisher and recorded
    by exact hashes. Those ignored temporary streams are not a pytest/fresh-
    checkout dependency. This gate checks the published ledger, every bound
    source, and its four distributed upstream summary/diagnostic artifacts.
    """
    data = json.loads((ROOT / combined.OUTPUT).read_text(encoding="utf-8"))
    assert data["complete"] and data["full_history"]
    assert tuple(data["counts"][name] for name in ("steps", "blocks", "pairs")) == (1810, 15220, 64010)
    assert data["exact_observation_pairs_compared"] == 64010
    rows = data["candidate_join"]
    assert len(rows) == len({(r["case"], r["step"], tuple(r["pair"])) for r in rows}) == 68
    assert sum(r["r2_pass"] for r in rows) == data["r2_baseline_counts"]["ROBUST_SINGLE_FIRST_COVER"] == 2
    assert sum(r["certified_union"] for r in rows) == data["counts"]["ROBUST_SINGLE_FIRST_COVER"]
    assert sum(r["newly_certified"] for r in rows) == data["newly_certified"]
    assert data["counts"]["ROBUST_SINGLE_FIRST_COVER"] == 2+data["newly_certified"]
    assert data["counts"]["MODEL_SENSITIVE_OR_UNPROVED"]+data["newly_certified"] == data["r2_baseline_counts"]["MODEL_SENSITIVE_OR_UNPROVED"]
    for phase in ("raw_df05", "post_df06"):
        for suffix in ("PRIMARY_REFERENCE_TOTAL", "SECONDARY_REFERENCE_TOTAL", "SHARED_EDGE_SLOT_TOTAL"):
            key = phase+":"+suffix
            assert data["references"][key] == data["r2_baseline_references"][key]
    assert data["initial_overlap_references"]["pairs"] == 16676
    assert data["initial_overlap_references"]["certified_exit_pairs"] == 0
    assert data["source_hashes"] == data["source_hashes_end"]
    for name, digest in data["source_hashes"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    # Every bound production/research Python source is shipped and checked,
    # while large ignored raw streams remain explicit evidence-script inputs.
    source_inputs = {name: digest for name, digest in data["input_hashes"].items()
                     if name.startswith(("src/", "tools/"))}
    assert {"tools/m5b_robust_replay.py", "tools/m5c_diagnostics.py", "src/eab/kernel2d/m5c_certificates.py"} <= set(source_inputs)
    for name, digest in source_inputs.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    for name in data["evidence_roles"].values():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == data["input_hashes"][name], name
    assert "NOT a second all-pairs P2 root solve" in data["scope"]



def test_research_counter_false_serialization_has_a_narrow_zero_count_normalization():
    # Literal real schema of bbF038/bbS038, not a production Counter helper.
    row = json.loads('{"candidates": 1, "r2_pass": false, "r3_pass": false, "certified_union": false}')
    normalized = combined.research_case_counts(row)
    assert dict(normalized) == {"candidates": 1, "r2_pass": 0, "r3_pass": 0, "certified_union": 0}
    assert all(type(number) is int for number in normalized.values())
    assert row["r2_pass"] is row["r3_pass"] is row["certified_union"] is False, "do not rewrite frozen evidence"


@pytest.mark.parametrize("field,value", (
    ("candidates", False), ("candidates", True), ("candidates", 1.0),
    ("r2_pass", True), ("r3_pass", True), ("certified_union", True),
    ("r2_pass", 0.0), ("r3_pass", -1), ("certified_union", "0"),
))
def test_research_count_compatibility_does_not_widen_other_count_types(field, value):
    row = {"candidates": 1, "r2_pass": 0, "r3_pass": 0, "certified_union": 0}
    row[field] = value
    with pytest.raises(ValueError, match="invalid nonnegative count map"):
        combined.research_case_counts(row)

