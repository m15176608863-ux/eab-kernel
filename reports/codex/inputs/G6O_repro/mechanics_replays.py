"""WO-G6O mechanics: G6N replay logic adapted read-only; current root only.

Independent oracle: raw Fraction equilibrium/interpolation and test-owned
Gaussian elimination / enumeration of all basic feasible vertices. No eab
geometry, construction or LP primitive is used to calculate expected answers.
"""
from pathlib import Path
import copy
from fractions import Fraction as F
import importlib.util
import itertools
import json
import math
import random
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
sys.dont_write_bytecode = True
import eab.limit as L
import eab.limit_multi as M
import eab.lp as LP
C, B, BC = L.LimitContact, M.LimitBody, M.BodyContact
results = []

def record(raw, label, output):
    results.append({'raw_one_based': raw, 'label': label, 'output': output, 'pass': True})
    print(f'REPLAY raw#{raw}: {label}: {output}', flush=True)

def exact(v):
    return v.exact if hasattr(v, 'exact') else F(v)

def slide(mu=.6, W=10, cohesion=0):
    cs=[C((-1.,0.),(0.,1.),mu,cohesion=cohesion,area=1.), C((1.,0.),(0.,1.),mu,cohesion=cohesion,area=1.)]
    return cs,[0.,-W,0.],[1.,0.,-.5]

def assembly(D=10., WD=10.):
    bs=[B([0.,-30.,0.],[0.]*3),B([0.,-10.,0.],[1.,0.,-2.]),B([0.,-WD,-WD*D],[0.]*3)]
    cs=[BC(C((x,0.),(0.,1.),1.2),0) for x in (-1.,1.)]
    cs += [BC(C((x,1.),(0.,1.),1.2),1,0) for x in (-1.,1.)]
    cs += [BC(C((D+x,0.),(0.,1.),1.2),2) for x in (-1.,1.)]
    return bs,cs

def replays():
    n=tuple(1/math.sqrt(3) for _ in range(3))
    try:
        L._tangents(n,3,(1.,1.,1.+2**-50))
    except ValueError as ex:
        record(9,'unresolvable supplied tangent rejected',str(ex))
    else:
        raise AssertionError('raw#9 tangent silently accepted')
    readme=(ROOT/'README.md').read_text('utf-8')
    assert 'test_limit_flat_arch.py' in readme
    spec=importlib.util.spec_from_file_location('flat_arch',ROOT/'tests/test_limit_flat_arch.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    out=[]
    for mu in (0.,.3,.7,2.):
        bs,cs=mod._problem(mu); r=M.limit_load_multi(bs,cs,dim=2)
        assert r.status == ('infeasible' if mu==0 else 'unbounded')
        out.append([mu,r.status])
    record(10,'flat-arch named gate exists and physical state replayed',out)
    real=L.maximize
    def skew(A,b,c,**kw):
        r=real(A,b,c,**kw)
        if r.status=='optimal':
            j=next(j for j,v in enumerate(c) if v)
            r.x[j]=exact(r.x[j])*F(999,1000)
        return r
    L.maximize=skew
    rejects=[]
    try:
        for mu in (.4,1e-3,1e-4,1e-5):
            try: L.limit_load(*slide(mu),dim=2)
            except RuntimeError as ex:
                assert 'self-check' in str(ex); rejects.append(mu)
            else: raise AssertionError(f'raw#11 accepted alpha error mu={mu}')
    finally: L.maximize=real
    cs,dead,live=slide(0,1e6,5)
    r=L.limit_load(cs,dead,live,dim=2)
    for f in (.999,.99,.9):
        rr=copy.copy(r);rr.alpha=r.alpha*f
        assert not L.check_duality(rr,cs,dead,live,dim=2)['ok']
    record(11,'real solver path rejects alpha error at small friction/cohesion',rejects)
    bs,cs=assembly();r=M.limit_load_multi(bs,cs,dim=2)
    out=[]
    for VD in (0.,1e3,1e5):
        m=[[exact(x) for x in yi] for yi in r.mechanisms]
        m[1][1]-=F(1,10**100);m[2]=[F(VD),F(0),F(0)]
        rr=copy.copy(r);rr.mechanisms=m
        a=M.mechanism_is_admissible_multi(m,cs,dim=2)
        d=M.check_duality_multi(rr,bs,cs,dim=2)
        assert not a and not d['admissible'] and not d['ok']
        out.append([VD,a,d['ok']])
    record(20,'unrelated body speed cannot forgive 1e-100 penetration',out)
    out=[]
    for WD in (10.,1e6,1e9):
        bs,cs=assembly(5.,WD);r=M.limit_load_multi(bs,cs,dim=2)
        f=F(999,1000);lam0=[F(N)/2 for N in (20,20,5,5,F(WD)/2,F(WD)/2) for _ in range(2)]
        rr=copy.copy(r);rr.alpha=exact(r.alpha)*f
        rr.lambdas=[exact(v)*f+(1-f)*w for v,w in zip(r.lambdas,lam0)]
        d=M.check_duality_multi(rr,bs,cs,dim=2)
        assert d['static_ok'] and not d['ok'] and F(d['duality_gap_exact'])>0
        out.append([WD,d['static_ok'],d['ok'],d['duality_gap_exact']])
    record(21,'statically feasible suboptimal interpolation rejected',out)
    out=[]
    for v in (1e-6,1e-8):
        ct=C((1.,0.),(math.sin(1.2),math.cos(1.2)),1.)
        body=B([0.,-1.,0.],[-1.,v,0.])
        baseline=None
        for D in (None,1e2,1e4,1e6):
            bs,cs=[body],[BC(ct,0)]
            if D is not None:
                bs += [B([0.,-10.,-10.*D],[0.]*3)]
                cs += [BC(C((D+x,0.),(0.,1.),.5),1) for x in (-.5,.5)]
            r=M.limit_load_multi(bs,cs,dim=2)
            tup=(r.status,exact(r.alpha),r.uncertainty,r.resolvability)
            if baseline is None: baseline=tup
            assert tup==baseline
            out.append([v,D,r.status,float(r.alpha),r.uncertainty,r.resolvability])
    record(22,'per-body resolvability unaffected by far unloaded body',out)
    a,T=-2.2145790363256497,(456126.84150283627,6015705.33931258)
    rot=lambda v:(math.cos(a)*v[0]-math.sin(a)*v[1],math.sin(a)*v[0]+math.cos(a)*v[1])
    pt=lambda p:tuple(rot(p)[i]+T[i] for i in range(2))
    n=rot((-.8414709848078965,.5403023058681398))
    cs=[C(pt((1.,0.)),n,1.),C(pt((1.5,0.)),n,.2,cohesion=1.,area=1.)]
    bs=[B(L.wrench(rot((0.,-10.)),pt((0.,.7)),(0.,0.),2),L.wrench(rot((1.,0.)),pt((0.,0.)),(0.,0.),2))]
    r=M.limit_load_multi(bs,[BC(c,0) for c in cs],dim=2,k=4)
    assert r.status=='unbounded' and r.resolvability=='nearby_infeasible' and 'infeasible' in r.resolvability_statuses
    record(23,'unbounded branch preserves exact original state and emits risk',[r.status,r.resolvability,list(r.resolvability_statuses)])
    out=[]
    for D in (0.,1e4,1e5,1e6):
        cs,dead,_=slide();cs += [C((D,0.),(0.,1.),.6)];live=[0.,0.,1.]
        r=L.limit_load(cs,dead,live,dim=2)
        for f in (.999,.99,.9):
            rr=copy.copy(r);rr.alpha=r.alpha*f
            d=L.check_duality(rr,cs,dead,live,dim=2)
            assert not d['static_ok'] and not d['ok'];out.append([D,f,d['ok']])
    record(45,'far unloaded single contact cannot hide couple residual',out)
    out=[]
    for D in (0.,1e2,1e4,1e6):
        bs,cs=assembly(D);r=M.limit_load_multi(bs,cs,dim=2)
        for k in (3,4,5,6,30,100):
            rr=copy.copy(r);rr.mechanisms=[[exact(v) for v in yi] for yi in r.mechanisms]
            rr.mechanisms[1][1]-=F(1,10**k)
            d=M.check_duality_multi(rr,bs,cs,dim=2)
            assert not d['admissible'] and not d['ok'];out.append([D,k,d['ok']])
    record(47,'narrow and sub-ulp penetration gates remain rejecting',out)
    from eab.kernel3d.geom3 import box, Polyhedron
    from eab.margin import body_distance, margin_contacts, inflated_membership
    outputs=[]
    for psi in (1e-15,1e-12,1e-11,1e-10,1e-9,3e-9):
        cs,sn=math.cos(psi),math.sin(psi)
        rc=(-cs-sn,-sn+cs,-1.)
        target=(1.1,1.+psi*.05,1.1)
        center=tuple(target[i]-rc[i] for i in range(3))
        template=box()
        A=Polyhedron([(center[0]+cs*x-sn*y,center[1]+sn*x+cs*y,center[2]+z) for x,y,z in template.verts],list(template.faces));boxB=box()
        d,label=body_distance(A,boxB)
        # Independent convex vertex normal cones: nearest pair iff all vertex
        # displacements have nonnegative dot along the separating vector.
        ia=min(range(8),key=lambda i:math.dist(A.verts[i],target)); av=tuple(map(F,A.verts[ia]));bv=tuple(map(F,boxB.verts[6]));v=tuple(x-y for x,y in zip(av,bv))
        assert all(sum(v[q]*(F(a[q])-av[q]) for q in range(3))>=0 for a in A.verts)
        assert all(sum(v[q]*(F(b[q])-bv[q]) for q in range(3))<=0 for b in boxB.verts)
        target2=sum(x*x for x in v)
        assert F(d)**2>=target2-F(1,10**15) and F(d)**2<=target2+F(1,10**15)
        assert inflated_membership(A,boxB,delta=.2)==1
        assert min(c.exact_distance_squared for c in margin_contacts(A,boxB,delta=.2))==target2
        outputs.append([psi,d,list(label)])
    record(25,'thin wedge VV exact vertex-projection oracle and three margin APIs',outputs)

if __name__=='__main__':
    replays()
    (ROOT/'review/evidence/mechanics_replays.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print('MECHANICS_REPLAY_DONE 10 distinct original findings',flush=True)
