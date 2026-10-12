"""Independent exact squares + Decimal root expose pre-rounded 2D VV construction."""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal,localcontext
import json,sys,math
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel2d.covers import vv_cover
q=float.fromhex('0x0.0000000000001p-1022')
def sqrt_fraction(square):
    with localcontext() as c:
        c.prec=160
        return float((Decimal(square.numerator)/Decimal(square.denominator)).sqrt())
def desired_normal(dx,dy):
    dx,dy=F(dx),F(dy);square=dx*dx+dy*dy
    return [sqrt_fraction(dx*dx/square),sqrt_fraction(dy*dy/square)]
out=[]
# float-only coordinates: norm(d) rounds into subnormal range before dividing.
s=2.**-600
A=[(q,q),(s,q),(s,s),(q,s)];B=[(-s,-s),(0.,-s),(0.,0.),(-s,0.)]
c=vv_cover(A,0,B,2)
want=desired_normal(q,q)
assert c.strict and c.normal==(1.,1.) and abs(math.hypot(*c.normal)-1)>0.4
out.append({'input':'binary64 d=(minsubnormal,minsubnormal)','gap':c.gap,
            'normal':c.normal,'normal_expected':want,'normal_norm':math.hypot(*c.normal)})
# Mixed/exact coordinates: components round before the norm and the final
# representable gap is therefore wrong by an entire subnormal ULP.
dx,dy=F(149,100)*F(q),F(49,100)*F(q);ss=F(s)
A=[(dx,dy),(dx+ss,dy),(dx+ss,dy+ss),(dx,dy+ss)]
B=[(-ss,-ss),(0,-ss),(0,0),(-ss,0)]
c=vv_cover(A,0,B,2);square=dx*dx+dy*dy
# Rigorous final-rounding proof independent of Decimal: sqrt(square) is between
# 1.5q and 2.5q, hence its nearest binary64 is 2q, not q.
assert (F(3,2)*F(q))**2<square<(F(5,2)*F(q))**2
truth=float(2*F(q))
assert c.strict and c.gap==q and c.gap!=truth
out.append({'input':'rational d=(1.49q,0.49q)','gap':c.gap,'gap_expected':truth,
            'normal':c.normal,'normal_expected':desired_normal(dx,dy)})
# float-only largest-range: true unit direction is perfectly representable.
m=float.fromhex('0x1.fffffffffffffp1023');h=m/2;k=m/4
A=[(h,h),(h+k,h),(h+k,h+k),(h,h+k)]
B=[(-h-k,-h-k),(-h,-h-k),(-h,-h),(-h-k,-h)]
c=vv_cover(A,0,B,2)
assert c.strict and c.normal==(0.,0.) and math.isinf(c.gap)
out.append({'input':'binary64 d=(maxfinite,maxfinite)','gap':str(c.gap),
            'normal':c.normal,'normal_expected':desired_normal(m,m),
            'expected_gap_policy':'unrepresentable norm should raise, not silently inf'})
print(json.dumps(out,indent=2))
