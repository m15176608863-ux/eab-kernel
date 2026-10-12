from pathlib import Path
import sys,copy,json,random,time
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel3d.geom3 import Polyhedron,box,exact_convex_view,point_in_polyhedron
from eab.margin import body_distance,_resolved
from eab.kernel3d import exact_sweep
from eab.kernel2d.covers import ve_cover,vv_cover
from eab.dual import Dual
r=random.Random(11014);t0=time.time();checks=0;errors=[]
def fingerprint(p):
 global checks
 H=exact_convex_view(p)
 out=(p.metrics(),p.edges(),p.vertex_faces(0),p.edge_faces(p.edges()[0]),p.vertex_edges(0),tuple(p.face_normal(i) for i in range(len(p.faces))),p.volume(),p.centroid(),tuple(H.verts),tuple(H.faces),H.source_vertices,H.source_faces)
 checks+=1;return out
for scale in (F(1,10**9),F(1),F(10**8)):
 for t in (F(0),F(1000),F(10**6)):
  P=box();P.verts=[tuple(scale*F(x)+t for x in p) for p in P.verts]
  Q=Polyhedron(list(P.verts),list(P.faces));baseline=fingerprint(P)
  # Poison every returned mutable topology list and non-self hull view.
  P.edges().clear();P.vertex_faces(0).clear();P.edge_faces(P.edges()[0]).clear();P.vertex_edges(0).clear()
  if fingerprint(P)!=baseline:errors.append('returned topology alias')
  v=P.verts[0];P.verts[0]=(v[0]-scale/8,v[1]-scale/11,v[2]-scale/13)
  fresh=Polyhedron(list(P.verts),list(P.faces))
  if fingerprint(P)!=fingerprint(fresh):errors.append('vertex-content stale')
  P.faces=[tuple(reversed(f)) for f in P.faces]
  fresh=Polyhedron(list(P.verts),list(P.faces))
  if fingerprint(P)!=fingerprint(fresh):errors.append('face-content stale')
  H=exact_convex_view(Q)
  if H is not Q:
   H.verts[0]=(F(123),F(124),F(125));H.faces.clear()
   if fingerprint(Q)!=baseline:errors.append('hull-view alias')
for j in range(8):
 A=box(center=(0,0,0));B=box(center=(4,F(j,16),F(j,32)))
 got=_resolved(A,B,0,None,None)
 if got[2]:
  for c,w,n,d2 in got[2]:c.gap=12345;c.point_a=(12345,)*3
  got[2].clear()
 x=body_distance(A,B,tol=0)
 y=body_distance(Polyhedron(list(A.verts),list(A.faces)),Polyhedron(list(B.verts),list(B.faces)),tol=0)
 # Call uncached implementation rather than merely an identical content lookup.
 import eab.margin as m
 z=m._resolve(A,B,0,None,None)
 if x[0] != m._exact.sqrt_rational(z[4]):errors.append('margin payload alias')
 old=x;A.verts=[(F(p[0])+F(1,8),p[1],p[2]) for p in A.verts]
 x=body_distance(A,B,tol=0);z=m._resolve(A,B,0,None,None)
 if x[0]!=m._exact.sqrt_rational(z[4]):errors.append('margin content stale')
 checks+=3
# Exact event cache payload and lists: separate roots must follow shifted input.
A=box();B=box(center=(4,0,0))
a=exact_sweep.surface_events(A,B,(1,0,0),t_max=8)
b=exact_sweep.surface_events(A,B,(1,0,0),t_max=8)
checks+=1
if a!=b:errors.append('event cache nondeterministic')
result={'checks':checks,'errors':errors,'elapsed_seconds':time.time()-t0,'seed':11014}
(ROOT/'review/logs/root_cache_pressure.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result));assert not errors
