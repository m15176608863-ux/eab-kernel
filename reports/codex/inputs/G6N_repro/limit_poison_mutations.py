"""WO-G6N C candidate injection and byte-safe isolated source mutations."""
from pathlib import Path
from fractions import Fraction as F
import hashlib
import json
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'src'))
import eab.lp as LP
import eab.limit as L
records=[]
def h(b):return hashlib.sha256(b).hexdigest()

def poison():
    cases=[([[1.,1.]],[1.],[0.,-1.],LP.OPTIMAL,F(-1)),
           ([[1.]],[-1.],[0.],LP.INFEASIBLE,None),
           ([[1.,-1.]],[1.],[0.,-1.],LP.UNBOUNDED,None)]
    real=LP._float_solve
    try:
        for i,(A,b,c,st,obj) in enumerate(cases):
            n=len(c)
            for lie in ('optimal','unbounded','infeasible'):
                # Lie at the actual float-candidate entry, not after output.
                LP._float_solve=lambda *a,lie=lie,**kw:(lie,[0],n-1,0)
                r=LP.solve(A,b,c)
                assert r.status==st,(i,lie,r)
                if obj is not None:
                    assert sum(F(x)*F(y) for x,y in zip(c,r.exact_x))==obj
                    assert r.x==[float(v) for v in r.exact_x]
                    assert r.y==[float(v) for v in r.exact_y]
                records.append({'kind':'lying_candidate','case':i,'lie':lie,'actual':r.status,'pass':True})
                print(f'POISON float case={i} lie={lie}: returned={r.status}, exact fallback/certificate protected',flush=True)
    finally:LP._float_solve=real
    real=L.maximize
    cs=[L.LimitContact((x,0.),(0.,1.),1e-5) for x in (-1.,1.)]
    args=(cs,[0.,-10.,0.],[1.,0.,-.5])
    for name in ('primal_view','dual_view','exact_x','exact_y'):
        def skew(A,b,c,**kw):
            r=real(A,b,c,**kw)
            if r.status=='optimal':
                if name=='primal_view':
                    j=next(i for i,v in enumerate(c) if v);r.x[j]=F(r.exact_x[j])*(1-F(1,10**100))
                elif name=='dual_view':r.y[0]=F(r.exact_y[0])+F(1,10**100)
                else:
                    seq=list(getattr(r,name));j=next(i for i,v in enumerate(c) if v) if name=='exact_x' else 0
                    seq[j]+=F(1,10**100);setattr(r,name,tuple(seq))
            return r
        L.maximize=skew
        try:L.limit_load(*args,dim=2)
        except RuntimeError as ex:
            assert 'self-check' in str(ex)
            records.append({'kind':'live_limit_poison','field':name,'exception':str(ex),'pass':True})
            print(f'POISON limit field={name} error=1e-100: self-check RuntimeError',flush=True)
        else:raise AssertionError(f'limit poison {name} survived')
    L.maximize=real

def mutations():
    dst=ROOT/'review/copies/limit_mutation'
    files=subprocess.run(['git','ls-files','-z'],cwd=ROOT,capture_output=True,check=True).stdout.decode('utf-8').split('\0')
    for rel in filter(None,files):
        src=ROOT/rel
        if src.is_file():
            target=dst/rel
            if target.exists():
                assert target.read_bytes()==src.read_bytes(),f'Existing snapshot differs: {rel}'
            else:
                target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,target)
    cases=[
      ('static_noise','src/eab/limit.py','all(v == 0 for v in residual)',
       'all(abs(v) <= F_noisy * sum(abs(z) for z in dead) for v in residual)',
       ['tests/test_limit_exact_selfcheck.py::test_exact_single_static_and_gap_reject_arbitrary_rational_alpha_error']),
      ('unbounded_screen','src/eab/limit_multi.py',
       'if rmin.status == OPTIMAL and _lp_values(rmin.x, rmin.exact_x)[ia] > 0:',
       'if False:',
       ['tests/test_limit_exact_selfcheck.py::test_multi_unbounded_screen_covers_both_rejection_branches_and_nonzero_body']),
    ]
    for name,rel,old,new,args in cases:
        path=dst/rel;before=path.read_bytes();text=before.decode('utf-8')
        assert text.count(old)==1,(name,text.count(old))
        if name=='static_noise':new=new.replace('F_noisy','Fraction(1,10**7)')
        changed=text.replace(old,new).encode('utf-8');path.write_bytes(changed)
        try:
            cmd=[sys.executable,'-X','utf8','-m','pytest','-q','-p','no:cacheprovider',*args,
                 '--basetemp='+str(dst/'review_tmp'/name),'--tb=short']
            p=subprocess.run(cmd,cwd=dst,capture_output=True,text=True,encoding='utf-8')
            log=ROOT/f'review/logs/limit_mutation_{name}.txt';log.write_text(p.stdout+p.stderr,encoding='utf-8')
            assert p.returncode==1,(name,p.returncode,p.stdout,p.stderr)
            assert 'FAILED' in p.stdout and 'AssertionError' in p.stdout
            expected='assert not d["static_ok"]' if name=='static_noise' else "assert r.resolvability =="
            assert expected in p.stdout,(name,p.stdout)
            records.append({'kind':'isolated_mutation','name':name,'returncode':p.returncode,
                            'before_sha256':h(before),'mutated_sha256':h(changed),
                            'assertion':expected,'log':str(log),'pass':True})
            print(f'MUTATION {name}: target assertion red; {p.stdout.splitlines()[-1]}',flush=True)
        finally:
            path.write_bytes(before);assert h(path.read_bytes())==h(before)
    # Parent source hashes prove no tracked target file was touched.
    records.append({'kind':'copy_restoration','source_hashes':{rel:h((ROOT/rel).read_bytes()) for _,rel,*_ in cases},'pass':True})

if __name__=='__main__':
    poison();mutations()
    (ROOT/'review/evidence/limit_poison_mutation_results.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    print('LIMIT_POISON_MUTATION_DONE',flush=True)
