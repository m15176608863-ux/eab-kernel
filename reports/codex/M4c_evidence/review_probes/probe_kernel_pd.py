"""Independent read-only reviewer probes; not an implementation/G6 test suite.

Primary PD oracle imports only Fraction for geometry: grid occupancy and
Cartesian coordinate clamping. No production cross/dot/clip/triangulation,
boundary, nearest-segment, or normal-cone function participates in that oracle.
The separately labelled consistency probes import M3 only as a comparator.
"""
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
import os
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "src"))
from eab.kernel2d.motion import motion_first_entrance, QuadraticTime
from eab.kernel2d.motion_exit import shortest_exit_fast
from eab.kernel2d.global_entrance import GlobalEntrance2
from eab.kernel2d import g0_oracle

OUT = Path(__file__).resolve().parent
TEMPORARY = OUT.parent / "tmp" / "review_probe_r4"
TEMPORARY.mkdir(exist_ok=True)
os.environ["TMP"] = os.environ["TEMP"] = str(TEMPORARY)
FILES = ("src/eab/kernel2d/motion.py", "src/eab/kernel2d/motion_exit.py",
         "docs/m4c_motion_entrance_design.md", "tests/test_m4c_motion.py",
         "tests/test_m4c_exit.py", "tests/test_m4c_numeric.py")

def hashes():
    return {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in FILES}

START_HASH = hashes()
START = time.perf_counter()
ROWS = []

def save(complete=False):
    result = {"complete": complete, "counts": {name: sum(row["kind"] == name for row in ROWS)
              for name in sorted({row["kind"] for row in ROWS})}, "rows": ROWS,
              "elapsed_seconds": time.perf_counter()-START,
              "initial_sha256": START_HASH, "final_sha256": hashes() if complete else None,
              "oracle_scope": "PD rectangle-grid oracle independent; M3 comparisons consistency only"}
    (OUT/"probe_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

def ring(bounds):
    a,b,c,d = map(F, bounds)
    return ((a,b),(c,b),(c,d),(a,d))

def independent_rectangle_union_boundary(rectangles, x):
    """Exact axis-grid occupancy, no tested half-plane/segment primitives."""
    xs = sorted({F(r[k]) for r in rectangles for k in (0,2)})
    ys = sorted({F(r[k]) for r in rectangles for k in (1,3)})
    occupied = set()
    for i in range(len(xs)-1):
        for j in range(len(ys)-1):
            u,v = (xs[i]+xs[i+1])/2, (ys[j]+ys[j+1])/2
            if any(a < u < c and b < v < d for a,b,c,d in rectangles):
                occupied.add((i,j))
    answer = []
    for i,j in occupied:
        for di,dj in ((-1,0),(1,0),(0,-1),(0,1)):
            if (i+di,j+dj) in occupied:
                continue
            if di:
                p = (xs[i+(di==1)], min(ys[j+1],max(ys[j],x[1])))
            else:
                p = (min(xs[i+1],max(xs[i],x[0])),ys[j+(dj==1)])
            answer.append(((p[0]-x[0])**2+(p[1]-x[1])**2,p))
    best = min(item[0] for item in answer)
    return best,tuple(sorted({p for d,p in answer if d==best}))

def pd_grid_probes():
    rng = random.Random(414261)
    cases = [[(-3,-3,-1,3),(1,-3,3,3),(-1,-3,1,-1),(-1,1,1,3)],
             [(-2,-2,0,0),(0,0,2,2)],
             [(-2,-2,0,2),(0,-2,2,2)],
             [(-3,-3,3,3),(-1,-1,1,1)]]
    for _ in range(200):
        rectangles = []
        for _ in range(rng.randrange(1,7)):
            a,c = sorted(rng.sample(range(-5,6),2))
            b,d = sorted(rng.sample(range(-5,6),2))
            rectangles.append((a,b,c,d))
        cases.append(rectangles)
    for index,rectangles in enumerate(cases):
        a,b,c,d = rectangles[0]
        for x in ((F(a+c,2),F(b+d,2)), (F(a),F(b)),
                  (F(2*a+c,3),F(b+2*d,3))):
            model = GlobalEntrance2(ring((0,0,1,1)),ring((0,0,1,1)))
            # Explicit white-box stress of finite-cell-union query, not a
            # claim that every arbitrary cell collection is a polygon E.
            model.cells = tuple(ring(r) for r in rectangles)
            got = shortest_exit_fast(model,x=x)
            expected = independent_rectangle_union_boundary(rectangles,x)
            assert (got.squared,got.tied_exact_points)==expected, (index,rectangles,x,got,expected)
            ROWS.append({"kind":"independent_PD_grid", "case":index,
                         "query":list(map(str,x)),"squared":str(got.squared),
                         "ties":len(got.tied_exact_points)})
        if index % 20==0:
            save()
    save()

def shift(P,v):
    return tuple((F(x)+v[0],F(y)+v[1]) for x,y in P)

def transform(P,c,s,scale,offset):
    return tuple((scale*(c*x-s*y)+offset[0],scale*(s*x+c*y)+offset[1]) for x,y in P)

def m3_translation_probes():
    shapes = [ring((0,0,1,1)),((0,0),(3,0),(3,1),(1,1),(1,3),(0,3)),
              ((0,0),(3,0),(3,3),(2,3),(2,1),(1,1),(1,3),(0,3)),
              ((0,0),(F(1,2),0),(1,0),(1,1),(0,1)),
              ((0,0),(2,0),(F(2,3),F(7,5)))]
    count=0
    for i,A in enumerate(shapes):
        for j,B in enumerate(shapes):
            A0 = shift(A,(-6,F(1,7)))
            move = (F(10),F(2,9))
            model = GlobalEntrance2(A0,B)
            old = model.first_entrance((0,0),move,t_max=1)
            got = motion_first_entrance(A0,B,shift(A0,move),B)
            if old is None:
                assert got.status=="no_contact"
                labels=set()
            else:
                assert got.exact_time==old.exact_time
                labels={c.label for c in model.clipped_covers
                        if g0_oracle.on_segment(old.exact_point,c.start,c.end)}
                translated=shift(A0,old.exact_point)
                labels.update(("VV",u,v) for u,p in enumerate(translated)
                              for v,q in enumerate(B) if p==q)
                assert set(got.features)==labels,(i,j,got,labels)
            for rotate in ((F(0),F(1)),(F(3,5),F(4,5))):
                data=[transform(P,*rotate,F(1,10**9),(10**6,-2*10**6))
                      for P in (A0,B,shift(A0,move),B)]
                changed=motion_first_entrance(*data)
                assert changed.exact_time==got.exact_time and changed.features==got.features
                assert changed.incidences==got.incidences
                count+=1
            ROWS.append({"kind":"M3_translation_consistency", "case":[i,j],
                         "time":None if old is None else str(old.exact_time),"ties":len(labels)})
            save()
    ROWS.append({"kind":"translation_covariance", "samples":count})

def affine_wall_probes():
    # Arbitrary linear per-vertex y motion above fixed floor y=0. All x
    # coordinates stay strictly within wide floor; its exact first time is
    # the minimum independent scalar endpoint zero, not a VE polynomial.
    rng=random.Random(7113)
    floor=ring((-10,-5,10,0))
    for case in range(100):
        # Different x velocities/shear and vertical rates; positive signed
        # area throughout follows bottom pair + upper point (y remains above
        # their affine interpolation by constant margin 1).
        y0=F(rng.randrange(1,9),3)
        yl=F(rng.randrange(-9,0),4)
        yr=F(rng.randrange(-9,0),4)
        A0=((-1,y0),(1,y0),(0,y0+1))
        A1=((-F(3,2),yl),(F(3,2),yr),(0,(yl+yr)/2+1))
        times=[y0/(y0-yl),y0/(y0-yr)]
        tau=min(times)
        vertices={i for i,t in enumerate(times) if t==tau}
        expected={("VE",i,2) for i in vertices}
        got=motion_first_entrance(A0,floor,A1,floor)
        assert got.exact_time==tau and set(got.features)==expected,(case,got,tau,expected)
        ROWS.append({"kind":"independent_affine_wall", "case":case,
                     "time":str(tau),"ties":len(vertices)})
    save()

def domain_probes():
    far=ring((50,50,51,51))
    # Endpoint orientation is unchanged, but area is (s-1/4)(s-3/4).
    triangle0=((0,0),(1,0),(1,F(3,16)))
    triangle1=((0,0),(1,1),(0,F(3,16)))
    cases=[(triangle0,triangle1), (ring((0,0,1,1)),ring((0,0,1,1))[2:]+ring((0,0,1,1))[:2])]
    for case,(begin,end) in enumerate(cases):
        try:
            motion_first_entrance(begin,far,end,far)
        except ValueError as exc:
            ROWS.append({"kind":"domain_midstep_invalid", "case":case,"error":str(exc)})
        else:
            raise AssertionError("domain escaped full-window rejection")
    # Root separation far below binary64 precision; independent monotonic
    # polynomial comparison establishes strict order without decimal roots.
    a=QuadraticTime(None,1,-1,1)
    b=QuadraticTime(None,1,-1-F(1,2**1000),1)
    assert a < b and a != b and b > a
    ROWS.append({"kind":"algebraic_near_roots", "separation_perturbation":"2^-1000"})
    save()

def independent_quadratic_family():
    # A's top follows (v*s,0); B's lower supporting edge is
    # y=h-k*s*(x+1)/2.  Its height at A's top is zero exactly when
    # v*s*s+s-2*h/k=0. A's other two vertices remain at y=-1,
    # below the entire moving edge. Thus no competing feature comes first.
    # These facts use scalar graphs, not any production geometry primitive.
    from math import isqrt
    for v in (F(1,2),F(3,4),F(1)):
        for h in (F(1,8),F(1,4),F(3,8)):
            k=F(1,2)
            A0=((0,0),(-F(1,20),-1),(F(1,20),-1))
            A1=shift(A0,(v,0))
            B0=((-1,h),(1,h),(1,3))
            B1=((-1,h),(1,h-k),(1,3))
            got=motion_first_entrance(A0,B0,A1,B1)
            b,c=1/v,-2*h/(k*v)
            d=b*b-4*c
            nr,dr=isqrt(d.numerator),isqrt(d.denominator)
            rational=(nr*nr==d.numerator and dr*dr==d.denominator)
            if rational:
                expected=(-b+F(nr,dr))/2
                assert got.exact_time==expected
            else:
                assert (got.exact_time.b,got.exact_time.c,got.exact_time.branch)==(b,c,1)
            assert got.features==(("VE",0,0),)
            ROWS.append({"kind":"independent_quadratic_family","v":str(v),
                         "h":str(h),"certificate":got.exact_time.certificate})
    save()

save()
pd_grid_probes()
m3_translation_probes()
affine_wall_probes()
domain_probes()
independent_quadratic_family()
assert START_HASH==hashes(),"reviewed inputs changed during independent probe"
save(True)
print(json.dumps({"complete":True,"rows":len(ROWS),"seconds":time.perf_counter()-START}))
