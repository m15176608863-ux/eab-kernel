"""Small read-only replay of verified returned constructions, not a G0 oracle."""
from pathlib import Path
import hashlib
import json
import math
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools")]
from osteomorphic import interlocking_pair
from eab.kernel3d.geom3 import Polyhedron, polyhedra_overlap
from eab.kernel3d.interlock import _candidates, escape_height_covers
from eab.margin import effective_geom_tol


def transform(poly, scale, translation, angle):
    c, s = math.cos(angle), math.sin(angle)
    def point(p):
        x, y, z = (scale * a for a in p)
        return (c*x-s*y+0.6*translation, s*x+c*y-0.48*translation,
                z+0.64*translation)
    return Polyhedron([point(p) for p in poly.verts], list(poly.faces))


start = time.perf_counter()
rows = []
for name, lx, scale, translation, angle, offset in (
    ("failed_steep_positive_side", 0.2, 1., 0., 0., (0.16+1e-11, 0., 0.)),
    ("engineering_general_offset", 2., 1e-3, 1e5, 0.7, (0.23, 0.07, 0.)),
    ("engineering_zero_offset", 2., 1e-3, 1e5, 0.7, (0., 0., 0.)),
    ("origin_zero_offset", 2., 1., 0., 0., (0., 0., 0.)),
):
    A, B = interlocking_pair(nx=5, ny=2, amp=0.3, phase=1.0, lx=lx)
    A, B = (transform(p, scale, translation, angle) for p in (A, B))
    c, s = math.cos(angle), math.sin(angle)
    x, y, z = (scale * a for a in offset)
    off = (c*x-s*y, s*x+c*y, z)
    At = A.translated(off)
    cands, r = _candidates(A, B, off, 1e-9, effective_geom_tol(At, B))
    initial = polyhedra_overlap(At, B, 0.0)
    sol = escape_height_covers(A, B, off)
    returned = A.translated((off[0], off[1], off[2]+sol.height))
    strict_state = polyhedra_overlap(returned, B, 0.0)
    assert strict_state != 1, (name, sol, strict_state)
    nominal = [(z, lab, nz) for z, lab, nz, _ in cands if lab == sol.cover_label]
    rows.append(dict(name=name, scale=scale, translation=translation, angle=angle,
        offset=off, initial_strict_state=initial, height=sol.height,
        cover_label=sol.cover_label, tied_count=len(sol.tied_labels),
        actual_returned_state=strict_state, rounding_floor=r,
        height_is_raw_candidate=any(z == sol.height for z, *_ in cands),
        winner_nominal_candidates=nominal))

out = dict(description="Construction-safety replay only; shares production relation, not independent G0.",
    interlock_sha256=hashlib.sha256((ROOT / "src/eab/kernel3d/interlock.py").read_bytes()).hexdigest(),
    elapsed_seconds=time.perf_counter()-start, rows=rows)
dest = Path(__file__).with_name("interlock_bridge_audit.json")
dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=2))
