"""Finite-input unbounded model, independently known alpha interval [1/u,inf)."""
from pathlib import Path
from fractions import Fraction as F
import sys,math,json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
import eab.limit as L
import eab.limit_multi as M
u=math.ulp(0.0)
cs=[L.LimitContact((-1,0),(0,1),.5),L.LimitContact((1,0),(0,1),.5)]
dead=[0.,1.,0.];live=[0.,-u,0.]
# Vertical force equilibrium is N=alpha*u-1>=0; both contacts can carry N/2
# with zero tangential force and equal lever cancellation. Thus feasible exactly
# for alpha>=1/u and no finite capacity upper bound. All inputs are binary64.
minimum=1/F(u)
assert minimum>F(sys.float_info.max)
results=[L.limit_load(cs,dead,live,dim=2),
         M.limit_load_multi([M.LimitBody(dead,live)],[M.BodyContact(c,0) for c in cs],dim=2)]
rows=[]
for result in results:
    assert result.status=='unbounded' and math.isinf(result.alpha)
    assert math.isnan(result.uncertainty) and result.resolvability=='resolved'
    rows.append(dict(type=type(result).__name__,status=result.status,alpha='inf',
                     uncertainty='NaN',resolvability=result.resolvability,
                     resolvability_statuses=result.resolvability_statuses))
print(json.dumps(dict(result='CONFIRMED REPORT DEFECT ONLY',core_capacity_correct=True,
                     all_inputs_finite=True,formula_U_without_display_underflow=str(F(L._U_IN)),rows=rows),indent=2))
