"""Independent input-representability and algebraic jet control sweep.

Reference: exact Fraction expressions and CPython's specified rational RN
conversion; no eab construction/domain/dual routine supplies expected values.
Not a libm accuracy proof; geometric/cache coverage remains separate.
"""
from pathlib import Path
from fractions import Fraction as F
import math, sys, random

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'));sys.dont_write_bytecode=True
from eab.numeric_domain import binary64_argument, ConstructionDomainError, check_mu
from eab.dual import Dual

inputs=[F(0),F(1,3),F(10**400),F(10)**-400]
for bits in (1,2,52,53,54,65):
    odd=(1<<(bits-1))+1 if bits>1 else 1
    for exponent in (-2000,-1075,-1074,-1073,-1022,-400,0,971,972,1023,1024,2000):
        for sign in (-1,1):
            inputs.append(sign*F(odd)*F(2)**exponent)
            inputs.append(sign*F(odd,3)*F(2)**exponent)
accepted=rejected=0
for q in inputs:
    try:v=float(q);expected=math.isfinite(v) and F(v)==q
    except OverflowError:expected=False
    try:actual=binary64_argument(q,'support.binary64')
    except ConstructionDomainError:
        assert not expected,('false refusal',q);rejected+=1
    else:
        assert expected and F(actual)==q,('lossy accept',q,actual);accepted+=1
print(f'BINARY64_ARGUMENT_REFERENCE_PASS cases={len(inputs)} accepted={accepted} rejected={rejected}')

for q in (F(0),F(2)**20,F(2)**20-F(2)**-2000,F(2)**20+F(2)**-2000,F(-1),F(2)**-2000):
    expected=0<=q<=F(2)**20
    try:actual=check_mu(q)
    except ConstructionDomainError:assert not expected
    else:assert expected and actual==q
print('MU_EXACT_BOUNDARY_PASS cases=6')

def rn(q):
    try:v=float(q)
    except OverflowError:return None
    return v if math.isfinite(v) and (q==0 or v!=0) else None

rng=random.Random(150014)
values=[F(0),F(1),F(-1),F(2)**-1074,F(2)**-1075,F(2)**-2000,F(2)**2000,F(2)**400,F(2)**-400,F(1,3)]
for _ in range(50):values.append(F(rng.randrange(-9,10))*F(2)**rng.choice((-1000,-500,-10,0,10,500,1000)))
operations=passed=refusals=0
for _ in range(2500):
    u,v,a,b=(rng.choice(values) for i in range(4))
    kind=rng.choice(('add','sub','mul','div','rdiv','power'))
    if kind in ('div','rdiv') and (not v or not u):continue
    if kind=='add':primal=u+v;derivative=a+b;fn=lambda x,y:x+y
    elif kind=='sub':primal=u-v;derivative=a-b;fn=lambda x,y:x-y
    elif kind=='mul':primal=u*v;derivative=a*v+u*b;fn=lambda x,y:x*y
    elif kind=='div':primal=u/v;derivative=(a*v-u*b)/v**2;fn=lambda x,y:x/y
    elif kind=='rdiv':primal=v/u;derivative=(b*u-v*a)/u**2;fn=lambda x,y:y/x
    else:
        p=rng.choice((1,2,3,4,5));primal=u**p;derivative=F(p)*u**(p-1)*a;fn=lambda x,y,p=p:x**p
    expected=(rn(primal),rn(derivative));operations+=1
    try:actual=fn(Dual(u,(a,)),Dual(v,(b,)))
    except ConstructionDomainError:
        assert None in expected,(kind,'incorrect refusal',u,v,a,b,expected);refusals+=1
    else:
        assert None not in expected,(kind,'range failure',u,v,a,b,actual)
        assert (actual.v,actual.e[0])==expected,(kind,'wrong answer',u,v,a,b,actual,expected);passed+=1
print(f'DUAL_COMPLETE_SINGLE_OPERATION_PASS cases={operations} finite_results={passed} named_output_refusals={refusals}')
print('SUPPORT_CONTROLS_PASS (finite sweep only; not universal libm or compound-geometry proof)')
