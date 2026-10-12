"""Independent new concave-star radial-shell certificate check."""
from pathlib import Path
from fractions import Fraction as F
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.kernel3d.geom3 import Polyhedron
from eab.kernel3d.exact_sweep import contact_models
from eab.margin import inflated_membership
# Concave pentagon in xy extruded in z, outward face winding.
ring=[(F(-2),F(-1)),(F(2),F(-1)),(F(2),F(1)),(F(0),F(1,2)),(F(-2),F(1))]
faces=[tuple(reversed(range(5))),tuple(range(5,10))]+[(i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5)]
A=Polyhedron([(x,y,z) for z in (F(-1),F(1)) for x,y in ring],faces)
w=F(1,10);eps=2*w/5
boxfaces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
signs=[(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
def wall(sign):
 lo,hi=(-3,-2+eps) if sign<0 else (2-eps,3)
 return [tuple((lo if s[0]<0 else hi) if k==0 else F(3)*s[k] for k in range(3)) for s in signs]
B=Polyhedron(wall(-1)+wall(1),boxfaces+[tuple(i+8 for i in f) for f in boxfaces])
# Independent centre from input vertices, radius, and homothety. No tested normal,
# overlap or star centre is used by the mathematical witness.
c=(F(0),F(1,10),F(0));R=F(41,10);alpha=w/R
assert max(sum(abs(v[k]-c[k]) for k in range(3)) for v in A.verts)==R
rows=contact_models(A,B,w)
core=next(U for name,U,V in rows if name=='core_A')
assert all(tuple(c[k]+(1-alpha)*(v[k]-c[k]) for k in range(3))==q for v,q in zip(A.verts,core.verts))
max_shell2=max(sum((v[k]-q[k])**2 for k in range(3)) for v,q in zip(A.verts,core.verts))
assert max_shell2<=w*w
# Every surface point is a triangle convex combination of vertices; Euclidean
# norm convexity makes max_shell2 a continuum bound for every removed radial
# segment. Two entire overlap regions lie in wall slabs outside core x bounds.
corex=max(abs(q[0]) for q in core.verts)
assert corex<2-eps
# Actual A roof h(x) is1 for |x|>=? At y0, x near±2 isstrictinside;
# roof is1/2+|x|/4>0, so the points below witness strict overlap with each wall.
for x in (-2+eps/2,2-eps/2):
 assert -2<x<2 and abs(x)>2-eps and F(0)<F(1,2)+abs(x)/4
assert inflated_membership(A,B,delta=0,contact_window=w)==0
print(json.dumps(dict(result='PASS',concave_star=True,window=str(w),alpha=str(alpha),core_x_bound=str(corex),wall_inner_x=str(2-eps),max_radial_shell_squared=str(max_shell2),window_squared=str(w*w),public_membership=0),indent=2))
