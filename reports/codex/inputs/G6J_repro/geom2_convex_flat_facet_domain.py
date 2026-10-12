"""Confirm a finite-facet domain error; oracle uses only Cartesian coordinates.

A triangle's minimum y is its unique vertex 0. B's maximum y is 1, so along
x=(1/2,2-t), no intersection is possible for t<1. At t=1 the only touching
A point is (1/2,1), which is on B edge 3 but not edge 2. No hull, cone,
membership or eab helper is used to establish this truth.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json,math
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel2d.entrance import first_entrance
A=[(0,0),(1,1),(0,2)]
B=[(0,0),(3,0),(3,1),(1,1),(0,1)]
def transformed(P,s,c,t):
    co,si=c
    return [(s*(co*F(x)-si*F(y))+t[0],s*(si*F(x)+co*F(y))+t[1]) for x,y in P]
assert min(y for x,y in A)==0 and [i for i,p in enumerate(A) if p[1]==0]==[0]
assert max(y for x,y in B)==1
assert 0<F(1,2)<1 and not 1<=F(1,2)<=3
outputs=[]
for s,c,t in [(F(1),(F(1),F(0)),(F(0),F(0))),
              (F(1,10**9),(F(1),F(0)),(F(0),F(0))),
              (F(10**8),(F(1),F(0)),(F(0),F(0))),
              (F(1),(F(3,5),F(4,5)),(F(10**8),F(-10**8)))]:
    At,Bt=transformed(A,s,c,t),transformed(B,s,c,t)
    x=transformed([(F(1,2),F(2))],s,c,(F(0),F(0)))[0]
    d=transformed([(F(0),F(-1))],s,c,(F(0),F(0)))[0]
    r=first_entrance(At,Bt,x,d)
    assert r.t_exact==1 and r.kind=='entrance'
    # Deliberately assert the current defect, making this a successful confirmation script.
    assert r.label==('VE',0,2) and ('VE',0,2) in r.tied_labels,r
    bad_distance=math.hypot(r.point_a[0]-r.point_b[0],r.point_a[1]-r.point_b[1])
    assert bad_distance>float(s)/4,(s,r)
    outputs.append({'scale':str(s),'rotation':list(map(str,c)),'translation':list(map(str,t)),
                    'expected_t':'1','expected_label':['VE',0,3],'actual_label':r.label,
                    'actual_tied_labels':r.tied_labels,'point_a':r.point_a,'point_b':r.point_b,
                    'gap':r.gap,'witness_separation':bad_distance})
# Same finite-domain omission, this time FF construction refuses an unrelated edge.
A2=[(0,-1),(1,-1),(1,0),(1,1),(0,1),(0,0)]
B2=[(-1,0),(0,0),(1,0),(1,1),(0,1),(-1,1)]
# These are closed rectangles [0,1]x[-1,1] and [-1,1]x[0,1].
# At x=(1,2), their only intersection is (1,1), so closed first entrance t=0.
try:first_entrance(A2,B2,(1,2),(2,1))
except ArithmeticError as err:
    assert 'face witness has no segment overlap' in str(err)
    ff_error=str(err)
else:raise AssertionError('known FF instance did not reproduce')
print(json.dumps({'finding':'G6I-GEOM2-01','confirmed':True,'oracle':'raw Cartesian support intervals',
                  'silent_wrong_label_and_witness':outputs,'valid_boundary_FF_error':ff_error},ensure_ascii=False,indent=2))
