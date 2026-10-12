from fractions import Fraction as F
from pathlib import Path
import hashlib,json,subprocess
from eab import margin as M
from eab.numeric_domain import ConstructionDomainError
from eab.kernel3d import interlock as I
from eab.kernel3d.geom3 import Polyhedron,polyhedra_overlap
from eab.kernel3d.exact_sweep import translate_exact
OUT=Path('reports/codex/R13FIXb_evidence/kernel/threshold_review')
faces=((0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5))
def box(s):
    return Polyhedron([(x*s,y*s,z*s) for x,y,z in ((0,0,0),(3,0,0),(3,4,0),(0,4,0),(0,0,12),(3,0,12),(3,4,12),(0,4,12))],list(faces))
rows=[]
for exp in (-1070,-400,0,396):
    s=F(2)**exp; p=box(s); q=translate_exact(p,(s/4,0,s/4))
    # 3-4-12 independent diagonal is exactly 13; never calls a geometry oracle.
    er=F(64)*F(2)**-52*13*s; eg=max(F(1e-9)*13*s,er)
    assert M._rounding_floor_exact(q,p)==er>0
    assert M._effective_geom_tol_exact(q,p)==eg>0
    if exp == -1070:
        for name in ('rounding_floor','effective_geom_tol','boundary_band'):
            try: getattr(M,name)(q,p)
            except ConstructionDomainError as exc:
                assert exc.quantity==name+' result', (name,str(exc))
            else: raise AssertionError(name+' silently accepted nonzero subnormal threshold')
    else:
        assert M.rounding_floor(q,p)==float(er)
        assert M.effective_geom_tol(q,p)==float(eg)
    rows.append({'scale_exp':exp,'exact_floor':str(er),'exact_geom_tol':str(eg),'passed':True})
# Entire finite rational predicate domain: below binary64 and above binary64,
# not merely the declared construction envelope. Exact interval truth is obvious.
for exp in (-1200,1200):
    p=box(F(2)**exp); s=F(2)**exp
    assert polyhedra_overlap(p,p,0)==1
    assert polyhedra_overlap(translate_exact(p,(3*s,0,0)),p,0)==0
    assert polyhedra_overlap(translate_exact(p,(4*s,0,0)),p,0)==-1
# A warmed cache must not hide a defect in the actual threshold producer.
s=F(2)**-1070; p=box(s); off=(s/4,0,s/4)
gtol=M._effective_geom_tol_exact(translate_exact(p,off),p)
I._candidates_cached.cache_clear()
_,r=I._candidates(p,p,off,1e-9,gtol)
assert r>0
before=I._candidates_cached.cache_info()
original=I._rounding_floor_exact
calls=[]
def early_rounding(*bodies):
    calls.append(1)
    return float(original(*bodies))
I._rounding_floor_exact=early_rounding
try:
    _,mutant_r=I._candidates(p,p,off,1e-9,gtol)
    after=I._candidates_cached.cache_info()
    assert calls and after.misses==before.misses+1
    assert mutant_r == 0.0 and not isinstance(mutant_r,F)
    try: assert isinstance(mutant_r,F) and mutant_r==r>0, 'internal threshold exact nonzero reference'
    except AssertionError as exc: killed=str(exc)
    else: raise AssertionError('early rounding unexpectedly survived')
finally:
    I._rounding_floor_exact=original
    I._candidates_cached.cache_clear()
old='tests/test_r13fix_event_bindings.py'
assert Path(old).read_bytes()==subprocess.check_output(['git','show','HEAD:'+old]), 'old gate edited'
files=('src/eab/margin.py','src/eab/kernel3d/interlock.py',old,'tests/test_r13fixb_dual_margin.py')
result={'threshold_numeric':rows,'predicate_scales':[-1200,1200],'predicate_states':[1,0,-1],'warm_cache_mutation':{'before':list(before),'after':list(after),'calls':len(calls),'killed_at':killed},'old_event_gate_unchanged_vs_HEAD':True,'sha256':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in files},'status':'PASS'}
(OUT/'independent_checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print('PASS: 4 exact threshold scales, 6 all-finite exact predicate states, 3 named public CDEs, warm-cache real helper early-rounding mutation, unchanged old gate')
