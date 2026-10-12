"""Read-only AST/document inventory for WO-G6F. Writes only review/notes/."""
from pathlib import Path
import ast, json, re, subprocess, hashlib

ROOT=Path(__file__).resolve().parents[2]
NOTE=ROOT/'review/notes'
def read(p):return p.read_text(encoding='utf-8-sig')
def defs(text):
    tree=ast.parse(text)
    return {n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
def assertions(node):
    return [ast.unparse(n) for n in ast.walk(node) if isinstance(n,ast.Assert)]
changed=subprocess.check_output(['git','diff','--name-only','b6126cf..HEAD','--','tests/'],cwd=ROOT,text=True).splitlines()
rows=[];testdefs={}
for p in (ROOT/'tests').glob('*.py'):
    for name,node in defs(read(p)).items():
        testdefs.setdefault(name,[]).append(str(p.relative_to(ROOT)))
for name in changed:
    path=ROOT/name
    old=subprocess.run(['git','show',f'b6126cf:{name}'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if old.returncode:continue
    oldtext=old.stdout.decode('utf-8-sig');newtext=read(path)
    a,b=defs(oldtext),defs(newtext)
    for fn,node in a.items():
        if fn in b and ast.dump(node,include_attributes=False)==ast.dump(b[fn],include_attributes=False):continue
        item={'file':name,'function':fn,'old_line':node.lineno,'current_line':b[fn].lineno if fn in b else None,
              'deleted_or_renamed':fn not in b,'old_assertions':assertions(node),
              'new_assertions':assertions(b[fn]) if fn in b else [],
              'old_source':ast.get_source_segment(oldtext,node),'new_source':ast.get_source_segment(newtext,b[fn]) if fn in b else None}
        rows.append(item)
docs=[]
for name in ['README.md','docs/canon_map.md','docs/exact_predicates_plan.md','docs/exact_3d_design.md']:
    for line_no,line in enumerate(read(ROOT/name).splitlines(),1):
        if not any(word in line for word in ['✔','已完成','已验证','已实现','有门']):continue
        refs=re.findall(r'\btest_[A-Za-z0-9_]+',line)
        mapped=[]
        for ref in refs:
            matches=testdefs.get(ref,[])
            kind='function'
            if not matches and (ROOT/'tests'/f'{ref}.py').is_file():
                matches=[f'tests/{ref}.py'];kind='file'
            if not matches and ref.endswith('_'):
                matches=[f'{p}::{n}' for n,paths in testdefs.items() if n.startswith(ref) for p in paths];kind='abbreviated_prefix'
            mapped.append({'name':ref,'kind':kind,'defs':matches})
        docs.append({'file':name,'line':line_no,'claim':line,'test_refs':mapped})
out={'baseline':'b6126cf','head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
     'changed_test_files':changed,'changed_original_functions':rows,'claim_lines':docs,
     'missing_named_tests':sorted({r['name'] for d in docs for r in d['test_refs'] if not r['defs']})}
(NOTE/'gates_docs_inventory.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('changed_test_files',len(changed),'changed_original_functions',len(rows))
print('deleted_or_renamed',[f"{x['file']}::{x['function']}" for x in rows if x['deleted_or_renamed']])
print('claim_lines',len(docs),'missing_named_tests',out['missing_named_tests'])
for x in rows:
    if x['function'].startswith('test_'):
        print(x['file'],x['function'],len(x['old_assertions']),'->',len(x['new_assertions']))
