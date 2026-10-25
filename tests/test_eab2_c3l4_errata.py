"""Small explicit JSON comparisons guard the owner's unchanged errata semantics.

The expected categories are hand-specified, independent of solver/harness code;
these tests verify ledger classification and serialization, not geometric truth.
"""

import copy
import gzip
import json
from pathlib import Path
import subprocess
import sys

import pytest

import eab2_c3l4_errata as errata


def row(parameter, **changes):
    result = dict(case_id="asymmetric", query_index=2, parameter=parameter, family="synthetic",
                  differentiability="smooth", quality="unresolved", reason="original", method="basis",
                  directional_values=dict(D_plus=None, D_minus=None), branch_proof_references=["proof-2"])
    result.update(changes)
    return result


def documents():
    old, new = [], []
    pairs = [
        ("certified_value_changed", dict(quality="exact_jet", directional_values=dict(D_plus=1, D_minus=2)),
         dict(quality="exact_jet", directional_values=dict(D_plus=3, D_minus=2))),
        ("certified_to_unresolved", dict(quality="exact_jet", directional_values=dict(D_plus=0, D_minus=None)), {}),
        ("unresolved_to_certified", {}, dict(quality="exact_jet", directional_values=dict(D_plus=None, D_minus=0))),
        ("class_changed", {}, dict(differentiability="nonsmooth")),
        ("reason_and_quality_changed", {}, dict(reason="fixed", quality="approximate")),
        ("reason_changed", {}, dict(reason="fixed")),
        ("quality_changed", {}, dict(quality="approximate")),
        ("method_changed", {}, dict(method="sandwich")),
        ("directional_values_changed", {}, dict(directional_values=dict(D_plus=3, D_minus=None))),
        ("unchanged", {}, dict(branch_proof_references=["metadata-only-change"], family="other")),
    ]
    for category, before, after in pairs:
        old_row, new_row = row(category), row(category)
        old_row.update(before)
        new_row.update(after)
        old.append(old_row)
        new.append(new_row)
    old.append(row("missing"))
    new.append(row("new-only"))
    return dict(queries=old), dict(queries=new, last_line="SYNTHETIC_L4_PASS")


def test_all_categories_use_the_full_case_query_parameter_key():
    old, new = documents()
    originals = copy.deepcopy((old, new))
    ledger = errata.build_ledger(old, new, old_run="accepted.json.gz", new_run="fixed.json")
    expected = {kind: 1 for kind in (
        "certified_value_changed", "certified_to_unresolved", "unresolved_to_certified",
        "class_changed", "reason_and_quality_changed", "reason_changed", "quality_changed",
        "method_changed", "directional_values_changed", "unchanged", "missing_in_new", "new_only_queries")}
    assert ledger["counts"] == expected
    assert len(ledger["entries"]) == 11
    assert ledger["new_last_line"] == "SYNTHETIC_L4_PASS"
    assert (old, new) == originals
    entries = {entry["parameter"]: entry for entry in ledger["entries"]}
    for category in expected.keys() - {"unchanged", "missing_in_new", "new_only_queries"}:
        assert entries[category]["kind"] == category
        assert entries[category]["proof_references"] == ["proof-2"]
        assert tuple(entries[category]["old"]) == errata.FIELDS
        assert tuple(entries[category]["new"]) == errata.FIELDS
    assert "unchanged" not in entries
    assert entries["missing"] == dict(case_id="asymmetric", query_index=2, parameter="missing", kind="missing_in_new")
    assert entries["new-only"]["kind"] == "new_only_queries"
    assert entries["new-only"]["old"] is None
    assert entries["new-only"]["new"]["method"] == "basis"


@pytest.mark.parametrize("before,after,expected", [
    (dict(quality="exact_jet", directional_values=dict(D_plus=1.0)),
     dict(quality="exact_jet", directional_values=dict(D_plus=1.0000000000000002),
          differentiability="nonsmooth", reason="fixed", method="sandwich"), "certified_value_changed"),
    (dict(quality="exact_jet", directional_values=dict(D_plus=0)),
     dict(differentiability="nonsmooth", reason="fixed", method="sandwich"), "certified_to_unresolved"),
    ({}, dict(quality="exact_jet", directional_values=dict(D_minus=0),
              differentiability="nonsmooth", reason="fixed", method="sandwich"), "unresolved_to_certified"),
    ({}, dict(differentiability="nonsmooth", reason="fixed", quality="approximate", method="sandwich"), "class_changed"),
    ({}, dict(reason="fixed", quality="approximate", method="sandwich"), "reason_and_quality_changed"),
    ({}, dict(reason="fixed", method="sandwich", directional_values=dict(D_plus=1)), "reason_changed"),
    ({}, dict(quality="approximate", method="sandwich", directional_values=dict(D_plus=1)), "quality_changed"),
    ({}, dict(method="sandwich", directional_values=dict(D_plus=1)), "method_changed"),
    (dict(quality="exact_jet"), dict(quality="approximate"), "quality_changed"),
    (dict(quality="approximate", directional_values=dict(D_plus=1)),
     dict(quality="approximate", directional_values=dict(D_plus=2)), "directional_values_changed"),
])
def test_classification_precedence_and_exact_certification_definition(before, after, expected):
    assert errata.classify(row("p", **before), row("p", **after)) == expected


def test_fields_and_python_equality_are_preserved_without_numeric_coercion():
    assert errata.FIELDS == ("differentiability", "quality", "reason", "method", "directional_values")
    old = row("p", quality="exact_jet", directional_values=dict(D_plus=1))
    same = row("p", quality="exact_jet", directional_values=dict(D_plus=1.0))
    ledger = errata.build_ledger(dict(queries=[old]), dict(queries=[same]))
    assert ledger["counts"] == dict(unchanged=1, new_only_queries=0)
    assert ledger["entries"] == []
    different = row("p", quality="exact_jet", directional_values=dict(D_plus="1"))
    changed = errata.build_ledger(dict(queries=[old]), dict(queries=[different]))
    assert changed["counts"] == dict(certified_value_changed=1, new_only_queries=0)


def test_distinct_cases_queries_and_parameters_remain_distinct_and_sorted():
    records = [row("b"), row("a"), row("a", query_index=1), row("a", case_id="another")]
    ledger = errata.build_ledger(dict(queries=records), dict(queries=[]))
    keys = [(entry["case_id"], entry["query_index"], entry["parameter"]) for entry in ledger["entries"]]
    assert keys == sorted([(item["case_id"], item["query_index"], item["parameter"]) for item in records])
    assert ledger["counts"] == dict(missing_in_new=4, new_only_queries=0)


def test_generate_and_original_four_argument_cli_round_trip(tmp_path):
    old, new = documents()
    old_path, new_path = tmp_path / "old.json.gz", tmp_path / "new.json"
    old_path.write_bytes(gzip.compress(json.dumps(old).encode("utf-8"), mtime=0))
    new_path.write_text(json.dumps(new), encoding="utf-8", newline="\n")
    api_json, api_md = tmp_path / "api.json", tmp_path / "api.md"
    result = errata.generate(old_path, new_path, api_json, api_md)
    assert json.loads(api_json.read_text(encoding="utf-8")) == result
    assert errata.load(old_path)[1] == old
    cli_json, cli_md = tmp_path / "cli.json", tmp_path / "cli.md"
    completed = subprocess.run(
        [sys.executable, "-X", "utf8", str(Path(errata.__file__)), str(old_path), str(new_path), str(cli_json), str(cli_md)],
        text=True, encoding="utf-8", capture_output=True, check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.splitlines()[-1] == "ERRATA_LEDGER " + json.dumps(result["counts"], sort_keys=True)
    assert api_json.read_bytes() == cli_json.read_bytes()
    assert api_md.read_bytes() == cli_md.read_bytes()
    markdown = api_md.read_text(encoding="utf-8")
    for entry in result["entries"]:
        assert entry["kind"] in markdown
    assert "method=sandwich" in markdown
    for artifact in (api_json, api_md, cli_json, cli_md):
        raw = artifact.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf")
        assert b"\r" not in raw
        assert raw.endswith(b"\n")
