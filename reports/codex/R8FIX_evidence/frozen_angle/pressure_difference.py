"""Finite selected mixed-scale pressure, independent Decimal reference."""
from pathlib import Path
from decimal import Decimal,localcontext
from fractions import Fraction as F
import random,sys,math,json
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/"src"))
from eab.kernel3d.frozen import _normalized_difference
rng=random.Random(8302)
rows=[]
for i in range(600):
    c=F(rng.randint(-100,100))*F(2)**rng.randint(-1100,1100)
    nn=sum((F(rng.randint(1,100))*F(2)**rng.randint(-600,600))**2 for _ in range(3))
    b=F(rng.randint(-100,100))*F(2)**rng.randint(-1100,1100)
    if i%4==0:
        # Deliberately exact rational normalized inputs, close subtraction.
        root=F(2)**rng.randint(-1100,1100)
        nn=root*root
        b=F(rng.randint(-100,100))*F(2)**rng.randint(-1100,1100)
        c=(b+F(rng.choice([-1,1]))*F(2)**rng.randint(-1100,100))*root
    with localcontext() as ctx:
        ctx.prec=1600
        def dec(q):return Decimal(q.numerator)/Decimal(q.denominator)
        value=dec(c)/dec(nn).sqrt()-dec(b)
        expected=float(value)
    expected_error=(not math.isfinite(expected)) or (not expected and bool(value))
    try:
        actual=_normalized_difference(c,nn,b)
    except (ArithmeticError,OverflowError) as exc:
        assert expected_error,(i,type(exc).__name__,expected)
        rows.append({"i":i,"kind":"range_error"})
    else:
        assert not expected_error and actual==expected,(i,actual,expected)
        rows.append({"i":i,"kind":"finite"})
print(json.dumps({"seed":8302,"cases":len(rows),"finite":sum(r["kind"]=="finite" for r in rows),
 "range_errors":sum(r["kind"]=="range_error" for r in rows),"status":"PASS",
 "reference":"Decimal precision=1600; finite deliberately bounded samples, not a formal all-input proof"},indent=2))
