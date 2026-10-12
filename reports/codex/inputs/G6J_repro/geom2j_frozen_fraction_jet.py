"""G6J reviewer-owned analytic VF jet oracle, Fraction polynomial + Decimal.

Expected c, N, dN, dc are assembled inline from three raw triangle coordinates
and a point, never by eab dot/cross/normal/jet/construction routines. Decimal
1000-digit radical evaluation is used only for the final binary64 displays.
"""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal,localcontext
import sys,random,math,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.dual import Dual
from eab.kernel3d.geom3 import Polyhedron
from eab.kernel3d.frozen import frozen_gap,frozen_normal

def minus(a,b):return tuple(x-y for x,y in zip(a,b))
def plus(a,b):return tuple(x+y for x,y in zip(a,b))
def times(a,b):return sum(x*y for x,y in zip(a,b))
def determinant(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def dec(q):return Decimal(q.numerator)/Decimal(q.denominator)

def main():
    rng=random.Random(7100013);cases=0;channels=0
    for case in range(200):
        scale=F(10)**rng.choice((-200,-40,0,40,200))
        origin=tuple(F(rng.randrange(-2,3))*F(10)**100 for _ in range(3))
        while True:
            p=[tuple(origin[k]+scale*rng.randrange(-10,11) for k in range(3)) for _ in range(4)]
            u,v=minus(p[1],p[0]),minus(p[2],p[0]);n=determinant(u,v);nn=times(n,n)
            if nn:break
        derivs=[[tuple(scale*F(rng.randrange(-4,5)) for _ in range(3)) for _ in range(4)] for _ in range(3)]
        # Three channel point/triangle affine jets.
        obj=[tuple(Dual(p[i][k],tuple(derivs[w][i][k] for w in range(3))) for k in range(3)) for i in range(4)]
        B=Polyhedron(obj[:3],[(0,1,2)]);A=Polyhedron([obj[3]],[])
        offset=scale*F(rng.randrange(-3,4),3)
        d_offset=tuple(scale*F(rng.randrange(-2,3),3) for _ in range(3))
        label=('VF',('vertex',0),('face',0))
        got=frozen_gap(A,B,label,(0,0,0),delta=Dual(offset,d_offset))
        with localcontext() as context:
            context.prec=1000
            length=dec(nn).sqrt();r=minus(p[3],p[0]);c=times(n,r)
            expected=float(dec(c)/length-dec(offset))
            assert got.v==expected,('primal analytic expression',case,got.v,expected)
            for w,dd in enumerate(derivs):
                du,dv=minus(dd[1],dd[0]),minus(dd[2],dd[0])
                dn=plus(determinant(du,v),determinant(u,dv));dr=minus(dd[3],dd[0])
                dc=times(dn,r)+times(n,dr)
                numerator=dc-c*times(n,dn)/nn
                expected=float(dec(numerator)/length-dec(d_offset[w]))
                assert got.e[w]==expected,('derivative analytic expression',case,w,got.e[w],expected)
                channels+=1
        # Passing the certificate-bearing display normal must retain EXACT jet.
        ndisplay=frozen_normal(A,B,label)
        same=frozen_gap(A,B,label,(0,0,0),n=ndisplay,delta=Dual(offset,d_offset))
        assert same.v==got.v and same.e==got.e,('retained raw jet',case)
        cases+=1
    print(json.dumps({'status':'PASS','seed':7100013,'primal_cases':cases,'derivative_channels':channels,
                     'raw_jet_certificate_reuses':cases,'decimal_precision':1000,'zero_disagreements':True},indent=2))

if __name__=='__main__':main()
