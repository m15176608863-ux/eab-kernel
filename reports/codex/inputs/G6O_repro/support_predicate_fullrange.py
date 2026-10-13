"""WO-G6O narrow full-Fraction predicate support audit.

Reference is independent interval algebra for axis-aligned rectangles/boxes;
no production geometry primitive, normalization, or constructed box is used.
All solids are manually outward-oriented closed boxes from exact Fraction data.
State convention: 1 open-interior overlap / 0 closed contact / -1 disjoint.
"""
from pathlib import Path
from fractions import Fraction as F
import sys, json, traceback

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'));sys.dont_write_bytecode=True
from eab.kernel3d.geom3 import Polyhedron, point_in_polyhedron, polyhedra_overlap
from eab.kernel3d.covers3 import membership_convex3
from eab.kernel2d.geom import polygons_overlap, is_convex
from eab.kernel2d.covers import membership_convex

faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
def solid(bounds):
    (x0,x1),(y0,y1),(z0,z1)=bounds
    return Polyhedron([(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
                       (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],faces)
def polygon(bounds):
    (x0,x1),(y0,y1)=bounds
    return [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
def point_state(p,bounds):
    if any(x<a or x>b for x,(a,b) in zip(p,bounds)):return -1
    return 0 if any(x==a or x==b for x,(a,b) in zip(p,bounds)) else 1
def overlap_state(a,b):
    widths=[min(ahi,bhi)-max(alo,blo) for (alo,ahi),(blo,bhi) in zip(a,b)]
    return -1 if any(w<0 for w in widths) else 0 if any(w==0 for w in widths) else 1

rows=[]
def check(case,api,expected,fn,inputs):
    row={'case':case,'api':api,'expected':expected,'inputs':inputs}
    try:actual=fn()
    except Exception as exc:
        row.update(actual_exception=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc(),passed=False)
        print('CANDIDATE',case,api,row['actual_exception'])
    else:
        row.update(actual=actual,passed=actual==expected)
        if actual!=expected:print('CANDIDATE',case,api,'expected=',expected,'actual=',actual)
    rows.append(row)

cases=[(e,F(0)) for e in (-4000,-2000,2000,4000)]
cases.extend((e,F(2)**4000) for e in (-2000,0,2000))
for exponent,t in cases:
    s=F(2)**exponent;case=f'scale_2^{exponent}_translate_'+('2^4000' if t else '0')
    bounds3=((t,t+s),)*3;bounds2=bounds3[:2]
    A=solid(bounds3);A2=polygon(bounds2)
    basic={'scale_exponent':exponent,'translation':'2^4000' if t else '0'}
    for factor in (F(1,2),F(1),F(1)+F(2)**-2000):
        p=(t+s*factor,t+s/2,t+s/2)
        check(case,'point_in_polyhedron',point_state(p,bounds3),lambda p=p:point_in_polyhedron(p,A,0),dict(basic,x_factor=str(factor)))
    for factor in (F(0),F(1),F(1)+F(2)**-2000):
        b3=((t+s*factor,t+s*(factor+1)),(t,t+s),(t,t+s));b2=b3[:2]
        B=solid(b3);B2=polygon(b2)
        expected=overlap_state(bounds3,b3)
        check(case,'polyhedra_overlap',expected,lambda B=B:polyhedra_overlap(A,B,0),dict(basic,b_shift_factor=str(factor)))
        check(case,'polygons_overlap',overlap_state(bounds2,b2),lambda B2=B2:polygons_overlap(A2,B2,0),dict(basic,b_shift_factor=str(factor)))
    # E=B-A of two identical boxes/rectangles is exactly [-s,s]^d.
    ebounds3=((-s,s),)*3;ebounds2=ebounds3[:2]
    for factor in (F(0),F(1),F(1)+F(2)**-2000):
        query=(s*factor,F(0),F(0))
        check(case,'membership_convex3',point_state(query,ebounds3),lambda query=query:membership_convex3(A,A,query,0),dict(basic,query_factor=str(factor)))
        check(case,'membership_convex',point_state(query[:2],ebounds2),lambda query=query:membership_convex(A2,A2,query[:2],0),dict(basic,query_factor=str(factor)))
    check(case,'is_convex',True,lambda:is_convex(A2,0),basic)

    # Strictly concave simple polygon: independently determinant at corner
    # (s/2,s/4) has negative sign -s^2/4; all lengths stay nonzero.
    concave=[(t,t),(t+s,t),(t+s/2,t+s/4),(t+s,t+s),(t,t+s)]
    check(case,'is_convex_concave',False,lambda concave=concave:is_convex(concave,0),basic)

result={'scope':'finite exact Fraction pure predicates, manually valid axis-aligned surfaces; no construction/distance APIs',
        'cases':len(rows),'passed':sum(r['passed'] for r in rows),'candidates':[r for r in rows if not r['passed']], 'rows':rows}
(ROOT/'review/evidence/support_predicate_fullrange.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'PREDICATE_FULLRANGE cases={len(rows)} passed={result["passed"]} candidates={len(result["candidates"])}')
if result['candidates']:sys.exit(1)
