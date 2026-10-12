"""Verify full-suite evidence, source freeze, fixtures, and original test grids."""
from pathlib import Path
import ast
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

def digest(data):
    return hashlib.sha256(data).hexdigest()

def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, check=True).stdout

def test_nodes(source):
    tree = ast.parse(source)
    return {n.name:ast.dump(ast.List(elts=n.decorator_list, ctx=ast.Load()))
            for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and n.name.startswith('test_')}

archive = OUT/'baseline_HEAD_30ee153.zip'
snapshot = json.loads((OUT/'full_suite_snapshot.json').read_text(encoding='utf-8'))
drift = [p for p,h in snapshot.items() if not (ROOT/p).is_file() or digest((ROOT/p).read_bytes()) != h]
current_files = {p.relative_to(ROOT).as_posix() for folder in ('src','tests','tools','docs','fixtures')
                 for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
current_files.update(('README.md','AGENTS.md','pyproject.toml'))
added_after_freeze = sorted(current_files-set(snapshot))
fixture_changed, removed_tests, changed_test_decorators, changed_test_files = [], [], [], []
fixture_count = 0
with zipfile.ZipFile(archive) as baseline:
    for name in baseline.namelist():
        if name.endswith('/'):
            continue
        if name.startswith('fixtures/'):
            fixture_count += 1
            if not (ROOT/name).is_file() or digest((ROOT/name).read_bytes()) != digest(baseline.read(name)):
                fixture_changed.append(name)
        if name.startswith('tests/') and name.endswith('.py'):
            original = baseline.read(name)
            if not (ROOT/name).exists():
                removed_tests.append(name)
                continue
            current = (ROOT/name).read_bytes()
            if current == original:
                continue
            changed_test_files.append(name)
            before, after = test_nodes(original.decode('utf-8-sig')), test_nodes(current.decode('utf-8-sig'))
            removed_tests.extend(name+'::'+n for n in before if n not in after)
            changed_test_decorators.extend(name+'::'+n for n in before if n in after and before[n] != after[n])

meta = json.loads((OUT/'full_suite.json').read_text(encoding='utf-8'))
junit = ET.parse(OUT/'full_suite.junit.xml')
cases = list(junit.iter('testcase'))
counts = {key:sum(c.find(key) is not None for c in cases) for key in ('failure','error','skipped')}
new_counts = {}
for case in cases:
    cls = case.get('classname','')
    if 'test_r8fix_' in cls:
        new_counts[cls] = new_counts.get(cls,0)+1
head = git('rev-parse', 'HEAD').decode().strip()
diff_check = subprocess.run(['git','-c','core.whitespace=cr-at-eol','diff','--check'],cwd=ROOT,capture_output=True)
(OUT/'diff_check.log').write_bytes(diff_check.stdout+diff_check.stderr)
(OUT/'working_tree.patch').write_bytes(git('diff','--binary'))
result = dict(head=head, expected_head='30ee15336f64540141d9ba89f8656539dcc08e7c',
              baseline_archive_sha256=digest(archive.read_bytes()), full_suite=meta,
              junit_testcases=len(cases), junit_counts=counts, new_test_counts=new_counts,
              original_suite_count=9851, tested_snapshot_files=len(snapshot), tested_file_drift=drift,
              files_added_after_freeze=added_after_freeze,
              fixture_count=fixture_count, fixture_changed=fixture_changed,
              removed_original_tests=removed_tests, changed_original_parametrize_decorators=changed_test_decorators,
              changed_original_test_files=changed_test_files, diff_check_exit=diff_check.returncode)
result['verified'] = (head==result['expected_head'] and meta['exit_code']==0 and not meta['tested_file_drift']
    and not any(counts.values()) and len(cases)==9851+sum(new_counts.values())
    and not drift and not added_after_freeze and not fixture_changed and not removed_tests and not changed_test_decorators
    and diff_check.returncode==0)
(OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(not result['verified'])
