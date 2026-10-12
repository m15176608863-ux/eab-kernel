"""G6J: public normal_cone explicit small-reflex window + in_cone inverse ray.

Independent exclusion certificate: a vector with negative dot product with
BOTH reported boundary rays is >pi/2 from each, hence cannot be inside a
sin-window 1/50 around their common downward ray. No production cone helper
is used for the certificate itself.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from eab.kernel2d.covers import normal_cone,in_cone

def main():
    P=[(0,0),(1,0),(2,F(-1,100)),(2,1),(0,1)]
    # Vertex 1 has exact right turn -1/100 and dot(e0,e1)=1.
    # It is intentionally admitted ONLY by the documented explicit sin window.
    assert normal_cone(P,1,tol=0) is None
    rows=[]
    for scale,shift,rot in ((F(1),(0,0),(F(1),F(0))),
                           (F(1,10**9),(10**8,-10**8),(F(3,5),F(4,5))),
                           (F(10**8),(10**8,-10**8),(F(3,5),F(4,5)))):
        c,s=rot
        def transform(p):
            x,y=map(F,p);return (scale*(c*x-s*y)+shift[0],scale*(s*x+c*y)+shift[1])
        A=list(map(transform,P))
        cone=normal_cone(A,1,tol=F(1,50))
        assert cone is not None,'explicit micro-reflex input is promised admissible'
        # Opposite-to-normal direction, rotated but not translated/scaled.
        v=(c*F(1,200)-s,s*F(1,200)+c)
        products=[F(n[0])*v[0]+F(n[1])*v[1] for n in cone]
        assert all(z<0 for z in products),'independent opposite-halfplane certificate'
        output=in_cone(cone,v,tol=F(1,50))
        assert output==1,'original wrong strict answer no longer reproduced'
        down=tuple(-x for x in v)
        rows.append({'scale':str(scale),'rotation':list(map(str,rot)),
                     'reported_cone':cone,'direction':list(map(str,v)),
                     'independent_dot_signs':['negative','negative'],
                     'angle_to_each_boundary':'>pi/2','window':'1/50',
                     'expected_inverse':'-1','got_inverse':output,
                     'got_downward_window':in_cone(cone,down,tol=F(1,50))})
    print(json.dumps({'status':'CONFIRMED','cases':rows,
                     'scope':'public helper composition only; ve_cover/vv_cover use other exact predicates'},indent=2))

if __name__=='__main__':main()
