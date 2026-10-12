"""Known-builtin higher-order calls bypass exact-construction gate.
No tracked file is written. Real cone function is recompiled in memory.
Independent expected answer: rational KKT equations + binary64 squared midpoint cells.
Run: python -X utf8 review/repro/numeric_static_higher_order.py
"""
from pathlib import Path
from fractions import Fraction as F
import sys,math,hashlib,importlib.util,inspect,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
spec=importlib.util.spec_from_file_location('g6l_gate',ROOT/'tools/check_exact_construction.py');gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
from eab.kernel3d import covers3 as covers
from eab.kernel3d.geom3 import tetra
tracked=ROOT/'src/eab/kernel3d/covers3.py';before=hashlib.sha256(tracked.read_bytes()).hexdigest();source=tracked.read_text(encoding='utf8');old='return norm_rational(p), noise';assert source.count(old)==1
q=F(1,2**1074);u=math.ulp(0.0);assert F(u)==q
rows=((-F(1),F(1),-q),(-q,-F(1),F(1)),(F(1),-q,-F(1)));point=(-q/3,)*3;square=q*q/3
assert point==tuple(sum(r[i] for r in rows)/3 for i in range(3))
assert all(sum(x*y for x,y in zip(point,r))==square for r in rows)
assert (q/2)**2 < square < (3*q/2)**2
shape=tetra((0.,0.,0.),(1.,-1.,u),(u,1.,-1.),(-1.,u,1.));baseline=covers.cone_intersection_margin(shape,0,shape.reflected(),0)[0];assert baseline==u
bodies={
'map_norm':'return tuple(map(norm_rational, [vector_rational(p, allow_underflow=True)]))[0], noise',
'map_sqrt':'return tuple(map(sqrt_rational, [scalar_rational(sum(x*x for x in p), allow_underflow=True)]))[0], noise',
'iter_callable':'root = next(iter([norm_rational]))\n    return root(vector_rational(p, allow_underflow=True)), noise',
'pop_callable':'box = [norm_rational]\n    root = box.pop()\n    return root(vector_rational(p, allow_underflow=True)), noise',
}
results=[]
for name,body in bodies.items():
 namespace=dict(vars(covers));function=inspect.getsource(covers.cone_intersection_margin).replace(old,body);exec(compile(function,'<G6L '+name+' real cone mutant>','exec'),namespace)
 output=namespace['cone_intersection_margin'](shape,0,shape.reflected(),0)[0];issues=gate.scan_text(source.replace(old,body),'src/eab/kernel3d/covers3.py')
 assert output==0.0 and output!=u,(name,output)
 assert issues==[],(name,issues)
 results.append({'case':name,'baseline':repr(baseline),'expected_by_independent_KKT_and_midpoints':repr(u),'mutant':repr(output),'gate_issues':issues,'body':body})
assert before==hashlib.sha256(tracked.read_bytes()).hexdigest()
print(json.dumps({'confirmed':True,'results':results,'tracked_sha256_before':before,'tracked_sha256_after':hashlib.sha256(tracked.read_bytes()).hexdigest()},ensure_ascii=False,indent=2))
