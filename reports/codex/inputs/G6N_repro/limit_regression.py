"""WO-G6N C: read-only production replay; all writes are review-local.

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
    code="import sys;sys.dont_write_bytecode=True;sys.path.insert(0,'tools');import ingest_bdda3d as m; s=m.source_note('cb2_locked'); assert not any(ord(c)<32 for c in s); print(repr(s[-100:]))"
    p=subprocess.run([sys.executable,'-X','utf8','-W','error::SyntaxWarning','-c',code],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    assert p.returncode==0,(p.stdout,p.stderr)
    record(2,'provenance source_note has no control bytes and warning-safe import',p.stdout.strip())

def gauss(A,b):
    n=len(b);T=[list(map(F,row))+[F(rhs)] for row,rhs in zip(A,b)]
    for j in range(n):
        pivot=next((i for i in range(j,n) if T[i][j]),None)
        if pivot is None:return None
        T[j],T[pivot]=T[pivot],T[j];d=T[j][j];T[j]=[v/d for v in T[j]]
        for i in range(n):
            if i!=j:
                f=T[i][j];T[i]=[a-f*v for a,v in zip(T[i],T[j])]
    return [row[-1] for row in T]

def lp_oracle_search():
    rng=random.Random(1407);checked=0;statuses={}
    for i in range(300):
        n=rng.randrange(3,8);m=rng.randrange(1,min(n,4))
        A=[[F(1)]*n]+[[F(rng.randrange(-8,9)) for _ in range(n)] for _ in range(m-1)]
        witness=[F(rng.randrange(0,5)) for _ in range(n)]
        if not any(witness):witness[0]=F(1)
        b=[sum(x*v for x,v in zip(row,witness)) for row in A]
        c=[F(rng.randrange(-7,8)) for _ in range(n)]
        # Independent row/column scaling across binary64 and beyond its range.
        row_scale=[F(2)**rng.choice((-1200,-1074,-400,0,400,1023,1200)) for _ in range(m)]
        col_scale=[F(2)**rng.choice((-1100,-400,0,400,1100)) for _ in range(n)]
        AE=[[v*row_scale[q]*col_scale[j] for j,v in enumerate(row)] for q,row in enumerate(A)]
        bE=[v*row_scale[q] for q,v in enumerate(b)];cE=[v*col_scale[j] for j,v in enumerate(c)]
        candidates=[]
        for js in itertools.combinations(range(n),m):
            v=gauss([[row[j] for j in js] for row in AE],bE)
            if v is not None and min(v)>=0:candidates.append(sum(cE[j]*x for j,x in zip(js,v)))
        assert candidates
        target=min(candidates)
        def view(v):
            try:return float(v)
            except OverflowError:return math.inf if v>0 else -math.inf
        r=LP.solve([[view(v) for v in row] for row in AE],[view(v) for v in bE],[view(v) for v in cE],exact=(AE,bE,cE))
        assert r.status=='optimal',(i,r.status)
        x,y=r.exact_x,r.exact_y
        assert x is not None and y is not None
        assert min(x)>=0 and all(sum(a*t for a,t in zip(row,x))==v for row,v in zip(AE,bE))
        assert sum(q*t for q,t in zip(cE,x))==target==sum(v*t for v,t in zip(bE,y))
        assert all(cE[j]-sum(y[q]*AE[q][j] for q in range(m))>=0 for j in range(n))
        assert r.x==[view(v) for v in x] and r.y==[view(v) for v in y] and r.obj==view(target)
        checked+=1;statuses[r.status]=statuses.get(r.status,0)+1
    print(f'INDEPENDENT LP oracle: {checked} exact vertex/certificate/float-view comparisons passed; {statuses}',flush=True)
    results.append({'label':'independent LP exhaustive BFS comparison','checked':checked,'statuses':statuses,'pass':True})

if __name__=='__main__':
    replays();lp_oracle_search()
    (ROOT/'review/evidence/limit_regression_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print('LIMIT_REPLAY_DONE 10 old findings; 300 independent LP problems',flush=True)
