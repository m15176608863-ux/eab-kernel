"""WO-G6G read-only old documentation replay and R6F10 equivalent checks."""
from pathlib import Path
import ast, json, sys, subprocess, os, hashlib
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT/'tools')]

def text(name): return (ROOT/name).read_text(encoding='utf-8-sig')
def line(name,fragment):
    return next((i+1,s) for i,s in enumerate(text(name).splitlines()) if fragment in s)
results=[]
def emit(ids,status,output):
    row={'g6e_ids':ids,'status':status,'command':'python -X utf8 review/repro/docs_replay_extra.py','verified_output':output}
    results.append(row);print(json.dumps(row,ensure_ascii=False,default=str),flush=True)

from eab.contact_record import ContactRecord, CoverType
from dataclasses import fields
emit([4,17,18],'已修描述并明确缺口',{
    'canon_contactrecord':line('docs/canon_map.md','溯源段没落地'),
    'contract_fields':[x.name for x in fields(ContactRecord)],
    'six_readers_gap':line('docs/canon_map.md','三种：`readers/bdda_df.py`'),
    'g0_limits':line('docs/canon_map.md','这不等于已普遍实现 07'),
    'g1_limits':line('docs/canon_map.md','不比锁态与滑动符号'),
    'phase0_limits':line('docs/canon_map.md','不是对原件逐字节'),
    'g4_limits':line('docs/canon_map.md','没有事先登记阈值')})
emit([1],'已修错误外部前提，读取器仍未实现',{
    'sibling':line('docs/sibling_observations.md','contact_diagnostics_v3.tsv'),
    'canon':line('docs/canon_map.md','DDA4.x 读取器没写是')})
emit([5],'已修凸 G0 跳样描述；全局双侧探针缺口显式保留',{
    'g0_description':line('docs/canon_map.md','band_skipped=0'),
    'g0_3d_description':line('docs/canon_map.md','E5a 三维票一也零跳样')})
emit([6,16],'主要矛盾已订正，独立复审状态残留小矛盾另列',{
    '03_status':line('docs/canon_map.md','03 砖一的 09-18 回写段仍是'),
    'first_entrance':line('docs/canon_map.md','二维、三维自 2026-10-10 起均有')})
emit([10],'已补实质平拱门并纠正引用',{
    'readme':line('README.md','test_limit_flat_arch.py'),
    'tests':[n.name for n in ast.parse(text('tests/test_limit_flat_arch.py')).body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]})
emit([12,13],'范围/版本已限定为历史，不当作当前全套',{
    'historical_count':line('README.md','全套 **6717**'),
    'r6fix_current':line('reports/codex/R6FIX_report.md','8866 passed'),
    'historical_failure_exception':line('README.md','例外如实记在报告末节')})
emit([14,32],'用按定义行执行门替代过期指针',{
    'canon':line('docs/canon_map.md','代码指针一律写成'),
    'pointer_test':'tests/test_doc_pointers.py::test_every_code_pointer_in_canon_map_names_a_function_at_its_current_line'})
emit([15],'报告处置列已补订正',{
    'report_lines':[(i+1,s) for i,s in enumerate(text('reports/g6d_20261010.md').splitlines()) if '| 18 ' in s or '| 36 ' in s]})
d=json.loads(text('fixtures/PROVENANCE.json'))
generated=[e for e in d['entries'] if e['dest'].startswith('bdda_df/') and 'kernel_sha256' in e]
assert len(generated)==48
assert all('input_sha256' in e and 'nonreproducible' in e for e in generated)
emit([19,33],'已修现有48条条目；没有再次重跑姊妹exe',{
    'generated_entries':len(generated),'all_input_hashes':True,'all_nonreproducible_fields':True,
    'four_differences':line('docs/sibling_observations.md','4 份')})

from eab.kernel3d.geom3 import box
from eab.margin import entrance_block_convex
A=box(center=(1.,0.,0.),half=(.5,.5,.5));B=box(center=(1e16,0.,0.),half=(4.,.5,.5))
E=entrance_block_convex(A,B)
exact_min=min(F(b[0])-F(a[0]) for a in A.verts for b in B.verts)
rounded_min=min(b[0]-a[0] for a in A.verts for b in B.verts)
actual=min(F(v[0]) for v in E.verts)
assert actual==exact_min and actual!=F(rounded_min)
assert '仍先浮点构造 b−a' not in text('docs/canon_map.md')
print(json.dumps({'G6F10_status':'已修','exact_min':str(exact_min),'rounded_min':str(F(rounded_min)),
    'actual_min':str(actual),'new_claim':line('docs/canon_map.md','先有理化输入再作 b−a')},ensure_ascii=False))

env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8'}
nodes=['tests/test_doc_pointers.py','tests/test_provenance_inputs.py','tests/test_limit_flat_arch.py']
cmd=[sys.executable,'-X','utf8','-m','pytest','-q','-p','no:cacheprovider',
     '--basetemp='+str(ROOT/'review/tmp/docs_extra'),*nodes]
p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
out=p.stdout+p.stderr
(ROOT/'review/logs/docs_extra_tests.log').write_text(out,encoding='utf-8')
assert p.returncode==0,out
results.append({'command':cmd,'exit_code':p.returncode,'verified_output':out})
(ROOT/'review/notes/docs_static_replay.json').write_text(json.dumps(results,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
print(out)
