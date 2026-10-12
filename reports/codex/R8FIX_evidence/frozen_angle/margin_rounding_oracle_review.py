"""Read-only production audit: independent EE Gram/midpoint construction gate."""
from pathlib import Path
from fractions import Fraction as F
import sys,math,struct,json,inspect
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT/"src"),str(ROOT/"tests")]
import test_invariance_geom as gate
import eab.margin as production

name,rotation,translation,scale="box_box_face",7,0.,.001
base,motion,A,B=gate._cell(name,rotation,translation,scale)
delta=scale*gate.PAIRS[name][3]
label=("EE",("edge",0,1),("edge",5,6))
# Test-owned raw endpoint model: no eab dot/cross/normal/witness primitive.
def sub(a,b):return tuple(F(x)-F(y) for x,y in zip(a,b))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
u=sub(A.verts[1],A.verts[0]);v=sub(B.verts[6],B.verts[5])
w=sub(A.verts[0],B.verts[5]);n=cross(u,v)
squared=dot(n,w)**2/dot(n,n)

def certified(value):
    previous=math.nextafter(value,-math.inf)
    following=math.nextafter(value,math.inf)
    assert math.isfinite(previous) and math.isfinite(following)
    lower=(F(previous)+F(value))/2
    upper=(F(following)+F(value))/2
    # sqrt(q)-delta compared with a rational target; shifted target negative
    # needs no squaring, otherwise q versus target^2 is an exact order test.
    def comparison(target):
        shifted=F(delta)+target
        if shifted<0:return 1
        difference=squared-shifted*shifted
        return (difference>0)-(difference<0)
    lo,hi=comparison(lower),comparison(upper)
    even=not(struct.unpack(">Q",struct.pack(">d",value))[0]&1)
    return (lo>0 or lo==0 and even) and (hi<0 or hi==0 and even)

def current():
    return next(m for m in gate.margin_contacts(A,B,delta=delta) if m.label==label)

original=production._normalized_difference
original_contacts=production.margin_contacts
source=inspect.getsource(original_contacts)
old_line="gap = _normalized_difference(d2, d2 or Fraction(1), Fraction(delta), allow_underflow=True)"
assert old_line in source
namespace=dict(vars(production))
exec(compile(source.replace(old_line,"gap = w - delta"),"MUTANT/margin.py","exec"),namespace)
old_contacts=namespace["margin_contacts"]
rows=[]
contact=current()
assert contact.exact_distance_squared==squared
assert certified(contact.margin_gap)
rows.append(dict(case="fixed",distance=contact.distance,gap=contact.margin_gap,
                 old_double_round=contact.distance-delta,midpoint_certified=True))
mutants={
 "old_subtraction": lambda c,nn,d,**kw: original(c,nn,0,**kw)-float(d),
 "omit_delta":lambda c,nn,d,**kw:original(c,nn,0,**kw),
 "reverse_delta":lambda c,nn,d,**kw:original(c,nn,-d,**kw),
 "double_distance":lambda c,nn,d,**kw:original(2*c,nn,d,**kw),
}
try:
    for name,mutant in mutants.items():
        production._normalized_difference=original if name=="old_subtraction" else mutant
        production.margin_contacts=old_contacts if name=="old_subtraction" else original_contacts
        item=current()
        assert item.exact_distance_squared==squared
        assert not certified(item.margin_gap),(name,item)
        rows.append(dict(case=name,gap=item.margin_gap,midpoint_certified=False,
                         target_assertion="exact sqrt(d2)-delta midpoint certificate"))
finally:
    production._normalized_difference=original
    production.margin_contacts=original_contacts
print(json.dumps({"target_label":label,"delta":delta,"rows":rows},indent=2))
