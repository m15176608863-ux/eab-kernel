import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.kernel3d.geom3 import Polyhedron, box, exact_convex_view,exact_point_in_convex_polyhedron, point_in_polyhedron,exact_convex_overlap
P0=box(half=(1,1,1)); P=Polyhedron(P0.verts,[tri for f in P0.faces for tri in ((f[0],f[1],f[2]),(f[0],f[2],f[3]))])
H=exact_convex_view(P)
source_before=(tuple(P.verts),tuple(P.faces))
assert not P.manifold_issues() and not H.manifold_issues()
print('view is source',H is P)
print('before point state',exact_point_in_convex_polyhedron((0,0,0),P))
H.verts[:]=[(x+100,y,z) for x,y,z in H.verts]
assert not H.manifold_issues()
assert source_before==(tuple(P.verts),tuple(P.faces))
print('source still origin-centred',min(v[0] for v in P.verts),max(v[0] for v in P.verts))
print('after returned-view mutation state',exact_point_in_convex_polyhedron((0,0,0),P))
print('fresh equivalent source state',exact_point_in_convex_polyhedron((0,0,0),Polyhedron(P.verts,P.faces)))
print('source exact general surface state',point_in_polyhedron((0,0,0),P))
small=box(half=(.5,.5,.5))
print('cached source exact convex overlap with contained small box',exact_convex_overlap(P,small))
assert all(-1 < p[k] < 1 for p in small.verts for k in range(3))
assert exact_point_in_convex_polyhedron((0,0,0),P)==-1
assert exact_point_in_convex_polyhedron((0,0,0),Polyhedron(P.verts,P.faces))==1
assert exact_convex_overlap(P,small)==-1
print('CONFIRMED valid-source unchanged; independent box oracle inside=1 overlap=1; cached results=-1/-1')
