import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from fractions import Fraction as F
from eab.kernel3d.geom3 import Polyhedron, box, exact_convex_view, exact_point_in_convex_polyhedron,exact_convex_overlap
from eab.kernel3d.covers3 import membership_convex3
P=box(half=(1,1,1)); faces=list(P.faces); faces[1]=tuple(reversed(faces[1])); P=Polyhedron(P.verts,faces)
Q=box(half=(F(1,2),)*3)
print('vertex-set oracle: origin inside hull =',all(-1<F(0)<1 for _ in range(3)))
print('canonical view retained malformed source hint =',exact_convex_view(P) is P)
print('exact_point_in_convex_polyhedron(origin) =',exact_point_in_convex_polyhedron((0,0,0),P))
print('exact_convex_overlap(contained Q,P) =',exact_convex_overlap(Q,P))
print('membership_convex3(Q,P,0) =',membership_convex3(Q,P,(0,0,0)))
empty_hint=Polyhedron(P.verts,[])
print('same vertices, empty source hints: convex point =',exact_point_in_convex_polyhedron((0,0,0),empty_hint),'E member =',membership_convex3(Q,empty_hint,(0,0,0)))
assert exact_point_in_convex_polyhedron((0,0,0),empty_hint)==1
assert membership_convex3(Q,empty_hint,(0,0,0))==1
assert exact_point_in_convex_polyhedron((0,0,0),P)==-1
assert membership_convex3(Q,P,(0,0,0))==-1
print('CONFIRMED explicit conv(vertices) contract violated by face-hint-only change; no general surface API called')
