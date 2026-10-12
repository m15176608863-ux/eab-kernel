"""G6M 新源默认拒绝漏检：dataclass 生命周期与继承初始化。
只写 review/copies/static_lifecycle，原树不修改。oracle仅用Fraction中点平方。
运行：python -X utf8 review/repro/static_lifecycle_bypass.py
"""
from pathlib import Path
from fractions import Fraction as F
import sys, json, math, hashlib, importlib.util, shutil, time
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
spec=importlib.util.spec_from_file_location('g6m_lifecycle_gate',ROOT/'tools/check_exact_construction.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
PREFIX='from dataclasses import dataclass\nfrom fractions import Fraction\nfrom eab.construction import norm_rational\n'
SOURCES={
'dataclass_post_init': PREFIX+'''@dataclass
class Holder:
    points: tuple[Fraction, Fraction]
    def __post_init__(self):
        self.points = tuple(component*1.0 for component in self.points)
def bad(q: Fraction):
    return norm_rational(Holder((q,q)).points)
''',
'inherited_init': PREFIX+'''class Parent:
    def __init__(self, points: tuple[Fraction,Fraction]):
        self.points = tuple(component*1.0 for component in points)
class Holder(Parent):
    points: tuple[Fraction,Fraction]
def bad(q: Fraction):
    return norm_rational(Holder((q,q)).points)
'''}
SOURCES['instance_method_mutation']=SOURCES['dataclass_post_init'].replace('    def __post_init__(self):','    def update(self):').replace('    return norm_rational(Holder((q,q)).points)','    holder=Holder((q,q))\n    holder.update()\n    return norm_rational(holder.points)')
q=F(1,2**1075);u=math.ulp(0.0);square=2*q*q
# ||(q,q)|| = sqrt(2)*q is strictly in binary64 minimum subnormal's cell.
assert (F(u)/2)**2 < square < (3*F(u)/2)**2
original_checker_hash=hashlib.sha256((ROOT/'tools/exact_construction_flow.py').read_bytes()).hexdigest()
results=[]
for name,source in SOURCES.items():
    path='src/eab/g6m_'+name+'_new.py'
    ns={};exec(compile(source,'<new runtime '+name+'>','exec'),ns)
    actual=ns['bad'](q);issues=gate.scan_text(source,path)
    assert actual==0.0 and actual!=u,(name,actual,u)
    assert gate._subset.approved_sites(source,path)==set(),'No legacy site exclusion can apply to this new path'
    assert issues==[],(name,issues)
    # Equivalent explicit ordinary initialization is refused: bug is the hidden
    # lifecycle/ancestor dispatch, not an assumed safety of float multiplication.
    control=PREFIX+"""@dataclass
class Holder:
    points: tuple[Fraction,Fraction]
def update(holder:Holder):
    holder.points=tuple(component*1.0 for component in holder.points)
def bad(q:Fraction):
    holder=Holder((q,q))
    update(holder)
    return norm_rational(holder.points)
"""
    control_issues=gate.scan_text(control,path)
    assert control_issues,(name,control_issues)
    results.append({'case':name,'path':path,'input_q':'1 / 2**1075','expected_by_independent_squared_midpoint_certificate':repr(u),'actual':repr(actual),'scan_text_issues':issues,'approved_sites':0,'explicit_ordinary_init_control_issues':control_issues,'source':source})
copy=ROOT/'review/copies/static_lifecycle'
copy.mkdir(parents=True,exist_ok=True)
for folder in ('src','tests','tools'):
    shutil.copytree(ROOT/folder,copy/folder,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
policy_hash=hashlib.sha256((copy/'tools/exact_construction_policy.json').read_bytes()).hexdigest()
assert policy_hash==hashlib.sha256((ROOT/'tools/exact_construction_policy.json').read_bytes()).hexdigest()
for result in results:
    (copy/result['path']).write_text(result['source'],encoding='utf-8')
start=time.perf_counter();whole_issues=gate.scan_repository(copy);elapsed=time.perf_counter()-start
assert whole_issues==[],whole_issues
assert original_checker_hash==hashlib.sha256((ROOT/'tools/exact_construction_flow.py').read_bytes()).hexdigest()
output={'confirmed':True,'kind':'static default-reject regression, not unmutated production numerical critical','results':results,'whole_repository_scan_issues':whole_issues,'whole_repository_scan_seconds':elapsed,'copied_policy_sha256':policy_hash,'policy_unchanged':True,'original_flow_sha256_unchanged':original_checker_hash}
(ROOT/'review/static_logs/lifecycle_bypass.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(output,ensure_ascii=False,indent=2))
