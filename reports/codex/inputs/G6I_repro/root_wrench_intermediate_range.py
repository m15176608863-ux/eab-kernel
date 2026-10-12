"""Exact raw-input cross-product oracle, independent of production helpers."""
from pathlib import Path
import sys,math,json
from fractions import Fraction as F
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.limit import wrench
rows=[]
for dim in (2,3):
 for scale in (1e160,1e200):
  f=(scale,)*dim;p=(scale,)*dim;o=(0.,)*dim
  # Every lever is equal to every force component, hence EACH antisymmetric
  # moment is exactly zero for the supplied binary64 data, not an ideal input.
  r=[F(a)-F(b) for a,b in zip(p,o)];fx=list(map(F,f))
  mx=([r[0]*fx[1]-r[1]*fx[0]] if dim==2 else
      [r[1]*fx[2]-r[2]*fx[1],r[2]*fx[0]-r[0]*fx[2],r[0]*fx[1]-r[1]*fx[0]])
  expected=list(f)+list(map(float,mx));actual=wrench(f,p,o,dim)
  assert all(math.isfinite(x) for x in f+p+o+tuple(expected))
  assert any(math.isnan(v) for v in actual[dim:])
  rows.append(dict(dim=dim,scale=scale,input_force=f,input_point=p,exact_moments=list(map(str,mx)),expected=expected,actual=[('nan' if math.isnan(v) else v) for v in actual],raised=False))
print(json.dumps(rows,indent=2))
