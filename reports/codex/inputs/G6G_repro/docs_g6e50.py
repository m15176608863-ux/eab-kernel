"""G6E #50 retired ambiguity constants; current exact vote counterexample."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from eab.kernel3d import g03,covers3
from test_covers3_g0_vote2 import _random_pair
A,B=_random_pair(0)
source=(ROOT/'src/eab/kernel3d/g03.py').read_text(encoding='utf-8-sig')
old_patterns=['<= 4.0 * ptol','<= 4.0 * eps','eps=eps_used']
assert not any(p in source for p in old_patterns)
normal=g03.g0_convex3(A,B,samples=20)
real=covers3.cones_intersect_relint
try:
    covers3.cones_intersect_relint=lambda *args:True
    altered=g03.g0_convex3(A,B,samples=20)
finally:covers3.cones_intersect_relint=real
assert normal.passed and not altered.passed and altered.hull_vertex_mismatch==24 and altered.e_vertices_ambiguous==0
out={'g6e_id':50,'original_noise_patterns_present':{p:p in source for p in old_patterns},
     'baseline_passed':normal.passed,'wrong_local_vv_mutant_passed':altered.passed,
     'mutant_extreme_vertex_mismatch':altered.hull_vertex_mismatch,'mutant_ambiguity_exemptions':altered.e_vertices_ambiguous,
     'status':'原三种带宽已退休；当前多报极点必须红且不能豁免'}
print(json.dumps(out,ensure_ascii=False,indent=2))
(ROOT/'review/notes/docs_g6e50.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
