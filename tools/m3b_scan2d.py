"""WO-M3b: complete bb52 contact-skeleton subdivisions, no skipped samples.

The final subdivision is a labelled coarsening, NOT the triangle-pair overlay:
all original VE/EV segments are arranged, then strictly-overlap strata removed.
Every remaining vertex, edge midpoint, face interior, and exact edge-side probe
is checked against independent integer winding/intersection g0_oracle.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools")]
from eab.kernel2d.global_entrance import GlobalEntrance2
from eab.kernel2d import g0_oracle as oracle
import bb52_g0


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str)+"\n", encoding="utf-8")


def supporting_line(a, b):
    nx, ny = b[1]-a[1], a[0]-b[0]
    c = -nx*a[0]-ny*a[1]
    return (1, ny/nx, c/nx) if nx else (0, 1, c/ny)


def adjacent_face_index(subdivision):
    """Independent rational support-line key; no SUT geometry helper."""
    lines = {}
    for face in subdivision.faces:
        for a, b in zip(face.vertices, face.vertices[1:]+face.vertices[:1]):
            lines.setdefault(supporting_line(a, b), []).append((a, b, face))
    result = {}
    for edge in subdivision.edges:
        a, b = edge.vertices
        result[edge.vertices] = [face for c, d, face in lines[supporting_line(a, b)]
                                if oracle.on_segment(a, c, d) and oracle.on_segment(b, c, d)]
    return result


def probe_rows(model):
    subdivision = model.subdivision
    for name, cells in (("vertex", subdivision.vertices), ("edge_midpoint", subdivision.edges),
                        ("face_interior", subdivision.faces)):
        for cell in cells:
            yield name, cell.sample, cell.state, None
    neighbors = adjacent_face_index(subdivision)
    box = tuple((min(c.sample[k] for c in subdivision.vertices), max(c.sample[k] for c in subdivision.vertices)) for k in (0, 1))
    for edge in subdivision.edges:
        for point in model.side_probes(*edge.vertices):
            inside = any(all(oracle.turn(a, b, point) > 0 for a, b in
                         zip(face.vertices, face.vertices[1:]+face.vertices[:1])) for face in neighbors[edge.vertices])
            a, b = edge.vertices
            outside = any((a[k] == b[k] == lo and point[k] < lo) or
                          (a[k] == b[k] == hi and point[k] > hi) for k, (lo, hi) in enumerate(box))
            yield "exact_edge_side", point, None, inside or outside


def scan(pair, A, B, out):
    start = time.perf_counter()
    model = GlobalEntrance2(A, B, merge_convex=True, compact_subdivision=True)
    made = time.perf_counter()
    write(out / "progress.json", dict(pair=pair, stage="arranging_all_contact_segments", completed=False))
    sub = model.subdivision
    arranged = time.perf_counter()
    counts, states, mismatches = {}, {"-1": 0, "0": 0, "1": 0}, []
    probe_hash = hashlib.sha256()
    adjacent_checked = 0
    for n, (kind, point, stored, adjacent_ok) in enumerate(probe_rows(model), 1):
        moved = oracle.translate(model.A, point)
        expected = oracle.overlap(moved, model.B)
        topology = (0 if oracle.boundary_has_exterior(moved, model.B) else 1) if expected == 0 else expected
        got, got_topology = model.membership(point), model.topology(point)
        counts[kind] = counts.get(kind, 0)+1
        states[str(expected)] += 1
        row = dict(kind=kind, point=point, expected=expected, actual=got,
                   expected_topology=topology, actual_topology=got_topology, stored=stored,
                   adjacent_open_face_or_exterior=adjacent_ok)
        adjacent_checked += adjacent_ok is not None
        probe_hash.update((json.dumps(row, sort_keys=True, default=str)+"\n").encode("utf-8"))
        if got != expected or got_topology != topology or (stored is not None and stored != expected) or adjacent_ok is False:
            mismatches.append(row)
        if n % 100 == 0:
            write(out / "progress.json", dict(pair=pair, stage="oracle_probes", probes_done=n,
                                               mismatches=len(mismatches), completed=False))
    assert len(sub.vertices)-len(sub.edges)+len(sub.faces) == 1, "labelled rectangle subdivision Euler mismatch"
    result = dict(pair=pair, input_vertex_counts=[len(model.A), len(model.B)],
                  original_triangle_pairs=(len(model.A)-2)*(len(model.B)-2),
                  merged_body_parts=[len(model.parts_a), len(model.parts_b)], convex_pairs=len(model.cells),
                  subdivision_kind="complete_contact_skeleton_vertical_coarsening_not_triangle_pair_overlay",
                  dimensions={"0": len(sub.vertices), "1": len(sub.edges), "2": len(sub.faces)},
                  probes_by_kind=counts, sample_count=sum(counts.values()), oracle_states=states,
                  adjacent_open_face_checks=adjacent_checked,
                  mismatch_count=len(mismatches), mismatches=mismatches, skipped=0,
                  probe_sha256=probe_hash.hexdigest(), construction_seconds=made-start,
                  arrangement_seconds=arranged-made, total_seconds=time.perf_counter()-start)
    write(out / (f"pair_{pair[0]}_{pair[1]}.json"), result)
    print(json.dumps({k: result[k] for k in ("pair", "sample_count", "mismatch_count", "total_seconds")}), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "reports/codex/M3b_evidence/two_d_bb52")
    args = parser.parse_args()
    out = args.out.resolve()
    if not out.is_relative_to(ROOT / "reports/codex/M3b_evidence"):
        parser.error("output must stay inside this worktree's M3b evidence directory")
    out.mkdir(parents=True, exist_ok=True)
    temp = ROOT / "reports/codex/M3b_evidence/tmp/two_d_scan"
    temp.mkdir(parents=True, exist_ok=True)
    os.environ.update(TEMP=str(temp), TMP=str(temp), PYTHONDONTWRITEBYTECODE="1")
    sources = [Path(__file__), ROOT / "src/eab/kernel2d/global_entrance.py", ROOT / "src/eab/kernel2d/g0_oracle.py",
               ROOT / "tools/bb52_g0.py", ROOT / "fixtures/bdda_df/studio_20260712/bdda_debug_verts.csv",
               ROOT / "reports/bb52_g1_g0.json"]
    hashes = lambda: {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    before = hashes()
    blocks, _ = bb52_g0.load_blocks(1)
    pairs = json.loads(sources[-1].read_text(encoding="utf-8"))["g0_pairs"]
    assert len(pairs) == 21 and len({tuple(p) for p in pairs}) == 21
    results = []
    for pair in pairs:
        results.append(scan(pair, blocks[pair[0]]["poly"], blocks[pair[1]]["poly"], out))
    assert before == hashes(), "sources changed during scan; discard this complete run and rerun"
    tree = ast.parse((ROOT / "src/eab/kernel2d/g0_oracle.py").read_text(encoding="utf-8-sig"))
    summary = dict(pair_count=len(results), sample_count=sum(r["sample_count"] for r in results),
                   mismatch_count=sum(r["mismatch_count"] for r in results), skipped=0,
                   total_seconds=sum(r["total_seconds"] for r in results), source_sha256=before,
                   source_unchanged_during_run=True, input_semantics="exact rational values of original binary64 fixture loader",
                   oracle_imports=[ast.unparse(n) for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))],
                   rows=results, status="COMPLETE" if not any(r["mismatch_count"] for r in results) else "FAILED")
    write(out / "summary.json", summary)
    write(out / "progress.json", dict(completed=True, pair_count=21, sample_count=summary["sample_count"]))
    return int(summary["mismatch_count"] > 0)


if __name__ == "__main__":
    raise SystemExit(main())
