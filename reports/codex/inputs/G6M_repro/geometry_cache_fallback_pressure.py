"""WO-G6M production shortcut/cache equivalence against exact product boxes.

Truth is from independent interval intersections/distance, not hulls/SAT.
Disabling sufficient shortcuts asks the real complete arrangement fallback.
Mutable input and returned aliases are stressed without changing tracked code.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import product
import sys,random,math,json,time
ROOT=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT/'src'))
from eab.kernel3d.geom3 import Polyhedron,polyhedra_overlap,exact_convex_view
from eab.kernel3d import exact_geom as G
from eab.margin import body_distance,_resolved
import eab.margin as M
SIGNS=((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))
FACES=((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))
def box(bounds):return Polyhedron([tuple(bounds[k][(p[k]+1)//2] for k in range(3)) for p in SIGNS],list(FACES))
def state(a,b):
    widths=[min(x[1],y[1])-max(x[0],y[0]) for x,y in zip(a,b)]
    return -1 if min(widths)<0 else 0 if min(widths)==0 else 1
def distance2(a,b):return sum(max(y[0]-x[1],x[0]-y[1],F(0))**2 for x,y in zip(a,b))
def sqrt_ok(q,g):
    if q==0:return g==0
    low=(F(math.nextafter(g,-math.inf))+F(g))/2;high=(F(math.nextafter(g,math.inf))+F(g))/2
    return low*low<=q<=high*high
def main():
    started=time.perf_counter();rng=random.Random(130503);rows=[];errors=[]
    A=box([(-1,1)]*3);B=box([(-1,1)]*3)
    saved=(G._convex_surface_sat,G._star_union_overlap,G._transverse_interior_witness)
    for k in range(120):
        scale=(F(1),F(1,10**9),F(10**8),F(1,10**15))[k%4];origin=F(10**8) if k%3 else F(0)
        a=tuple((origin-scale,origin+scale) for _ in range(3))
        displacement=tuple(scale*F(rng.randrange(-24,25),8) for _ in range(3))
        if k%6==0:displacement=(2*scale,F(0),F(0))
        if k%6==1:displacement=(2*scale+F(1,10**30)*scale,F(0),F(0))
        b=tuple((lo+d,hi+d) for (lo,hi),d in zip(a,displacement))
        A.verts[:]=box(a).verts;B.verts[:]=box(b).verts
        # Prime geometry-specific object caches, then mutate returned aliases.
        # Exact canonical input intentionally returns itself (not a cache leak).
        # Only the non-self canonicalization contract promises isolated output.
        hints=Polyhedron(list(A.verts),[])
        view=exact_convex_view(hints);view.verts[0]=(F(0),F(0),F(0))
        assert exact_convex_view(hints).verts==A.verts
        edges=A.edges();edges[:]=[]
        want=state(a,b);got=polyhedra_overlap(A,B,0)
        try:
            G._convex_surface_sat=lambda *args:None
            G._star_union_overlap=lambda *args:None
            G._transverse_interior_witness=lambda *args:None
            forced=polyhedra_overlap(A,B,0)
        finally:G._convex_surface_sat,G._star_union_overlap,G._transverse_interior_witness=saved
        row=dict(case=k,want=want,got=got,forced_arrangement=forced)
        if (got,forced)!=(want,want):errors.append(dict(row,problem='fallback'))
        if want==-1:
            cached=body_distance(A,B,tol=0);payload=_resolved(A,B,0,None,None)
            for cover,_,_,_ in payload[2]:cover.point_a=(F(999),)*3;cover.normal=(F(999),)*3
            after_alias=body_distance(A,B,tol=0)
            M._resolved_cached.cache_clear();fresh=body_distance(A,B,tol=0)
            row.update(cached=repr(cached),after_alias=repr(after_alias),fresh=repr(fresh))
            if cached!=after_alias or cached!=fresh or not sqrt_ok(distance2(a,b),cached[0]):errors.append(dict(row,problem='cache/distance'))
        rows.append(row)
    out=dict(cases=len(rows),errors=errors,rows=rows,seconds=time.perf_counter()-started,oracle='independent Cartesian interval products and exact squared gap; correct rounding by independent adjacent-float-midpoint enclosure')
    (ROOT/'review/geometry/cache_fallback_pressure.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in out.items() if k!='rows'},ensure_ascii=False,indent=2));assert not errors,errors[:3]
if __name__=='__main__':main()
