"""Read-only source/claim/migration inventories. Inventories are not proofs."""
from pathlib import Path
import ast, collections, json, re, subprocess
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'review/evidence'
rows=[]
for path in sorted((ROOT/'src/eab').rglob('*.py')):
    source=path.read_text(encoding='utf-8-sig'); tree=ast.parse(source)
    parents={child:parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    for node in ast.walk(tree):
        if not isinstance(node,ast.Compare): continue
        at=node; scope=[]
        while at in parents:
            at=parents[at]
            if isinstance(at,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):scope.append(at.name)
        text=ast.get_source_segment(source,node)
        flags=[word for word in ('tol','noise','eps','gap','scale','bound','float','height','alpha','power') if word in text]
        float_literal=any(isinstance(n,ast.Constant) and isinstance(n.value,float) for n in ast.walk(node))
        rows.append({'file':path.relative_to(ROOT).as_posix(),'line':node.lineno,
                     'scope':'.'.join(reversed(scope)),'comparison':text,
                     'lexical_risk_flags':flags,'float_literal':float_literal})
OUT.joinpath('all_source_comparisons.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')

definitions=collections.defaultdict(list)
for path in sorted((ROOT/'tests').rglob('*.py')):
    source=path.read_text(encoding='utf-8-sig')
    for n in ast.walk(ast.parse(source)):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith('test_'):
            definitions[n.name].append({'file':path.relative_to(ROOT).as_posix(),'line':n.lineno})
claims=[]
for name in ('README.md','docs/canon_map.md','docs/exact_predicates_plan.md','docs/exact_3d_design.md'):
    for i,line in enumerate((ROOT/name).read_text(encoding='utf-8-sig').splitlines(),1):
        if re.search('✔|已实现|已完成|已验证|有门|保证|通过',line):
            names=sorted(set(re.findall(r'\btest_[A-Za-z0-9_]+',line)))
            claims.append({'file':name,'line':i,'claim':line,
                           'same_line_test_names':{n:definitions.get(n,[]) for n in names},
                           'manual_meaning_verification':'See report; existence alone is not a proof'})
OUT.joinpath('document_claim_inventory.json').write_text(json.dumps(claims,ensure_ascii=False,indent=2),encoding='utf-8')

def functions(source):
    tree=ast.parse(source);out={}
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            out[n.name]={'source':ast.get_source_segment(source,n),
                         'assertions':[ast.dump(a,include_attributes=False) for a in ast.walk(n) if isinstance(a,ast.Assert)]}
    return out
changed=subprocess.check_output(['git','diff','--name-only','b6126cf..HEAD','--','tests/'],cwd=ROOT,text=True).splitlines()
migration=[]
for name in changed:
    if not name.endswith('.py') or not (ROOT/name).exists():continue
    old=subprocess.run(['git','show','b6126cf:'+name],cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace')
    if old.returncode:continue
    before=functions(old.stdout);after=functions((ROOT/name).read_text(encoding='utf-8-sig'))
    for key in before.keys() & after.keys():
        if before[key]['source']==after[key]['source']:continue
        migration.append({'file':name,'function':key,'old':before[key],'new':after[key],
                          'removed_assertion_asts':list((collections.Counter(before[key]['assertions'])-collections.Counter(after[key]['assertions'])).elements()),
                          'review_boundary':'AST changes inventoried; see separate independent mutation evidence'})
OUT.joinpath('test_migration_inventory.json').write_text(json.dumps(migration,ensure_ascii=False,indent=2),encoding='utf-8')
summary={'source_modules':len(list((ROOT/'src/eab').rglob('*.py'))),'all_compare_nodes':len(rows),
         'lexical_candidate_nodes':sum(bool(x['lexical_risk_flags']) or x['float_literal'] for x in rows),
         'claim_lines':len(claims),'changed_shared_test_or_helper_functions':len(migration),
         'by_source_file':dict(collections.Counter(x['file'] for x in rows))}
OUT.joinpath('inventory_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
