"""WO-G6J: exact closed-set first entrance must include a touching initial point.

Primary oracle: Cartesian interval products, supplied rational affine rotation,
and box difference intervals. No eab geometry primitive is used for truth.
"""
from pathlib import Path
from fractions import Fraction as F
import sys, json
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from eab.kernel3d.geom3 import Polyhedron
from eab.kernel3d.entrance3 import first_entrance3

FACES = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
def box_vertices(center):
    signs = [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
             (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
    return [tuple(F(c)+s for c,s in zip(center,p)) for p in signs]

def pose(v, scale, shift, rotated):
    x,y,z = map(F,v)
    if rotated:
        x,y = F(3,5)*x-F(4,5)*y, F(4,5)*x+F(3,5)*y
    return tuple(scale*c+t for c,t in zip((x,y,z),shift))

def main():
    rows=[]
    # A=[-3/4,5/4]x[-7/8,9/8]x[1,3]; B=[-1,1]^3.
    # Closed products meet in a nonempty rectangle at z=1 at t=0.
    intersection=[(max(a,b),min(c,d)) for a,c,b,d in
                  ((F(-3,4),F(5,4),F(-1),F(1)),
                   (F(-7,8),F(9,8),F(-1),F(1)),
                   (F(1),F(3),F(-1),F(1)))]
    assert intersection == [(F(-3,4),F(1)),(F(-7,8),F(1)),(F(1),F(1))]
    # min{t>=0 : (A+t*d) intersects B} is 0 for every direction and cap>=0.
    for scale, shift, rotated in ((F(1),(0,0,0),False),
                                  (F(1,10**9),(10**8,-10**8,10**8),True),
                                  (F(10**8),(10**8,-10**8,10**8),True)):
        A=Polyhedron([pose(v,scale,shift,rotated) for v in box_vertices((F(1,4),F(1,8),2))],FACES)
        B=Polyhedron([pose(v,scale,shift,rotated) for v in box_vertices((0,0,0))],FACES)
        for direction,cap in (((1,0,0),F(0)),((1,0,0),F(1,16)),((0,0,1),F(1,16)),((0,0,-1),F(1,16))):
            d=pose(direction,scale,(0,0,0),rotated)
            try:
                got=first_entrance3(A,B,(0,0,0),d,tol=0,t_max=cap)
                row={'scale':str(scale),'rotated':rotated,'direction':direction,'cap':str(cap),
                     'want_kind':'entrance','want_exact_t':'0','got_kind':got.kind,
                     'got_exact_t':str(got.exact_t),'wrong':got.kind!='entrance' or got.exact_t!=0}
            except Exception as error:
                row={'scale':str(scale),'rotated':rotated,'direction':direction,'cap':str(cap),
                     'want_kind':'entrance','want_exact_t':'0','exception':repr(error),'wrong':True}
            rows.append(row)
    assert any(r.get('got_kind')=='none' and r['wrong'] for r in rows), 'original silent defect no longer reproduced'
    assert any(r.get('got_kind')=='entrance' and not r['wrong'] for r in rows), 'entering control must be correct'
    print(json.dumps({'status':'CONFIRMED','oracle_initial_intersection':str(intersection),'cases':rows},indent=2))

if __name__=='__main__':main()
