"""Zero-constraint OPTIMAL LP witness contract and zero power boundary."""
import sys,json
from pathlib import Path
from fractions import Fraction as F
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.lp import solve,maximize
from eab.dual import Dual
for name,f,c in [('min',solve,[0.,1.]),('max',maximize,[0.,-1.])]:
 r=f([],[],c)
 print(name,'status=',r.status,'x=',r.x,'y=',r.y,'exact_x=',r.exact_x,'exact_y=',r.exact_y)
 assert r.status=='optimal' and r.x==[0.,0.] and r.exact_x is None and r.exact_y is None
r=solve([[1.]],[0.],[1.]); print('one-row reference exact_x=',r.exact_x,'exact_y=',r.exact_y)
for base in [0.,2.]:
 try: r=Dual(base,(1.,))**0.; print('pow0',base,r)
 except Exception as e: print('pow0',base,type(e).__name__,str(e))
print('python_float_zero_power=',0.**0.)
