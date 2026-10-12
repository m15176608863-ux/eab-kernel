"""Independent random rounding-cell audit; no production primitive makes truth."""
import sys, math, random, struct, json, time
from pathlib import Path
from fractions import Fraction as F
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'src'))
from eab import construction as C
from eab import oracle_construction as O
MAX=F(sys.float_info.max)
BOUND=(MAX+F(2)**1024)/2

def cert(out,q,power):
    assert math.isfinite(out) and out>=0
    even=struct.unpack('>Q',struct.pack('>d',out))[0]%2==0
    if out:
        lo=(F(math.nextafter(out,0.0))+F(out))/2
        assert q>lo**power or q==lo**power and even, ('lower',out,q,power)
    nxt=math.nextafter(out,math.inf)
    hi=(F(out)+(F(nxt) if math.isfinite(nxt) else F(2)**1024))/2
    assert q<hi**power or q==hi**power and even, ('upper',out,q,power)

rng=random.Random(91743)
cases=[F(rng.getrandbits(rng.randrange(1,170))+1,rng.getrandbits(rng.randrange(1,170))+1)*F(2)**rng.randrange(-4200,2200) for _ in range(1200)]
counts={'sqrt':0,'scalar':0,'sqrt_overflow':0,'scalar_overflow':0,'signed_unit':0}
start=time.perf_counter()
for q in cases:
    for constructor,power,key in ((C.sqrt_rational,2,'sqrt'),(O.sqrt_exact,2,'sqrt'),
                                 (C.scalar_rational,1,'scalar'),(O.scalar_exact,1,'scalar')):
        if q>=BOUND**power:
            try:constructor(q,allow_underflow=True)
            except OverflowError:counts[key+'_overflow']+=1
            else:raise AssertionError(('missing-overflow',q,power))
        else:
            cert(constructor(q,allow_underflow=True),q,power)
            counts[key]+=1
for _ in range(100):
    v=tuple(F(rng.choice((-1,1)))*F(rng.randrange(1,1000))*F(2)**rng.randrange(-2000,2000) for _ in range(3))
    square=sum(x*x for x in v)
    for fn in (C.unit_rational,O.unit_exact):
        direction=fn(v,allow_underflow=True)
        for a,b in zip(v,direction):
            assert math.copysign(1,b)==(1 if a>0 else -1)
            cert(abs(b),a*a/square,2)
        counts['signed_unit']+=1
result={'counts':counts,'elapsed_s':time.perf_counter()-start,'status':'PASS'}
print(json.dumps(result,indent=2))
