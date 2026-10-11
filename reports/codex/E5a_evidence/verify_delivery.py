"""Read-only source/fixture audit; writes only its workspace evidence JSON."""
import hashlib
import json
from pathlib import Path
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]


def read(name):
    return json.loads((OUT / name).read_text(encoding='utf-8-sig'))


run = read('full_leave_tree_final.json')
assert run['returncode'] == 0 and run['changed_during_run'] == []
source_drift = [name for name, expected in run['source_test_sha256'].items()
                if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected]
assert not source_drift, source_drift
inventory = read('test_inventory_audit.json')
assert inventory['all_old_test_functions_preserved']
assert inventory['no_new_skip_xfail_references']
mutants = read('mutations.json')
assert len(mutants['mutations']) == 11 and mutants['all_listed_internal_mutants_killed']
dispositions = read('g6e_dispositions.json')
assert len(dispositions['findings']) == 10
assert read('final_status.json')['acceptance'] == 'VOID_SCOPE_VIOLATION'
report = (ROOT / 'reports/codex/E5a_report.md').read_text(encoding='utf-8')
assert run['last_line'] in report
assert '正在集成验证' not in report
assert report.rstrip().splitlines()[-1].startswith('E5a_BLOCKED：')

fixtures = subprocess.check_output(['git', 'ls-files', '-z', '--', 'fixtures'], cwd=ROOT)
fixture_records = []
for raw in fixtures.split(b'\0'):
    if not raw:
        continue
    name = raw.decode('utf-8')
    original = subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT)
    current = (ROOT / name).read_bytes()
    fixture_records.append(dict(path=name,bytes=len(current),
                                sha256=hashlib.sha256(current).hexdigest(),unchanged=current == original))
assert all(item['unchanged'] for item in fixture_records)
branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT).decode().strip()
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
assert branch == 'codex-work'
assert head == 'a47933682d9764b15e20d7200a6a37a1e8f14aee'
result = dict(status='LEAVE_TREE_EVIDENCE_CHECKED_NOT_VALID_ACCEPTANCE',
              acceptance='VOID_SCOPE_VIOLATION',branch=branch,head=head,
              full_suite_last_line=run['last_line'],source_drift=source_drift,
              old_test_functions_preserved=True,no_new_skip_xfail_references=True,
              required_internal_mutants_killed=11,assigned_fifth_round_findings=10,
              test_rewrite_entries=len(read('test_rewrites.json')['entries']),
              tracked_fixtures=fixture_records,
              scope_audit_limit='This checks the retained worktree artifacts, not an exhaustive OS write audit. scope_violation.json remains authoritative about confirmed external writes and uncertainty.')
(OUT / 'final_delivery_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({key:value for key,value in result.items() if key != 'tracked_fixtures'},ensure_ascii=False))
print(f'Tracked fixture files byte-identical to unchanged HEAD: {len(fixture_records)}')
