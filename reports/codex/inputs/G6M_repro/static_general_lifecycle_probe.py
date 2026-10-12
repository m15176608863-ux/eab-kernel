from pathlib import Path
import sys,importlib.util,json,math
from fractions import Fraction
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'src'));spec=importlib.util.spec_from_file_location('sg',ROOT/'tools/check_exact_construction.py');gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
prefix='from dataclasses import dataclass\nfrom fractions import Fraction\nfrom eab.construction import norm_rational\n'
cases={
'post_init': prefix+'''@dataclass
class Holder:
    points: tuple[Fraction, Fraction]
    def __post_init__(self):
        self.points = tuple(component*1.0 for component in self.points)
def bad(q: Fraction):
    return norm_rational(Holder((q,q)).points)
''',
'inherited_init':prefix+'''class Parent:
    def __init__(self, points: tuple[Fraction,Fraction]):
        self.points = tuple(component*1.0 for component in points)
class Holder(Parent):
    points: tuple[Fraction,Fraction]
def bad(q: Fraction):
    return norm_rational(Holder((q,q)).points)
''',
'round_launder':prefix+'''def bad(q: float):
    return norm_rational((round(q,323),round(q,323)))
'''}
for k,s in cases.items():
 ns={};exec(compile(s,k,'exec'),ns);q=Fraction(1,2**1075) if k!='round_launder' else math.ulp(0.0);print(k,ns['bad'](q),gate.scan_text(s,'src/eab/'+k+'.py'))
