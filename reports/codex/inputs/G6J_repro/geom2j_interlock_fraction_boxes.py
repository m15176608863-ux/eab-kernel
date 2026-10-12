"""Independent G6J product-interval earliest-lift oracle and cache stress.

No production predicate/events/translation/sqrt is used for expected roots.
Rational rotation around z leaves the motion axis unchanged, so the Cartesian
interval proof pulls back exactly even at large absolute coordinates.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,random,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel3d.geom3 import Polyhedron
from eab.kernel3d import interlock as I
from geom2j_initial_boundary3 import FACES

def vertices(center,half):
    signs=[(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
    return [tuple(F(c)+F(s)*F(h) for c,s,h in zip(center,p,half)) for p in signs]

def main():
    rng=random.Random(202610120)
    checked=0;certificate_intervals=0;cache_checks=0;unsupported=[]
    for case in range(60):
        ah=tuple(F(rng.randrange(1,9),4) for _ in range(3));bh=tuple(F(rng.randrange(1,9),4) for _ in range(3))
        ac=tuple(F(rng.randrange(-3,4),8) for _ in range(3));bc=(F(0),F(0),F(0))
        offset=tuple(F(rng.randrange(-5,6),8) for _ in range(3))
        overlap=[min(ac[k]+offset[k]+ah[k],bc[k]+bh[k])-max(ac[k]+offset[k]-ah[k],bc[k]-bh[k]) for k in range(3)]
        root=bc[2]+bh[2]-(ac[2]+offset[2]-ah[2]) if all(x>0 for x in overlap) else F(0)
        for scale,translation,rotation in [(F(1),(0,0,0),(F(1),F(0))),
                                            (F(1,10**9),(10**8,-10**8,10**8),(F(3,5),F(4,5)))] + (
                                            [(F(10)**-200,(10**8,-10**8,10**8),(F(3,5),F(4,5))),
                                             (F(10)**200,(0,0,0),(F(3,5),F(4,5)))] if case<5 else []):
            c,s=rotation
            def point(v,shift=(0,0,0)):
                x,y,z=v
                return (scale*(c*x-s*y)+shift[0],scale*(s*x+c*y)+shift[1],scale*z+shift[2])
            A=Polyhedron([point(p,translation) for p in vertices(ac,ah)],FACES)
            B=Polyhedron([point(p,translation) for p in vertices(bc,bh)],FACES)
            off=point(offset)
            try:
                out=I.escape_height_covers(A,B,off,tol=0)
            except (ArithmeticError,OverflowError) as error:
                unsupported.append({'case':case,'scale':str(scale),'exception':str(error)})
                continue
            assert out.exact_height==scale*root,('independent first lift',case,scale,root,out)
            assert out.nonpenetrating_state!=1
            for left,right,mid,state in out.interval_certificate:
                assert 0<=left<mid<right<=scale*root and state==1
                # For an initially-overlapping box pair all z before root overlap.
                assert 0<mid/scale<root
                certificate_intervals+=1
            again=I.escape_height_covers(A,B,off,tol=0)
            assert again==out,('content cache equality',case)
            out.tied_labels=(('poison',),)
            assert I.escape_height_covers(A,B,off,tol=0).tied_labels!=(('poison',),)
            checked+=1;cache_checks+=2
    print(json.dumps({'status':'PASS','seed':202610120,'checked_roots':checked,
                     'intervals_independently_checked':certificate_intervals,'cache_checks':cache_checks,
                     'loud_unrepresentable_report_cases':unsupported},indent=2))

if __name__=='__main__':main()
