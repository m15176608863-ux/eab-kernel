"""Delivery audit: explicit main, scope-set checks and evidence consistency."""
from pathlib import Path
import ast
from collections import Counter
import hashlib
import json
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
E = ROOT / 'reports/codex/R6FIX_evidence'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_snapshot(root):
    paths = {p for folder in ('src', 'tests', 'docs', 'tools')
             for p in (root/folder).rglob('*') if p.is_file()
             and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    paths.update(root/name for name in ('README.md', 'pyproject.toml', 'AGENTS.md') if (root/name).is_file())
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(paths)}


def snapshot_changes(initial, final):
    return dict(added=sorted(final.keys()-initial.keys()), removed=sorted(initial.keys()-final.keys()),
                modified=sorted(p for p in initial.keys() & final.keys() if initial[p] != final[p]))


def tests_and_marks(source):
    tests = {}
    def visit(node, prefix=()):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                name = (*prefix, child.name)
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name.startswith('test_'):
                    tests['.'.join(name)] = [ast.dump(d, include_attributes=False) for d in child.decorator_list]
                visit(child, name)
            else:
                visit(child, prefix)
    visit(ast.parse(source))
    return tests


def skip_syntax(source):
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and ast.unparse(node.func) in ('pytest.skip', 'pytest.xfail', 'pytest.importorskip'):
            found.append(ast.dump(node, include_attributes=False))
        elif isinstance(node, ast.Attribute) and ast.unparse(node) in ('pytest.mark.skip', 'pytest.mark.skipif', 'pytest.mark.xfail'):
            found.append(ast.dump(node, include_attributes=False))
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'pytestmark' for t in node.targets):
            found.append(ast.dump(node, include_attributes=False))
    return Counter(found)


def full_run_errors(record, log):
    errors = []
    lines = [line for line in log.splitlines() if line.strip()]
    terminal = lines[-1] if lines else ''
    if record.get('exit_code') != 0:
        errors.append('full suite exit code is not zero')
    if record.get('last_line') != terminal:
        errors.append('JSON terminal summary differs from actual log')
    match = re.fullmatch(r'(\d+) passed in .+', terminal)
    if not match or int(match[1]) < 8582:
        errors.append('expected an all-passed full-suite summary with at least the original 8582 cases')
    command = record.get('command', [])
    try:
        args = command[command.index('pytest')+1:]
    except ValueError:
        errors.append('command is not a pytest invocation')
        args = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ('-q', 'tests') or arg.startswith(('--basetemp=', '--durations=')):
            i += 1
        elif arg in ('-p', '--basetemp', '--durations') and i+1 < len(args):
            if arg == '-p' and args[i+1] != 'no:cacheprovider':
                errors.append('unexpected pytest plugin selection')
            i += 2
        else:
            errors.append('unexpected/selective pytest argument: '+arg)
            i += 1
    return errors


def main():
    initial = json.loads((E/'verified_tree_start.json').read_text(encoding='utf-8'))
    changes = snapshot_changes(initial, source_snapshot(ROOT))
    baseline = json.loads((E/'baseline.json').read_text(encoding='utf-8'))['sha256']
    fixture_paths = {p for p in baseline if p.startswith('fixtures/')}
    current_fixtures = {p.relative_to(ROOT).as_posix() for p in (ROOT/'fixtures').rglob('*') if p.is_file()}
    fixture_changes = dict(added=sorted(current_fixtures-fixture_paths), removed=sorted(fixture_paths-current_fixtures),
                           modified=sorted(p for p in fixture_paths & current_fixtures if digest(ROOT/p) != baseline[p]))
    input_paths = {p.relative_to(ROOT).as_posix() for p in (ROOT/'reports/codex/inputs').rglob('*') if p.is_file()}
    baseline_inputs = {p for p in baseline if p.startswith('reports/codex/inputs/')}
    observed_inputs = {p: digest(ROOT/p) for p in sorted(input_paths)}
    input_changes = sorted(p for p in baseline_inputs if p not in observed_inputs or observed_inputs[p] != baseline[p])
    unbaselined_inputs = sorted(input_paths-baseline_inputs)
    missing_tests, changed_old_decorators, new_skip_calls = [], [], []
    with zipfile.ZipFile(E/'baseline_tracked.zip') as backup:
        before_names = {p for p in backup.namelist() if p.startswith('tests/') and p.endswith('.py')}
        after_names = {p.relative_to(ROOT).as_posix() for p in (ROOT/'tests').rglob('*.py') if '__pycache__' not in p.parts}
        for name in sorted(before_names | after_names):
            bs = backup.read(name).decode('utf-8-sig') if name in before_names else ''
            fs = (ROOT/name).read_text(encoding='utf-8-sig') if (ROOT/name).is_file() else ''
            before, after = tests_and_marks(bs), tests_and_marks(fs)
            missing_tests.extend(f'{name}::{test}' for test in before if test not in after)
            changed_old_decorators.extend(f'{name}::{test}' for test in before.keys() & after.keys() if before[test] != after[test])
            new_skip_calls.extend(f'{name}: {syntax}' for syntax in (skip_syntax(fs)-skip_syntax(bs)).elements())
    diff_check = subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True, text=True)
    full = json.loads((E/'full_suite.json').read_text(encoding='utf-8'))
    full_errors = full_run_errors(full, (E/'full_suite.log').read_text(encoding='utf-8'))
    result = {
        'branch': subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT).decode().strip(),
        'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(),
        'source_test_doc_tool_file_count': len(initial), 'scope_changes_since_full_suite_start': changes,
        'changed_during_full_suite': changes['modified'], 'fixture_changes_vs_initial': fixture_changes,
        'input_files_with_initial_hash_changed_or_missing': input_changes,
        'input_files_without_initial_hash': unbaselined_inputs,
        'input_hashes_current_observation_only': observed_inputs,
        'input_integrity_limitation': ('New G6F inputs had no initial hash; current hashes are observations, not proof of unchanged bytes since task start.' if unbaselined_inputs else None),
        'removed_preexisting_test_functions': missing_tests, 'changed_preexisting_test_decorators': changed_old_decorators,
        'new_test_skip_or_xfail_syntax': new_skip_calls,
        'test_audit_limitation': 'AST inventory is not proof that every assertion or indirect parameter grid was unweakened; see the manual rewrite ledger.',
        'git_diff_check_exit_code': diff_check.returncode, 'git_diff_check_output': diff_check.stdout+diff_check.stderr,
        'full_suite': full, 'full_suite_evidence_errors': full_errors,
        'full_suite_log_sha256': digest(E/'full_suite.log'), 'full_suite_json_sha256': digest(E/'full_suite.json'),
        'freeze_manifest_sha256': digest(E/'verified_tree_start.json'),
    }
    result['passed'] = (not any(changes.values()) and not any(fixture_changes.values()) and not input_changes
                        and not missing_tests and not changed_old_decorators and not new_skip_calls
                        and diff_check.returncode == 0 and not full_errors and result['branch'] == 'codex-work'
                        and result['head'] == '2f6c51811edba364e846923da04c45c901a9af8c')
    (E/'delivery_audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1


def self_test():
    assert snapshot_changes({'a': '1'}, {'a': '1', 'b': '2'})['added'] == ['b']
    assert snapshot_changes({'a': '1'}, {})['removed'] == ['a']
    good = dict(exit_code=0, last_line='8855 passed in 1200.00s', command=['python', '-X', 'utf8', '-m', 'pytest', '-q'])
    assert not full_run_errors(good, good['last_line'])
    assert full_run_errors(dict(good, command=good['command']+['-k', 'r6fix']), good['last_line'])
    assert full_run_errors(good, '6 failed, 8849 passed in 1312.89s')
    assert full_run_errors(dict(good, exit_code=1), good['last_line'])
    assert len(tests_and_marks('class A:\n def test_same(self): pass\nclass B:\n def test_same(self): pass\n')) == 2
    assert skip_syntax('import pytest\npytest.skip("no")\n')
    print('audit_delivery self-test: 8 checks passed; no full audit executed')


if __name__ == '__main__':
    if sys.argv[1:] == ['--self-test']:
        self_test()
    else:
        raise SystemExit(main())
