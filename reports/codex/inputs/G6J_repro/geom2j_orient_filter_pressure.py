"""G6J independent Fraction orient2d audit across the binary64 exponent range."""
from pathlib import Path
from fractions import Fraction as F
import sys,random,struct,math,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel2d.geom import orient2d

def value(rng):
    bits=rng.getrandbits(64)
    if (bits>>52)&2047==2047:bits &= ~(2047<<52);bits|=2046<<52
    return struct.unpack('>d',struct.pack('>Q',bits))[0]

def main():
    rng=random.Random(103127331);checks=0;subnormal=0;overflow_derived=0
    for case in range(12000):
        if case<8000:
            a,b,c=[tuple(value(rng) for _ in range(2)) for _ in range(3)]
        else:
            e=rng.randrange(-1074,1022);s=math.ldexp(1.,e)
            a=(s,s);b=(math.nextafter(s,math.inf),s);c=(s,math.nextafter(s,math.inf))
            if case%2:c=(s,math.nextafter(s,0))
        ax,ay,bx,by,cx,cy=[F(x) for p in (a,b,c) for x in p]
        exact=(ax-cx)*(by-cy)-(ay-cy)*(bx-cx)
        expected=(exact>0)-(exact<0)
        assert orient2d(a,b,c)==expected,('filter wrong sign',case,a,b,c,str(exact))
        floating=(a[0]-c[0])*(b[1]-c[1])-(a[1]-c[1])*(b[0]-c[0])
        if not math.isfinite(floating):overflow_derived+=1
        if any(0<abs(x)<sys.float_info.min for p in (a,b,c) for x in p):subnormal+=1
        checks+=1
    print(json.dumps({'status':'PASS','seed':103127331,'checks':checks,
                     'subnormal_input_cases':subnormal,'nonfinite_float_determinant_cases':overflow_derived,
                     'zero_wrong_signs':True},indent=2))

if __name__=='__main__':main()
