"""Own exact nearest-hull-point and binary64-midpoint certificate.
cone_intersection_margin docstring promises distance to an exact positively
rescaled constraint hull. It rounds p coordinates before norm, although norm
of the exact p is representable. Boolean cone feasibility is checked separately.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json,math
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.kernel3d.geom3 import tetra
from eab.kernel3d.covers3 import cone_intersection_margin,cones_intersect_relint
unit=F(2)**-1074
rows=[];mismatches=[]
for m in range(1,25):
 delta=m*unit
 # Every input coordinate is a finite binary64 value, not an unexpressed ideal.
 d=float(delta);assert F(d)==delta
 g=((F(1),F(-1),delta),(delta,F(1),F(-1)),(F(-1),delta,F(1)))
 # N_B intersects -N_A; B reflected therefore the six incident constraints
 # are two copies of -g. Their L-infinity positive normalization is exactly 1.
 q=tuple(tuple(-c for c in row) for row in g)
 p=tuple(sum(row[i] for row in q)/3 for i in range(3))
 exact_squared=sum(x*x for x in p)
 assert p==(-delta/3,)*3 and exact_squared==delta*delta/3
 # p is in the hull (barycentric weights1/3), and its inner product with every
 # extreme point equals |p|^2. Thus p is the unique Euclidean projection of0.
 assert all(sum(x*y for x,y in zip(p,row))==exact_squared for row in q)
 # Correct rounding in subnormal units, using rational midpoint squares only.
 j=next(j for j in range(2*m+1) if F(m*m,3)<F(2*j+1,2)**2)
 assert j>0 and F(2*j-1,2)**2<F(m*m,3)<F(2*j+1,2)**2
 expected=float(j*unit)
 A=tetra((0.,0.,0.),(1.,-1.,d),(d,1.,-1.),(-1.,d,1.));B=A.reflected()
 # det of the three raw edges is delta*(3+delta^2)>0: nonzero bounded tetra.
 exact_det=delta*(3+delta*delta);assert exact_det>0
 actual,noise=cone_intersection_margin(A,0,B,0)
 strict=cones_intersect_relint(A,0,B,0)
 assert strict is True
 row=dict(multiplier=m,all_inputs_binary64=True,actual_margin=actual,expected_margin=expected,
          actual_units=F(actual)/unit,expected_units=j,boolean_cone_feasible=strict,noise=noise,
          nearest_point_certificate=tuple(map(str,p)))
 rows.append(row)
 if actual!=expected:mismatches.append(row)
assert rows[0]['actual_margin']==math.ulp(0.) and rows[0]['expected_margin']==math.ulp(0.)
assert len(mismatches)==0
print(json.dumps(dict(result='FIXED',cases=len(rows),wrong_cases=len(mismatches),
 summary='positive representable cone margin lost or distorted by component-first rounding',
 verified_midpoint_case1='d^2/3 > d^2/4 and < 9*d^2/4 so nearest binary64 is d, not0',
 mismatches=mismatches,rows=rows),default=str,indent=2))
