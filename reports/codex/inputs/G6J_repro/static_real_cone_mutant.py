"""Reintroduce G6I-03 in a real production return, in-memory only.

No tracked files are edited. A keyword argument in the SAME expression is
not reflection or an arbitrary user function hiding cross-procedural flow.
"""
from pathlib import Path
from fractions import Fraction as F
import importlib.util, inspect, math, sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
import eab.kernel3d.covers3 as c
from eab.kernel3d.geom3 import tetra
spec=importlib.util.spec_from_file_location('gate',ROOT/'tools/check_exact_construction.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
old='return norm_rational(p), noise'
bad='return norm_rational(values=vector_rational(p, allow_underflow=True)), noise'
full=(ROOT/'src/eab/kernel3d/covers3.py').read_text(encoding='utf-8')
assert full.count(old)==1
issues=gate.scan_text(full.replace(old,bad),'src/eab/kernel3d/covers3.py')
assert not issues, issues
source=inspect.getsource(c.cone_intersection_margin)
namespace=dict(vars(c))
exec(compile(source.replace(old,bad),'<G6J cone keyword-rounded-vector mutant>','exec'),namespace)
d=math.ulp(0.)
A=tetra((0.,0.,0.),(1.,-1.,d),(d,1.,-1.),(-1.,d,1.));B=A.reflected()
baseline=c.cone_intersection_margin(A,0,B,0)[0]
mutated=namespace['cone_intersection_margin'](A,0,B,0)[0]
# Independent rational KKT witness and half-subnormal cell proof.
delta=F(d);point=(-delta/3,)*3;squared=delta*delta/3
constraints=((-F(1),F(1),-delta),(-delta,-F(1),F(1)),(F(1),-delta,-F(1)))
assert all(sum(x*y for x,y in zip(point,row))==squared for row in constraints)
assert (delta/2)**2<squared<(3*delta/2)**2
assert baseline==d and mutated==0
print('full real covers3 source AST violations:',issues)
print('real cone margin baseline:',baseline.hex())
print('real cone margin mutant:',mutated.hex())
print('independent KKT midpoint expected:',d.hex())
print('STATIC_REAL_CONE_MUTANT CONFIRMED: keyword known component-first defect accepted by AST')
