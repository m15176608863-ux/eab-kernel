"""WO-G6O new independent oracle: exact H-polytope vertices, no kernel helpers.

The oracle derives four tetrahedron inequalities inline from the four input
points. It enumerates plane triples with Cramer's rule and determines the
intersection dimension by independent rational Gaussian elimination. This is
not SAT and imports no production hull, triangulation, sign or LP routine.
Only the functions called as the system under test import eab.
"""
from fractions import Fraction as Q
from itertools import combinations
from pathlib import Path
import json, random, sys, time, math
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from eab.kernel3d.geom3 import tetra, Polyhedron, polyhedra_overlap, point_in_polyhedron
from eab.kernel3d.exact_geom import segment_distance_squared, polygon_locate

def dot(a,b):return sum(x*y for x,y in zip(a,b))
def minus(a,b):return tuple(Q(x)-Q(y) for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def det(a,b,c):return dot(a,cross(b,c))
def planes(vertices):
    p=[tuple(Q(x) for x in v) for v in vertices];out=[]
    for omitted in range(4):
        a,b,c=[v for i,v in enumerate(p) if i!=omitted]
        n=cross(minus(b,a),minus(c,a));h=dot(n,a)
        if dot(n,p[omitted])>h:n=tuple(-x for x in n);h=-h
        out.append((n,h))
    return out
def rank(matrix):
    m=[list(row) for row in matrix];r=0
    for k in range(3):
        j=next((j for j in range(r,len(m)) if m[j][k]),None)
        if j is None:continue
        m[j],m[r]=m[r],m[j];pivot=m[r][k]
        m[r]=[x/pivot for x in m[r]]
        for i in range(r+1,len(m)):
            a=m[i][k];m[i]=[x-a*y for x,y in zip(m[i],m[r])]
        r+=1
    return r
def intersection_state(a,b):
    constraints=planes(a)+planes(b);vertices=set()
    for triple in combinations(constraints,3):
        ns,hs=tuple(n for n,h in triple),tuple(h for n,h in triple)
        d=det(*ns)
        if not d:continue
        # n_i.x=h_i; replace each column rather than using a shared solver.
        p=tuple(det(*(tuple(hs[j] if k==axis else ns[j][k] for k in range(3)) for j in range(3)))/d for axis in range(3))
        if all(dot(n,p)<=h for n,h in constraints):vertices.add(p)
    if not vertices:return -1
    p=next(iter(vertices));return 1 if rank([minus(q,p) for q in vertices])==3 else 0
def member(p,vertices):
    residual=[h-dot(n,p) for n,h in planes(vertices)]
    return -1 if min(residual)<0 else 0 if min(residual)==0 else 1
def segment_reference(a,b,c,d):
    # Independent active-set minimization of ||a+s(b-a)-c-t(d-c)||^2.
    a,b,c,d=(tuple(Q(x) for x in p) for p in (a,b,c,d))
    u,v,w=minus(b,a),minus(d,c),minus(a,c)
    uu,vv,uv,wu,wv=dot(u,u),dot(v,v),dot(u,v),dot(w,u),dot(w,v)
    candidates=[(Q(0),Q(0)),(Q(0),Q(1)),(Q(1),Q(0)),(Q(1),Q(1))]
    clamp=lambda x:max(Q(0),min(Q(1),x))
    if vv:candidates += [(s,clamp((wv+s*uv)/vv)) for s in (Q(0),Q(1))]
    if uu:candidates += [(clamp((t*uv-wu)/uu),t) for t in (Q(0),Q(1))]
    determinant=uu*vv-uv*uv
    if determinant:
        s=(uv*wv-vv*wu)/determinant;t=(uu*wv-uv*wu)/determinant
        if 0<=s<=1 and 0<=t<=1:candidates.append((s,t))
    return min(sum((w[k]+s*u[k]-t*v[k])**2 for k in range(3)) for s,t in candidates)
def run():
    start=time.time();rng=random.Random(151013);stats={};failures=[]
    def check(kind,actual,expected,case):
        stats[kind]=stats.get(kind,0)+1
        if actual!=expected:failures.append({'kind':kind,'actual':str(actual),'expected':str(expected),'case':str(case)})
    def transform(p,s,thin,t,rotate):
        x,y,z=(Q(x) for x in p);z*=thin
        if rotate:x,y=Q(5,13)*x-Q(12,13)*y,Q(12,13)*x+Q(5,13)*y
        return (s*x+t,s*y-t,s*z+t)
    base=[(0,0,0),(2,0,0),(0,3,0),(0,0,5)]
    for case in range(280):
        s=Q(2)**rng.choice([-1200,-1074,-550,-30,0,30,550,1100])
        thin=Q(2)**rng.choice([-1100,-53,-20,0]);t=Q(2)**rng.choice([0,27,1000])
        rotate=bool(case%2);aa=[transform(p,s,thin,t,rotate) for p in base]
        bbase=[(0,0,0),(2,0,0),(0,3,0),(0,0,5)] if case%3 else [(0,0,0),(1,2,0),(2,-1,0),(0,0,3)]
        bb=[transform(p,s,thin,t,not rotate) for p in bbase]
        offset=tuple(Q(rng.randint(-8,8),4)*s*(thin if k==2 else 1) for k in range(3))
        # Include exact point touch, edge touch, face touch, complete coincidence.
        if case%7==0:bb=[tuple(aa[0][k]+aa[0][k]-a[k] for k in range(3)) for a in aa];offset=(Q(0),)*3
        if case%11==0:bb=aa;offset=(Q(0),)*3
        bb=[tuple(v[k]+offset[k] for k in range(3)) for v in bb]
        a,b=tetra(*aa),tetra(*bb)
        check('tetra_overlap_H_vertices',polyhedra_overlap(a,b),intersection_state(aa,bb),(case,s,thin,t,offset))
        queries=[tuple(sum(v[k] for v in aa)/4 for k in range(3)),aa[0],tuple((aa[1][k]+aa[2][k])/2 for k in range(3)),bb[0]]
        for p in queries:check('tetra_member_H',point_in_polyhedron(p,a),member(p,aa),(case,p))
    for case in range(600):
        s=Q(2)**rng.choice([-1200,-1074,-550,0,550,1100]);t=Q(2)**rng.choice([0,30,1000])
        points=[tuple(Q(rng.randint(-8,8),4)*s+t for k in range(3)) for j in range(4)]
        if case%3==0:
            a,b,c,d=points;u=minus(b,a);tiny=Q(2)**-rng.choice([53,300,1500])
            points[3]=tuple(c[k]+u[k]+(tiny*s if k==case%3 else 0) for k in range(3))
        if case%13==0:points[1]=points[0]
        check('segment_squared_active_set',segment_distance_squared(*points),segment_reference(*points),(case,points))
    # An exact horizontal rectangle: independent four segment distances and
    # Cartesian closed interval membership, including rational RN-zero windows.
    for case in range(700):
        s=Q(2)**rng.choice([-1500,-1074,-400,0,400,1200]);t=Q(2)**rng.choice([0,30,1000])
        ring=[(t+x*s,t+y*s,t) for x,y in [(0,0),(2,0),(2,3),(0,3)]]
        w=rng.choice([Q(0),Q(1,10),Q(2)**-1500])*s
        x,y=rng.choice([Q(-1,10),Q(0),Q(1),Q(2),Q(21,10)]),rng.choice([Q(-1,10),Q(0),Q(1),Q(3),Q(31,10)])
        if case%4==0:x=-w/s+Q(2)**-2000
        p=(t+x*s,t+y*s,t)
        nearest=min(segment_reference(p,p,a,b) for a,b in zip(ring,ring[1:]+ring[:1]))
        expected=0 if nearest<=w*w else (1 if 0<x<2 and 0<y<3 else -1)
        check('interval_polygon_window',polygon_locate(p,ring,w),expected,(case,s,t,x,y,w))
    result={'head':'03a41b5','oracle_independence':'No production helpers in reference path; tetra H intersection is plane-triple Cramer plus rational rank, not SAT.','stats':stats,'failures':failures,'seconds':round(time.time()-start,3)}
    (ROOT/'review/evidence/geometry_fraction_hpoly_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2));assert not failures
if __name__=='__main__':run()
