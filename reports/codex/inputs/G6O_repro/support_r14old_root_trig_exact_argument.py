"""Inside-D400 phase error, independently enclosed by rational series.

Machin pi=16 atan(1/5)-4 atan(1/239); alternating series enclose pi.
Range reduction is rational on that interval. A rational Taylor polynomial,
its next-term bound, and |sin'|/|cos'| <= 1 enclose the reference value.
No libm, Decimal, mpmath or eab construction computes reference values.
"""
from pathlib import Path
from fractions import Fraction as F
import json, sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from eab.dual import sin, cos, Dual
from eab.numeric_domain import check_input

def arctan_interval(q,terms=48):
    assert 0<q<1
    value=sum(((-1)**j*q**(2*j+1)/F(2*j+1) for j in range(terms)),F(0))
    next_term=(-1)**terms*q**(2*terms+1)/F(2*terms+1)
    return min(value,value+next_term),max(value,value+next_term)

a,b=arctan_interval(F(1,5));c,d=arctan_interval(F(1,239))
pi_low,pi_high=16*a-4*d,16*b-4*c
assert 3<pi_low<pi_high<F(22,7)

def trigonometric_interval(x,kind):
    middle=(pi_low+pi_high)/2
    k=(x/(2*middle)+F(1,2)).numerator//(x/(2*middle)+F(1,2)).denominator
    assert k>=0
    low,high=x-2*k*pi_high,x-2*k*pi_low
    # Prove the chosen reduction is in [-pi,pi], not an uncertified float mod.
    assert -pi_low<low<=high<pi_low
    scale=10**35;mid=(low+high)/2
    scaled=mid*scale;point=F(scaled.numerator//scaled.denominator,scale)
    radius=max(abs(point-low),abs(point-high))
    value=F(0);term=point if kind=='sin' else F(1)
    terms=42
    for j in range(terms):
        value+=(-1)**j*term
        if kind=='sin':term*=point*point/F((2*j+2)*(2*j+3))
        else:term*=point*point/F((2*j+1)*(2*j+2))
    # Tail is alternating with decreasing absolute terms after these indices.
    assert abs(point)<4 and terms>2
    error=radius+abs(term)
    return value-error,value+error

rows=[]
for q in (F(2**54+1),F(2**54)+F(1,3)):
    check_input(q,'root.trig.exact_argument')
    for kind,function in (('sin',sin),('cos',cos)):
        low,high=trigonometric_interval(q,kind)
        scalar=function(q);jet=function(Dual(q,(F(1),)))
        assert not low<=F(scalar)<=high
        assert not low<=F(jet.v)<=high
        error_lower=min(abs(F(scalar)-low),abs(F(scalar)-high))
        assert error_lower>F(1,100), 'exhibit must be macroscopic, not a missing libm ulp bound'
        rows.append({'api':kind,'input_exact':str(q),'input_inside_D400':True,
                     'input_float':repr(float(q)),'actual_scalar':repr(scalar),
                     'actual_dual':repr(jet),'reference_interval_decimal_view':[float(low),float(high)],
                     'reference_interval_exact':[str(low),str(high)],
                     'certified_absolute_error_lower':str(error_lower)})
        print(f'{kind}({q}): scalar={scalar!r}, Dual={jet!r}, '
              f'independent enclosure=[{float(low):.17g},{float(high):.17g}], '
              f'absolute error > {float(error_lower):.17g}')
out={'confirmed':True,'cases':len(rows),'oracle':'Fraction Machin pi + rational Taylor remainder + Lipschitz input interval',
     'results':rows}
(ROOT/'review/evidence/root_trig_exact_argument.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print('TRIG_EXACT_ARGUMENT_CONFIRMED: 4 domain-inside macroscopic phase errors')
