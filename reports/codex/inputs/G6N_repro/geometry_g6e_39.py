# Original raw finding index 39; current HEAD replay, no repair.
import sys; sys.path[:0]=['src']
from eab.kernel3d.geom3 import box, convex_hull_3d, sub
from eab.kernel3d.covers3 import local_facets3
from eab.kernel3d.g03 import facet_vote3
A=box(half=(1,1,1)); B=box(center=(0.3,0.2,3),half=(2,1.5,0.7))
d=[sub(b,a) for a in A.verts for b in B.verts]
print('facet_vote3', facet_vote3(A,B,local_facets3(A,B,1e-12),convex_hull_3d(d),d))

