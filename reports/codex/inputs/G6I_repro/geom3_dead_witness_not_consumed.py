from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.kernel3d import geom3 as G
from eab.kernel3d.entrance3 import first_entrance3
from eab.margin import body_distance
names=('_inward_vertex_direction','_edge_edge_contacts','_active_normals','_gordan_direction','_min_norm_on_simplex','_contact_cone_witness')
original={n:getattr(G,n) for n in names};p=Path(G.__file__);before=hashlib.sha256(p.read_bytes()).hexdigest()
def forbidden(*args,**kwargs):raise AssertionError('retired float witness helper consumed by a live core API')
rows=[]
try:
 for n in names:setattr(G,n,forbidden)
 A=G.box();B=G.box(center=(1,0,0));rows.append(('convex_overlap',G.polyhedra_overlap(A,B,0)))
 ring=[(0,0),(3,0),(3,1),(1,1),(1,3),(0,3)];n=len(ring)
 vertices=[(x,y,z) for z in (0,1) for x,y in ring]
 faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 L=G.Polyhedron(vertices,faces);C=G.box(center=(1.25,1.25,.5),half=(.5,.5,.25))
 rows.append(('concave_overlap',G.polyhedra_overlap(L,C,0)))
 distant=G.box(center=(4,0,0));rows.append(('separated_distance',body_distance(distant,A,tol=0)))
 e=first_entrance3(distant,A,(0,0,0),(-1,0,0),tol=0);rows.append(('first_entrance',e.kind,str(e.exact_t)))
 assert rows[0][1]==1 and rows[1][1]==1 and rows[2][1][0]==2 and e.exact_t==2
finally:
 for n,fn in original.items():setattr(G,n,fn)
 after=hashlib.sha256(p.read_bytes()).hexdigest();assert before==after
print(json.dumps(dict(result='PASS',disabled_internal_helpers=names,live_results=rows,sha256_before=before,sha256_after=after),indent=2))
