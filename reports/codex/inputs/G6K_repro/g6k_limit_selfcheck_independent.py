"""Wrong candidate injection and resolution checks, not existing test helpers."""
import sys,copy,math,json
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
import eab.limit as L
import eab.limit_multi as M

rows=[];baseline=[]
for dim in [2,3]:
 for loadscale in [F(1,2**300),F(1),F(2**300)]:
  origin=tuple(0 for _ in range(dim));normal=(0,1) if dim==2 else (0,0,1)
  pts=[(-1,0),(1,0)] if dim==2 else [(x,y,0) for x in [-1,1] for y in [-1,1]]
  cts=[L.LimitContact(p,normal,F(1,2),cohesion=F(1,4),area=F(1)) for p in pts]
  dead=[F(0)]*(3 if dim==2 else 6);live=list(dead);dead[dim-1]=-10*loadscale;live[0]=loadscale
  # No moment -> symmetric sliding closed form, and Fraction loads exact.
  r=L.limit_load(cts,dead,live,dim=dim,k=4)
  assert L.check_duality(r,cts,dead,live,dim=dim,k=4)['ok']
  b=[M.LimitBody(dead,live)];bcs=[M.BodyContact(ct,0,None) for ct in cts];q=M.limit_load_multi(b,bcs,dim=dim,k=4)
  assert M.check_duality_multi(q,b,bcs,dim=dim,k=4)['ok']
  assert r.alpha.exact==q.alpha.exact
  baseline.append(dict(dim=dim,loadscale=str(loadscale),alpha_exact=str(r.alpha.exact),uncertainty=r.uncertainty,resolvability=r.resolvability))
  for k in [1,53,100,1000]:
   for model,base,check in [('single',r,lambda z:L.check_duality(z,cts,dead,live,dim=dim,k=4)),('multi',q,lambda z:M.check_duality_multi(z,b,bcs,dim=dim,k=4))]:
    wrong=copy.deepcopy(base);wrong.alpha=base.alpha.exact*(1-F(1,2**k));d=check(wrong)
    rows.append(dict(dim=dim,model=model,loadscale=str(loadscale),k=k,accepted=d['ok'],gap_exact=d['duality_gap_exact']));assert not d['ok']
# Inject a wrong exact candidate within the displayed float's rounding bucket.
real=L.maximize
cts=[L.LimitContact((-1,0),(0,1),F(1,2)),L.LimitContact((1,0),(0,1),F(1,2))];dead=[0,-10,0];live=[1,0,0]
for side in ['primal','dual']:
 def lie(A,b,c,**kw):
  r=real(A,b,c,**kw)
  if r.status=='optimal':
   if side=='primal':
    j=next(j for j,v in enumerate(c) if v);v=list(r.exact_x);v[j]-=F(1,2**100);r.exact_x=tuple(v)
   else:
    v=list(r.exact_y);v[0]+=F(1,2**100);r.exact_y=tuple(v)
  return r
 L.maximize=lie
 try:L.limit_load(cts,dead,live,dim=2);caught=False
 except RuntimeError as exc:caught=True
 rows.append(dict(case='lying sub-ULP exact candidate',side=side,caught=caught));assert caught
L.maximize=real
# NaN/Inf diagnostic injection must not classify resolved, including finite-alpha optimal and unbounded branches.
for model in ['single','multi']:
 mod=L if model=='single' else M;real_u=mod._live_uncertainty
 for v in [float('nan'),float('inf')]:
  mod._live_uncertainty=lambda *args:v
  rr=L.limit_load(cts,dead,live,dim=2) if model=='single' else M.limit_load_multi([M.LimitBody(dead,live)],[M.BodyContact(ct,0,None) for ct in cts],dim=2)
  rows.append(dict(case='nonfinite-diagnostic',model=model,value=str(v),resolvability=rr.resolvability));assert rr.resolvability=='unresolved'
 mod._live_uncertainty=real_u
result=dict(baselines=baseline,injections=len(rows),all_rejected_or_unresolved=True,rows=rows);print(json.dumps(result,indent=2));(ROOT/'review/agents/limit_selfcheck_result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
