"""Repro finding tests/test_limit_multi.py:238: tiny penetrating motion at a far block."""
import sys,types
from pathlib import Path
import eab
if "--baseline" in sys.argv:
    base=Path(__file__).resolve().parent/"tmp/limit_baseline"
    for leaf in ("limit","limit_multi"):
        name="eab."+leaf
        mod=types.ModuleType(name);mod.__package__="eab";mod.__file__=str(base/(leaf+".py"))
        sys.modules[name]=mod;setattr(eab,leaf,mod)
        exec(compile((base/(leaf+".py")).read_text(encoding="utf-8"),mod.__file__,"exec"),mod.__dict__)
from eab.limit import LimitContact as C
from eab.limit_multi import LimitBody as B, BodyContact as BC,limit_load_multi,check_duality_multi,mechanism_is_admissible_multi
from fractions import Fraction as F
b=[B([0.,-30.,0.],[0.]*3),B([0.,-10.,0.],[1.,0.,-2.]),B([0.,-10.,-1e5],[0.]*3)]
cs=[BC(C((x,0.),(0.,1.),1.2),0) for x in (-1.,1.)]+[BC(C((x,1.),(0.,1.),1.2),1,0) for x in (-1.,1.)]+[BC(C((1e4+x,0.),(0.,1.),1.2),2) for x in (-1.,1.)]
for k in (3,9,30,100):
    r=limit_load_multi(b,cs,dim=2)
    r.mechanisms=[[getattr(v,"exact",F(v)) for v in m] for m in r.mechanisms]
    r.mechanisms[1][1]-=F(1,10**k)
    admissible=mechanism_is_admissible_multi(r.mechanisms,cs,dim=2)
    ok=check_duality_multi(r,b,cs,dim=2)["ok"]
    print(k,"admissible",admissible,"ok",ok)
    if "--assert-rejected" in sys.argv:
        assert not admissible and not ok,(k,admissible,ok)
