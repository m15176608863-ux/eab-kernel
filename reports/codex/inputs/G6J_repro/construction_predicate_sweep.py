"""Independent mixed-range Fraction sign / integer-arithmetic sweep."""
from fractions import Fraction as F
from pathlib import Path
import random, sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab import predicates as p, rational3 as q
r=random.Random(193610)
def sign(v):return (v>0)-(v<0)
def dot(a,b):return sum(F(x)*F(y) for x,y in zip(a,b))
def cross(a,b):return tuple(F(a[i])*F(b[j])-F(a[j])*F(b[i]) for i,j in [(1,2),(2,0),(0,1)])
def sub(a,b):return tuple(F(x)-F(y) for x,y in zip(a,b))
def v():
    out=[]
    for _ in range(3):
        x=F(r.randint(-31,31),r.randint(1,31))*F(2)**r.choice([-1200,-1074,-1022,-600,-200,-1,0,1,200,600,1023,1200])
        if r.random()<.45:
            try:x=float(x)
            except OverflowError:pass
            if isinstance(x,float) and abs(x)==float('inf'):x=F(2)**1200
        out.append(x)
    return tuple(out)
for i in range(2500):
    a,b,c,d=(v() for _ in range(4))
    assert p.cross2_sign(a[:2],b[:2])==sign(F(a[0])*F(b[1])-F(a[1])*F(b[0])),('cross2',i)
    assert p.dot2_sign(a[:2],b[:2])==sign(dot(a[:2],b[:2])),('dot2',i)
    assert p.orient3d(a,b,c,d)==sign(dot(cross(sub(b,a),sub(c,a)),sub(d,a))),('orient3d',i)
    af,bf=tuple(map(F,a)),tuple(map(F,b))
    assert q.dot(af,bf)==dot(a,b)
    assert q.cross(af,bf)==cross(a,b)
    assert q.fraction_vectors(af,bf)
print('CONSTRUCTION_PREDICATE_SWEEP PASS 2500 mixed-range quadruples; 12500 exact comparisons')
