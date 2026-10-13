"""Large exact M3 2D scans, outside the fast regression suite.

All vertices, edge midpoints, face samples and exact side probes in each
requested subdivision are checked, without skipping contact/near-band points.
The historical bb52 replay is explicitly the 21x60 translation series; its
complete planar arrangements are a separate, potentially much larger task.
"""
from __future__ import annotations

import argparse
import ast
from fractions import Fraction as F
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = [ROOT/"src/eab/kernel2d/global_entrance.py", ROOT/"src/eab/kernel2d/g0_oracle.py", Path(__file__)]
SOURCE_HASH_BEFORE_IMPORT = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCE_FILES}
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
from eab.kernel2d.global_entrance import GlobalEntrance2
from eab.kernel2d import g0_oracle as oracle


def write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str)+"\n", encoding="utf-8")


def load_families():
    spec = importlib.util.spec_from_file_location("m3_cases", ROOT / "tests/test_m3_global2d.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._families()


def scan(name, A, B, out):
    started = time.perf_counter()
    model = GlobalEntrance2(A, B)
    constructed = time.perf_counter()
    subdivision = model.subdivision
    arranged = time.perf_counter()
    kinds = {"vertex": [c.sample for c in subdivision.vertices],
             "edge_midpoint": [c.sample for c in subdivision.edges],
             "face_interior": [c.sample for c in subdivision.faces],
             "edge_sides": [p for c in subdivision.edges for p in model.side_probes(*c.vertices)]}
    mismatches = []
    states = {"-1": 0, "0": 0, "1": 0}
    unique = set()
    for kind, probes in kinds.items():
        for p in probes:
            unique.add(p)
            moved = oracle.translate(A, p)
            expected = oracle.overlap(moved, oracle.points(B))
            topo = (0 if oracle.boundary_has_exterior(moved, oracle.points(B)) else 1) if expected == 0 else expected
            got, got_topo = model.membership(p), model.topology(p)
            states[str(expected)] += 1
            if (got, got_topo) != (expected, topo):
                mismatches.append(dict(kind=kind, point=p, got=(got, got_topo), expected=(expected, topo)))
    for dimension, cells in enumerate((subdivision.vertices, subdivision.edges, subdivision.faces)):
        for cell in cells:
            expected = oracle.overlap(oracle.translate(A, cell.sample), oracle.points(B))
            if cell.state != expected:
                mismatches.append(dict(kind="stored_cell_label", dimension=dimension,
                                       point=cell.sample, actual=cell.state, expected=expected))
    exposed_count = hidden_count = 0
    for piece in model.clipped_covers:
        midpoint = tuple((piece.start[k]+piece.end[k])/2 for k in (0, 1))
        moved = oracle.translate(A, midpoint)
        state = oracle.overlap(moved, oracle.points(B))
        boundary = state == 0 and oracle.boundary_has_exterior(moved, oracle.points(B))
        if piece.exposed != boundary:
            mismatches.append(dict(kind="local_cover_exposure", point=midpoint, actual=piece.exposed, expected=boundary))
        if piece.exposed:
            exposed_count += 1
        else:
            hidden_count += 1
    origin = next(c.sample for c in subdivision.faces if c.state == 1)
    rng = random.Random(20261014)
    directions = set()
    while len(directions) < 12:
        direction = (rng.randint(-19, 19), rng.randint(-19, 19))
        if direction != (0, 0):
            directions.add(direction)
    ray_rows = []
    for direction in sorted(directions):
        parameter = oracle.ray_exit(oracle.translate(A, origin), oracle.points(B), direction)
        hit = tuple(origin[k]+parameter*direction[k] for k in (0, 1))
        moved = oracle.translate(A, hit)
        contact = oracle.overlap(moved, oracle.points(B)) == 0
        exterior_sector = contact and oracle.boundary_has_exterior(moved, oracle.points(B))
        local_covered = any(oracle.on_segment(hit, p.start, p.end) for p in model.clipped_covers if p.exposed)
        global_covered = any(oracle.on_segment(hit, a, b) for a, b in model.boundary)
        ray_rows.append(dict(direction=direction, parameter=parameter, point=hit,
                             true_boundary=exterior_sector, local_covered=local_covered, global_covered=global_covered))
        if not (exterior_sector and local_covered and global_covered):
            mismatches.append(dict(kind="random_oracle_ray_exit", point=hit, direction=direction,
                                   true_boundary=exterior_sector, local_covered=local_covered, global_covered=global_covered))
    result = dict(name=name, a=A, b=B, convex_pairs=len(model.cells),
                  dimensions={"0": len(subdivision.vertices), "1": len(subdivision.edges), "2": len(subdivision.faces)},
                  probes_by_kind={k: len(v) for k, v in kinds.items()}, unique_probes=len(unique),
                  sample_count=sum(map(len, kinds.values())), oracle_states=states,
                  mismatch_count=len(mismatches), mismatches=mismatches,
                  stored_cell_labels_checked=sum(len(c) for c in (subdivision.vertices, subdivision.edges, subdivision.faces)),
                  local_cover_midpoints_checked=exposed_count+hidden_count, exposed_pieces=exposed_count, hidden_pieces=hidden_count,
                  random_ray_origin=origin, random_ray_count=len(ray_rows), random_ray_exits=ray_rows,
                  construction_seconds=constructed-started, arrangement_seconds=arranged-constructed,
                  total_seconds=time.perf_counter()-started, skipped=0)
    write(out / (name + ".json"), result)
    print(name, result["sample_count"], "mismatches", len(mismatches), "seconds", round(result["total_seconds"], 2), flush=True)
    return result


def bb52(out):
    import bb52_g0
    blocks, _ = bb52_g0.load_blocks(1)
    old = json.loads((ROOT / "reports/bb52_g1_g0.json").read_text(encoding="utf-8"))
    pairs = old["g0_pairs"]
    assert len(pairs) == 21
    samples, mismatches, counts, pair_rows = [], [], {"-1": 0, "0": 0, "1": 0}, []
    started = time.perf_counter()
    for bi, bj, translations in bb52_g0.g0_draws(pairs, 60, 0):
        A, B = blocks[bi]["poly"], blocks[bj]["poly"]
        model = GlobalEntrance2(A, B)
        for index, x in enumerate(translations):
            expected = oracle.overlap(oracle.translate(A, x), oracle.points(B))
            got = model.membership(x)
            row = dict(pair=[bi, bj], index=index, translation=[F(q) for q in x], expected=expected, actual=got)
            samples.append(row)
            counts[str(expected)] += 1
            if got != expected:
                mismatches.append(row)
        pair_rows.append(dict(pair=[bi, bj], samples=len(translations), convex_pairs=len(model.cells)))
    assert len(samples) == 1260
    result = dict(name="bb52_historical_1260", sample_count=len(samples), oracle_states=counts,
                  pairs=pair_rows, mismatch_count=len(mismatches), mismatches=mismatches, samples=samples,
                  total_seconds=time.perf_counter()-started, skipped=0,
                  probe_scope="Historical translations only; not the full bb52 arrangements")
    write(out / "bb52_historical_1260.json", result)
    print(result["name"], len(samples), "mismatches", len(mismatches), flush=True)
    return result


def star(seed):
    rng = random.Random(seed)
    directions = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
    return [
        (r*x, r*y) for i, (x, y) in enumerate(directions)
        for r in [F(rng.randint(16, 24) if i % 2 == 0 else rng.randint(3, 6), 10)]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT/"reports/codex/M3_evidence/scans2d")
    parser.add_argument("--section", choices=("all", "families", "random", "bb52"), default="all")
    args = parser.parse_args()
    out = args.out.resolve()
    if not out.is_relative_to(ROOT/"reports/codex/M3_evidence"):
        parser.error("output must stay within M3 evidence")
    out.mkdir(parents=True, exist_ok=True)
    source_files, before = SOURCE_FILES, SOURCE_HASH_BEFORE_IMPORT
    temp = ROOT / "reports/codex/M3_evidence/tmp"
    os.environ.update(TEMP=str(temp), TMP=str(temp), PYTHONDONTWRITEBYTECODE="1")
    results = []
    if args.section in ("all", "bb52"):
        results.append(bb52(out))
    if args.section in ("all", "families"):
        for name, A, B in load_families():
            results.append(scan(name, A, B, out))
    if args.section in ("all", "random"):
        for seed in range(3):
            A, B = star(seed), [(0, 0), (F(3, 5), F(1, 7)), (F(1, 8), F(4, 7))]
            for scale in (F(1, 1000), F(1), F(1000)):
                transform = lambda P: [(scale*x, scale*y) for x, y in P]
                results.append(scan(f"star_{seed}_scale_{scale.numerator}_{scale.denominator}", transform(A), transform(B), out))
    after = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
    assert before == after, "source changed during scan; results cannot be attributed to one revision"
    oracle_tree = ast.parse(source_files[1].read_text(encoding="utf-8-sig"))
    summary = dict(rows=[{k: r[k] for k in ("name", "sample_count", "mismatch_count", "total_seconds", "skipped")} for r in results],
                   oracle_imports=[ast.unparse(n) for n in ast.walk(oracle_tree) if isinstance(n, (ast.Import, ast.ImportFrom))],
                   source_sha256=before, source_unchanged_during_run=True)
    write(out / ("summary_" + args.section + ".json"), summary)
    return int(any(r["mismatch_count"] for r in results))


if __name__ == "__main__":
    raise SystemExit(main())
