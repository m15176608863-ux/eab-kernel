"""Independent squared-midpoint derivative oracle, no production sqrt oracle.

For sqrt(v) with seed a>0 the analytic derivative has exact squared value
a*a/(4*v). Thus Fraction squares of neighboring binary64 midpoints decide
its correctly rounded value without computing an irrational square root.
"""
from pathlib import Path
from fractions import Fraction as F
import sys, math, json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.dual import Dual,sqrt
u=math.ulp(0.0)
v=math.nextafter(1.0,math.inf)
rows=[]
for m in (3,7,11,15):
    seed=m*u
    result=sqrt(Dual(v,(seed,)))
    squared=F(seed)**2/(4*F(v))
    expected=(m//2)*u
    lower=(F(math.nextafter(expected,0.0))+F(expected))/2
    upper=(F(expected)+F(math.nextafter(expected,math.inf)))/2
    assert lower**2 < squared < upper**2
    assert result.e[0] != expected
    assert result.e[0] == (m//2+1)*u
    rows.append(dict(v_hex=v.hex(),seed_units=m,actual_primal=result.v,
                     actual_derivative_units=str(F(result.e[0])/F(u)),
                     correct_derivative_units=m//2,
                     proof='a^2/(4*v) lies strictly inside expected neighboring midpoint squares'))
print(json.dumps(dict(result='CONFIRMED',kind='representable derivative double-rounding',rows=rows),indent=2))
for v,a in ((2.0**1022,2.0**-600),(u,2.0**1023)):
    r=sqrt(Dual(v,(a,)))
    assert r.e[0]==0 or math.isinf(r.e[0])
    print('UNCHECKED DERIVATIVE RANGE:',repr(r))
