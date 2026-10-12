"""Fraction midpoint-cell oracle for constructors; no production oracle/sqrt helper.
Verify returned binary64 cell using exact algebra and parity, not a guessed Decimal precision.
"""
from pathlib import Path
import sys,math,random,struct,json,time
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.construction import sqrt_rational,norm_rational,unit_rational,normalized_difference_rational
M=F(sys.float_info.max);overflow=(M+F(2)**1024)/2; tiny=F(math.ulp(0.0))

def cmp(a,b):return (a>b)-(a<b)
def bits(f):return struct.unpack('>Q',struct.pack('>d',f))[0]
def verify_cell(f,compare):
    assert math.isfinite(f)
    if f<0:return verify_cell(-f,lambda q:-compare(-q))
    lo=(F(math.nextafter(f,-math.inf))+F(f))/2 if f else -tiny/2
    hi=(F(f)+F(math.nextafter(f,math.inf)))/2 if f<sys.float_info.max else overflow
    assert compare(lo)>=0 and compare(hi)<=0,(f,str(lo),str(hi),compare(lo),compare(hi))
    if compare(lo)==0 or compare(hi)==0:assert bits(f)%2==0,('ties to even',f)

def root_cmp(q,r):
    if r<0:return 1
    return cmp(q,r*r)

def diff_cmp(c,n,o,r):
    r=r+o
    if c>=0 and r<0:return 1
    if c<0 and r>=0:return -1
    v=cmp(c*c,r*r*n)
    return -v if c<0 else v

def run():
    rng=random.Random(132626);t=time.time();out={'sqrt_cells':0,'norm_cells':0,'unit_cells':0,'difference_cells':0,'range_rejections':0}
    for case in range(5000):
        q=F(rng.randrange(1,10**8),rng.randrange(1,10**8))*F(2)**rng.randrange(-2800,2400)
        try:r=sqrt_rational(q,allow_underflow=True)
        except OverflowError:assert q>=overflow**2;out['range_rejections']+=1
        else:verify_cell(r,lambda x:root_cmp(q,x));out['sqrt_cells']+=1
        vs=[F(rng.randrange(-99,100),rng.randrange(1,99))*F(2)**rng.randrange(-1400,1200) for _ in range(rng.randrange(1,5))]
        if not any(vs):continue
        sq=sum(v*v for v in vs)
        try:r=norm_rational(vs,allow_underflow=True)
        except OverflowError:assert sq>=overflow**2;out['range_rejections']+=1
        else:verify_cell(r,lambda x:root_cmp(sq,x));out['norm_cells']+=1
        us=unit_rational(vs,allow_underflow=True)
        for u,v in zip(us,vs):
            if not v:assert u==0
            else:
                assert math.copysign(1,u)==(1 if v>0 else -1);verify_cell(abs(u),lambda x:root_cmp(v*v/sq,x))
            out['unit_cells']+=1
    for case in range(2500):
        e=rng.randrange(-1400,1400);p=rng.randrange(1,2800)
        c=rng.choice((-1,1))*F(rng.randrange(1,9))*F(2)**e
        n=1+F(2)**(-p)
        o=c if case%3 else c-F(2)**rng.randrange(-1400,1400)
        compare=lambda x:diff_cmp(c,n,o,x)
        try:r=normalized_difference_rational(c,n,o,allow_underflow=True)
        except OverflowError:
            assert compare(overflow)>=0 or compare(-overflow)<=0;out['range_rejections']+=1
        else:verify_cell(r,compare);out['difference_cells']+=1
    out['seconds']=time.time()-t;print(json.dumps(out,indent=2));(ROOT/'review/evidence/root_constructor_pressure.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
if __name__=='__main__':run()
