"""Recompute offline M4 evidence and the three required internal red/green probes.

Does not capture/run an executable, update expected tallies, or modify fixtures.
Run with PYTHONDONTWRITEBYTECODE=1 python -X utf8 tools/m4_verify_evidence.py.
"""
from collections import Counter
import csv
import json
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests"), str(ROOT / "tools")]
import pytest
import test_m4_bdda_shadow as gate
import m4_bdda_shadow as shadow
from eab.adapters import bdda2d
from eab.readers import bdda_df

EVIDENCE = ROOT / "reports/codex/M4a_evidence"


def verify():
    results = {name: gate._gate_case(name) for name in gate.CASES}
    (EVIDENCE / "shadow_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    categories = sorted({key for rows in results.values() for row in rows for key in row["counts"]})
    totals = Counter()
    with (EVIDENCE / "per_step_summary.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["case", "step", "legacy", "legacy_unique", "eab", *categories])
        writer.writeheader()
        for name, rows in results.items():
            for row in rows:
                totals.update(row["counts"])
                common = row["counts"].get("MATCH", 0)+row["counts"].get("VV_IDENTITY_MATCH_TWO_REFERENCE_NORMAL", 0)
                assert sum(row["counts"].values()) == row["legacy"]+row["eab"]-common, "category accounting"
                writer.writerow({"case": name, **{k: row[k] for k in ("step", "legacy", "legacy_unique", "eab")},
                                 **{key: row["counts"].get(key, 0) for key in categories}})
    mutations = []
    original_enum, original_classify, original_read = (
        bdda2d.covers.enumerate_covers, shadow.classify_extra, bdda_df._read_csv)

    def drop_window(A, B, **kwargs):
        kwargs["cone_tol"] = 0.0
        return original_enum(A, B, **kwargs)

    def wrong_class(key, sg, window):
        value = original_classify(key, sg, window)
        return "ANGULAR_WINDOW_COVER_NOT_SELECTED" if value == "EXACT_LOCAL_COVER_NOT_SELECTED" else value

    def shift_column(path):
        rows = original_read(path)
        if path.name == "bdda_debug_contacts.csv":
            for row in rows:
                if row["mtype"] == "0":
                    row["p1"] = row["p2"]
        return rows

    probes = [
        ("drop_domain_window", bdda2d.covers, "enumerate_covers", drop_window, ("unclassified differences", "pinned shadow tally")),
        ("misclassify_difference", shadow, "classify_extra", wrong_class, ("pinned shadow tally",)),
        ("legacy_column_shift", bdda_df, "_read_csv", shift_column, ("legacy p1 column misread",)),
    ]
    for name, module, attribute, function, reasons in probes:
        gate._gate_case("bb52_N3")
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(module, attribute, function)
            try:
                gate._gate_case("bb52_N3")
            except AssertionError as error:
                assert any(reason in str(error) for reason in reasons), (name, "wrong failure", error)
                text = traceback.format_exc()
                (EVIDENCE / f"mutation_{name}_red.txt").write_text(text, encoding="utf-8")
                mutations.append(dict(name=name, injected=f"{module.__name__}.{attribute}",
                                      status="KILLED", assertion=str(error), raw_red_log=f"mutation_{name}_red.txt"))
            else:
                raise AssertionError(f"mutation survived: {name}")
        gate._gate_case("bb52_N3")
        mutations[-1]["restored_baseline"] = "PASS"
    summary = dict(cases=len(results), steps=sum(map(len, results.values())), categories=dict(totals),
                   unclassified=0, mutations=mutations)
    (EVIDENCE / "verification.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    verify()
