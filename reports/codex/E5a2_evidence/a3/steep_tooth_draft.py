"""Stage and exercise a stronger test entirely in memory; never edit live tests."""
from pathlib import Path
import hashlib
import json
import sys
import time
import types

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools"), str(ROOT / "tests")]
path = ROOT / "tests/test_interlock_sensitivity.py"
old = path.read_text(encoding="utf-8")
anchor = '            own = sl if side < 0 else sr\n'
helper = '''def _steep_two_branches_in_report_band(d, s, center, truth):
    """Independent source-feature oracle, not production covers/windows.

    The two analytic profile branches are upper bottom faces i=0 and i=1
    against lower endpoint i=nx, j=0: FV(10,30) and FV(12,30).
    The test oracle uses cyclic Fraction Newell, its own vertex-cone and
    face-extent predicates, and explicit L/r/gtol formulas.  Normal proximity
    alone is insufficient: each branch must also be in its own extent band.
    """
    import e5a_escape_oracle as O
    A, B = interlocking_pair(nx=5, ny=2, amp=0.3*s, phase=1.0,
                            lx=0.2*s, ly=s, lz=s, center=center)
    av = O.move(tuple(A.verts), (s*d, 0.0, 0.0))
    bv, af, bf = tuple(B.verts), tuple(A.faces), tuple(B.faces)
    a, b = O.model(av, af), O.model(bv, bf)
    band, _ = O.windows(av, bv)
    for fi in (10, 12):
        label = ("FV", ("face", fi), ("vertex", 30))
        record = O.facet(a, b, label)
        if record is None or record[0][2] <= 0:
            return False
        nz, gap = record[0][2], record[1]
        z = -gap/nz
        # Strict interior of the normal band; no assertion about its edge.
        if z <= 0 or abs(z-truth)*nz >= 0.5*band:
            return False
        az = O.model(O.move(av, (0.0, 0.0, z)), af)
        at_root = O.facet(az, b, label, extent=band)
        if at_root is None or not at_root[2]:
            return False
    return True


'''
added = '''            if _steep_two_branches_in_report_band(d, s, c, truth):
                assert not r["differentiable_by"]["tan_psi"], (
                    side * e, r["derivative_range"]["tan_psi"], "带内漏支")
'''
assert old.count(anchor) == 1
new = old.replace(anchor, anchor + added)
new = new.replace('def _steep_check(s, t):', helper + 'def _steep_check(s, t):')
new = new.replace('with pytest.raises(AssertionError, match="另一支"):',
                  'with pytest.raises(AssertionError, match="带内漏支"):')
namespace = types.ModuleType("steep_tooth_in_memory_draft")
namespace.__file__ = str(path)
exec(compile(new, str(path) + "::draft", "exec"), namespace.__dict__)

import pytest
import eab.kernel3d.interlock as I

started = time.perf_counter()
rows = []
for scale, translation in ((1., 0.), (1e-3, 0.), (1e3, 1e5), (1., 1e5)):
    namespace._steep_check(scale, translation)
    rows.append(dict(scale=scale, translation=translation, all_18_original_cells="passed"))

original = I._escape_solution
def vertical_window(z, nz, cands, gtol, r):
    pos = [c for c in cands if c[0] > 0.0]
    lab = next(c[1] for c in pos if c[0] == z)
    tied = tuple(c[1] for c in pos if abs(c[0]-z) <= 1e-9*max(1.0, abs(z)) and c[1] != lab)
    return I.EscapeSolution(z, lab, len(cands), (lab,)+tied)

try:
    I._escape_solution = vertical_window
    try:
        namespace._steep_check(1., 0.)
    except AssertionError as exc:
        message = str(exc)
        assert "带内漏支" in message, message
    else:
        raise AssertionError("the stronger gate did not kill the internal vertical-window mutation")
finally:
    I._escape_solution = original

out = dict(live_test_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
           staged_helper=helper, staged_assertion=added, original_grids_retained=rows,
           mutation="same _escape_solution internal vertical-window replacement",
           target_assertion_message=message, elapsed_seconds=time.perf_counter()-started)
dest = Path(__file__).with_name("steep_tooth_draft.json")
dest.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(out, indent=2, ensure_ascii=False))
