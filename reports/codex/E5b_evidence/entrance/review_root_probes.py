"""Read-only cross-review, independent rational fixtures and equivalence checks."""
from pathlib import Path
from fractions import Fraction as F
from itertools import permutations
import random,json,time,sys,subprocess,types
sys.path[:0]=['src','tests']
from eab.kernel3d import exact_geom as E,geom3 as G
from e5a2_surface_oracle import star_overlap
from test_e5b_triangle_boolean import _feasible
from test_e5a2_surface import l_block
start=time.perf_counter(); report={'findings':[], 'checks':{}}
rng=random.Random(871231)
# Brand-new rational pairs, skew/coplanar/point-contact/same triangle and all orders.
pairs=[]
for seed in range(40):
 a=tuple(tuple(F(rng.randrange(-20,21),rng.randrange(1,15)) for k in range(3)) for j in range(3))
 b=tuple(tuple(F(rng.randrange(-20,21),rng.randrange(1,15)) for k in range(3)) for j in range(3))
 pairs.append((a,b))
base=((F(0),F(0),F(0)),(F(2),F(0),F(0)),(F(0),F(2),F(0)))
for e in (F(0),F(1,2**160),-F(1,2**160)):
 b=((F(2),F(0),e),(F(3),F(0),e),(F(2),F(1),e))
 for order in permutations(range(3)):
  pairs.append((base,tuple(b[i] for i in order)))
for scale,shift in ((F(1,10**120),F(10**6)),(F(10**120),F(0))):
 for delta in (F(0),F(1,2**120),-F(1,2**120)):
  b=((F(1),F(1),delta),(F(3),F(1),delta),(F(1),F(3),delta))
  move=lambda tri:tuple(tuple(shift+scale*x for x in p) for p in tri)
  pairs.append((move(base),move(b)))
for a,b in pairs:
 assert E._triangles_intersect_prepared(E._triangle_data(a),E._triangle_data(b))==_feasible(a,b)
report['checks']['new_boolean_barycentric_pairs']=len(pairs)
# Independent axis inequalities on extreme-scale L-prism membership.
count=0;states=set()
for scale,shift in ((F(1),F(0)),(F(1,10**120),F(10**6)),(F(10**120),F(-10**150))):
 raw=l_block(); poly=G.Polyhedron([tuple(shift+scale*F(x) for x in p) for p in raw.verts],raw.faces)
 triangles=E.triangles(poly)
 points=[tuple(F(rng.randrange(-10,41),10) for _ in range(3)) for j in range(80)]
 points += [(F(1)+e,F(2),F(1,2)) for e in (F(0),F(1,2**160),-F(1,2**160))]
 for x,y,z in points:
  closed=((0<=x<=3 and 0<=y<=1) or (0<=x<=1 and 0<=y<=3)) and 0<=z<=1
  strict=((0<x<3 and 0<y<1) or (0<x<1 and 0<y<3)) and 0<z<1
  want=1 if strict else 0 if closed else -1
  got=E._point_in_triangles(tuple(shift+scale*v for v in (x,y,z)),triangles)
  assert got==want,(scale,shift,(x,y,z),got,want)
  count+=1;states.add(got)
report['checks']['integer_parity_extreme_scale']=dict(count=count,states=sorted(states))
# Independent tetra-union SAT on nonplanar, certified radial surfaces.
states=set();certified=0
for j in range(32):
 def deformed(shift):
  p=G.box()
  return G.Polyhedron([tuple(F(x)+F(rng.randrange(-6,7),100)+shift[k] for k,x in enumerate(v)) for v in p.verts],p.faces)
 a=deformed((F(0),)*3);b=deformed((F(rng.randrange(-30,31),10),F(rng.randrange(-20,21),10),F(rng.randrange(-20,21),10)))
 actual=E._star_union_overlap(a,b)
 assert actual is not None
 assert actual==star_overlap(a,b)
 assert actual==G.polyhedra_overlap(a,b)
 certified+=1;states.add(actual)
report['checks']['new_nonplanar_star_pairs']=dict(count=certified,states=sorted(states))
# Content-signature cache through tuple replacement, ordering change and revert.
p=G.box();p.verts[6]=(1.,1.,1.25)
old=G.exact_convex_view(p); original=list(p.verts)
for displacement in (10.,-4.,0.,1e6):
 p.verts[:]=[(x+displacement,y,z) for x,y,z in original]
 p.faces[1]=p.faces[1][1:]+p.faces[1][:1]
 view=G.exact_convex_view(p)
 assert G.exact_point_in_convex_polyhedron((displacement,0,0),p)==1
 assert G.exact_point_in_convex_polyhedron((displacement+100,0,0),p)==-1
 assert view is not old;old=view
report['checks']['cache_modify_revert_cycles']=4
# Nested mutable vertex input is outside Vec3's tuple type but doc mentions it.
p=G.box();p.verts=[list(v) for v in p.verts]
try:G.exact_convex_view(p)
except TypeError as ex:report['findings'].append({'severity':'minor/documentation','issue':'cache doc says nested lists; geometry wrappers still require hashable Vec3 tuple','error':str(ex)})
# Closed star-union boundary and both infinitesimal sides.
a=G.box();a.verts[6]=(F(4,5),F(4,5),F(4,5))
track=[]
for gap in (-F(1,2**120),F(0),F(1,2**120)):
 b=G.box(center=(2+gap,0,0),half=(F(1),)*3)
 got=E._star_union_overlap(a,b);want=star_overlap(a,b)
 assert got==want==(-1 if gap>0 else 0 if gap==0 else 1)
 track.append(got)
report['checks']['nonconvex_star_boundary_track']=track
# Strict transverse certificate checked in independent inverse-coordinate boxes.
a=l_block();at=E.triangles(a);ap=E._planes(at);positive=0
for j in range(96):
 cx,cy=F(rng.randrange(-5,35),10),F(rng.randrange(-5,35),10)
 hx,hy=F(rng.randrange(2,15),10),F(rng.randrange(2,15),10)
 raw=G.box(half=(hx,hy,F(1,5)))
 b=G.Polyhedron([(cx+F(3,5)*F(x)-F(4,5)*F(y),cy+F(4,5)*F(x)+F(3,5)*F(y),F(z)+F(1,2)) for x,y,z in raw.verts],raw.faces)
 bt=E.triangles(b);bp=E._planes(bt)
 point=E._transverse_interior_witness(at,bt,ap,bp)
 if point is None:continue
 x,y,z=point
 assert 0<z<1 and ((0<x<3 and 0<y<1) or (0<x<1 and 0<y<3))
 u=F(3,5)*(x-cx)+F(4,5)*(y-cy);v=-F(4,5)*(x-cx)+F(3,5)*(y-cy)
 assert -hx<u<hx and -hy<v<hy and F(3,10)<z<F(7,10)
 positive+=1
assert positive>20
report['checks']['transverse_certificate_inverse_box_oracle']={'trials':96,'certified':positive}
report['seconds']=time.perf_counter()-start
Path('reports/codex/E5b_evidence/entrance/review_root_probes.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
