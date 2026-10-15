"""Freeze/verify compact endpoint-only examples, never general first-contact claims."""
import argparse
from fractions import Fraction as F
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools")]
import m5a2_affine_replay as replay

OUTPUT = Path(__file__).with_suffix(".json")


def exact(poly):
    return tuple(tuple(F(v) for v in p) for p in poly)


def freeze():
    summary = json.loads(Path(__file__).with_name("affine_full_summary.json").read_text(encoding="utf-8"))
    chosen = {name: summary["cases"]["bb05"]["examples"][name] for name in
              ("endpoint_state_flip__affine_matches_snapshot", "same_endpoint_state__affine_matches_snapshot")}
    worst, row = F(-1), None
    for path in sorted((replay.TMP / "affine_full_r4").glob("*/block_residuals.jsonl.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            for line in stream:
                item = json.loads(line)
                gap = None if item["nearest_gap_square"] is None else F(item["nearest_gap_square"])
                if gap:
                    ratio = F(item["delta_affine"])**2/gap
                    if ratio > worst:
                        worst, row = ratio, item
    assert str(worst) == summary["distributions"]["affine_over_gap_square"]["quantiles_exact"]["max"]
    paths = replay.input_paths(row["case"])
    _, frames, _ = replay.rigid.chord.snapshot.read_snapshot(paths["snapshot"])
    terminal = replay.rigid.chord.load_geometry_csv(paths["terminal"], frames)
    _, sg, eg = replay.rigid.chord.paired_geometries(frames, terminal)[row["step"]-1]
    start = {b: replay.rigid.chord._exact_poly(block.poly) for b, block in sg.blocks.items()}
    b = row["block"]
    other = min((j for j in start if j != b), key=lambda j: replay.gap_square(start[b], start[j]))
    chosen["roundoff_sized_affine_residual_exceeds_gap"] = {
        **row, "ratio_square": str(worst), "neighbor": other,
        "start": replay.json_points(start[b]), "end": replay.json_points(replay.rigid.chord._exact_poly(eg.blocks[b].poly)),
        "neighbor_start": replay.json_points(start[other])}
    replay.write_json(OUTPUT, {"complete": True, "examples": chosen,
        "full_summary_sha256": replay.file_hash(Path(__file__).with_name("affine_full_summary.json"))})


def verify():
    payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert payload["full_summary_sha256"] == replay.file_hash(Path(__file__).with_name("affine_full_summary.json")), "minimal examples must bind the current complete full summary"
    verified = []
    for name, row in payload["examples"].items():
        if name == "roundoff_sized_affine_residual_exceeds_gap":
            A, end, B = exact(row["start"]), exact(row["end"]), exact(row["neighbor_start"])
            fit = replay.fit_affine(A, end)
            gap = replay.gap_square(A, B)
            assert fit.delta == F(row["delta_affine"]) and gap == F(row["nearest_gap_square"])
            assert fit.delta*fit.delta/gap == F(row["ratio_square"]) > 1
            assert fit.endpoint_certificate == "UNCERTIFIED_NONAFFINE_ENDPOINTS"
        else:
            A, Aend, B, Bend = (exact(row[key]) for key in ("A0", "A1", "B0", "B1"))
            af, bf = replay.fit_affine(A, Aend), replay.fit_affine(B, Bend)
            ar, br = replay.rigid.fit_rigid(A, Aend), replay.rigid.fit_rigid(B, Bend)
            actual = {"snapshot_chord": replay.oracle.overlap(Aend, Bend),
                      "affine_fit": replay.oracle.overlap(tuple(af.endpoint(p) for p in A), tuple(bf.endpoint(p) for p in B)),
                      "rigid": replay.oracle.overlap(tuple(ar.motion.endpoint(p) for p in A), tuple(br.motion.endpoint(p) for p in B))}
            assert actual == row["endpoint_states"]
            assert [str(af.delta), str(bf.delta)] == row["delta_affine"]
            assert [str(ar.delta), str(br.delta)] == row["delta_rigid"]
        verified.append(name)
    replay.write_json(OUTPUT.with_name("affine_minimal_examples_verified.json"), {
        "complete": True, "verified": verified, "examples_sha256": replay.file_hash(OUTPUT),
        "scope": "endpoint states and residual/gap only; no general affine first entrance"})
    print("3 self-contained affine endpoint examples verified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    if args.freeze:
        freeze()
    verify()
