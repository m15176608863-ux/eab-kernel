"""Extract and recheck the two new-contact pairs with no post-df06 first cover.

Only the two selected endpoint geometries are recomputed. Selection exhausts
the immutable complete 1810-frame batch, not a sample or incomplete run.
The JSON remains self-contained for verification after temporary sources are
removed. This is a targeted reproduction, not a new independent root oracle.
"""
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "src"))
import m4c_motion_replay as replay
from eab.kernel2d.motion import motion_first_entrance

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
BATCH = BASE / "full_replay_r4"
OUTPUT = HERE / "post_no_first_cover_pairs.json"
RESULT = HERE / "post_no_first_cover_pairs_check.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def feature_keys(features, a, b):
    result = set()
    for tag, i, j in features:
        if tag == "VV":
            result.add(("VV", *sorted((a[i], b[j]))))
        elif tag == "VE":
            result.add(("VE", a[i], *sorted((b[j], b[(j + 1) % len(b)]))))
        else:
            assert tag == "EV"
            result.add(("VE", b[j], *sorted((a[i], a[(i + 1) % len(a)]))))
    return tuple(sorted(result))


def exact_poly(poly):
    return [[str(Fraction(x)), str(Fraction(y))] for x, y in poly]


def extract():
    summary_path = BATCH / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["complete"] is True and summary["audit"] == "GREEN" and summary["steps"] == 1810
    assert summary["code_hashes"] == replay.code_hashes()
    selected = []
    contact_pairs = 0
    visited_frames = 0
    normalized_hashes = {}
    for case, case_summary in summary["cases"].items():
        normalized = BATCH / case / "normalized.jsonl.gz"
        normalized_hashes[case] = sha(normalized)
        assert normalized_hashes[case] == case_summary["normalized_sha256"]
        assert sha(BATCH / case / "audit.json") == case_summary["audit_sha256"]
        case_selected = []
        with gzip.open(normalized, "rt", encoding="utf-8") as stream:
            for line in stream:
                row = json.loads(line)
                visited_frames += 1
                for pair in row["pairs"]:
                    if pair["initial_state"] != -1 or pair["actual"]["status"] != "contact":
                        continue
                    contact_pairs += 1
                    covers = {tuple(x) for x in pair["actual"]["features"]}
                    records = {phase: [r for r in row["phases"][phase]["records"] if r["pair"] == pair["pair"]]
                               for phase in replay.PHASES}
                    references = [r[key] for r in records["post_df06"]
                                  for key in ("primary_reference", "secondary_reference") if r[key] is not None]
                    if any(tuple(ref) in covers for ref in references):
                        continue
                    assert records["raw_df05"] and records["post_df06"], "not a missing-pair example"
                    assert not pair.get("missing_both_legacy_tables", False)
                    case_selected.append((row, pair, records))
        if not case_selected:
            continue
        source = BASE / "tmp/kinematics_inputs" / case / "shadow.jsonl"
        terminal = source.with_name("geom.csv")
        assert sha(source) == case_summary["input_hashes"]["snapshot"]
        assert sha(terminal) == case_summary["input_hashes"]["terminal_source"]
        _, frames, _ = replay.snapshot.read_snapshot(source)
        endpoint = replay.load_geometry_csv(terminal, frames)
        for row, pair, records in case_selected:
            step = row["step"]
            start = frames[step - 1]
            end = frames[step] if step < len(frames) else {**start, "geometry": endpoint}
            sg, eg = replay.snapshot.geometry_from_frame(start), replay.snapshot.geometry_from_frame(end)
            ba, bb = pair["pair"]
            aliases = {}
            for phase in replay.PHASES:
                original = [raw for raw in start[phase] if replay._legacy_pair(raw, sg) == (ba, bb)]
                assert original == [r["tuple7"] for r in records[phase]], "all source pair rows preserved in order"
                for raw in original:
                    for vertex in raw[1:]:
                        if vertex:
                            aliases[str(vertex)] = sg.canon(vertex)
            selected.append({
                "case": case, "step": step, "pair": pair["pair"],
                "vertex_ids_A": sg.blocks[ba].vidx, "vertex_ids_B": sg.blocks[bb].vidx,
                "A0": exact_poly(sg.blocks[ba].poly), "A1": exact_poly(eg.blocks[ba].poly),
                "B0": exact_poly(sg.blocks[bb].poly), "B1": exact_poly(eg.blocks[bb].poly),
                "legacy_vertex_aliases": aliases, "all_legacy_rows_for_pair": records,
                "actual": pair["actual"], "initial_state": pair["initial_state"],
                "missing_both_legacy_tables": False,
                "source_hashes": {**case_summary["input_hashes"], "normalized": normalized_hashes[case],
                                  "audit": case_summary["audit_sha256"], "frame": replay.digest(row),
                                  "start_geometry": replay.digest(start["geometry"]),
                                  "end_geometry": replay.digest(end["geometry"])}})
        assert sha(source) == case_summary["input_hashes"]["snapshot"]
        assert sha(terminal) == case_summary["input_hashes"]["terminal_source"]
    assert visited_frames == 1810 and contact_pairs == 68 and len(selected) == 2
    payload = {"schema": "eab.m4c.post-no-first-cover-pairs.v1", "selection_complete_frames": visited_frames,
               "all_new_contact_step_pairs": contact_pairs, "post_pairs_without_any_first_cover_reference": len(selected),
               "selection_rule": "initial_state=-1 and actual contact, no post primary or secondary reference in actual first-cover set; both legacy tables must contain this pair",
               "geometry_scope": "Only the two involved blocks; exact rational endpoint coordinates, stable vertex IDs and every legacy row for this pair.",
               "full_summary_sha256": sha(summary_path), "normalized_source_hashes": normalized_hashes,
               "code_hashes": replay.code_hashes(), "examples": selected, "script_sha256": sha(Path(__file__))}
    json_write(OUTPUT, payload)
    return payload


def verify(payload):
    started = time.perf_counter()
    results = []
    assert payload["code_hashes"] == replay.code_hashes()
    for example in payload["examples"]:
        poly = {name: tuple(tuple(Fraction(x) for x in p) for p in example[name]) for name in ("A0", "B0", "A1", "B1")}
        result = motion_first_entrance(poly["A0"], poly["B0"], poly["A1"], poly["B1"])
        assert result.initial_state == -1 and result.status == "contact"
        assert result.exact_time.certificate == example["actual"]["time"]
        incidences, features = replay.independent_features(poly["A0"], poly["B0"], poly["A1"], poly["B1"], result.exact_time)
        assert result.features == features and result.incidences == incidences
        keys = feature_keys(features, example["vertex_ids_A"], example["vertex_ids_B"])
        inc_keys = feature_keys(incidences, example["vertex_ids_A"], example["vertex_ids_B"])
        assert keys == tuple(tuple(x) for x in example["actual"]["features"])
        assert inc_keys == tuple(tuple(x) for x in example["actual"]["incidences"])
        aliases = example["legacy_vertex_aliases"]
        phase_results = {}
        for phase, rows in example["all_legacy_rows_for_pair"].items():
            assert rows, "legacy pair is present, not omitted"
            references = []
            for row in rows:
                raw = row["tuple7"]
                canonical = lambda v: aliases[str(v)]
                primary = ("VE", canonical(raw[1]), *sorted((canonical(raw[2]), canonical(raw[3]))))
                assert primary == tuple(row["primary_reference"])
                references.append(primary)
                secondary = None
                if raw[0] == 1 and all(raw[k] for k in (4, 5, 6)):
                    secondary = ("VE", canonical(raw[4]), *sorted((canonical(raw[5]), canonical(raw[6]))))
                    references.append(secondary)
                assert secondary == (None if row["secondary_reference"] is None else tuple(row["secondary_reference"]))
                for reference, category in ((primary, row["category"]), (secondary, row["secondary_category"])):
                    if reference is not None:
                        expected = "FIRST_COVER_MATCH" if reference in keys else "FIRST_INCIDENCE_NOT_COVER" if reference in inc_keys else "OTHER_FEATURE_FIRST"
                        assert category == expected
            phase_results[phase] = {"rows_present": len(rows), "primary_plus_secondary_references": len(references),
                                    "references_in_first_covers": sum(x in keys for x in references)}
        assert phase_results["post_df06"]["references_in_first_covers"] == 0
        results.append({"case": example["case"], "step": example["step"], "pair": example["pair"],
                        "root_certificate_recomputed": True, "complete_cover_set_recomputed": True,
                        "independent_fraction_incidence_and_cone_check": True, "phases": phase_results,
                        "actual": example["actual"]})
    assert len(results) == 2
    output = {"complete": True, "status": "PASS", "artifact_sha256": sha(OUTPUT), "script_sha256": sha(Path(__file__)),
              "results": results, "seconds": time.perf_counter() - started,
              "scope": "Self-contained exact two-pair recomputation; no full replay rerun; production roots with independent Fraction first-time incidence/cone checks."}
    json_write(RESULT, output)
    print("POST_NO_FIRST_COVER_PAIRS_PASS", len(results), "of", payload["all_new_contact_step_pairs"])
    for result in results:
        print(result["case"], result["step"], result["pair"], result["phases"])


if __name__ == "__main__":
    payload = json.loads(OUTPUT.read_text(encoding="utf-8")) if "--verify-only" in sys.argv else extract()
    verify(payload)
