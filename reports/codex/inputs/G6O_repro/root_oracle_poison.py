"""Poison production geometry: independently recompute expected answers."""
from pathlib import Path
from fractions import Fraction as F
from types import SimpleNamespace
import sys,importlib,json
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from eab.kernel3d.geom3 import box
from eab.kernel3d import geom3,exact_geom,covers3,g03_exact
from eab.kernel2d import exact,geom
import e5a_cover_oracle as O
import e5a2_surface_oracle as S
import e5b_margin_oracle as M
from eab.kernel2d import g0_oracle as G
raw=box();a=SimpleNamespace(verts=tuple(raw.verts),faces=tuple(raw.faces))
b=SimpleNamespace(verts=tuple(tuple(F(v[i])+ (F(5) if i==0 else 0) for i in range(3)) for v in raw.verts),faces=tuple(raw.faces))
before=(g03_exact.overlap(a.verts,b.verts,(0,0,0)),S.star_overlap(a,b),G.overlap([(0,0),(1,0),(1,1),(0,1)],[(2,0),(3,0),(3,1),(2,1)]),M.cover_squared(a,b))
def forbidden(*args,**kwargs):raise AssertionError('POISONED tested geometry primitive was called')
poisoned=[]
for module,names in [(geom3,['sub','dot','cross','convex_hull_3d','exact_convex_view','point_in_polyhedron','polyhedra_overlap']), (exact_geom,['vector','sub','dot','cross','_ring_triangles','point_in_polyhedron','polyhedra_overlap']), (covers3,['_qnormal','_qedge','enumerate_covers3','local_facets3','membership_convex3']), (exact,['_sub','_cross','_dot','hull_exact','polygons_overlap_exact']), (geom,['sub','dot','cross','convex_hull','polygons_overlap'])]:
 for name in names:
  if hasattr(module,name):setattr(module,name,forbidden);poisoned.append(module.__name__+'.'+name)
# Clear independent caches to ensure results are not simply stale payload hits.
for module in (g03_exact,S,O,M,G):
 for value in vars(module).values():
  if callable(value) and hasattr(value,'cache_clear'):value.cache_clear()
after=(g03_exact.overlap(a.verts,b.verts,(0,0,0)),S.star_overlap(a,b),G.overlap([(0,0),(1,0),(1,1),(0,1)],[(2,0),(3,0),(3,1),(2,1)]),M.cover_squared(a,b))
assert before==after
assert before[:3]==(-1,-1,-1)
print('POISON PASS:',len(poisoned),'production primitives; caches cleared; independent SAT/surface/2D/cover-distance answers unchanged')
(ROOT/'review/evidence/root_oracle_poison.json').write_text(json.dumps({'poisoned':poisoned,'states':before[:3],'independent_cover_count':len(before[3]),'passed':True},indent=2),encoding='utf-8')
