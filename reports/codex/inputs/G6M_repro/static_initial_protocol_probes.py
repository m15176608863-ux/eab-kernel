from pathlib import Path
import sys, importlib.util, math, json
from fractions import Fraction
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'src'))
spec=importlib.util.spec_from_file_location('g6m_static_probe',ROOT/'tools/check_exact_construction.py');gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
sources={
'inherited_getattribute': '''from dataclasses import dataclass
from fractions import Fraction
from eab.construction import norm_rational
class Parent:
    def __getattribute__(self, name):
        return (5e-324 * .5, 5e-324 * .5)
@dataclass
class Holder(Parent):
    points: tuple[Fraction, Fraction]
def bad(q: Fraction):
    return norm_rational(Holder((q, q)).points)
''',
'inherited_init': '''from fractions import Fraction
from eab.construction import norm_rational
class Parent:
    def __init__(self):
        self.points = (5e-324*.5, 5e-324*.5)
class Holder(Parent):
    points: tuple[Fraction, Fraction]
def bad(q: Fraction):
    return norm_rational(Holder().points)
''',
'dataclass_post_init': '''from dataclasses import dataclass
from fractions import Fraction
from eab.construction import norm_rational
@dataclass
class Holder:
    points: tuple[Fraction, Fraction]
    def __post_init__(self):
        self.points = (5e-324*.5, 5e-324*.5)
def bad(q: Fraction):
    return norm_rational(Holder((q,q)).points)
''',
'classmethod_property': '''from dataclasses import dataclass
from fractions import Fraction
from eab.construction import norm_rational
class Holder:
    @property
    @classmethod
    def points(cls):
        return (5e-324*.5, 5e-324*.5)
def bad(q: Fraction):
    return norm_rational(Holder().points)
''',
'round_supplied_float':'''from eab.construction import norm_rational
def bad(q: float):
    return norm_rational((round(q, 323), round(q,323)))
''',
'fractional_pow_alias':'''from fractions import Fraction
from eab.construction import norm_rational
def bad(q: Fraction):
    r=q*1.0
    expo=Fraction(1,2)
    return r**expo
''',
'changed_callee_via_union':'''from fractions import Fraction
from eab.construction import norm_rational
def twice(q: Fraction):
    return q*1.0
if True:
    def twice(q: Fraction):
        return q
def bad(q: Fraction):
    return norm_rational((twice(q),twice(q)))
''',
'annotation_unary_rounding':'''from eab.construction import norm_rational
def bad(q: float):
    return norm_rational((round(q,323),round(q,323)))
''',
'math_literal_return':'''import math
from eab.construction import norm_rational
def bad(q: float):
    return norm_rational((math.sin(q),math.sin(q)))
''',
}
results=[]
for label,source in sources.items():
    issues=gate.scan_text(source, 'src/eab/'+label+'_audit.py')
    ns={}
    try:
        exec(compile(source,label,'exec'),ns)
        q=Fraction(1,2**1075) if 'float' not in label else math.ulp(0.0)
        answer=ns['bad'](q)
    except Exception as e: answer=repr(e)
    results.append({'case':label,'answer':repr(answer),'issues':issues,'source':source})
print(json.dumps(results,ensure_ascii=False,indent=2))
(ROOT/'review/static_logs/initial_protocol_probes.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
