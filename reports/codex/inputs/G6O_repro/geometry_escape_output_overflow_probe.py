"""Candidate audit: upward escape display after a valid RN-even scalar boundary.
Pure rational long box geometry; independent z-interval translation root.
"""
from pathlib import Path
from fractions import Fraction as Q
import sys, math, json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel3d.geom3 import Polyhedron,polyhedra_overlap
from eab.kernel3d.interlock import escape_height_covers
from eab.construction import scalar_rational
faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
def bounds_cube(x0,x1,y0,y1,z0,z1):
    return Polyhedron([(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],faces)
maximum=Q(sys.float_info.max);target=maximum+1
a=bounds_cube(Q(-1,8),Q(1,8),Q(-1,8),Q(1,8),Q(0),target/2)
b=bounds_cube(Q(-1,4),Q(1,4),Q(-1,4),Q(1,4),Q(-1,4),target)
row={'target_gt_max':target>maximum,'target_RN_finite':math.isfinite(scalar_rational(target)),'independent_interval_escape':str(target),'initial_expected':1}
try:
    row['initial_actual']=polyhedra_overlap(a,b)
    out=escape_height_covers(a,b,(0,0,0),tol=0)
    row.update({'height':repr(out.height),'height_finite':math.isfinite(out.height),'exact_height_equals_interval_root':out.exact_height==target,'nonpenetrating_state':out.nonpenetrating_state,'n_candidates':out.n_candidates})
except Exception as e:row['exception']=type(e).__name__+': '+str(e)
print(json.dumps(row,indent=2))
(ROOT/'review/evidence/geometry_escape_output_overflow_probe.json').write_text(json.dumps(row,indent=2),encoding='utf-8')
