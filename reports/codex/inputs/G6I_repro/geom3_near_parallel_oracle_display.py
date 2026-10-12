from pathlib import Path
import sys,json
from fractions import Fraction as F
sys.path[:0]=[str(Path(__file__).resolve().parents[2]/'src'),str(Path(__file__).resolve().parents[2]/'tests')]
from test_near_parallel_edges import exact_seg_seg
from eab.kernel3d.geom3 import _seg_seg_distance
p=(0.,0.,0.);q=(1.,0.,0.);g=1e-200;r=(0.,g,0.);s=(1.,g,0.)
expected=g
actual=exact_seg_seg(p,q,r,s)
squared=exact_seg_seg(p,q,r,s,squared=True)
production=_seg_seg_distance(p,q,r,s)
assert squared==F(g)**2
assert actual==0. and production==expected
print(json.dumps(dict(result='CONFIRMED_ORACLE_DISPLAY_ONLY',expected=expected,actual_oracle_display=actual,production_distance=production,exact_squared=str(squared),scope='default display helper retains preexisting square-before-sqrt range defect; new squared certificate is correct, no demonstrated old-red/new-green migration weakening'),indent=2))
