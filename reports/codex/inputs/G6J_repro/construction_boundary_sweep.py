"""G6J independent Fraction-cell audit; no production oracle is used."""
from fractions import Fraction as F
from pathlib import Path
import math, random, struct, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from eab import construction as p, oracle_construction as o

MAX = float.fromhex('0x1.fffffffffffffp1023')
SUCCESSOR = F(2)**1024
OVERFLOW = (F(MAX)+SUCCESSOR)/2
def bits(x): return struct.unpack('>Q', struct.pack('>d', x))[0]
def fb(k): return struct.unpack('>d', struct.pack('>Q', k))[0]
def cell(y, q, power=1):
    assert math.isfinite(y) and y >= 0
    even = not bits(y)%2
    if y:
        low = (F(math.nextafter(y, 0.0))+F(y))/2
        assert q > low**power or (q == low**power and even), (y.hex(), 'lower')
    hi = math.nextafter(y, math.inf)
    up = (F(y)+(F(hi) if math.isfinite(hi) else SUCCESSOR))/2
    assert q < up**power or (q == up**power and even), (y.hex(), 'upper')

def cmp_algebraic(c, nn, off, x):
    """Sign(c/sqrt(nn)-off-x), using only independent rational comparisons."""
    r = off+F(x)
    if c == 0: return (r<0)-(r>0)
    if c > 0 and r <= 0: return 1
    if c < 0 and r >= 0: return -1
    z = c*c-r*r*nn
    return ((z>0)-(z<0)) * (1 if c>0 else -1)

def normalized_cell(y, c, nn, off):
    sign=cmp_algebraic(c,nn,off,0)
    if not sign:
        assert y==0; return
    assert y==0 or (y>0)==(sign>0)
    if sign<0: y,c,off=-y,-c,-off
    assert math.isfinite(y) and y>=0
    even=not bits(y)%2
    if y:
        low=(F(math.nextafter(y,0.))+F(y))/2
        z=cmp_algebraic(c,nn,off,low)
        assert z>0 or (not z and even), (y.hex(),'normalized lower')
    hi=math.nextafter(y,math.inf)
    up=(F(y)+(F(hi) if math.isfinite(hi) else SUCCESSOR))/2
    z=cmp_algebraic(c,nn,off,up)
    assert z<0 or (not z and even), (y.hex(),'normalized upper')

counts={'scalar':0,'sqrt':0,'norm':0,'unit_component':0,'normalized':0}
r=random.Random(631010)
anchor_bits=[0,1,2,0xfffffffffffff,0x10000000000000,0x3ff0000000000000,0x7feffffffffffffe,0x7fefffffffffffff]
anchor_bits += [r.randrange(0x7ff0000000000000) for _ in range(600)]
for k in anchor_bits:
    lo=F(fb(k)); hi=F(fb(k+1)) if k<0x7fefffffffffffff else SUCCESSOR
    mid=(lo+hi)/2
    for value in [lo,mid-(hi-lo)/64,mid,mid+(hi-lo)/64]:
        for f,power in [(p.scalar_rational,1),(o.scalar_exact,1),(p.sqrt_rational,2),(o.sqrt_exact,2)]:
            q=value**power
            if value>=OVERFLOW:
                try: f(q,allow_underflow=True)
                except OverflowError: pass
                else: raise AssertionError(('overflow accepted',f.__name__))
            else: cell(f(q,allow_underflow=True),q,power)
            counts['scalar' if power==1 else 'sqrt'] += 1
        for sign in [1,-1]:
            c,nn,off=sign*(value+F(2)**1100),F(1),sign*F(2)**1100
            if value>=OVERFLOW:
                try: p.normalized_difference_rational(c,nn,off,allow_underflow=True)
                except OverflowError: pass
                else: raise AssertionError('normalized overflow accepted')
            else: normalized_cell(p.normalized_difference_rational(c,nn,off,allow_underflow=True),c,nn,off)
            counts['normalized'] += 1

for exponent in [-2200,-1075,-1074,-1022,-600,0,600,1023,1100,2200]:
    v=(F(2)**exponent,F(-3)*F(2)**(exponent-1),F(5)*F(2)**(exponent-1076))
    nn=sum(x*x for x in v)
    for norm,unit in [(p.norm_rational,p.unit_rational),(o.norm_exact,o.unit_exact)]:
        if nn>=OVERFLOW*OVERFLOW:
            try: norm(v,allow_underflow=True)
            except OverflowError: pass
            else: raise AssertionError('norm overflow accepted')
        else: cell(norm(v,allow_underflow=True),nn,2)
        counts['norm']+=1
        u=unit(v,allow_underflow=True)
        for x,y in zip(v,u):
            assert y==0 or (y>0)==(x>0)
            cell(abs(y),x*x/nn,2);counts['unit_component']+=1

for exponent in [-1074,-600,0,100,1024,2000,5000]:
    c=F(2)**exponent; nn=F(2)
    if exponent>=0: off=F(math.isqrt(c.numerator*c.numerator//2))
    else: off=F(0)
    for sign in [1,-1]:
        for delta in [F(0),F(1,7),F(2)**-1074]:
            C,O=sign*c,sign*off+delta
            y=p.normalized_difference_rational(C,nn,O,allow_underflow=True)
            normalized_cell(y,C,nn,O);counts['normalized']+=1
print('CONSTRUCTION_BOUNDARY_SWEEP PASS',counts)
