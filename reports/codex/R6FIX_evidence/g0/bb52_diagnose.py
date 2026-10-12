from pathlib import Path
import sys,json,math
from fractions import Fraction as F
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
import bb52_g0
from eab.kernel2d import g0,geom,covers as cv
blocks,_=bb52_g0.load_blocks(1)
pairs=bb52_g0.analyze(samples_per_pair=0)['g0_pairs']
real=cv.ve_cover
cv.ve_cover=lambda A,ia,B,jb,tol=0.,cone_tol=None:None if ia%7==3 else real(A,ia,B,jb,tol,cone_tol)
out={'exact_samples':0,'exact_failures':0,'rounded_samples':0,'rounded_failures':0,'examples':[]}
for bi,bj,xs in bb52_g0.g0_draws(pairs,60,0):
    A,B=blocks[bi]['poly'],blocks[bj]['poly']
    exact=g0.g0_distance_completeness(A,B,xs)
    with patch.object(g0.independent,'translate',geom.translate):
        rounded=g0.g0_distance_completeness(A,B,xs)
    out['exact_samples']+=exact.samples;out['exact_failures']+=len(exact.failures)
    out['rounded_samples']+=rounded.samples;out['rounded_failures']+=len(rounded.failures)
    for x,got,truth,arg in rounded.failures:
        aq=g0.independent.translate(A,x);ar=geom.translate(A,x)
        qcov=cv.enumerate_covers(aq,B,window=math.inf)
        rcov=cv.enumerate_covers(ar,B,window=math.inf)
        nearest=lambda cov:min(((math.hypot(c.point_a[0]-c.point_b[0],c.point_a[1]-c.point_b[1]),c.kind,c.a_index,c.b_index) for c in cov),default=None)
        out['examples'].append(dict(pair=[bi,bj],x=x,index=xs.index(x),got=got,truth=truth,arg=arg,exact_nearest=nearest(qcov),rounded_nearest=nearest(rcov),coordinate_deltas=[[str(F(r)-q) for r,q in zip(rp,qp)] for rp,qp in zip(ar,aq)]))
print(json.dumps(out,ensure_ascii=False,indent=2))
(ROOT/'reports/codex/R6FIX_evidence/g0/bb52_rounding_diagnosis.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
