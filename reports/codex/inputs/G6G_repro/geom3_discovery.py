from pathlib import Path
import sys
sys.path.insert(0,str(Path.cwd()/'src'))
from fractions import Fraction as F
from eab.kernel3d.geom3 import Polyhedron,box,brute_feature_distance
from eab.kernel3d import exact_geom as G
import random,json
base=box().faces
rng=random.Random(71025)
for i in range(500):
 def make(z):
  return Polyhedron([tuple(F(x)+F(rng.randint(-3,3),10)+(F(z) if k==2 else 0) for k,x in enumerate(p)) for p in box().verts],base)
 a,b=make(0),make(4)
 at=[tri for _,tri in G.triangulate(tuple(a.verts),tuple(a.faces))];bt=[tri for _,tri in G.triangulate(tuple(b.verts),tuple(b.faces))]
 aa,bb=Polyhedron(a.verts,at),Polyhedron(b.verts,bt)
 one,two=brute_feature_distance(a,b),brute_feature_distance(aa,bb)
 if one>two*(1+1e-12):
  print('FOUND',i,one,two)
  payload=dict(av=[[str(x) for x in p] for p in a.verts],bv=[[str(x) for x in p] for p in b.verts],faces=base,at=at,bt=bt,one=one,two=two)
  Path('review/notes/brute_diag_candidate.json').write_text(json.dumps(payload,indent=2),encoding='utf-8');break
else:print('none')
s=F(1,2**1074)
p=Polyhedron([(0,0,0),(1,0,0),(1,s,0)],[(0,1,2)])
print('area exact',s/2,'actual',p.face_area(0))
