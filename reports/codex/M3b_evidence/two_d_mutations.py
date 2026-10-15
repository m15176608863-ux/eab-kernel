"""Reproduce five uncaught semantic-red M3b mutants in separate processes.

Only loaded Python function bodies are mutated. No source-hash gate is called
inside a child, and no production file is written by this script.
"""
from fractions import Fraction as F
import inspect
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eab.kernel2d import global_entrance as module
from eab.kernel2d import g0_oracle as oracle
from eab.kernel2d.global_entrance import GlobalEntrance2

SQUARE = ((0, 0), (1, 0), (1, 1), (0, 1))
L = ((0, 0), (3, 0), (3, 1), (1, 1), (1, 3), (0, 3))
FLAT = ((0, 0), (F(1, 3), 0), (1, 0), (1, 1), (0, 1))
POCKET = ((0, 0), (6, 0), (6, 2), (5, 2), (5, 1), (1, 1), (1, 5), (5, 5), (5, 4), (6, 4), (6, 6), (0, 6))
PLUG = ((1, 1), (5, 1), (5, 5), (1, 5))
EXPECTED = {
    "nonconvex_merge": "nonconvex union must not be filled by convex merging",
    "index_candidate_loss": "spatial index omitted a contributing cell",
    "strict_only_local_cover": "nonstrict local weak cover omits boundary",
    "drop_isolated_contact": "isolated contact vertex was regularized away",
    "compact_probe_event_loss": "compact side probe left its adjacent open face",
}


def mutate(target, name, old, new):
    value = getattr(target, name)
    source = textwrap.dedent(inspect.getsource(value.fget if isinstance(value, property) else value))
    if old not in source:
        raise RuntimeError("mutant target no longer exists")
    namespace = dict(module.__dict__)
    exec(compile(source.replace(old, new), "<M3b 2D internal mutant>", "exec"), namespace)
    setattr(target, name, namespace[name])


def child(kind):
    if kind == "nonconvex_merge":
        mutate(module, "_merge_convex_parts", "if _area2(hull) == _area2(a)+_area2(b):", "if True:")
        g = GlobalEntrance2(SQUARE, L, merge_convex=True)
        assert g.membership((F(3, 2), F(3, 2))) == -1, EXPECTED[kind]
    elif kind == "index_candidate_loss":
        mutate(GlobalEntrance2, "_candidate_cells", "in self._indexed_cells", "in self._indexed_cells[1:]")
        g = GlobalEntrance2(SQUARE, L, merge_convex=True)
        for p in ((-1, -1), (3, 0), (0, 3), (F(3, 2), F(3, 2)), (0, 0)):
            assert g.membership(p) == oracle.overlap(oracle.translate(g.A, p), g.B), EXPECTED[kind]
    elif kind == "strict_only_local_cover":
        mutate(GlobalEntrance2, "clipped_covers", " >= 0:", " > 0:")
        g = GlobalEntrance2(FLAT, SQUARE)
        local = [(p.start, p.end) for p in g.clipped_covers if p.exposed]
        for a, b in g.boundary:
            axis = 0 if a[0] != b[0] else 1
            intervals = []
            for p, q in local:
                if oracle.turn(a, b, p) == oracle.turn(a, b, q) == 0:
                    lo, hi = sorted(((p[axis]-a[axis])/(b[axis]-a[axis]), (q[axis]-a[axis])/(b[axis]-a[axis])))
                    if hi >= 0 and lo <= 1:
                        intervals.append((max(F(0), lo), min(F(1), hi)))
            end = F(0)
            for lo, hi in sorted(intervals):
                assert lo <= end, "nonstrict local weak cover leaves a boundary gap"
                end = max(end, hi)
            assert end == 1, EXPECTED[kind]
    elif kind == "drop_isolated_contact":
        mutate(GlobalEntrance2, "_contact_subdivision", "contact_points = {p for e in arranged for p in e if self.membership(p) == 0}",
               "contact_points = {p for e in contacts for p in e}")
        g = GlobalEntrance2(PLUG, POCKET, merge_convex=True, compact_subdivision=True)
        assert any(c.sample == (0, 0) and c.state == 0 for c in g.subdivision.vertices), EXPECTED[kind]
    elif kind == "compact_probe_event_loss":
        mutate(GlobalEntrance2, "side_probes", "for p, q in probe_edges:", "for p, q in self._contact_edges:")
        sys.path.insert(0, str(ROOT / "tests"))
        from test_m3b_2d import test_compact_side_probes_stay_in_adjacent_open_faces_before_every_event
        test_compact_side_probes_stay_in_adjacent_open_faces_before_every_event(0, "isolated_point")


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--child":
        child(sys.argv[2])
        return 0
    temp = ROOT / "reports/codex/M3b_evidence/tmp/two_d_mutants"
    temp.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, TEMP=str(temp), TMP=str(temp), PYTHONDONTWRITEBYTECODE="1")
    paths = (ROOT / "src/eab/kernel2d/global_entrance.py", ROOT / "tests/test_m3b_2d.py", Path(__file__))
    hashes = lambda: {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    before = hashes()
    rows = []
    for kind, assertion in EXPECTED.items():
        proc = subprocess.run([sys.executable, "-X", "utf8", __file__, "--child", kind], cwd=ROOT,
                              env=env, capture_output=True, text=True, encoding="utf-8")
        output = proc.stdout+proc.stderr
        log = Path(__file__).with_name("two_d_mutant_"+kind+".txt")
        log.write_text(output, encoding="utf-8")
        rows.append(dict(kind=kind, returncode=proc.returncode, expected_assertion=assertion,
                         semantic_red=proc.returncode != 0 and "AssertionError: "+assertion in output,
                         source_hash_gate="not_executed", traceback=log.name))
    assert before == hashes(), "mutation source changed during complete run"
    Path(__file__).with_name("two_d_mutations.json").write_text(json.dumps(dict(rows=rows, all_semantic_red=all(r["semantic_red"] for r in rows), source_sha256=before,
                                                                            source_unchanged_during_run=True), indent=2)+"\n", encoding="utf-8")
    return int(not all(r["semantic_red"] for r in rows))


if __name__ == "__main__":
    raise SystemExit(main())
