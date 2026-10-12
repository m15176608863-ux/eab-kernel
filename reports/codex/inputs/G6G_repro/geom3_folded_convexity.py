"""Independent midpoint nonconvexity witness in a valid folded roof surface."""
from pathlib import Path
from fractions import Fraction as F
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.kernel3d.geom3 import Polyhedron,exact_surface,point_in_polyhedron
faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
verts=[(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,0),(1,1,1),(-1,1,0)]
# Actual solid has -1<=z<=|x+y|/2, |x|,|y|<=1. The two triangles
# determined by diagonal(5,7) cover the entire square; roof is a continuous
# piecewise-affine graph, all side faces vertical: closed, outward, embedded.
a,b=verts[4],verts[6]
p=tuple((F(x)+y)/2 for x,y in zip(a,b))
assert a[2]==F(abs(a[0]+a[1]),2) and b[2]==F(abs(b[0]+b[1]),2)
assert p==(0,0,1) and p[2]>F(abs(p[0]+p[1]),2)
P=Polyhedron(verts,faces)
Q=exact_surface(P)
result=dict(independent_convex=False,midpoint=list(p),midpoint_roof_height='0',
 source_is_convex=P.is_convex(tol=0),source_reflex=P.reflex_edges(tol=0),
 same_surface_expanded_is_convex=Q.is_convex(tol=0),same_surface_expanded_reflex=Q.reflex_edges(tol=0),
 supplementary_surface_states=[point_in_polyhedron(x,P) for x in (a,b,p)],expanded_manifold_issues=Q.manifold_issues())
print(json.dumps(result,default=str,indent=2))
assert result['source_is_convex'] is True and result['source_reflex']==[]
assert result['same_surface_expanded_is_convex'] is False and result['same_surface_expanded_reflex']==[(5,7)]
print('CONFIRMED exact source-ring is_convex misses folded-face internal concavity; valid surface is nonconvex')
