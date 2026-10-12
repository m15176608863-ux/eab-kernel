"""New frozen exact-jet arithmetic independently checked by closed forms.
At t=3/4, sqrt(1+t²)=5/4. Exact derivatives of normalized (t,0,-1),
(0,-t,1),(t,1,0) are rational constants, not production normals/Dual math.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.dual import Dual
from eab.kernel3d.geom3 import Polyhedron
from eab.kernel3d.frozen import ee_normal_generic,face_normal_generic,frozen_normal
count=0;t=F(3,4)
def check(n,values,derivs):
 global count
 for c,v,d in zip(n,values,derivs):
  assert c.v==float(v),(c.v,v)
  assert c.e==(float(d),float(-2*d)),(c.e,d)
 count+=1
for ae,be in [(-600,-600),(-600,600),(600,-600),(600,600),(0,0)]:
 a,b=2.**ae,2.**be
 A=Polyhedron([(0,0,0),(a,0,Dual(float(t)*a,(a,-2*a)))],[])
 B=Polyhedron([(0,0,0),(0,b,0)],[])
 check(ee_normal_generic(A,(0,1),B,(0,1)),(F(3,5),0,-F(4,5)),(F(64,125),0,F(48,125)))
 P=Polyhedron([(0,0,0),(a,0,0),(0,b,Dual(float(t)*b,(b,-2*b)))],[(0,1,2)])
 check(face_normal_generic(P,0),(0,-F(3,5),F(4,5)),(0,-F(64,125),-F(48,125)))
 A=Polyhedron([(Dual(float(t)*a,(a,-2*a)),a,0)],[]);B=Polyhedron([(0,0,0)],[])
 check(frozen_normal(A,B,('VV3',('vertex',0),('vertex',0))),(F(3,5),F(4,5),0),(F(64,125),-F(48,125),0))
 # A vertex over the x line: affine z derivative produces a perpendicular
 # y-z normal jet. Both 0-primal nonzero-derivative components must survive.
 A=Polyhedron([(a/2,b,Dual(0,(b,-2*b)))],[])
 B=Polyhedron([(0,0,0),(a,0,0)],[])
 check(frozen_normal(A,B,('VE3',('vertex',0),('edge',0,1))),(0,1,0),(0,0,1))
print(json.dumps(dict(result='PASS',new_independent_frozen_jet_cases=count,multi_channel_width=2,exponent_pairs=[[-600,-600],[-600,600],[600,-600],[600,600],[0,0]]),indent=2))
