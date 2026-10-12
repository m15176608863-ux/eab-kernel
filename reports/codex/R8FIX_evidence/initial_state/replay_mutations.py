"""Reintroduce R8 defects inside production call paths, without writing source."""
from pathlib import Path
import hashlib
import json
import math
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))

import pytest
from eab.kernel2d import covers, entrance, geom
from eab.kernel2d.exact import polygons_overlap_exact


def source_hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in ('src/eab/kernel2d/exact.py', 'src/eab/kernel2d/entrance.py',
                         'src/eab/kernel2d/covers.py', 'src/eab/kernel2d/geom.py')}


mode = sys.argv[1]
before = source_hashes()
if mode == 'entrance':
    entrance.entrance_membership_exact = polygons_overlap_exact
    target = 'test_tight_fit_interior_uses_shortest_exit_not_zero_time_entrance'
elif mode == 'membership':
    covers.entrance_membership_exact = polygons_overlap_exact
    target = 'test_nonconvex_membership_reports_topological_interior_at_tight_seam'
elif mode == 'cone_width':
    def premature(cone):
        lo, hi = cone
        return math.atan2(lo[0]*hi[1]-lo[1]*hi[0], lo[0]*hi[0]+lo[1]*hi[1])
    covers.cone_width = premature
    target = 'test_2d_cone_width'
elif mode == 'point_side':
    def premature(p, a, b):
        return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
    geom.point_side = premature
    target = 'test_2d_point_side'
else:
    raise ValueError(mode)

code = pytest.main(['-q', '-p', 'no:cacheprovider',
                    str(ROOT / 'tests/test_r8fix_initial_state.py'), '-k', target,
                    '--basetemp=' + str(ROOT / 'reports/codex/R8FIX_evidence/tmp' / ('replay_'+mode))])
after = source_hashes()
assert before == after, 'process-local mutation wrote production source'
metadata = dict(mode=mode, target=target, pytest_exit_code=code,
                source_hashes_before=before, source_hashes_after=after,
                restored_by='subprocess exit; no source file modified')
(Path(__file__).parent / ('mutation_'+mode+'.json')).write_text(
    json.dumps(metadata, indent=2)+'\n', encoding='utf-8')
raise SystemExit(code)
