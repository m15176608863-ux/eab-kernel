"""WO-G6M nonmonotone exact escape against Cartesian open-interval unions.

Construct two disjoint shelves. A can escape, re-enter, and escape again. The
oracle uses independent interval products in t, including isolated zero-width
nonpenetrating gaps. It neither calls events, overlap, star_core nor contact_models.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json,time
ROOT=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True;sys.path[:0]=[str(ROOT/'src'),str(ROOT/'review/repro')]
from geometry_cache_fallback_pressure import box
from eab.kernel3d.geom3 import Polyhedron
from eab.kernel3d.interlock import escape_height_covers
def join(bodies):
    v=[];faces=[]
    for P in bodies:
        n=len(v);v.extend(P.verts);faces.extend(tuple(i+n for i in f) for f in P.faces)
    return Polyhedron(v,faces)
def intervals(a,bs):
    return [(b[2][0]-a[2][1],b[2][1]-a[2][0]) for b in bs
            if all(max(a[k][0],b[k][0])<min(a[k][1],b[k][1]) for k in (0,1))]
def root(a,bs):
    regions=intervals(a,bs)
    def inside(t):return any(lo<t<hi for lo,hi in regions)
    if not inside(F(0)):return F(0)
    return next(t for t in sorted({t for pair in regions for t in pair if t>0}) if not inside(t))
def main():
    started=time.perf_counter();rows=[];errors=[]
    for scale in (F(1,10**9),F(1),F(10**8)):
        for origin in (F(0),F(10**8)):
            for gap in (F(-1,10**15),F(0),F(1,10**30),F(1)):
                for window in (None,scale/8):
                    a=tuple((origin-scale,origin+scale) for _ in range(3))
                    cells=[((origin-2*scale,origin+2*scale),(origin-2*scale,origin+2*scale),(origin-2*scale,origin)),
                           ((origin-2*scale,origin+2*scale),(origin-2*scale,origin+2*scale),(origin+(2+gap)*scale,origin+4*scale))]
                    A=box(a);B=join([box(c) for c in cells]);models=[a]
                    if window is not None:
                        # Independently verify B has no star centre: outward
                        # normals on the two separated shelf-facing surfaces
                        # demand c_z<first.top and c_z>second.bottom simultaneously.
                        assert cells[0][2][1]<cells[1][2][0]
                        alpha=min(window/(3*scale),F(1,2))
                        models.append(tuple((origin-(1-alpha)*scale,origin+(1-alpha)*scale) for _ in range(3)))
                        for axis in range(3):
                            for sign in (-1,1):models.append(tuple((lo+(sign*window if k==axis else 0),hi+(sign*window if k==axis else 0)) for k,(lo,hi) in enumerate(a)))
                    expected=min(root(model,cells) for model in models)
                    solution=escape_height_covers(A,B,(0,0,0),tol=0,contact_window=window)
                    row=dict(scale=str(scale),origin=str(origin),gap=str(gap),window=str(window),expected=str(expected),got=str(solution.exact_height),winner=solution.window_core,interval_count=len(solution.interval_certificate))
                    if solution.exact_height!=expected:errors.append(row)
                    # Winning-model interval certificate must be all inside;
                    # its samples alone are not a proof over losing models.
                    assert all(q[3]==1 for q in solution.interval_certificate)
                    rows.append(row)
    out=dict(cases=len(rows),errors=errors,rows=rows,seconds=time.perf_counter()-started,oracle='independent open Cartesian overlap intervals; exact interval-union first nonpenetration; explicit documented homothetic-box models')
    (ROOT/'review/geometry/escape_union_pressure.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in out.items() if k!='rows'},ensure_ascii=False,indent=2));assert not errors,errors[:3]
if __name__=='__main__':main()
