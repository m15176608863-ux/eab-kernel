"""Independent rational box-product oracle; no production geometry oracle.

Runs current checkout, creates no tracked artifacts. Tests the actual OR policy,
each advertised model's displacement / shell bound, and public margin state.
"""
from pathlib import Path
import sys, json
from fractions import Fraction as F
from itertools import product
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from eab.kernel3d.geom3 import Polyhedron
from eab.kernel3d.exact_sweep import contact_models
from eab.margin import inflated_membership, ON_BOUNDARY, INSIDE

FACES = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
SIGNS = [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
FRAMES = [((1,0,0),(0,1,0),(0,0,1)), ((F(5,13),-F(12,13),0),(F(12,13),F(5,13),0),(0,0,1))]

def make(centre, half, frame, scale, origin):
    return Polyhedron([tuple(F(origin[k])+scale*sum(F(frame[k][j])*(F(centre[j])+sign[j]*F(half[j])) for j in range(3)) for k in range(3)) for sign in SIGNS], list(FACES))

def intervals(body, frame):
    points = [tuple(sum(F(frame[k][j])*F(p[k]) for k in range(3)) for j in range(3)) for p in body.verts]
    bounds = [(min(p[j] for p in points),max(p[j] for p in points)) for j in range(3)]
    assert set(points) == set(product(*bounds)), 'not an exact product box'
    return bounds

def state(a,b,frame):
    widths = [min(x[1],y[1])-max(x[0],y[0]) for x,y in zip(intervals(a,frame),intervals(b,frame))]
    return -1 if min(widths)<0 else 0 if min(widths)==0 else 1

def model_check(original, core, w):
    centre=tuple(sum(F(v[k]) for v in original.verts)/8 for k in range(3))
    factors={(F(q[k])-centre[k])/(F(p[k])-centre[k]) for p,q in zip(original.verts,core.verts) for k in range(3) if F(p[k])!=centre[k]}
    assert len(factors)==1
    factor=factors.pop()
    assert F(1,2)<=factor<1
    # Norm is convex, hence this vertex maximum bounds every surface radial ray.
    assert max(sum((F(p[k])-F(q[k]))**2 for k in range(3)) for p,q in zip(original.verts,core.verts))<=w*w

def main():
    rows=[]
    for frame,scale,origin,axis,penetration in product(FRAMES,[F(1,10**9),F(1),F(10**5)],[(0,0,0),(10**8,-10**8,3*10**7)],range(3),[F(1,8),F(1,4),F(3,8)]):
        w=scale/4
        centre=tuple(2-penetration if k==axis else 0 for k in range(3))
        a=make((0,0,0),(1,1,1),frame,scale,origin)
        b=make(centre,(1,1,1),frame,scale,origin)
        assert state(a,b,frame)==1
        models=contact_models(a,b,w)
        accepted=[]
        for name,ca,cb in models:
            if name=='core_A': model_check(a,ca,w)
            if name=='core_B': model_check(b,cb,w)
            if name.startswith('shift_'):
                displacement=tuple(F(ca.verts[0][k])-F(a.verts[0][k]) for k in range(3))
                assert sum(x*x for x in displacement)==w*w
                assert all(tuple(F(q[k])-F(p[k]) for k in range(3))==displacement for p,q in zip(a.verts,ca.verts))
            if state(ca,cb,frame)<=0:accepted.append(name)
        got=inflated_membership(a,b,delta=0,contact_window=w)
        expected=ON_BOUNDARY if accepted else INSIDE
        assert got==expected,(axis,scale,origin,penetration,accepted,got,expected)
        rows.append({'axis':axis,'scale':str(scale),'origin':origin,'penetration':str(penetration),'accepted':accepted,'state':got})
    out={'cases':len(rows),'mismatches':0,'oracle':'independent Fraction product boxes; exact rational orthogonal frames; no production membership, normals, distance, SAT, triangulation, or star-centre oracle','rows':rows}
    path=ROOT/'review'/'logs'/'root_window_certificates.json'
    path.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in out.items() if k!='rows'},ensure_ascii=False))

if __name__=='__main__':main()
