from pathlib import Path
import sys
sys.path.insert(0,str(Path.cwd()/'src'))
from fractions import Fraction as F
from eab.kernel3d.geom3 import Polyhedron,box,brute_feature_distance,polyhedra_overlap,point_in_polyhedron
from eab.kernel3d import exact_geom as G
base=box();av=[tuple(F(x) for x in p) for p in base.verts];bv=list(av)
av=[(x,y,F(-1) if i<4 else (F(1) if i in (5,7) else F(0))) for i,(x,y,z) in enumerate(av)]
bv=[(-y,x,F(6) if i>=4 else (F(3) if i in (1,3) else F(4))) for i,(x,y,z) in enumerate(bv)]
a,b=Polyhedron(av,base.faces),Polyhedron(bv,base.faces)
at=[tri for _,tri in G.triangulate(tuple(a.verts),tuple(a.faces))];bt=[tri for _,tri in G.triangulate(tuple(b.verts),tuple(b.faces))]
aa,bb=Polyhedron(av,at),Polyhedron(bv,bt)
print('verts',av,bv)
print('tris',at,bt)
print('distance source',brute_feature_distance(a,b),'triangle surface',brute_feature_distance(aa,bb),'expected',2)
print('valid triangles',aa.manifold_issues(),bb.manifold_issues(),'overlap',polyhedra_overlap(a,b))
print('ridge midpoints boundary',point_in_polyhedron((0,0,1),a),point_in_polyhedron((0,0,3),b))
print('convex source and surface',a.is_convex(),aa.is_convex(),b.is_convex(),bb.is_convex())
