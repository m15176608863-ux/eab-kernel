"""G6M exploratory check: 2D distance gate's output-resolution boundary.

Truth: a wide rectangle lies one exact unit above the higher of two Cartesian
towers. Deleting both higher-tower EV labels inside the cover producer leaves
only a tower whose exact clearance is 1+delta. This is not a production finding.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json
ROOT=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT/'src'))
import eab.kernel2d.covers as C
from eab.kernel2d.g0 import g0_distance_completeness

rows=[]
for delta in (F(1,2**60),F(1,2**45)):
    A=[(F(-1),F(2)),(F(4),F(2)),(F(4),F(3)),(F(-1),F(3))]
    B=[(F(0),F(0)),(F(3),F(0)),(F(3),1-delta),(F(2),1-delta),(F(2),F(1,2)),(F(1),F(1,2)),(F(1),F(1)),(F(0),F(1))]
    baseline=g0_distance_completeness(A,B,[(0,0)],tol=0,atol=0)
    original=C.ev_cover
    def omit_higher_tower(a,ka,b,ib,*args,**kwargs):
        if ib in (6,7):return None
        return original(a,ka,b,ib,*args,**kwargs)
    try:
        C.ev_cover=omit_higher_tower
        mutant=g0_distance_completeness(A,B,[(0,0)],tol=0,atol=0)
        actual=C.enumerate_covers(A,B,window=float('inf'))
        exact_sq=[]
        for cover in actual:
            p,q=cover.point_a,cover.point_b
            exact_sq.append(sum((F(p[k])-F(q[k]))**2 for k in range(2)))
        rows.append(dict(delta=str(delta),baseline_passed=baseline.passed,mutant_passed=mutant.passed,
                         mutant_failures=repr(mutant.failures),truth_squared='1',
                         remaining_minimum_squared=str(min(exact_sq)),
                         remaining_minimum_is_wrong=min(exact_sq)>1,
                         finite_outward_search_window='nextafter(correctly rounded true root, +inf)'))
    finally:C.ev_cover=original
out=dict(rows=rows,status='contract boundary only; minor/major not confirmed; static whole-repository gate not rerun on a copy for this runtime exploratory injection')
(ROOT/'review/geometry/g0_subulp_probe.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False,indent=2))
