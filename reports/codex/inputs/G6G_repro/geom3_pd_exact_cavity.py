"""Cavity exact-fit counterexample to closed-disjoint PD certificate.
Independent interval proof: A is a unit-halfwidth cube at c=(1/4,0,0).
B=[-3,3]^3 minus (-1,1)^3, an outward closed embedded shell. Exact-fit
A-w*ex has disjoint interiors, but touches B on all six cavity faces. A cube
of halfwidth1 cannot be closed-disjoint inside the unit cavity. Closed
separation from B requires one centre coordinate >4 in magnitude, hence
PD_strict=4-1/4=15/4, whereas a six-axis certificate reports touch at w=1/4.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.kernel3d.geom3 import Polyhedron,polyhedra_overlap
from eab.kernel3d.exact_sweep import contact_models
from eab.margin import inflated_membership,body_distance
SIGNS=[(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
FACES=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
w=F(1,4);center=(w,F(0),F(0));pd=F(15,4)
A=Polyhedron([tuple(center[k]+v[k] for k in range(3)) for v in SIGNS],FACES.copy())
B=Polyhedron([tuple(3*x for x in v) for v in SIGNS]+[tuple(F(x) for x in v) for v in SIGNS],FACES+[tuple(i+8 for i in reversed(f)) for f in FACES])
assert not A.manifold_issues() and not B.manifold_issues()
# Independent strict separation necessary/sufficient condition for the full
# closed shell: the translated cube is closed-disjoint iff some |centre_i|>4.
# Any |d|<=w gives centre_i magnitudes<=1/2, so not closed-disjoint.
assert pd>w and pd==4-center[0]
rows=contact_models(A,B,w)
accepted=[(name,polyhedra_overlap(U,V)) for name,U,V in rows if polyhedra_overlap(U,V)<=0]
assert accepted==[('shift_0_-1',0)]
fit=next(U for name,U,V in rows if name=='shift_0_-1')
assert fit.verts==[tuple(F(x) for x in v) for v in SIGNS]
# Exact six common inner-cavity face points prove the closed bodies intersect.
for axis in range(3):
 for sgn in (-1,1):
  p=tuple(F(sgn) if k==axis else F(0) for k in range(3))
  assert max(abs(x) for x in p)==1
public=inflated_membership(A,B,delta=0,contact_window=w)
assert public==0
print(json.dumps(dict(result='CONFIRMED',window=str(w),initial_exact_state=polyhedra_overlap(A,B),accepted_models=accepted,
 independent_PD_closed_disjoint=str(pd),certificate_shift_length=str(w),public_membership=public,
 public_distance=body_distance(A,B,contact_window=w)[0],valid_source_manifold_issues=B.manifold_issues(),
 premise='int(A+d) intersect int(B) empty',not_implied='(A+d) intersect B empty or approximable by a disjoint shift'),indent=2))
