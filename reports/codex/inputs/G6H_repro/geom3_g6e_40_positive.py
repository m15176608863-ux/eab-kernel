import sys
sys.path[:0]=['src','tests']
from eab.kernel3d.geom3 import box, convex_hull_3d, sub
from eab.kernel3d.covers3 import local_facets3
from eab.kernel3d.g03 import facet_vote3
A=box(half=(1,1,1)); B=box(center=(0.3,0.2,3),half=(2,1.5,0.7))
d=[sub(b,a) for a in A.verts for b in B.verts]
print(facet_vote3(A,B,local_facets3(A,B,1e-12),convex_hull_3d(d),d))
# Original direct-default call no longer crashes. Rounded difference points
# are a different model and are correctly rejected as anomalous. Rebuild the
# exact supplied-data E to assert its intended theorem result independently.
from fractions import Fraction as F
exact_d=[tuple(F(b[k])-F(a[k]) for k in range(3)) for a in A.verts for b in B.verts]
result=facet_vote3(A,B,local_facets3(A,B,1e-12),convex_hull_3d(exact_d),exact_d)
assert result==(0,6,0,0,[]),result
print('exact-data direct-default result',result)
