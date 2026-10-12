"""Independent topological E oracle using finite unions of exact rectangles."""
from pathlib import Path
from fractions import Fraction as F
import random,sys,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel2d.g0 import brute_ray_exit

def inside_union(cells,p):
    # A point is interior the finite closed union iff all four infinitesimal
    # coordinate quadrants belong to it. Choose exact rational points smaller
    # than every nonincident rectangle boundary coordinate.
    steps=[]
    for k in (0,1):
        values=[abs(F(v)-p[k]) for c in cells for v in c[2*k:2*k+2] if F(v)!=p[k]]
        steps.append(min(values,default=F(1))/2)
    return all(any(c[0]<p[0]+sx*steps[0]<c[1] and c[2]<p[1]+sy*steps[1]<c[3] for c in cells) for sx in (-1,1) for sy in (-1,1))
def expected(cells,x,u):
    assert inside_union(cells,x)
    times=set()
    for cell in cells:
        for k in (0,1):
            if u[k]:
                for b in cell[2*k:2*k+2]:
                    t=(b-x[k])/u[k]
                    if t>0:times.add(t)
    for t in sorted(times):
        if not inside_union(cells,(x[0]+t*u[0],x[1]+t*u[1])):return t
    raise AssertionError('bounded union must exit')
cases=[('L',[(0,0),(3,0),(3,1),(1,1),(1,3),(0,3)],[(0,3,0,1),(0,1,1,3)]),('U',[(-1,-1),(2,-1),(2,2),(1,2),(1,0),(0,0),(0,2),(-1,2)],[(-1,2,-1,0),(-1,0,0,2),(1,2,0,2)])]
rng=random.Random(1081);n=0;seams=0
for name,B,cells in cases:
    for width in (F(1,4),F(1,2),F(1),F(3,2)):
        A=[(0,0),(width,0),(width,width),(0,width)]
        ecells=[(F(a)-width,F(b),F(c)-width,F(d)) for a,b,c,d in cells]
        if name=='U' and width==1:
            x=(F(0),F(1,2));u=(F(0),F(1))
            assert inside_union(ecells,x) and not any(c[0]<x[0]<c[1] and c[2]<x[1]<c[3] for c in ecells)
            want=expected(ecells,x,u)
            assert brute_ray_exit([(F(a)+x[0],F(b)+x[1]) for a,b in A],B,u)==want==F(3,2)
            seams+=1;n+=1
        for i in range(200):
            x=(F(rng.randrange(-20,21),8),F(rng.randrange(-20,21),8))
            if not inside_union(ecells,x):continue
            u=(F(rng.randrange(-4,5)),F(rng.randrange(-4,5)))
            if u==(0,0):continue
            want=expected(ecells,x,u)
            moved=[(F(a)+x[0],F(b)+x[1]) for a,b in A]
            got=brute_ray_exit(moved,B,u)
            assert got==want,(name,width,x,u,got,want)
            n+=1
            if not any(c[0]<x[0]<c[1] and c[2]<x[1]<c[3] for c in ecells):seams+=1
out={'comparisons':n,'interior_seam_initial_cases':seams,'mismatches':0,'seed':1081,'independence':'topological interior via Cartesian quadrant cells and line-plane times; no production geometry/oracle primitive shared'}
print(json.dumps(out,indent=2))
(ROOT/'review/agents/geom2/ray_exit_pressure.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
