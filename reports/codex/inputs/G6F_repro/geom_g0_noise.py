from pathlib import Path
import sys,json,math
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel2d import g0,geom as G,covers as C
from geom_independent_scan import state
S=[(0.,0.),(1.,0.),(1.,1.),(0.,1.)]
def move(dx):return [(x+dx,y) for x,y in S]
# State differences are exact input differences, no reconstructed ideal inputs.
gap=2.**-44
outside=move(1.+gap)
inside=move(1.-gap)
results={'gap':gap,'outside_exact':state(outside,S),'outside_legacy':G.polygons_overlap(outside,S),'inside_exact':state(inside,S),'inside_legacy':G.polygons_overlap(inside,S)}
# Inject the missing-all-covers defect into actual kernel generation entry points.
original_side=C._ve_side;original_vv=C.vv_cover
C._ve_side=lambda *a,**k:-1
C.vv_cover=lambda *a,**k:None
try:
    assert C.enumerate_covers(outside,S,window=math.inf)==[]
    d=g0.g0_distance_completeness(outside,S,[(0.,0.)])
    e=g0.g0_exit_completeness(inside,S,[(0.,0.)],[(1.,0.)])
    results['mutant_distance']={'passed':d.passed,'samples':d.samples,'touching':d.touching,'draws':d.draws}
    results['mutant_exit']={'passed':e.passed,'samples':e.samples,'touching':e.touching,'draws':e.draws}
finally:C._ve_side=original_side;C.vv_cover=original_vv
# This sample meets brute_ray_exit's own stated precondition polygons_overlap == 1.
A=move(1.-2.**-39)
true_exit=1-F(A[0][0])
assert G.polygons_overlap(A,S)==1
reported=g0.brute_ray_exit(A,S,(1.,0.))
results['exit_oracle']={'initial_exact':state(A,S),'initial_legacy':G.polygons_overlap(A,S),'exact_first_exit':str(true_exit),'float_first_exit':float(true_exit),'reported':reported,'at_reported_exact':state(A,S,(reported,0.))}
assert reported==0.0 and state(A,S,(reported,0.))==1
assert results['mutant_distance']=={'passed':True,'samples':0,'touching':1,'draws':1}
assert results['mutant_exit']=={'passed':True,'samples':0,'touching':1,'draws':1}
print(json.dumps(results,ensure_ascii=False,indent=2))
(ROOT/'review/notes/geom_g0_noise_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
