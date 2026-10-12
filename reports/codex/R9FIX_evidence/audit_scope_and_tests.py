"""Rerun the original-node/assertion/fixture preservation audit without Git writes."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
initial = json.loads((OUT/'initial_state.json').read_text(encoding='utf8'))
audit = dict(head_current=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT).decode().strip(),
             branch_current=subprocess.check_output(['git','branch','--show-current'], cwd=ROOT).decode().strip(),
             tracked_changed=[], deleted=[], fixture_changed=[], test_ast=[])
with zipfile.ZipFile(OUT/'baseline_tracked.zip') as z:
    for name, sha in initial['sha256'].items():
        path = ROOT/name
        if not path.is_file():
            audit['deleted'].append(name)
            continue
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() == sha:
            continue
        audit['tracked_changed'].append(name)
        if name.startswith('fixtures/'):
            audit['fixture_changed'].append(name)
        if name.startswith('tests/') and name.endswith('.py'):
            before = ast.parse(z.read(name).decode('utf-8-sig'))
            after = ast.parse(data.decode('utf-8-sig'))
            def functions(tree):
                return {n.name for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')}
            def assertions(tree):
                return sum(isinstance(n,ast.Assert) for n in ast.walk(tree))
            audit['test_ast'].append(dict(path=name, asserts_before=assertions(before), asserts_after=assertions(after),
                removed_test_functions=sorted(functions(before)-functions(after)),
                added_test_functions=sorted(functions(after)-functions(before))))
base = json.loads((OUT/'baseline_collection.json').read_text(encoding='utf8'))['nodes']
current = [line for line in (OUT/'full_collection.log').read_text(encoding='utf8').splitlines()
           if line.startswith('tests/') and '::' in line]
audit.update(baseline_test_nodes=len(base), final_test_nodes=len(current),
             removed_nodes=sorted(set(base)-set(current)), added_nodes=sorted(set(current)-set(base)))
audit['all_original_nodes_retained'] = not audit['removed_nodes']
audit['no_deleted_or_fixture_changed'] = not(audit['deleted'] or audit['fixture_changed'])
(OUT/'change_and_test_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({key:value for key,value in audit.items()
                  if key not in ('tracked_changed','test_ast','added_nodes')},ensure_ascii=False,indent=2))
print('tracked changes:',len(audit['tracked_changed']),'old test files changed:',len(audit['test_ast']))
print('assertion decreases:',[x for x in audit['test_ast'] if x['asserts_after']<x['asserts_before']])
assert audit['head_current'] == initial['head'] and audit['branch_current'] == initial['branch']
assert audit['all_original_nodes_retained'] and audit['no_deleted_or_fixture_changed']
assert not any(x['removed_test_functions'] for x in audit['test_ast'])
