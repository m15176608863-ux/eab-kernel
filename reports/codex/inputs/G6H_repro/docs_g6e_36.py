"""G6E #36 original geometry, with exact current-data G0 checks added."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from test_invariance_geom import Motion
from eab.kernel3d.geom3 import box,convex_hull_3d
from eab.margin import margin_contacts
from eab.kernel3d.covers3 import enumerate_covers3
from eab.kernel3d.g03 import g0_convex3
d=2.0**-10
B=box(half=(1.,1.,.5))
pts=[(0.,-1-d,.6),(2.,-1+d,.6),(2.,1+d,.6),(0.,1-d,.6)]
A=convex_hull_3d(pts+[(x,y,1.6) for x,y,_ in pts])
labels=lambda a,b:{(c.label(),c.strict) for c in enumerate_covers3(a,b,window=float('inf'),tol=1e-9) if c.in_extent}
base_c=labels(A,B);base_m={m.label for m in margin_contacts(A,B,delta=.2)}
M=Motion(7,0.,1.)
A1,B1=M.poly(A),M.poly(B)
rep0=g0_convex3(A,B,samples=20);rep1=g0_convex3(A1,B1,samples=20)
assert rep0.passed and rep1.passed
out={'g6e_id':36,'covers_lost':sorted(base_c-labels(A1,B1)),
     'margin_lost':sorted(base_m-{m.label for m in margin_contacts(A1,B1,delta=.2)}),
     'g0_original_data':rep0.passed,'g0_rounded_rotated_data':rep1.passed,
     'status':'原参数带缺陷已删除；逐数据精确门通过，边界标签不承诺浮点旋转完全不变'}
print(json.dumps(out,ensure_ascii=False,indent=2))
(ROOT/'review/agents/docs_gates/docs_g6e36.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
