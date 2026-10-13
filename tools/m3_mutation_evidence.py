"""Compile production mutations in isolated processes and preserve real red logs.

No source is overwritten. The process mutates the implementation before the
guard calls it; the parent requires pytest exit 1 and the intended assertion.
"""
from __future__ import annotations

import argparse
import inspect
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import textwrap

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/codex/M3_evidence/mutations"
CASES = {
    "remove_clipping": "cover clipping exposure mismatch",
    "label_inversion": "body label mismatch",
    "open_endpoint": "isolated closed contact",
    "missing_piece": "body label mismatch",
    "label_propagation": "topological label mismatch",
    "local_exit": "global exit cannot return the local zero-gap seam",
    "open_union_join": "open interval endpoint must remain physical contact",
    "missing_piece3d": "global3d physical-state zero mismatch",
    "local_escape": "global root not local cover event",
}


def replace_function(module, owner, name, old, new):
    function = getattr(owner, name)
    if isinstance(function, property):
        function = function.fget
    source = textwrap.dedent(inspect.getsource(function))
    assert source.count(old) == 1, (name, old)
    namespace = dict(vars(module))
    exec(compile(source.replace(old, new, 1), "<M3 actual internal mutant>", "exec"), namespace)
    setattr(owner, name, namespace[name])


def child(kind, guard):
    sys.path[:0] = [str(ROOT/"src"), str(ROOT/"tests"), str(ROOT/"tools")]
    import pytest
    from eab.kernel2d import global_entrance as G2
    from eab.kernel3d import global_entrance as G3, interlock
    cls = G2.GlobalEntrance2
    replacements = {
        "remove_clipping": (G2, cls, "clipped_covers", "exposed = (states[0] >= 0) != (states[1] >= 0)", "exposed = True"),
        "label_inversion": (G2, cls, "membership", "return 1", "return -1"),
        "open_endpoint": (G2, cls, "ray_intervals", "low < high if strict else low <= high", "low < high"),
        "missing_piece": (G2, cls, "__init__", "for pa in self.parts_a for pb in self.parts_b)", "for pa in self.parts_a for pb in self.parts_b[:1])"),
        "label_propagation": (G2, cls, "topology", "if state != 0:", "if state >= -1:"),
        "local_exit": (G2, cls, "_nearest_boundary", "for a, b in self.boundary:", "for a, b in ((p.start, p.end) for p in self.clipped_covers):"),
        "open_union_join": (G3, G3, "_merge", "lo < result[-1][1] if strict", "lo <= result[-1][1] if strict"),
        "missing_piece3d": (G3, G3, "_decompose", "return parts\n", "return parts[:-1]\n"),
        "local_escape": (interlock, interlock, "_exact_escape_cached", "state=_nonpenetrating_at(A,B,offset,height)", "state=0  # mutant: trust local event"),
    }
    replace_function(*replacements[kind])
    os.environ["M3_MUTANT"] = kind
    return pytest.main([str(guard), "-q", "-p", "no:cacheprovider"])


GUARD = '''from fractions import Fraction as F
import os
import test_m3_global2d as T2
import test_m3_global3d as T3
from eab.kernel2d.global_entrance import GlobalEntrance2
from eab.kernel3d import global_entrance as G3

def test_mutated_implementation_must_preserve_the_specific_contract():
    kind = os.environ["M3_MUTANT"]
    if kind == "remove_clipping":
        T2.test_clipped_covers_are_exactly_boundary_and_cover_oracle_ray_exits("tight", T2.PIN, T2.U)
    elif kind == "label_inversion":
        T2._assert_states(GlobalEntrance2(T2.SQUARE, T2.THIN_L), [(0, 0)])
    elif kind == "missing_piece":
        T2._assert_states(GlobalEntrance2(T2.SQUARE, T2.THIN_L), [(0, 2)])
    elif kind == "label_propagation":
        T2._assert_states(GlobalEntrance2(T2.PIN, T2.U), [(0, 0)])
    elif kind == "open_endpoint":
        assert GlobalEntrance2(T2.SQUARE, T2.SQUARE).first_entrance((-2, 0), (1, 1)) is not None, "isolated closed contact"
    elif kind == "local_exit":
        T2.test_global_shortest_exit_distinguishes_tight_contact_seam()
    elif kind == "open_union_join":
        T3._assert_join_endpoint()
    elif kind == "missing_piece3d":
        _, A, B = T3._families()[0]
        T3._assert_states(G3.global_entrance(A, B), A, B, [(F(0), F(2), F(0))])
    elif kind == "local_escape":
        A, B = T3._wall(16)
        expected = T3.earliest_wall_escape(A, B)
        assert T3.I.escape_height_covers(A, B, (0, 0, 0)).exact_height == expected, "global root not local cover event"
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", choices=CASES)
    parser.add_argument("--guard", type=Path)
    args = parser.parse_args()
    if args.child:
        return child(args.child, args.guard)
    OUT.mkdir(parents=True, exist_ok=True)
    temp = ROOT / "reports/codex/M3_evidence/tmp/mutation_guards"
    temp.mkdir(parents=True, exist_ok=True)
    guard = temp / "test_m3_external_mutant_guards.py"
    guard.write_text(GUARD, encoding="utf-8")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", TEMP=str(temp), TMP=str(temp))
    rows = []
    for kind, assertion in CASES.items():
        result = subprocess.run([sys.executable, "-X", "utf8", str(Path(__file__)), "--child", kind, "--guard", str(guard)],
                                cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = result.stdout.decode("utf-8", errors="replace")
        (OUT/(kind+".txt")).write_text(output, encoding="utf-8")
        actual_assertions = re.findall(r"^E\s+AssertionError:.*$", output, re.MULTILINE)
        row = dict(mutant=kind, exit_code=result.returncode, expected_assertion=assertion,
                   actual_assertion_lines=actual_assertions,
                   killed_at_expected_assertion=result.returncode == 1 and any(assertion in line for line in actual_assertions),
                   last_line=output.splitlines()[-1])
        rows.append(row)
        print(kind, row["killed_at_expected_assertion"], row["last_line"], flush=True)
    (OUT/"summary.json").write_text(json.dumps(rows, indent=2)+"\n", encoding="utf-8")
    return int(not all(r["killed_at_expected_assertion"] for r in rows))


if __name__ == "__main__":
    raise SystemExit(main())
