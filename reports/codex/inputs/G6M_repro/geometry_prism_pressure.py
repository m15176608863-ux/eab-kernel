"""WO-G6M product-prism adversarial first-contact oracle.

The 3D oracle is reduced by construction to 2D horizontal slab arrangements.
Independent 2D scanline code is review-owned (historical G6L oracle replay).
No eab primitive defines oracle truth, surfaces, event times or feature planes.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,random,time,json
ROOT=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'review/repro')]
import geometry_scanline_pressure as O
from eab.kernel3d.geom3 import Polyhedron,polyhedra_overlap
from eab.kernel3d.entrance3 import first_entrance3
from eab.kernel3d.interlock import escape_height_covers

def prism(ring,lo=F(-1),hi=F(1)):
    n=len(ring);verts=[(x,y,z) for z in (lo,hi) for x,y in ring]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return Polyhedron(verts,faces)
def joined(bodies):
    verts=[];faces=[]
    for body in bodies:
        offset=len(verts);verts+=body.verts;faces += [tuple(i+offset for i in f) for f in body.faces]
    return Polyhedron(verts,faces)
def main():
    rng=random.Random(130505);rows=[];errors=[];started=time.perf_counter()
    for k in range(96):
        a=O.ring(rng,3+k%4);b=O.ring(rng,3+(k+1)%4)
        # Guaranteed initially separated; movement may touch then leave before
        # hitting a second disconnected solid, testing whole-prefix firstness.
        offset_y=F(rng.randrange(-16,17),8)
        a=[(x-F(12),y+offset_y) for x,y in a]
        scale=(F(1),F(1,10**9),F(10**8),F(1,10**15))[k%4]
        origin=(F(10**8),F(-10**8)) if k%3 else (F(0),F(0))
        c,s=(F(3,5),F(4,5)) if k%2 else (F(1),F(0))
        a=[O.pose(p,scale,origin,c,s) for p in a];b=[O.pose(p,scale,origin,c,s) for p in b]
        d=O.pose((F(1),F(rng.randrange(-3,4),8)),scale,(0,0),c,s)
        b2=[(x+F(12)*scale*c,y+F(12)*scale*s) for x,y in b]
        want=O.state(a,b);want_t=O.ray(a,b,d,F(40))
        if k%3==0:
            second_t=O.ray(a,b2,d,F(40));want_t=min((v for v in (want_t,second_t) if v is not None),default=None)
        A=prism(a,-scale,scale);B=prism(b,-scale,scale)
        if k%3==0:B=joined([B,prism(b2,-scale,scale)])
        row=dict(case=k,scale=str(scale),want=want,want_t=str(want_t),disconnected=k%3==0)
        try:
            state=polyhedra_overlap(A,B,0);e=first_entrance3(A,B,(0,0,0),(*d,0),tol=0,t_max=40)
            row.update(got=state,kind=e.kind,got_t=str(e.exact_t))
            if state!=want:errors.append(dict(row,problem='overlap'))
            if (want_t is None and e.kind!='none') or want_t is not None and (e.kind!='entrance' or e.exact_t!=want_t):errors.append(dict(row,problem='first-contact'))
        except Exception as exc:errors.append(dict(row,problem='exception',error=repr(exc)))
        rows.append(row)
        out=dict(cases=len(rows),errors=errors,rows=rows,seconds=time.perf_counter()-started,oracle='review-owned independent 2D Fraction horizontal slab arrangement and raw endpoint/edge time enumeration; exact product prism model')
        (ROOT/'review/geometry/prism_pressure.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
        print(k,row.get('kind'),str(want_t),row.get('got_t'),flush=True)
    print(json.dumps({k:v for k,v in out.items() if k!='rows'},ensure_ascii=False,indent=2));assert not errors,errors[:3]
if __name__=='__main__':main()
