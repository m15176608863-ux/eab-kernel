"""Independent exact power-of-two derivative oracle; never uses Dual as oracle."""
import sys, math, json
from pathlib import Path
from fractions import Fraction as F
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from eab.dual import Dual

def half_power(base_exponent, p):
    exponent=F(base_exponent)*p
    assert exponent.denominator == 1
    return F(2)**int(exponent)

examples=[]
checked=wrong=loud=0
for exponent in (-200,-180,-160,-140,140,160,180,200):
    for seed_exp in (-200,-100,0,100,200):
        for p in [F(k,2) for k in range(-16,17) if k]:
            q=p*half_power(exponent,p-1)*F(2)**seed_exp
            try: expected=float(q)
            except OverflowError: continue
            if expected==0: continue
            # Restrict to a finite, nonzero primal and finite, nonzero derivative.
            try: primal=float(half_power(exponent,p))
            except OverflowError: continue
            if primal==0 or not math.isfinite(primal): continue
            checked+=1
            try: got=Dual(math.ldexp(1.,exponent),(math.ldexp(1.,seed_exp),))**float(p)
            except (OverflowError,ArithmeticError) as e:
                loud+=1
                continue
            if got.e[0] != expected:
                wrong+=1
                if len(examples)<8:
                    examples.append(dict(base_exp=exponent,seed_exp=seed_exp,p=str(p),
                                         primal=got.v,got_derivative=got.e[0],expected_derivative=expected))

x=2.**200
r=Dual(x,(x,))**-5
truth=float(F(-5)*F(x)**-6*F(x))
assert r.v==2.**-1000 and truth!=0 and math.isfinite(truth)
assert r.e[0]==0 and r.e[0]!=truth
print(json.dumps(dict(checked=checked,silent_wrong=wrong,loud_refusals=loud,examples=examples,
                     minimal=dict(x=x,p=-5,seed=x,got_primal=r.v,got_derivative=r.e[0],expected_derivative=truth,
                                  expected_hex=truth.hex())),indent=2))
