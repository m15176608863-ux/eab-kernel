"""Equivalent replays of eight G6E limit/self-check classes and one 2D hull class.
Original keys are file:line in reports/codex/inputs/g6e_findings_raw.json.
"""
from pathlib import Path
from fractions import Fraction as F
import importlib.util,sys,json,math,copy
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import eab.limit as L
import eab.limit_multi as M
from eab.kernel2d.geom import convex_hull
import test_limit_exact_selfcheck as T
rows=[]
n=tuple(v/math.sqrt(3) for v in (1.,1.,1.))
try:L._tangents(n,3,(1.,1.,1.+2**-50))
except ValueError:rows.append({'original_key':'src/eab/limit.py:206','result':'ValueError; near-parallel tangent rejected'})
else:raise AssertionError('old unsafe tangent still accepted')
for k in (3,9,30,100):
 for case in ('small_mu','small_cohesion','far','tall'):T.test_exact_single_static_and_gap_reject_arbitrary_rational_alpha_error(k,case)
rows.append({'original_key':'src/eab/limit.py:732','result':'16 exact-alpha corruptions rejected (1e-3..1e-100)'})
for k in (3,9,30,100):T.test_exact_admissibility_has_no_tall_body_or_other_body_speed_tolerance(k)
rows.append({'original_key':'src/eab/limit_multi.py:147','result':'4 exact penetrations rejected despite unrelated body speed 1e20'})
for k in (3,9,30,100):
 for W in (10.,1e6,1e20):T.test_multi_exact_duality_rejects_statically_feasible_suboptimal_interpolation(k,W)
rows.append({'original_key':'src/eab/limit_multi.py:348','result':'12 statically feasible suboptimal interpolations rejected; exact gap>0'})
for v in (1e-6,1e-8):
 for D in (1e2,1e4,1e6):T.test_multi_resolvability_uses_only_each_bodys_local_frame(v,D)
rows.append({'original_key':'src/eab/limit_multi.py:177','result':'6 unrelated-far-body additions preserve status/alpha/U'})
for loaded in (0,1):
 for branch in ('infeasible','finite'):T.test_multi_unbounded_screen_covers_both_rejection_branches_and_nonzero_body(loaded,branch)
rows.append({'original_key':'tests/test_limit_multi.py:268','result':'4 unbounded-neighbour regimes report nearby_infeasible/unresolved without changing exact unbounded'})
T.test_single_unloaded_far_contact_cannot_hide_a_pure_couple_residual()
rows.append({'original_key':'src/eab/limit.py:729','result':'unloaded contact at 1e6 cannot hide 0.999 capacity corruption'})
# exact small perturbations in both single and multi mechanisms use the same
# actual checker path old test had allowed in 1e-4..3e-7 cases.
for k in (3,9,30,100):T.test_exact_admissibility_has_no_tall_body_or_other_body_speed_tolerance(k)
rows.append({'original_key':'tests/test_limit_multi.py:238','result':'equivalent tiny rational mechanism probes reject through admissibility and self-check'})
points=[(0.,0.),(1e-15,-1e-3),(1.,0.),(1.,1.),(0.,1.)];h=convex_hull(points,tol=1e-12)
assert (1e-15,-1e-3) in h
rows.append({'original_key':'src/eab/kernel2d/geom.py:434','result':'true extreme (1e-15,-1e-3) retained; tol does not pop'})
print(json.dumps({'replayed_original_keys':len(rows),'rows':rows,'no_old_failure_confirmed':True},ensure_ascii=False,indent=2))
