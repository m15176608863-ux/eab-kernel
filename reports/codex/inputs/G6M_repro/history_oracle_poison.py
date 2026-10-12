"""Fresh uncached expected-answer computations after poisoning production primitives.
No expected path may rely on a same faulty production helper or constructor.
"""
from pathlib import Path
import sys,importlib,inspect,json
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from eab.kernel3d.geom3 import box
import e5a_cover_oracle as C,e5a_escape_oracle as E,e5a_convex_oracle as V,e5a2_surface_oracle as S,e5b_margin_oracle as M,e5b_wall_oracle as W,e5a_g2_oracle as G
from eab.kernel3d import g03_exact as Q
A=box(center=(0,0,.75),half=(.5,.5,.5));B=box(half=(.5,.5,.5))
SEP=box(center=(0,0,2),half=(.5,.5,.5))
computations={
 'local_full_cover_set':lambda:C.cover_labels(SEP,B),
 'raw_hull_canonical_payload':lambda:V.canonical_payload(tuple(SEP.verts),tuple(SEP.faces)),
 'star_union_overlap':lambda:S.star_overlap(A,B),
 'exact_convex_ray_model':lambda:Q.overlap(tuple(SEP.verts),tuple(B.verts),(0,0,-1)),
 'default_margin_complete_cover_squared':lambda:M.cover_squared(SEP,B),
 'independent_wall_star_earliest_root':lambda:W.earliest_star_escape(A,B),
 'local_escape_candidates':lambda:E.candidates(A,B,(0,0,0)),
 'support_sets':lambda:G.support_sets(tuple(SEP.verts)),
}
def clear():
 for mod in (C,E,V,S,M,W,G,Q):
  for x in vars(mod).values():
   if hasattr(x,'cache_clear'):x.cache_clear()
clear();truth={k:fn() for k,fn in computations.items()}
modules=['eab.construction','eab.rational3','eab.kernel2d.geom','eab.kernel2d.exact','eab.kernel3d.geom3','eab.kernel3d.covers3','eab.kernel3d.exact_geom','eab.kernel3d.exact_sweep','eab.kernel3d.entrance_topology','eab.margin','eab.kernel3d.interlock']
patched=[]
def forbidden(*a,**kw):raise AssertionError('production primitive entered expected-answer oracle')
try:
 for name in modules:
  mod=importlib.import_module(name)
  for key,val in list(vars(mod).items()):
   if inspect.isfunction(val) and val.__module__==name:
    patched.append((mod,key,val));setattr(mod,key,forbidden)
 clear();results=[]
 for key,fn in computations.items():
  got=fn();assert got==truth[key],key;results.append({'path':key,'uncached_equal':True})
 print(json.dumps(dict(poisoned_production_functions=len(patched),results=results),ensure_ascii=False,indent=2))
finally:
 for mod,key,val in reversed(patched):setattr(mod,key,val)
