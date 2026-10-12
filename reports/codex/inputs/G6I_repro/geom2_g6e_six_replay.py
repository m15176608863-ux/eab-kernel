"""Replays raw G6E entries 26/27/30/38/41/49 on current HEAD.
Independent oracle: exact raw-coordinate projections / Cartesian relations.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,math,random,json,subprocess,shutil,hashlib
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel2d.covers import convex_entrance_block,membership_convex,vv_cover,enumerate_covers
from eab.kernel2d.geom import convex_hull
from eab.kernel2d.g0 import g0_convex
def sat(A,B,x):
    FA=[(F(a)+F(x[0]),F(b)+F(x[1])) for a,b in A];FB=[tuple(map(F,p)) for p in B]
    touching=False
    for P,Q in ((FA,FB),(FB,FA)):
        for a,b in zip(P,P[1:]+P[:1]):
            nx,ny=b[1]-a[1],a[0]-b[0]
            pp=[nx*p[0]+ny*p[1] for p in P];qq=[nx*p[0]+ny*p[1] for p in Q]
            w=min(max(pp),max(qq))-max(min(pp),min(qq))
            if w<0:return -1
            touching |= w==0
    return 0 if touching else 1
def rot(P,th,t):
    c,s=math.cos(th),math.sin(th)
    return [(c*x-s*y+t[0],s*x+c*y+t[1]) for x,y in P]
def main():
    results=[]
    h=1e-14;B=[(0.,0.),(1.-h,0.),(1.,h),(1.,1.),(0.,1.)]
    A=[(0.,0.),(-.25,-.25*math.sqrt(3)),(.25,-.25*math.sqrt(3))]
    eb=convex_entrance_block(A,B);x=(1.1,.5)
    assert membership_convex(A,B,x)==sat(A,B,x)==1
    rng=random.Random(26);n=0
    for _ in range(2000):
        x=(rng.uniform(-1,2),rng.uniform(-1,2));assert membership_convex(A,B,x)==sat(A,B,x);n+=1
    results.append({'raw_id':'G6E-26','status':'FIXED','original_probe_state':1,'random_exact_SAT_matches':n,'facets':eb.facets})
    A=[(0.,0.),(.1,0.),(.1,.1),(0.,.1)];cells=[]
    for C,h,ap in [(0.,1e-14,.2),(0.,2e-14,.2),(0.,3e-14,.2),(0.,1e-13,.2),(1e5,3e-9,.2),(1e5,1e-8,.05)]:
        B=[(C,C),(C+1-h,C),(C+1,C),(C+.5,C+ap)]
        convex_entrance_block(A,B);cells.append({'C':C,'h':h,'ap':ap,'result':'accepted'})
    results.append({'raw_id':'G6E-27','status':'FIXED','original_valid_convex_cells':cells})
    SQ=[(0.,0.),(1.,0.),(1.,1.),(0.,1.)];R=[(0.,0.),(1000.,0.),(1000.,1.),(0.,1.)]
    cells=[]
    for C in (0.,1e3,1e4):
        for d in (1.05e-9,1.25e-9):
            A=rot(SQ,0.,(C,.3*C));B=rot(R,d,(C,.3*C))
            forward=g0_convex(A,B,samples=100);reverse=g0_convex(B,A,samples=100)
            assert forward.passed and reverse.passed
            cells.append({'C':C,'d':d,'forward':forward.passed,'reverse':reverse.passed,'symdiff':forward.facet_symmetric_diff})
    results.append({'raw_id':'G6E-30','status':'FIXED','cells':cells})
    pts=[(0.,0.),(1e-15,-1e-3),(1e-15,1.),(1e-3,-1e-3),(2.,-1e-3),(2.,1.)]
    H=convex_hull(pts);assert (1e-15,-1e-3) in H
    for a,b in zip(H,H[1:]+H[:1]):
        assert all((F(b[0])-F(a[0]))*(F(p[1])-F(a[1]))-(F(b[1])-F(a[1]))*(F(p[0])-F(a[0]))>=0 for p in pts)
    A=rot([(-1e-3,-1e-3),(1e-3,-1e-3),(1e-3,1e-3),(-1e-3,1e-3)],1e-6,(3.,1e-3+2e-9))
    B=[(-1e3,-1e3),(1e3,-1e3),(1e3,0.),(-1e3,0.)]
    r1=g0_convex(A,B,samples=200,seed=2)
    T=lambda p:(1e-3*p[0]+600.,1e-3*p[1]-800.)
    r2=g0_convex([T(p) for p in A],[T(p) for p in B],samples=200,seed=2)
    assert r1.passed and r2.passed
    results.append({'raw_id':'G6E-38','status':'FIXED','extreme_kept':True,'identity_passed':r1.passed,'scaled_translated_passed':r2.passed,'hull_mismatch':r2.hull_vertex_mismatch})
    A=[(0.,0.),(.1,0.),(.1,.1),(0.,.1)];B=[(0.,0.),(1.,0.),(1.,1.),(0.,1.),(0.,.5001),(5e-7,.5)]
    rejected=[]
    for tol in (0.,1e-6,1.):
        try:convex_entrance_block(A,B,tol=tol)
        except ValueError as e:rejected.append(str(e))
        else:raise AssertionError('micro-reflex must not enter exact convex construction')
    ms=[membership_convex(A,B,(-.1+d,.2),tol=1e-6) for d in (1e-5,1e-4)]
    assert ms==[1,1]
    results.append({'raw_id':'G6E-41','status':'FIXED','exact_convex_rejection':rejected,'concave_fallback_states':ms})
    TRI=[(0.,0.),(-1.,1.),(-1.,-1.)];cells=[]
    for th in (0.,.3,1.1):
        g=1e-6;ang=math.radians(-5)
        A=rot([(u+g*math.cos(ang),v+g*math.sin(ang)) for u,v in SQ],th,(1e5,1e5));B=rot(TRI,th,(1e5,1e5))
        c=vv_cover(A,0,B,0);labels=[z.label() for z in enumerate_covers(A,B,window=1e-3)]
        # Raw neighbor support gives a negative dot product: exact strict is false.
        dx,dy=F(A[0][0])-F(B[0][0]),F(A[0][1])-F(B[0][1])
        vals=[dx*(F(A[k][0])-F(A[0][0]))+dy*(F(A[k][1])-F(A[0][1])) for k in (3,1)]
        assert min(vals)<0 and not c.strict and ('VV',0,0) not in labels
        cells.append({'theta':th,'strict':c.strict,'labels':labels,'negative_independent_support':str(min(vals))})
    results.append({'raw_id':'G6E-49','status':'FIXED','old_noise_variable_removed':True,'outside_cone_cells':cells})
    print(json.dumps(results,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
