"""WO-G6I: independent interval truth exposes squared-distance pre-rounding.

Writes nothing; production and test helper are both exercised on the exact
same raw boxes. No production geometric primitive computes expected truth.
"""
from pathlib import Path
from fractions import Fraction as F
import json
import inspect
import ast
import subprocess
import math
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]
from eab.kernel3d.geom3 import Polyhedron
from eab.margin import body_distance
from e5b_margin_oracle import check_exact_margin
import eab.margin as production
import pytest

FACES = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
SIGNS = [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
         (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]

def cube(center, scale):
    return Polyhedron([tuple(center[k] + sign[k]*scale for k in range(3))
                       for sign in SIGNS], FACES.copy())

rows = []
for exponent in (-500, -540, -600):
    scale = F(2)**exponent
    a, b = cube((4*scale, F(0), F(0)), scale), cube((F(0),)*3, scale)
    # Cartesian product truth: separation only in x, lower A.x - upper B.x = 2s.
    truth = 2*scale
    got, label = body_distance(a, b)
    assert got == float(truth) and got > 0
    prematurely_rounded = math.sqrt(float(truth**2))
    try:
        check_exact_margin(a, b, 3*scale, state=-1, minimum_squared=truth**2)
        status = "PASS"
    except AssertionError as error:
        status = f"AssertionError: {error}"
    rows.append({"exponent": exponent, "production": got,
                 "independent_interval_truth": float(truth),
                 "sqrt_float_squared_oracle": prematurely_rounded,
                 "test_oracle_status": status, "label": label})
assert all(row['test_oracle_status']=='PASS' for row in rows),rows
print(json.dumps(dict(result='FIXED',rows=rows),indent=2))
# Real internal mutation remains test-owned/in-memory, never output fabrication.
originals={n:getattr(production,n) for n in ('body_distance','margin_contacts')}
faults=(('body_distance','_exact.sqrt_rational(d2)','math.sqrt(float(d2))'),
        ('margin_contacts','w = _exact.sqrt_rational(d2, allow_underflow=True)','w = math.sqrt(float(d2))'))
for name,anchor,replacement in faults:
    source=inspect.getsource(originals[name]);assert source.count(anchor)>=1
    scope=dict(vars(production));exec(compile(source.replace(anchor,replacement),__file__,'exec'),scope)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(production,name,scope[name]);scale=F(2)**-600
        a,b=cube((4*scale,F(0),F(0)),scale),cube((F(0),)*3,scale)
        try:check_exact_margin(a,b,3*scale,state=-1,minimum_squared=4*scale**2)
        except AssertionError as e:
            assert ('distance construction' if name=='body_distance' else 'cover distance') in str(e),e
            print('MUTATION REJECTED:',name,str(e))
        else:raise AssertionError('real internal premature square rounding escaped')
assert all(getattr(production,n) is o for n,o in originals.items())
