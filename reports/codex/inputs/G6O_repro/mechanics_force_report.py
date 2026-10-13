"""G6O production force-report counterexample, exact independent 2D statics.
No mutation. Independent oracle uses two known friction rays (-1/2,1),
(1/2,1). Solve statics by closed form: F_contact=(-H,W), moment=W
for p=(1,0), pure live couple=-1 gives alpha=W. Every column is selected
because tol=0; reported zero H therefore is not display truncation.
"""
from pathlib import Path
from fractions import Fraction as F
import json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'));sys.dont_write_bytecode=True
from eab.limit import LimitContact,limit_load,check_duality
from eab.limit_multi import LimitBody,BodyContact,limit_load_multi,check_duality_multi
output=[]
for W,H in [(F(10),F(1,2**60)),(F(2**60),F(1)),(F(2**400),F(1))]:
 ct=LimitContact((1,0),(0,1),F(1,2));dead=[H,-W,0];live=[0,0,-1]
 for which in ('single','multi'):
  if which=='single':
   r=limit_load([ct],dead,live,dim=2,tol=0);d=check_duality(r,[ct],dead,live,dim=2)
  else:
   bodies=[LimitBody(dead,live)];contacts=[BodyContact(ct,0,None)]
   r=limit_load_multi(bodies,contacts,dim=2,tol=0);d=check_duality_multi(r,bodies,contacts,dim=2)
  # Closed form eigenray decomposition independent of code paths.
  expected_lambda=(W/2+H,W/2-H)
  assert tuple(v.exact for v in r.lambdas)==expected_lambda
  expected=(-H,W)
  expected_RN=tuple(float(v) for v in expected)
  assert r.status=='optimal' and r.alpha.exact==W and d['ok']
  assert all(v>0 for v in expected_lambda)
  actual=r.contact_forces[0]
  assert actual[0]==0 and expected_RN[0]!=0 and actual!=expected_RN
  rec=dict(api=which,dead=list(map(str,dead)),live=live,tol=0,status=r.status,alpha=str(r.alpha.exact),check_duality_ok=d['ok'],exact_lambdas=list(map(str,expected_lambda)),expected_force=list(map(str,expected)),expected_RN=expected_RN,actual_force=actual)
  output.append(rec)
  print(which,'W=',str(W),'H=',str(H),'status=',r.status,'alpha=',float(r.alpha),'selfcheck=',d['ok'],'expected_RN=',expected_RN,'actual=',actual,flush=True)
# 3D variant: y load is exactly zero; round-and-cancel summation invents
# a nonzero y reaction despite exact equilibrium and zero display threshold.
for W,H in [(F(10),F(1,2**60)),(F(2**60),F(1))]:
 ct=LimitContact((1,0,0),(0,0,1),F(1,2));dead=[H,0,-W,0,0,0];live=[0,0,0,0,1,0]
 for which in ('single3d','multi3d'):
  if which=='single3d':
   r=limit_load([ct],dead,live,dim=3,k=4,tol=0);d=check_duality(r,[ct],dead,live,dim=3,k=4)
  else:
   bodies=[LimitBody(dead,live)];contacts=[BodyContact(ct,0,None)]
   r=limit_load_multi(bodies,contacts,dim=3,k=4,tol=0);d=check_duality_multi(r,bodies,contacts,dim=3,k=4)
  expected=(-H,F(0),W);expected_RN=tuple(float(v) for v in expected);actual=r.contact_forces[0]
  assert r.status=='optimal' and r.alpha.exact==W and d['ok']
  assert actual[1]!=0 and actual!=expected_RN
  rec=dict(api=which,dead=list(map(str,dead)),live=live,tol=0,status=r.status,alpha=str(r.alpha.exact),check_duality_ok=d['ok'],expected_force=list(map(str,expected)),expected_RN=expected_RN,actual_force=actual)
  output.append(rec)
  print(which,'W=',str(W),'H=',str(H),'status=',r.status,'alpha=',float(r.alpha),'selfcheck=',d['ok'],'expected_RN=',expected_RN,'actual=',actual,flush=True)
(ROOT/'review/evidence/mechanics_force_output.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
print('CONFIRMED 10 actual force reports lose nonzero shear or invent zero-axis force; zero display tolerance',flush=True)
