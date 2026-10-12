"""15 cases x 3 detection snapshots; named, pinned, fail-closed differences.

Oracle: tools/m4_bdda_shadow implements separate Fraction neighbour halfspaces,
edge dot/cross and squared windows; no production geometry primitives. The raw
CSV identity check below uses split columns, not the production CSV reader.
This is local geometry and representation reconciliation, not solver equivalence.
"""
from collections import Counter
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import m4_bdda_shadow as shadow
from eab.adapters import bdda2d
from eab.readers import bdda_df

CASES = ("bb52_N3", "bb12_N3", "bb50_N3", "bb51_N3", "bb03_N3", "bb05_N3", "bb06_N3",
         "bb09_N3", "bb10_N3", "bbv01_N3", "bbv01_dbv01a_N3", "bbv02_N3", "bbv02_dbv02a_N3",
         "bbF038_N3", "bbS038_N3")
EXPECTED_PATH = Path(__file__).with_name("m4_shadow_expected.json")


def _digest(differences):
    return hashlib.sha256(json.dumps(differences, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _legacy_identity_gate(path, records):
    lines = (path / "bdda_debug_contacts.csv").read_text(encoding="utf-8").splitlines()
    head = lines[0].split(",")
    raw = {}
    for line in lines[1:]:
        row = dict(zip(head, line.split(",")))
        key = (int(row["step"]), int(row["contact"]))
        assert key not in raw, "duplicate raw row id"
        raw[key] = row
    assert set(raw) == {(r.step, r.contact_index) for r in records}, "legacy row coverage"
    for r in records:
        row = raw[(r.step, r.contact_index)]
        assert r.extra["raw_p1"] == int(row["p1"]), "legacy p1 column misread"
        assert r.extra["raw_p2"] == int(row["p2"]), "legacy p2 column misread"
        assert r.extra["p3"] == int(row["p3"]), "legacy p3 column misread"
        assert r.raw_cover == int(row["mtype"]), "legacy mtype column misread"


def _gate_case(case):
    path = ROOT / "fixtures" / "bdda_df" / case
    legacy = bdda_df.load_records(path)
    _legacy_identity_gate(path, legacy)
    actual = shadow.compare_fixture(path)
    _assert_baseline(case, actual)
    return actual


def _assert_baseline(case, actual):
    expected = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))[case]
    assert [r["step"] for r in actual] == [1, 2, 3], "missing/extra detection step"
    shadow.assert_classified(actual)
    for row, want in zip(actual, expected):
        for key in ("step", "legacy", "legacy_unique", "eab", "counts", "window",
                    "legacy_ve_metrics_observed", "legacy_metrics_geometry_only"):
            assert row[key] == want[key], ("pinned shadow tally", case, row["step"], key, row[key], want[key])
        assert _digest(row["differences"]) == want["difference_sha256"], "pinned row-by-row classification"
        # Neither dropped duplicates nor an extra unknown category can disappear.
        assert len(row["differences"]) == sum(n for k, n in row["counts"].items() if k != "MATCH")
        assert row["legacy"] >= row["legacy_unique"]
        assert row["legacy"]-row["legacy_unique"] == row["counts"].get("LEGACY_DUPLICATE_PRIMARY_REFERENCE", 0)


@pytest.mark.parametrize("case", CASES)
def test_fifteen_family_three_steps_have_only_pinned_classified_differences(case):
    _gate_case(case)


def test_family_capture_coverage_and_detection_products_are_not_all_identical():
    manifest = json.loads((ROOT / "reports/codex/M4a_evidence/family_manifest.json").read_text(encoding="utf-8"))
    assert tuple(Path(c["fixture"]).name for c in manifest["cases"]) == CASES
    assert all(c["steps"] == 3 for c in manifest["cases"])
    expected = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))
    assert set(expected) == set(CASES)
    geometries = {}
    for name in CASES:
        p = ROOT / "fixtures/bdda_df" / name
        digest = hashlib.sha256((p / "bdda_debug_verts.csv").read_bytes()).hexdigest()
        geometries.setdefault(digest, []).append(name)
        geoms = shadow.load_step_geometries(p / "bdda_debug_verts.csv")
        assert set(geoms) == {1, 2, 3}
        for step in geoms:
            window = shadow.load_window(p, step)
            assert window.source == "detparams" and window.fallback_fields == ()
    # No uniqueness claim based on uninitialised o3/o4 noise. F/S happen to
    # have the same three geometric frames; retain and expose that limitation.
    assert len(geometries) == 14
    assert [names for names in geometries.values() if len(names) > 1] == [["bbF038_N3", "bbS038_N3"]]


def test_dropped_adapter_domain_window_is_rejected_through_real_enumeration(monkeypatch):
    original = bdda2d.covers.enumerate_covers
    def no_angle_window(A, B, **kwargs):
        kwargs["cone_tol"] = 0.0
        return original(A, B, **kwargs)
    _gate_case("bb52_N3")
    monkeypatch.setattr(bdda2d.covers, "enumerate_covers", no_angle_window)
    with pytest.raises(AssertionError, match="unclassified differences|pinned shadow tally"):
        _gate_case("bb52_N3")


def test_misclassified_difference_is_rejected_by_named_counts(monkeypatch):
    original = shadow.classify_extra
    def wrong_category(key, sg, window):
        value = original(key, sg, window)
        return "ANGULAR_WINDOW_COVER_NOT_SELECTED" if value == "EXACT_LOCAL_COVER_NOT_SELECTED" else value
    _gate_case("bb52_N3")
    monkeypatch.setattr(shadow, "classify_extra", wrong_category)
    with pytest.raises(AssertionError, match="pinned shadow tally"):
        _gate_case("bb52_N3")


def test_legacy_reader_shifted_column_is_rejected_by_independent_raw_identity(monkeypatch):
    original = bdda_df._read_csv
    def shifted_column(path, **kwargs):
        rows = original(path, **kwargs)
        if path.name == "bdda_debug_contacts.csv":
            for row in rows:
                if row["mtype"] == "0":
                    row["p1"] = row["p2"]
        return rows
    _gate_case("bb52_N3")
    monkeypatch.setattr(bdda_df, "_read_csv", shifted_column)
    with pytest.raises(AssertionError, match="legacy p1 column misread"):
        _gate_case("bb52_N3")


@pytest.mark.parametrize("field", ["normal", "gap"])
def test_exported_legacy_metrics_are_checked_not_just_reconstructed(monkeypatch, field):
    original = bdda_df.load_records
    def bad_metric(path):
        records = original(path)
        r = next(r for r in records if r.cover.value == "VE" and "df18_cs1" in r.extra)
        if field == "gap":
            r.extra["df18_cs1"] = "1.0"
        else:
            r.extra["df18_s"][:2] = [-x for x in r.extra["df18_s"][:2]]
        return records
    monkeypatch.setattr(bdda_df, "load_records", bad_metric)
    with pytest.raises(AssertionError, match="normal direction reversed|gap outside fit precision"):
        shadow.compare_fixture(ROOT / "fixtures/bdda_df/bb52_N3")


def test_unknown_difference_never_passes():
    for name in ("UNCLASSIFIED_NEW_DEFECT", "NOT_A_REGISTERED_CATEGORY"):
        with pytest.raises(AssertionError, match="unclassified differences"):
            shadow.assert_classified([dict(step=1, counts={name: 1})])
    with pytest.raises(AssertionError, match="no detection steps compared"):
        shadow.assert_classified([])


@pytest.mark.parametrize("kind", ["verts", "contacts", "detparams"])
@pytest.mark.parametrize("remove_all", [False, True])
def test_missing_geometry_contact_or_parameter_steps_fail_closed(tmp_path, kind, remove_all):
    """Actual input-path mutation, not appending manufactured output rows."""
    source = ROOT / "fixtures/bdda_df/bb50_N3"
    for p in source.glob("*.csv"):
        shutil.copyfile(p, tmp_path / p.name)
    target = tmp_path / f"bdda_debug_{kind}.csv"
    lines = target.read_text(encoding="utf-8").splitlines()
    lines = lines[:1] if remove_all else [lines[0]]+[line for line in lines[1:] if not line.startswith("2,")]
    target.write_text("\n".join(lines)+"\n", encoding="utf-8")
    # df18/df22 must not synthesize a missing main-table detection snapshot.
    with pytest.raises(AssertionError, match="missing/extra|legacy row coverage"):
        records = bdda_df.load_records(tmp_path)
        _legacy_identity_gate(tmp_path, records)
        shadow.compare_fixture(tmp_path)


def test_duplicate_primary_reference_second_row_metrics_are_not_skipped(monkeypatch):
    original = bdda_df.load_records
    def bad_duplicate_metric(path):
        records = original(path)
        r = next(r for r in records if (r.step, r.contact_index) == (1, 54))
        r.extra["df18_s"][:2] = [-x for x in r.extra["df18_s"][:2]]
        return records
    monkeypatch.setattr(bdda_df, "load_records", bad_duplicate_metric)
    with pytest.raises(AssertionError, match="normal direction reversed"):
        shadow.compare_fixture(ROOT / "fixtures/bdda_df/bbv01_N3")
