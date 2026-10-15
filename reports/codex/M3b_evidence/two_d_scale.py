"""Measure the largest bb52 unreduced overlay without expanding all slabs."""
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools")]
import bb52_g0
from eab.kernel2d import global_entrance as module

start = time.perf_counter()
blocks, _ = bb52_g0.load_blocks(1)
g = module.GlobalEntrance2(blocks[1]["poly"], blocks[2]["poly"], merge_convex=True)
made = time.perf_counter()
segments = module._split_segments(g.cell_edges)
done = time.perf_counter()
xs = len({p[0] for e in segments for p in e})
result = dict(pair=[1, 2], original_triangle_pairs=1344, certified_merged_pairs=len(g.cells),
              input_cell_edges=len(g.cell_edges), unreduced_atomic_edges=len(segments),
              unreduced_x_events=xs, naive_vertical_edge_event_visits=(xs-1)*len(g.cell_edges),
              construction_seconds=made-start, splitting_seconds=done-made,
              full_vertical_overlay_expanded=False,
              reason="Equivalent complete contact-skeleton subdivision is measured separately; do not materialize an unnecessary billion-visit overlay.",
              source_sha256=hashlib.sha256((ROOT / "src/eab/kernel2d/global_entrance.py").read_bytes()).hexdigest())
Path(__file__).with_suffix(".json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
