"""Positive post-fix assertions on every original G6F07/11/12 input."""
import sys,math,json
from pathlib import Path
from fractions import Fraction as F
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.dual import Dual,atan2
from eab.lp import solve,maximize
out=[]
for scale in (1.,1e200,1e-200):
    got=atan2(Dual(scale,(0.,)),Dual(scale,(1.,)))
    expected=float(-F(1)/(2*F(scale)))
    assert got.e==(expected,)
    out.append(dict(case='G6F07 atan2',scale=scale,got=got.e[0],expected=expected))
for scale in (1e200,1e-200):
    got=Dual(scale,(scale,))/scale
    assert got.v==1 and got.e==(1.,)
    out.append(dict(case='G6F07 quotient',scale=scale,got=repr(got)))
for base in (0.,2.):
    got=Dual(base,(1.,))**0.
    assert got.v==1 and got.e==(0.,)
    out.append(dict(case='G6F11',base=base,got=repr(got)))
for name,fn,c in [('min',solve,[0.,1.]),('max',maximize,[0.,-1.])]:
    got=fn([],[],c)
    assert got.status=='optimal' and got.exact_x==(F(0),F(0)) and got.exact_y==()
    assert got.x==list(map(float,got.exact_x)) and got.y==list(map(float,got.exact_y))
    out.append(dict(case='G6F12',name=name,x=got.x,y=got.y,exact_x=list(map(str,got.exact_x)),exact_y=[]))
print(json.dumps(out,ensure_ascii=False,indent=2))
