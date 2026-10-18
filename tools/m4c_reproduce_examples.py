"""Recompute geometric witnesses in M4c's portable minimal examples.

This is a production-path reproduction, not an independent geometric oracle.
Legacy absence still requires the source-normalized table hash evidence.
"""
from __future__ import annotations

from frozen_evidence import data_path
import argparse
from fractions import Fraction as F
import json
from pathlib import Path
from types import SimpleNamespace

import m4c_motion_replay as replay


def reproduce(example):
    polygons = {key: tuple(tuple(F(x) for x in p) for p in example[key])
                for key in ("A0", "A1", "B0", "B1")}
    A0, A1, B0, B1 = (polygons[key] for key in ("A0", "A1", "B0", "B1"))
    a = SimpleNamespace(vidx=example["vertex_ids_A"])
    b = SimpleNamespace(vidx=example["vertex_ids_B"])
    saved = example["result"]
    hit = replay.motion.motion_first_entrance(A0, B0, A1, B1)
    actual = replay._motion_record(hit, a, b)
    assert hit.initial_state == saved["initial_state"], "minimal example initial state"
    assert replay.digest(actual) == replay.digest(saved["actual"]), "minimal example actual contact"
    pd = replay._pd(A0, B0, a, b, 0) if hit.initial_state == 1 else None
    assert replay.digest(pd) == replay.digest(saved["pd"]), "minimal example PD complete ties"
    if "translation" in saved:
        At, da = replay.translation_surrogate(A0, A1)
        Bt, db = replay.translation_surrogate(B0, B1)
        surrogate = replay._motion_record(replay.motion.motion_first_entrance(A0, B0, At, Bt), a, b)
        expected = saved["translation"]
        assert replay.digest(surrogate) == replay.digest(expected["result"]), "minimal example surrogate"
        assert str(da+db) == expected["delta_linf"]
        assert replay.translation_certificate(da+db) == expected["certificate"]
        assert (actual["status"] == surrogate["status"] and actual["features"] == surrogate["features"]) == expected["same_first_cover_set"]
    if "depth_witness" in saved:
        assert replay._penetration_witness(A1, B1) == saved["depth_witness"], "minimal example depth witness"
    prediction = saved.get("prediction", {})
    if prediction.get("status") == "EVALUATED_PREVIOUS_DISPLACEMENT":
        Ap, Bp = (tuple(tuple(F(x) for x in p) for p in example[key])
                  for key in ("A_previous", "B_previous"))
        Ae = tuple(tuple(2*p[k]-q[k] for k in (0, 1)) for p, q in zip(A0, Ap))
        Be = tuple(tuple(2*p[k]-q[k] for k in (0, 1)) for p, q in zip(B0, Bp))
        predicted = replay._motion_record(replay.motion.motion_first_entrance(A0, B0, Ae, Be), a, b)
        assert replay.digest(predicted) == replay.digest(prediction["result"]), "minimal example prediction"
        assert (actual["status"] == predicted["status"] and actual["features"] == predicted["features"]) == prediction["same_first_cover_set"]
    row = example.get("legacy_row")
    if row is not None:
        assert replay.classify_reference(hit.initial_state, tuple(row["primary_reference"]), actual, pd) == row["category"]
        if row["secondary_reference"] is not None:
            assert replay.classify_reference(hit.initial_state, tuple(row["secondary_reference"]), actual, pd) == row["secondary_category"]
    return {"case": example["case"], "step": example["step"], "pair": example["pair"],
            "status": "PASS", "actual_status": actual["status"], "time_display": actual["time_display"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, nargs="?", default=data_path(replay.ROOT, "reports/codex/M4c_evidence/minimal_examples.json"))
    parser.add_argument("--name")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    examples = json.loads(args.path.read_text(encoding="utf-8"))
    names = [args.name] if args.name else sorted(examples)
    results = {name: reproduce(examples[name]) for name in names}
    result = {"complete": True, "audit": "GREEN", "source_sha256": replay.file_hash(args.path),
              "examples": results, "code_hashes": replay.code_hashes(),
              "scope": "Recomputed geometry and feature classifications; legacy table absence certified by complete source replay, not by these isolated shapes"}
    if args.out:
        replay.write_json(args.out, result)
    print("M4C_MINIMAL_EXAMPLES_GREEN", len(results))


if __name__ == "__main__":
    main()
