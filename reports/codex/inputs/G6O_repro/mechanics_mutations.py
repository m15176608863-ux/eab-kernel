"""WO-G6O scoped in-memory real-path mutants; tracked bytes never modified.
Red assertion is the exact property guarding each fault, not setup or some
solver vertex selection. Oracles use Fraction cross products / input statics.
"""
from pathlib import Path
from fractions import Fraction as F
import hashlib,inspect,json,sys,traceback
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'));sys.dont_write_bytecode=True
import eab.limit as L
sources=['src/eab/limit.py','src/eab/limit_multi.py','src/eab/lp.py','src/eab/margin.py']
hash_before={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}
results=[]
# Remove only the actual generator cone acceptance guard; compare actual
# directions against raw normal cross products independent of the routine.
orig=L._certified_friction_direction
source=inspect.getsource(orig);needle='if _inside_friction_cone(n,g,mu):';assert source.count(needle)==1
scope=dict(vars(L));exec(compile(source.replace(needle,'if True:'),'<mechanics cone guard removed>','exec'),scope)
L._certified_friction_direction=scope['_certified_friction_direction']
try:
 ct=L.LimitContact((0,0,0),(1,2,3),.5)
 actual=L.friction_generators(ct.normal,ct.mu,3,4)
 bad=[]
 for j,g in enumerate(actual):
  n,g=tuple(map(F,ct.normal)),tuple(map(F,g));p=sum(a*b for a,b in zip(n,g));cross=(n[1]*g[2]-n[2]*g[1],n[2]*g[0]-n[0]*g[2],n[0]*g[1]-n[1]*g[0]);outside=not(p>0 and sum(x*x for x in cross)<=F(ct.mu)**2*p*p)
  if outside:bad.append(j)
 try:assert not bad,'independent exact cross-square cone containment'
 except AssertionError as ex:
  results.append(dict(mutant='remove actual _certified_friction_direction acceptance condition',red_assertion=str(ex),outside_indices=bad));print('MUTANT_CONE RED:',str(ex),'indices',bad)
 else:raise AssertionError('cone mutation unexpectedly escaped independent guard')
 # Existing independent selfchecker must reject this genuine generator fault.
 try:L._check_columns([ct],(0,0,0),3,4)
 except L.ConstructionDomainError as ex:
  assert ex.quantity=='selfcheck friction generator';results.append(dict(mutant='same actual cone fault; independent selfcheck',red_guard=str(ex)));print('MUTANT_SELFHECK RED:',str(ex))
 else:raise AssertionError('bad actual cone was not caught by independent physical checker')
finally:L._certified_friction_direction=orig
# Ignore the LP moment reference point inside actual wrench coefficient path.
# Keep calls to original input wrench before injection, mimicking real API data.
cts=[L.LimitContact((x,-3),(0,1),1.5) for x in (4,6)]
dead=L.wrench((0,-10),(5,-2.5),(0,0),2);live=L.wrench((1,0),(5,-1),(0,0),2)
base=L.limit_load(cts,dead,live,dim=2);assert base.alpha.exact==5
orig=L._exact_wrench
L._exact_wrench=lambda force,point,origin,dim:orig(force,point,(0,)*dim,dim)
try:
 try:L.limit_load(cts,dead,live,dim=2)
 except RuntimeError as ex:
  assert 'self-check failed' in str(ex);results.append(dict(mutant='LP actual moment column ignores centroid reference',red_guard=str(ex)));print('MUTANT_MOMENT RED:',str(ex))
 else:raise AssertionError('real-column reference error escaped exact independent statics')
finally:L._exact_wrench=orig
hash_after={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}
assert hash_before==hash_after
(ROOT/'review/evidence/mechanics_mutations.json').write_text(json.dumps(dict(results=results,tracked_source_sha256_before=hash_before,tracked_source_sha256_after=hash_after),ensure_ascii=False,indent=2),encoding='utf-8')
print('MECHANICS_MUTATIONS_DONE 2 single-site production faults; exact property/physical selfcheck red; tracked SHA unchanged')
