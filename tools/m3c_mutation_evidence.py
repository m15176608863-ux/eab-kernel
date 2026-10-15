"""Uncaught semantic reds from real internal M3c mutations, then fresh greens.

Only the selected semantic check is called; source-hash/static/frozen-summary
tripwires are deliberately not executed. Production files are never edited.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import time

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/codex/M3c_evidence"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests"), str(ROOT)]

CASES = {}
for family in ("tight_pin", "cavity", "separated_slabs"):
    CASES["merge_line_"+family] = "closed-E contact seam is not an interval endpoint"
    CASES["merge_contact_"+family] = "g03 closed-E exit must cross the internal contact seam"
    CASES["merge_overlap_"+family] = "g03 closed-E exit must cross the internal contact seam"
CASES.update(dict(
    nonaxial_singleton="nonaxial singleton tangency survives closed AABB pruning",
    start_right="g03 boundary-start zero belongs to the closed interval",
    start_left="g03 boundary-start zero belongs to the closed interval",
    order_side_probes="compact side_probes fields depend on public call order",
    order_clipped_covers="compact clipped_covers fields depend on public call order",
    source_planes_sides="independent adjacent-open-cell side probe crossed a support event",
    source_planes_coverage="independent ray boundary point has an exposed polygon",
    source_planes_exit="independent Cartesian-union shortest closed exit",
    strict_ee="T3L closed-only EE covers the independent exposed-face interior",
    noncoplanar_clip="clipped local cover must be a nondegenerate planar polygon"))


def replace(module, function, before, after, count=1):
    source = textwrap.dedent(inspect.getsource(function))
    assert source.count(before) == count, "the requested internal mutation site must be unique/count-checked"
    namespace = dict(vars(module))
    exec(compile(source.replace(before, after), "<M3c real internal mutation>", "exec"), namespace)
    return namespace[function.__name__]


def child(case, mutant):
    if case.startswith("merge_") or case in ("nonaxial_singleton", "start_left", "start_right"):
        import test_m3c_sections as t
        if case.startswith("merge_"):
            _, mode, family = case.split("_", 2)
            if mutant:
                t.G._merge = replace(t.G, t.G._merge, "lo <= result[-1][1]", "lo < result[-1][1]")
            if mode == "line":
                t._assert_seam_line(family)
            else:
                base = (0, 0, 0) if mode == "contact" else (t.F(-1, 8),)*3
                t.test_g03_closed_E_exit_crosses_internal_contact_seams(family, base)
        elif case == "nonaxial_singleton":
            if mutant:
                t.G._line_candidate = replace(t.G, t.G._line_candidate, "if lower > upper:", "if lower >= upper:")
            t._assert_nonaxial_singleton_tangencies()
        else:
            right = case == "start_right"
            if mutant:
                t.g03.g0_distance_completeness3 = replace(t.g03, t.g03.g0_distance_completeness3,
                    "lo <= 0 <= hi", "lo <= 0 < hi" if right else "lo < 0 <= hi")
            t.test_g03_boundary_face_edge_vertex_start_uses_closed_zero_membership((1, 0, 0) if right else (-1, 0, 0))
    elif case.startswith("order_"):
        import test_m3c_determinism as t
        if mutant:
            t.GlobalEntrance2.side_probes = replace(t.module, t.GlobalEntrance2.side_probes,
                "    if self._compact_subdivision and self._subdivision_cache is None:\n        self.subdivision\n", "")
        t._assert_call_order_fields(0, case[len("order_"):])
    else:
        import test_m3c_boundary3d as t
        if case.startswith("source_planes_"):
            fixture = t._fixture("narrow_pocket")
            model = t.G.global_entrance(*fixture[:2])
            if mutant:
                t.B.explicit_boundary = replace(t.B, t.B.explicit_boundary,
                    "_sides(model, piece, normal, planes)",
                    "_sides(model, piece, normal, tuple(_plane(n, h) for i, j in sources "
                    "for n, lo, hi in G._pair_slabs(model.parts_a[i], model.parts_b[j]) for h in (lo, hi)))")
            t._semantic_checks(t.B.explicit_boundary(model), fixture, case[len("source_planes_"):])
        elif case == "strict_ee":
            if mutant:
                t.B._edge_closed = replace(t.B, t.B._edge_closed, ">= 0", "> 0", count=2)
            t._closed_ee_case(t.F(1), t.O.IDENTITY, (t.F(0),)*3)
        else:
            cube = t._box((-1,)*3, (1,)*3)
            boundary = t.B.explicit_boundary(t.G.global_entrance(cube, cube))
            candidates = t.B.local_cover_candidates(cube, cube)
            if mutant:
                t.B.clip_local_covers = replace(t.B, t.B.clip_local_covers,
                    "            if any(G._dot(n, G._sub(p, patch.polygon[0])) for p in candidate.polygon):\n"
                    "                continue\n", "")
            t.assert_clipped_polygons_nondegenerate(t.B.clip_local_covers(boundary, candidates))
    print("M3C_SEMANTIC_GREEN", case)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=tuple(CASES))
    parser.add_argument("--mutant", action="store_true")
    parser.add_argument("--name", default="mutations")
    args = parser.parse_args()
    if args.case:
        child(args.case, args.mutant)
        return 0
    if Path(args.name).name != args.name or args.name in (".", ".."):
        parser.error("one new output directory name required")
    out = EVIDENCE / args.name
    out.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1",
               TEMP=str(EVIDENCE / "tmp"), TMP=str(EVIDENCE / "tmp"))
    paths = sorted((ROOT/"src").rglob("*.py"))
    before = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    rows = []
    start = time.perf_counter()
    for case, assertion in CASES.items():
        stages = []
        for stage in ("before", "mutant", "restored"):
            command = [sys.executable, "-X", "utf8", str(Path(__file__).resolve()), "--case", case]
            if stage == "mutant":
                command.append("--mutant")
            result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, encoding="utf-8", errors="replace")
            content = result.stdout+result.stderr
            (out / (case+"_"+stage+".txt")).write_text(content, encoding="utf-8")
            lines = content.splitlines()
            last = lines[-1] if lines else ""
            good = (result.returncode != 0 and last.startswith("AssertionError:") and assertion in last) if stage == "mutant" else (result.returncode == 0 and last == "M3C_SEMANTIC_GREEN "+case)
            stages.append(dict(stage=stage, exit_code=result.returncode, last_line=last, expected=good))
        rows.append(dict(case=case, semantic_assertion=assertion, stages=stages))
        (out / "progress.json").write_text(json.dumps(dict(complete=False, completed=len(rows), rows=rows), ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        print(case, "EXPECTED" if all(s["expected"] for s in stages) else "ERROR", flush=True)
    after = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    good = before == after and all(s["expected"] for r in rows for s in r["stages"])
    result = dict(status="GREEN" if good else "RED", complete=True, count=len(rows), rows=rows,
        source_files_unchanged=before == after, source_hash_tripwires="NOT EXECUTED: direct semantic entry only",
        seconds=time.perf_counter()-start)
    for name in ("summary.json", "progress.json"):
        (out / name).write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
