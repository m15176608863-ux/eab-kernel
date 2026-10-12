"""Six original G6E 2D cases, exact inline oracles, no sibling writes."""
from pathlib import Path
from fractions import Fraction as F
import math,json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel2d import covers as C,geom as G,g0
S=[(0.,0.),(1.,0.),(1.,1.),(0.,1.)]
def sat(A,B,x=(0,0)):
    A=[(F(a)+F(x[0]),F(b)+F(x[1])) for a,b in A];B=[tuple(map(F,p)) for p in B];touch=False
    for P in [A,B]:
        for a,b in zip(P,P[1:]+P[:1]):
            nx,ny=b[1]-a[1],a[0]-b[0]
            ap=[nx*p[0]+ny*p[1] for p in A];bp=[nx*p[0]+ny*p[1] for p in B]
            h=min(max(ap),max(bp))-max(min(ap),min(bp))
            if h<0:return -1
            touch|=h==0
    return 0 if touch else 1
def rot(P,th,t=(0,0)):
    c,s=math.cos(th),math.sin(th);return [(c*x-s*y+t[0],s*x+c*y+t[1]) for x,y in P]
out=[]
# G6E-26 exactly the original micro-chamfer counterexample.
h=1e-14;B=[(0.,0.),(1-h,0.),(1.,h),(1.,1.),(0.,1.)]
Q=[(0.,0.),(.25,.25*math.sqrt(3)),(-.25,.25*math.sqrt(3))];A=[(-x,-y) for x,y in Q];x=(1.1,.5)
got=C.membership_convex(A,B,x);truth=sat(A,B,x);r=g0.g0_convex(A,B,samples=2000)
assert got==truth==1 and r.passed,(got,truth,r)
out.append({'id':'G6E-26','status':'已修','member':got,'independent_SAT':truth,'g0_mismatches':len(r.mismatches),'g0_passed':r.passed})
# G6E-27 acute polygon with short flat edge, same four h and engineering cases.
A=[(0.,0.),(.1,0.),(.1,.1),(0.,.1)];values=[]
for off,h,ap in [(0.,h,.2) for h in (1e-14,2e-14,3e-14,1e-13)]+[(1e5,3e-9,.2),(1e5,1e-8,.05)]:
    B=[(off,off),(off+1-h,off),(off+1,off),(off+.5,off+ap)]
    eb=C.convex_entrance_block(A,B);assert len(eb.vertices)==7
    values.append({'offset':off,'h':h,'vertices':len(eb.vertices)})
out.append({'id':'G6E-27','status':'已修','cases':values})
# G6E-30 prior double-standard angular merging: six original cells, both directions.
R=[(0.,0.),(1000.,0.),(1000.,1.),(0.,1.)];values=[]
for off in (0.,1e3,1e4):
    for angle in (1.05e-9,1.25e-9):
        t=(off,.3*off);A=rot(S,0,t);B=rot(R,angle,t);tol=1e-12*g0.char_length(A,B)
        eb=C.convex_entrance_block(A,B,(0,0),tol)
        r1=g0.g0_convex(A,B,samples=100);r2=g0.g0_convex(B,A,samples=100)
        assert not any(l[0]=='FF' for l in eb.facets) and r1.passed and r2.passed
        values.append({'offset':off,'angle':angle,'FF':[],'g0_forward':r1.passed,'g0_reverse':r2.passed})
out.append({'id':'G6E-30','status':'已修','cases':values})
# G6E-38 missing real hull extreme. Every original point on left of every hull edge.
pts=[(0.,0.),(1e-15,-1e-3),(1e-15,1.),(1e-3,-1e-3),(2.,-1e-3),(2.,1.)]
H=G.convex_hull(pts)
assert (1e-15,-1e-3) in H
for a,b in zip(H,H[1:]+H[:1]):
    for p in pts:
        assert (F(b[0])-F(a[0]))*(F(p[1])-F(a[1]))-(F(b[1])-F(a[1]))*(F(p[0])-F(a[0]))>=0
out.append({'id':'G6E-38','status':'已修','hull':H,'all_points_contained_exactly':True})
# G6E-41 original micro-concave T input rejected by convex API, accepted generic member.
A=[(0.,0.),(.1,0.),(.1,.1),(0.,.1)]
P=[(0.,0.),(1.,0.),(1.,1.),(0.,1.),(0.,.5001),(.5e-6,.5)]
try:C.convex_entrance_block(A,P,(0,0),1e-6)
except ValueError as e:exception=repr(e)
else:raise AssertionError('microconcavity improperly accepted')
values=[]
for d in [1e-5,1e-4]:
    x=(-.1+d,.2);got=C.membership_convex(A,P,x)
    # A crosses P left border y=.2..3 where border is exactly x=0.
    assert got==1
    values.append({'x':x,'member':got,'expected':1})
out.append({'id':'G6E-41','status':'已修','convex_rejection':exception,'generic_member':values})
# G6E-49 same separation direction five degrees outside VV intersection.
g=1e-6;off=1e5;a=-math.radians(5)
A=rot([(x+g*math.cos(a),y+g*math.sin(a)) for x,y in S],0,(off,off));B=rot([(0,0),(-1,1),(-1,-1)],0,(off,off))
c=C.vv_cover(A,0,B,0);v=tuple(F(A[0][k])-F(B[0][k]) for k in (0,1))
independent=all(sum(v[k]*(F(A[j][k])-F(A[0][k])) for k in (0,1))>0 for j in [1,3]) and all(sum(v[k]*(F(B[j][k])-F(B[0][k])) for k in (0,1))<0 for j in [1,2])
labels=[c.label() for c in C.enumerate_covers(A,B,window=1e-3)]
assert not c.strict and not independent and ('VV',0,0) not in labels
out.append({'id':'G6E-49','status':'已修','strict':c.strict,'independent_support':independent,'labels':labels,'old_du_noise_path_exists':False})
print(json.dumps(out,ensure_ascii=False,indent=2))
(ROOT/'review/agents/geom2/g6e_replay.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
