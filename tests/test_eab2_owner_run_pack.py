"""Synthetic disk evidence, independent of any solver or running owner process."""
import hashlib
import gzip
import json
from pathlib import Path

import pytest

import eab2_owner_run_pack as pack_module
from eab2_owner_run_pack import LAYERS, pack


def write_json(path, value):
    with open(path, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream)


def test_partial_pack_is_read_only_and_never_infers_exit(tmp_path):
    source, output = tmp_path / "source", tmp_path / "output"
    source.mkdir()
    (source / "summary.txt").write_bytes("BUILD_EXIT 0\n".encode("utf-8-sig"))
    (source / "build.log").write_bytes("build finished\n".encode("utf-16"))
    (source / "c0diff.log").write_text("looks good\n", encoding="utf-8")
    write_json(source / "c0diff.json", dict(last_line="C0 OK", sample_count=8, mismatches=[], dll_sha256="a" * 64))
    write_json(source / "l4diff.progress.json", dict(queries=10))
    write_json(source / "meta_progress.json", dict(complete=True, exit_code=0))
    before = {p.name: p.read_bytes() for p in source.iterdir()}
    result = pack(source, output)
    assert result["layers"]["build"]["status"] == "complete"
    assert result["layers"]["build"]["log_last_line"] == "build finished"
    assert result["layers"]["c0diff"]["exit_code"] is None
    assert result["layers"]["c0diff"]["status"] == "pending"
    assert result["errata_ledger"]["status"] == "pending"
    assert "meta_progress" not in result["layers"]
    assert result["layers"]["meta"]["status"] == "pending"
    assert result["files"]["meta_progress.json"]["role"] == "progress_only_not_final"
    assert result["files"]["c0diff.json"]["extracted"]["sample_count"] == 8
    assert result["dll_sha256"]["c0diff.json"] == "a" * 64
    assert result["files"]["build.log"]["sha256"] == hashlib.sha256(before["build.log"]).hexdigest()
    assert {p.name: p.read_bytes() for p in source.iterdir()} == before
    assert result["package_bytes"] == sum(p.stat().st_size for p in output.iterdir()) <= 300_000
    assert all(not p.read_bytes().startswith(b"\xef\xbb\xbf") for p in output.iterdir())


def test_finished_l4_invokes_ledger_and_preserves_diagnostics(tmp_path):
    source, output = tmp_path / "source", tmp_path / "output"
    source.mkdir()
    (source / "summary.txt").write_text("\n".join(f"{name.upper()}_EXIT 0" for name in LAYERS), encoding="utf-8")
    (source / "build.log").write_text("build ok\n", encoding="utf-8")
    for name in LAYERS:
        if name != "build":
            write_json(source / (name + ".json"), dict(complete=True))
    old = tmp_path / "old.json"
    write_json(old, dict(queries=[]))
    row = dict(case_id="a", query_index=0, parameter="x", family="branch", quality="exact_jet",
               differentiability="smooth", reason="ok", method="branch_certificate",
               directional_values=dict(D_plus="1", D_minus="1"))
    write_json(source / "l4diff.json", dict(complete=True, last_line="L4 OK", queries=[row], mismatches=[],
               errata=[dict(kind="test")], branch_certificate_statistics={"branch": {"cpp/certified": 2}}))
    result = pack(source, output, old)
    assert result["status"] == "complete"
    assert result["errata_ledger"]["counts"]["new_only_queries"] == 1
    assert b"new_only_queries" in gzip.decompress((output / "errata_ledger.md.gz").read_bytes())
    assert json.loads(gzip.decompress((output / "errata_ledger.json.gz").read_bytes()))["counts"]["new_only_queries"] == 1
    fields = result["files"]["l4diff.json"]["extracted"]
    assert fields["errata"] == [dict(kind="test")]
    assert fields["branch_certificate_statistics"]["branch"]["cpp/certified"] == 2


def test_failure_truncation_and_large_diagnostics_are_not_hidden(tmp_path):
    source, output = tmp_path / "source", tmp_path / "output"
    source.mkdir()
    (source / "summary.txt").write_text("C0DIFF_EXIT 3\nL1DIFF_EXIT 0\n", encoding="utf-8")
    write_json(source / "c0diff.json", dict(mismatches=[dict(kind="wrong", detail="x" * 500)] * 50))
    (source / "l1diff.json").write_text('{"incomplete":', encoding="utf-8")
    result = pack(source, output)
    assert result["layers"]["c0diff"]["status"] == "failed"
    assert result["layers"]["l1diff"]["status"] == "pending"
    assert result["files"]["c0diff.json"]["extracted"]["mismatches"]["count"] == 50
    assert result["status"] == "failed"


def test_pack_refuses_output_under_read_only_source(tmp_path):
    with pytest.raises(ValueError, match="disjoint"):
        pack(tmp_path, tmp_path / "output")


def test_pack_enforces_whole_package_budget(tmp_path):
    source, output = tmp_path / "source", tmp_path / "output"
    source.mkdir()
    output.mkdir()
    (output / "other_evidence.txt").write_bytes(b"x" * 300_000)
    with pytest.raises(ValueError, match="exceeds"):
        pack(source, output)


def test_exit_zero_without_artifacts_is_pending(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "summary.txt").write_text("\n".join(f"{name.upper()}_EXIT 0" for name in LAYERS), encoding="utf-8")
    result = pack(source, tmp_path / "output")
    assert result["status"] == "partial"
    assert result["layers"]["l4diff"]["status"] == "pending"
    assert result["errata_ledger"]["status"] == "pending"


def test_pending_snapshot_refuses_stale_ledger(tmp_path):
    source, output = tmp_path / "source", tmp_path / "output"
    source.mkdir()
    output.mkdir()
    (output / "errata_ledger.json.gz").write_bytes(b"prior evidence")
    with pytest.raises(ValueError, match="older errata ledger"):
        pack(source, output)
    assert (output / "errata_ledger.json.gz").read_bytes() == b"prior evidence"


def test_large_ledger_is_lossless_and_bounded(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "summary.txt").write_text("L4DIFF_EXIT 0\n", encoding="utf-8")
    old = tmp_path / "old.json"
    write_json(old, dict(queries=[]))
    rows = [dict(case_id=f"asymmetric_{i}", query_index=i, parameter="random_0", family="asymmetric",
                 quality="exact_jet", differentiability="one_sided", reason="branch_switch", method="branch_certificate",
                 directional_values=dict(D_plus="7061/65536", D_minus="-21749/65536"),
                 branch_proof_references={"python": "proof.jsonl#" + str(i), "cpp": "proof.jsonl#" + str(i + 1)})
            for i in range(800)]
    write_json(source / "l4diff.json", dict(complete=True, queries=rows, last_line="L4 OK"))
    output = tmp_path / "output"
    result = pack(source, output, old)
    ledger = json.loads(gzip.decompress((output / "errata_ledger.json.gz").read_bytes()))
    assert len(ledger["entries"]) == 800
    assert result["package_bytes"] <= 300_000
    assert ledger["entries"][0]["new"]["directional_values"] == rows[0]["directional_values"]


def test_failed_incomplete_l4_keeps_failure_manifest(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "summary.txt").write_text("L4DIFF_EXIT 1\n", encoding="utf-8")
    write_json(source / "l4diff.json", dict(complete=False, last_line="L4 FAILED"))
    result = pack(source, tmp_path / "output")
    assert result["status"] == "failed"
    assert result["layers"]["l4diff"]["exit_code"] == 1
    assert result["errata_ledger"]["status"] == "pending"


def test_ledger_uses_hashed_snapshot_not_second_read(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    (source / "summary.txt").write_text("L4DIFF_EXIT 0\n", encoding="utf-8")
    old = tmp_path / "old.json"
    write_json(old, dict(queries=[]))
    path = source / "l4diff.json"
    write_json(path, dict(complete=True, queries=[], last_line="BEFORE"))
    original = pack_module.read_snapshot

    def changing_file(target):
        result = original(target)
        if target == path:
            write_json(path, dict(complete=True, queries=[], last_line="AFTER"))
        return result

    monkeypatch.setattr(pack_module, "read_snapshot", changing_file)
    output = tmp_path / "output"
    result = pack(source, output, old)
    ledger = json.loads(gzip.decompress((output / "errata_ledger.json.gz").read_bytes()))
    assert result["layers"]["l4diff"]["json_last_line"] == ledger["new_last_line"] == "BEFORE"


def sharded_values():
    """Independent tiny inventory: three queries per identity are still one case."""
    expected, values = {}, {}
    for index, name in enumerate(pack_module.L4_SHARDS):
        group = "asymmetric" if index >= 4 else name[3:]
        identity = group + "/" + str(index)
        expected[identity] = group
        rows = [dict(case_id=identity, query_index=i, parameter="p" + str(i), family=group,
                     differentiability="smooth", quality="exact_jet", reason=None,
                     method="branch_certificate", directional_values=dict(D_plus="1/1", D_minus="1/1"))
                for i in range(3)]
        values[name] = dict(format="eab2.c3l4.differential.v1", complete=True, exit_code=0,
            cpp_executed=True, source_pre_post_equal=True, dll_sha256="a" * 64,
            queries=rows, last_line=name + " DONE", mismatches=[], errata=[dict(case_id=identity)],
            family_counts={group: 3}, differentiability_counts={"smooth": 3},
            branch_certificate_statistics={group: {"cpp/certified": 6, "python/certified": 6}},
            branch_proof_archive=dict(records=6))
    return expected, values


def test_sharded_l4_complete_merge_counts_cases_and_ledger(tmp_path, monkeypatch):
    expected, values = sharded_values()
    source, old = tmp_path / "source", tmp_path / "old.json"
    source.mkdir()
    for name, value in values.items():
        write_json(source / (name + ".json"), value)
    write_json(old, dict(queries=[]))
    monkeypatch.setattr(pack_module, "catalog", lambda: (expected, dict(expected_case_count=10)))
    output = tmp_path / "output"
    result = pack(source, output, old)
    aggregate = result["l4_aggregate"]
    assert aggregate["status"] == "complete"
    assert result["layers"]["l4diff"]["exit_code"] is None
    assert aggregate["observed_case_count"] == 10
    assert aggregate["missing_case_ids"] == aggregate["validation_errors"] == []
    totals = aggregate["totals"]
    assert totals["queries_count"] == 30
    assert totals["errata_count"] == 10
    assert totals["branch_proof_records"] == 60
    assert totals["differentiability_counts"] == {"smooth": 30}
    assert totals["family_counts"]["asymmetric"] == 18
    assert totals["branch_certificate_statistics"]["asymmetric"]["cpp/certified"] == 36
    assert result["files"]["l4_asym5.json"]["extracted"]["last_line"] == "l4_asym5 DONE"
    ledger = json.loads(gzip.decompress((output / "errata_ledger.json.gz").read_bytes()))
    assert ledger["counts"]["new_only_queries"] == 30
    assert ledger["new_last_line"] == result["layers"]["l4diff"]["json_last_line"]
    assert result["package_bytes"] <= 300_000


@pytest.mark.parametrize("fault,status,fragment", [
    ("missing_shard", "pending", None),
    ("no_exit", "pending", None),
    ("partial_json", "pending", None),
    ("incomplete", "pending", None),
    ("explicit_failed", "failed", None),
    ("duplicate_case", "failed", "duplicate case across shards"),
    ("duplicate_query", "failed", "duplicate query"),
    ("missing_case", "failed", "missing cases"),
    ("unknown_case", "failed", "unknown/wrong-family case"),
    ("unexpected_shard", "failed", "unexpected L4 shards"),
    ("mismatch", "failed", None),
    ("wrong_counts", "failed", "does not match query rows"),
    ("mixed_dll", "failed", "different DLL hashes"),
    ("source_changed", "failed", None),
    ("bad_statistics", "failed", "statistics must be nested integer maps"),
])
def test_sharded_l4_rejects_bad_inventory_or_waits_for_missing_evidence(tmp_path, monkeypatch, fault, status, fragment):
    expected, values = sharded_values()
    source, old = tmp_path / "source", tmp_path / "old.json"
    source.mkdir()
    for name, value in values.items():
        write_json(source / (name + ".json"), value)
    write_json(old, dict(queries=[]))
    monkeypatch.setattr(pack_module, "catalog", lambda: (expected, dict(expected_case_count=10)))
    path = source / "l4_asym5.json"
    value = json.loads(path.read_bytes())
    if fault == "missing_shard":
        path.unlink()
    elif fault == "partial_json":
        path.write_bytes(b'{"complete":')
    else:
        if fault == "no_exit":
            del value["exit_code"]
        elif fault == "incomplete":
            value["complete"] = False
        elif fault == "explicit_failed":
            value["exit_code"] = 1
        elif fault == "duplicate_case":
            for row in value["queries"]:
                row["case_id"] = "asymmetric/8"
                row["query_index"] += 10
        elif fault == "duplicate_query":
            value["queries"].append(value["queries"][0])
        elif fault == "missing_case":
            value["queries"] = []
        elif fault == "unknown_case":
            value["queries"][0]["case_id"] = "unexpected"
        elif fault == "unexpected_shard":
            write_json(source / "l4_extra.json", value)
        elif fault == "wrong_counts":
            value["family_counts"]["asymmetric"] = 99
        elif fault == "mixed_dll":
            value["dll_sha256"] = "a" * 64
            other = json.loads((source / "l4_asym4.json").read_bytes())
            other["dll_sha256"] = "b" * 64
            write_json(source / "l4_asym4.json", other)
        elif fault == "source_changed":
            value["source_pre_post_equal"] = False
        elif fault == "bad_statistics":
            value["branch_certificate_statistics"] = []
        elif fault == "mismatch":
            value["mismatches"] = [dict(case_id="asymmetric/9", error="wrong")]
        write_json(path, value)
    result = pack(source, tmp_path / "output", old)
    assert result["layers"]["l4diff"]["status"] == status
    assert result["errata_ledger"]["status"] == ("generated" if fault == "no_exit" else "pending")
    if fault == "no_exit":
        assert result["l4_aggregate"]["artifact_complete"] is True
        assert result["l4_aggregate"]["process_exit_status"] == "pending"
        assert result["status"] == "partial"
    if fragment is not None:
        assert any(fragment in message for message in result["l4_aggregate"]["validation_errors"])


def test_sharded_l4_ledger_uses_hashed_snapshot_not_reread(tmp_path, monkeypatch):
    expected, values = sharded_values()
    source, old = tmp_path / "source", tmp_path / "old.json"
    source.mkdir()
    for name, value in values.items():
        write_json(source / (name + ".json"), value)
    write_json(old, dict(queries=[]))
    monkeypatch.setattr(pack_module, "catalog", lambda: (expected, dict(expected_case_count=10)))
    original = pack_module.read_snapshot
    path = source / "l4_formal.json"

    def changing_file(target):
        result = original(target)
        if target == path:
            write_json(path, dict(complete=False, queries=[]))
        return result

    monkeypatch.setattr(pack_module, "read_snapshot", changing_file)
    result = pack(source, tmp_path / "output", old)
    assert result["errata_ledger"]["counts"]["new_only_queries"] == 30
    assert result["files"]["l4_formal.json"]["extracted"]["complete"] is True


def test_source_catalog_lists_frozen_identities_without_loading_solvers():
    cases, inventory = pack_module.catalog()
    assert inventory["family_case_counts"] == dict(formal=114, t1b=36, thickness=25, branch=5, asymmetric=161)
    assert len(cases) == 341
    assert cases["asymmetric/g5_n3_mu1"] == "asymmetric"  # finite load, no threshold
    assert "asymmetric/regression_b_bare_vv" not in cases
    # A finite-capacity source without contact primitives has no load-jet
    # channel (acceptance 2026-10-24: the channel asserted on it).
    assert "asymmetric/coverage_separated" not in cases
    assert cases["branch/closed_singleton_t1b03"] == "branch"


def test_job_pid_lines_are_not_shard_exit_codes(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "summary.txt").write_text("L4JOB_EXIT 1234 \nL4JOB_EXIT 5678 0\n", encoding="utf-8")
    (source / "l4_asym0.log").write_text("", encoding="utf-8")
    result = pack(source, tmp_path / "output")
    assert "l4job" not in result["layers"]
    assert result["layers"]["l4_asym0"]["exit_code"] is None
    assert result["layers"]["l4diff"]["status"] == "pending"


@pytest.mark.parametrize("fault", [None, "incomplete", "nonzero", "unstable", "wrong_schema"])
def test_native_shards_without_exit_codes_bind_artifacts_not_process_success(tmp_path, monkeypatch, fault):
    expected, values = sharded_values()
    source, old = tmp_path / "source", tmp_path / "old.json"
    source.mkdir()
    for name, value in values.items():
        del value["exit_code"]  # Native differential writer has no process exit field.
        if name == "l4_asym5" and fault == "incomplete":
            value["complete"] = False
        elif name == "l4_asym5" and fault == "wrong_schema":
            value["format"] = "unrecognised"
        write_json(source / (name + ".json"), value)
    if fault == "nonzero":
        (source / "summary.txt").write_text("L4_ASYM5_EXIT 1\n", encoding="utf-8")
    if fault == "unstable":
        original = pack_module.read_snapshot

        def unstable_snapshot(path):
            raw, metadata = original(path)
            if path.name == "l4_asym5.json":
                metadata["stable_during_read"] = False
            return raw, metadata

        monkeypatch.setattr(pack_module, "read_snapshot", unstable_snapshot)
    write_json(old, dict(queries=[]))
    monkeypatch.setattr(pack_module, "catalog", lambda: (expected, dict(expected_case_count=10)))
    result = pack(source, tmp_path / "output", old)
    aggregate = result["l4_aggregate"]
    assert aggregate["artifact_complete"] is (fault is None)
    assert result["errata_ledger"]["status"] == ("generated" if fault is None else "pending")
    assert result["layers"]["l4_formal"]["exit_code"] is None
    assert result["layers"]["l4_formal"]["status"] == "pending"
    assert result["status"] == ("failed" if fault in ("nonzero", "wrong_schema") else "partial")
    if fault == "nonzero":
        assert aggregate["process_exit_status"] == "failed"
    if fault is None:
        assert aggregate["process_exit_status"] == "pending"
        assert aggregate["missing_shards"] == []
        assert len(aggregate["unconfirmed_exit_shards"]) == 10
        assert result["errata_ledger"]["counts"]["new_only_queries"] == 30
        assert result["errata_ledger"]["process_exit_status"] == "pending"
