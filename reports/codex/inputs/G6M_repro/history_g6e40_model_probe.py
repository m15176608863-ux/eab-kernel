from pathlib import Path
import sys,json
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel3d.geom3 import box,convex_hull_3d,sub
from eab.kernel3d.covers3 import local_facets3
from eab.kernel3d.g03 import facet_vote3,g0_convex3
A=box(half=(1,1,1));B=box(center=(.3,.2,3),half=(2,1.5,.7))
rounded=[sub(b,a) for a in A.verts for b in B.verts]
exact=[tuple(F(b[k])-F(a[k]) for k in range(3)) for a in A.verts for b in B.verts]
result=dict(id=40,rounded_distinct_from_exact=sum(tuple(map(F,r))!=q for r,q in zip(rounded,exact)),rounded_vote=facet_vote3(A,B,local_facets3(A,B,1e-12),convex_hull_3d(rounded),rounded),exact_vote=facet_vote3(A,B,local_facets3(A,B,1e-12),convex_hull_3d(exact),exact),public_g0_passed=g0_convex3(A,B,samples=0).passed)
assert result['exact_vote'][-1]==[] and result['public_g0_passed']
print(json.dumps(result,ensure_ascii=False,default=str,indent=2))
