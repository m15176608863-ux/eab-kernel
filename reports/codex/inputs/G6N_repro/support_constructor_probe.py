"""Independent Fraction RN-cell audit of production scalar/sqrt boundary.
The oracle imports no eab constructor/geometry function; it certifies cell
inequalities directly, including conceptual successor 2**1024 of max float.
Run: python -X utf8 review/repro/support_constructor_probe.py
"""
from pathlib import Path
import sys,random,math,struct
from fractions import Fraction as F
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
from eab.construction import scalar_rational,sqrt_rational
from eab.numeric_domain import ConstructionDomainError

MIN_HALF=F(2)**-1075
MAX=F(float.fromhex("0x1.fffffffffffffp+1023"))
MAX_HALF=(MAX+F(2)**1024)/2

def certify(actual,q,power):
    assert math.isfinite(actual)
    if q<0: actual,q=-actual,-q
    assert actual>=0
    bits=struct.unpack(">Q",struct.pack(">d",actual))[0]
    even=bits%2==0
    if actual:
        lower=(F(math.nextafter(actual,0.0))+F(actual))/2
        assert q>lower**power or (q==lower**power and even)
    upper_float=math.nextafter(actual,math.inf)
    upper=(F(actual)+(F(upper_float) if math.isfinite(upper_float) else F(2)**1024))/2
    assert q<upper**power or (q==upper**power and even)
    assert q==0 or actual!=0

r=random.Random(614)
qs=[F(0), MIN_HALF,MIN_HALF*F(3,2),MAX_HALF,MAX_HALF-1,MAX_HALF+1]
for i in range(2048):
    e=r.randrange(-2400,2401)
    qs.append(F(r.randrange(1,2**55),r.randrange(1,2**55))*F(2)**e)
# Include exact midpoint radicands for ties; production root must obey parity.
for e in (-1074,-1000,-400,-1,0,400,1000,1023):
    x=math.ldexp(1.0,e)
    for i in range(16):
        upper=math.nextafter(x,math.inf)
        if math.isfinite(upper): qs.append(((F(x)+F(upper))/2)**2)
        x=upper
checks=accepted=rejected=0
for q in qs:
    for f,power in ((scalar_rational,1),(sqrt_rational,2)):
        checks+=1
        valid=q==0 or MIN_HALF**power<q<MAX_HALF**power
        try: got=f(q)
        except ConstructionDomainError:
            assert not valid,(f.__name__,q,"unexpected domain rejection")
            rejected+=1
        else:
            assert valid,(f.__name__,q,got,"out-of-domain silent result")
            certify(got,q,power);accepted+=1
print(f"independent Fraction cell checks={checks}; accepted={accepted}; correctly rejected={rejected}; mismatches=0")
