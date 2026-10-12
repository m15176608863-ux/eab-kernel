from pathlib import Path
import ast,hashlib,json,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
entries=[]
for stage,key in [('E5a','entries'),('E5a2',None),('E5b','rewrites')]:
    path=ROOT/f'reports/codex/{stage}_evidence/test_rewrites.json'
    payload=json.loads(path.read_text(encoding='utf-8-sig'));items=payload if key is None else payload[key]
    for i,item in enumerate(items):
        names=item.get('test',item.get('function',item.get('name','')))
        file=item.get('file','')
        files=sorted(set(re.findall(r'tests/[^ ;:]+\.py',str(names))+([file] if file else [])))
        refs=[]
        for file in files:
            path=ROOT/file
            if not path.exists():refs.append({'file':file,'exists':False});continue
            source=path.read_text(encoding='utf-8-sig')
            nodes={n.name:n for n in ast.parse(source).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
            wanted=re.findall(r'::([A-Za-z_][A-Za-z_0-9]*)',str(names))
            if not wanted and 'function' in item:wanted=[item['function']]
            selected=[nodes[n] for n in wanted if n in nodes]
            refs.append({'file':file,'exists':True,'functions':wanted,'located':[n.name for n in selected],
                         'test_count':sum(n.startswith('test_') for n in nodes),
                         'function_asserts':{n.name:sum(isinstance(x,ast.Assert) for x in ast.walk(n)) for n in selected},
                         'production_convex_view_lines':[j for j,line in enumerate(source.splitlines(),1) if 'exact_convex_view(' in line]})
        entries.append({'stage':stage,'index':i,'scope':str(names),'references':refs,
                        'historical_reason':item.get('reason',item.get('reason_not_weaker',item.get('not_weaker',''))),
                        'current_review':'raw-coordinate oracle audit plus active-path mutation inventory; see report for tested subset'})
# No original parameter decorators removed/changed by this work order.
changes=[]
for file in ('tests/test_invariance_geom.py','tests/test_covers3_g0_vote2.py','tests/test_frozen_ee_sign.py'):
    old=subprocess.check_output(['git','show','HEAD:'+file],cwd=ROOT).decode('utf-8-sig')
    new=(ROOT/file).read_text(encoding='utf-8-sig')
    def functions(s):return {n.name:n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
    a,b=functions(old),functions(new)
    for name in sorted(set(a)&set(b)):
        original,current=ast.get_source_segment(old,a[name]),ast.get_source_segment(new,b[name])
        if original==current:continue
        assert [ast.dump(x) for x in a[name].decorator_list]==[ast.dump(x) for x in b[name].decorator_list]
        changes.append({'file':file,'function':name,'decorators_identical':True,
                        'old_assert_count':sum(isinstance(x,ast.Assert) for x in ast.walk(a[name])),
                        'new_assert_count':sum(isinstance(x,ast.Assert) for x in ast.walk(b[name])),
                        'old_source':original,'new_source':current})
    assert set(a)<=set(b),'no removed function'
(OUT/'migration_inventory.json').write_text(json.dumps({'historical_entries':len(entries),'unique_files':sorted({r['file'] for e in entries for r in e['references']}),'entries':entries,
 'scope_limit':'Static full inventory is not proof of arbitrary-mutation equivalence. Executed old/new comparisons are explicitly listed in old_gate_comparison.json and other_gate_comparison.json.',
 'E2_inventory':'reports/codex/E2_evidence/legacy_rewrites_plan.json: 3 files, unchanged in gate-teeth subtask'},ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'test_rewrites.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
print('historical_entries',len(entries),'unique_files',len({r['file'] for e in entries for r in e['references']}),'modified_existing_tests',len(changes))
