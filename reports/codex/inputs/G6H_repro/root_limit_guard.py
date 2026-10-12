"""Reviewer independent 2-D equilibrium and wrong-candidate rejection.
Oracles use Fraction formulas, no production wrench/shift/LP assembly helpers.
Monkeypatches affect in-process code only; restored in finally.
"""
import sys, json, copy, random
from pathlib import Path
from fractions import Fraction as F
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
import eab.limit as L
import eab.limit_multi as M
import eab.lp as P

def case(mu,W,h,s,T):
 cs=[L.LimitContact((T-s,0),(0,1),mu),L.LimitContact((T+s,0),(0,1),mu)]
 dead=[0,-W,-T*W]; live=[1,0,-h]
 truth=min(F(mu)*F(W),F(W)*F(s)/F(h))
 return cs,dead,live,truth

def main():
 solved=single_reject=multi_reject=live_reject=0
 for exp in (-600,-40,0,40,600):
  W=2.**exp
  for mu,h in ((.125,.5),(.5,2.),(.5,4.),(0.,2.)):
   for T,s in ((0.,1.),(2.**20,1.),(2.**20,2.**-20)):
    cs,dead,live,truth=case(mu,W,h,s,T)
    r=L.limit_load(cs,dead,live,dim=2)
    assert r.status=='optimal' and r.alpha.exact==truth,(exp,mu,h,T,s,r,truth)
    assert L.check_duality(r,cs,dead,live,dim=2)['ok']
    mr=M.limit_load_multi([M.LimitBody(dead,live)],[M.BodyContact(c,0) for c in cs],dim=2)
    assert mr.status=='optimal' and mr.alpha.exact==truth
    solved+=1
    for field in ('alpha','lambdas','mechanism'):
     bad=copy.deepcopy(r); mbad=copy.deepcopy(mr); tiny=F(1,10**100)
     if field=='alpha': bad.alpha=r.alpha.exact+tiny; mbad.alpha=mr.alpha.exact+tiny
     elif field=='lambdas': bad.lambdas[0]=r.lambdas[0].exact+tiny; mbad.lambdas[0]=mr.lambdas[0].exact+tiny
     else: bad.mechanism[1]=r.mechanism[1].exact-tiny; mbad.mechanisms[0][1]=mr.mechanisms[0][1].exact-tiny
     assert not L.check_duality(bad,cs,dead,live,dim=2)['ok'],field
     assert not M.check_duality_multi(mbad,[M.LimitBody(dead,live)],[M.BodyContact(c,0) for c in cs],dim=2)['ok'],field
     single_reject+=1; multi_reject+=1
 # Real limit_load path: poisoned LP view or poisoned exact witness must be rejected.
 cs,dead,live,_=case(.125,10.,.5,1.,0.)
 real=L.maximize
 for mode in ('float_alpha','fraction_alpha','exact_x','exact_y'):
  def poison(A,b,c,**kw):
   r=real(A,b,c,**kw)
   if r.status=='optimal':
    j=next(j for j,v in enumerate(c) if v)
    if mode=='float_alpha': r.x[j]*=.999
    elif mode=='fraction_alpha': r.x[j]=r.exact_x[j]-F(1,10**100)
    else:
     seq=list(getattr(r,mode)); seq[j if mode=='exact_x' else 0]+=F(1,10**100); setattr(r,mode,tuple(seq))
   return r
  L.maximize=poison
  try:
   try: L.limit_load(cs,dead,live,dim=2)
   except RuntimeError as e: assert 'self-check' in str(e); live_reject+=1
   else: raise AssertionError('wrong LP candidate was accepted: '+mode)
  finally: L.maximize=real
 print(json.dumps(dict(exact_closed_form_pairs=solved,single_wrong_candidate_rejections=single_reject,multi_wrong_candidate_rejections=multi_reject,limit_load_live_path_poison_rejections=live_reject,all_equal=True),indent=2))
if __name__=='__main__':main()
