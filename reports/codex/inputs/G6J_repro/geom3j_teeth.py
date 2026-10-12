import sys,inspect,textwrap,json
from pathlib import Path
from fractions import Fraction as F
import pytest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from eab.kernel3d import geom3 as G,covers3 as C,g03 as H
import test_r9fix_topology as T
import test_r9fix_solid_cones as S
import test_r7fix_geom3 as R
records=[]
def tooth(name,target,assertion,setup,check):
 with pytest.MonkeyPatch.context() as mp:
  setup(mp)
  try:check()
  except AssertionError as e:
   assert assertion in str(e),(name,'wrong assertion',str(e))
   row={'name':name,'target':target,'result':'RED at intended invariant','assertion':str(e)}
   records.append(row);print(name,': RED',str(e),flush=True)
  else:raise AssertionError((name,'MUTATION ESCAPED'))
def restore_source(method):
 def mutate(mp):
  old=getattr(G.Polyhedron,method);source=textwrap.dedent(inspect.getsource(old));needle='P = exact_surface(self)';assert source.count(needle)==1
  ns=dict(vars(G));exec(compile(source.replace(needle,'P = self'),'<g6j-source-topology>', 'exec'),ns)
  mp.setattr(G.Polyhedron,method,ns[method])
 return mutate
tooth('folded-convexity','Polyhedron.is_convex','declared-roof-midpoint-concavity',restore_source('is_convex'),lambda:T.test_g6i02_declared_folded_surface_is_not_convex(F(1,2),F(1),False,False))
tooth('folded-reflex','Polyhedron.reflex_edges','declared-folded-reflex-ridge',restore_source('reflex_edges'),lambda:T.test_g6i02_reflex_edges_include_declared_internal_ridge(F(1,2),F(1),False,False))
def edge_mut(mp):
 source=textwrap.dedent(inspect.getsource(C.edge_arc_contains));ns=dict(vars(C));exec(compile(source.replace('geom3.exact_surface(P)','P'),'<g6j-source-edge-cone>','exec'),ns);mp.setattr(C,'edge_arc_contains',ns['edge_arc_contains'])
tooth('folded-edge-arc','edge_arc_contains','declared-triangle-cone-endpoint',edge_mut,lambda:S.test_public_edge_arc_uses_declared_adjacent_triangle_normal(F(1),F(0),(4,5),(0,0,1),False))
def bogus_vertices(mp):mp.setattr(C,'cones_intersect_relint',lambda *a,**k:True)
def check_vertices():
 from test_covers3_g0_vote2 import _random_pair
 report=H.g0_convex3(*_random_pair(0),samples=0)
 assert report.passed,'false-local-extreme-vertices: exact symmetric difference='+str(report.hull_vertex_mismatch)
tooth('G0-false-extremes','cones_intersect_relint','false-local-extreme-vertices',bogus_vertices,check_vertices)
def omit_ridges(mp):mp.setattr(G,'_surface_distance_edges',lambda P:P.edges())
tooth('brute-folded-ridge','_surface_distance_edges','folded-ridge-slab-distance',omit_ridges,lambda:R.test_g6g04_folded_internal_ridges_attain_slab_distance(F(0),((1,0,0),(0,1,0),(0,0,1)),F(1)))
(ROOT/'review/logs/geom3j_teeth.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
print('LIVE_MUTATION_TEETH_PASS',len(records),'mutations; no tracked bytes changed')
