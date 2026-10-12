"""Independent interval proof: nonpenetrating exact fit need not give closed-set PD.

No tested geometry primitive is used for the PD oracle.  A is an interval cube.
B is outer interval cube minus open inner interval cube.  A connected cube that
avoids B entirely must lie strictly inside the inner cube or entirely outside
the outer cube; the equal side lengths make the first alternative impossible.
"""
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from eab.kernel3d.geom3 import Polyhedron,box,polyhedra_overlap
from eab.kernel3d.exact_sweep import contact_models
from eab.margin import body_distance,inflated_membership

half=F(1,2);outer_half=F(2);w=F(1,8);center=(-w,F(0),F(0))
outer=box(half=(outer_half,)*3);inner=box(half=(half,)*3)
B=Polyhedron([tuple(map(float,p)) for p in (*outer.verts,*inner.verts)],list(outer.faces)+
             [tuple(i+8 for i in reversed(face)) for face in inner.faces])
A=box(center=center,half=(half,)*3)
A=Polyhedron([tuple(map(float,p)) for p in A.verts],A.faces)
shift=(w,F(0),F(0))
At=Polyhedron([tuple(F(v[i])+shift[i] for i in range(3)) for v in A.verts],A.faces)

# Independent model sanity and interval oracle, exact values only.
assert set(A.verts)==set(product(*[(center[i]-half,center[i]+half) for i in range(3)]))
assert set(At.verts)==set(product((-half,half),repeat=3))
assert set(B.verts[:8])==set(product((-outer_half,outer_half),repeat=3))
assert set(B.verts[8:])==set(product((-half,half),repeat=3))
strict_fit_possible=2*half < 2*half
assert not strict_fit_possible
# To be outside outer cube, at least one axis interval has a strict gap.
# inf(norm(delta)) is then the nearest axis threshold; the first x is left.
closed_set_pd=min(outer_half+half-abs(c) for c in center)
assert closed_set_pd==F(19,8) and closed_set_pd>w

initial=polyhedra_overlap(A,B,0)
at_fit=polyhedra_overlap(At,B,0)
default_distance=body_distance(A,B)
window_distance=body_distance(A,B,contact_window=w)
default_state=inflated_membership(A,B,delta=F(0))
window_state=inflated_membership(A,B,delta=F(0),contact_window=w)
assert initial==1 and at_fit==0
assert window_distance[0]==0 and window_state==0
out={'A_center':list(map(str,center)),'A_half':str(half),'B_outer_half':str(outer_half),
     'B_open_cavity_half':str(half),'contact_window':str(w),'initial_overlap':initial,
     'after_plus_x_window_state':at_fit,'default_distance':default_distance,
     'window_distance':window_distance,'default_inflated_state':default_state,
     'window_inflated_state':window_state,'closed_set_PD_independent':str(closed_set_pd),
     'strictly_disjoint_cavity_fit_possible':strict_fit_possible,
     'int_disjoint_escape_distance':str(w),
     'claim_refuted':'six-axis int-disjoint certificate does not imply 01 closed-set PD <= w'}
canon01=next(Path('D:/E(A, B)').glob('01*'))
canonlines=canon01.read_text(encoding='utf-8-sig').splitlines()
out['theory01_closed_set_PD_definition']=next((i+1,line) for i,line in enumerate(canonlines)
    if 'PD = inf' in line and '∩B = ∅' in line)
doclines=(ROOT/'docs/exact_3d_design.md').read_text(encoding='utf-8-sig').splitlines()
out['reviewed_six_axis_PD_claim']=next((i+1,line) for i,line in enumerate(doclines) if '六轴分支：存在' in line)
print(json.dumps(out,ensure_ascii=False,indent=2,default=str))
(ROOT/'review/notes/docs_tight_cavity_pd_output.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
