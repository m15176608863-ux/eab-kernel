"""Produce clickable evidence index and verify the delivered source-bound state."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
from urllib.parse import unquote, urlparse

E = Path(__file__).resolve().parent
ROOT = E.parents[2]
def read(relative):
    return json.loads((E/relative).read_text(encoding='utf8'))
def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, encoding='utf8')
def link(p):
    return f'[{p.relative_to(ROOT).as_posix()}]({p.as_uri()})'

run = read('final_full.json')
audit = read('audit/retention_audit.json')
helper = read('audit/oracle_helper_audit.json')
source_now = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in run['source_after']}
changed = git('diff', '--name-only').stdout.splitlines()
new = [p.relative_to(ROOT).as_posix() for directory in ('tests', 'tools')
       for p in sorted((ROOT/directory).glob('*perf*.py'))
       if p.relative_to(ROOT).as_posix() not in read('baseline_manifest.json')]
manifest = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(changed+new)) if (ROOT/p).is_file()}
(E/'changed_files_sha256.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf8')

lines = ['# WO-PERF 交付与证据索引', '',
         '- 本树未提交改动。旧证据和失败轮保留，不冒充最终绿灯。',
         '- 微基准是同输入局部比值；正式时间只取最终独占全套进程墙钟。',
         '- baseline/ 是回滚字节锚点；tmp/ 为测试产物，不是源文件。', '',
         '## 关键交付', '']
for relative in ['reports/codex/PERF_report.md', 'reports/codex/PERF_evidence/final_full.log',
                 'reports/codex/PERF_evidence/final_full.json', 'reports/codex/PERF_evidence/final_full.xml',
                 'reports/codex/PERF_evidence/audit/retention_audit.json',
                 'reports/codex/PERF_evidence/audit/oracle_helper_audit.json',
                 'reports/codex/PERF_evidence/mutation_table.json',
                 'reports/codex/PERF_evidence/final_artifact_audit.json']:
    lines.append('- '+link(ROOT/relative))
lines += ['', '## 源码、原文档及新增门', '']
for relative in sorted(set(changed+new)):
    lines.append('- '+link(ROOT/relative))
lines += ['', '## 逐项证据及可复跑脚本', '']
for p in sorted(E.rglob('*')):
    relative = p.relative_to(E)
    if not p.is_file() or relative.parts[0] in ('baseline', 'tmp') or p.suffix == '.pyc' or p.name == 'INDEX.md':
        continue
    lines.append('- '+link(p))
lines += ['', '## 目录', '', '- '+link(E/'baseline'), '- '+link(E/'tmp'), '']
(E/'INDEX.md').write_text('\n'.join(lines), encoding='utf8')

report = (ROOT/'reports/codex/PERF_report.md').read_text(encoding='utf8')
expected = 'PERF_DONE' if run['wall_seconds'] <= 900 else 'PERF_PARTIAL：全套独占进程墙钟仍超过 900 s'
bad_links = []
for p in [ROOT/'reports/codex/PERF_report.md', E/'INDEX.md']:
    for uri in re.findall(r'\]\((file:///[^\n]+?)\)', p.read_text(encoding='utf8')):
        path = Path(unquote(urlparse(uri).path).lstrip('/'))
        if path == E/'final_artifact_audit.json':
            continue
        if not path.exists():
            bad_links.append(dict(file=p.relative_to(ROOT).as_posix(), uri=uri))
checks = dict(
    final_exit_zero=run['exit_code'] == 0,
    source_frozen_during_and_after_full_run=run['sources_unchanged_during_run'] and source_now == run['source_after'],
    retention_audit_pass=audit['status'] == 'PASS',
    oracle_helper_audit_pass=helper['status'] == 'PASS',
    original_8267_nodes_retained=audit['baseline_collected_nodes'] == 8267 and not audit['missing_baseline_nodes'],
    original_test_gate_files_byte_identical=all(p.read_bytes() == (ROOT/'tests'/p.relative_to(E/'baseline/tests')).read_bytes() for p in (E/'baseline/tests').rglob('test_*.py')),
    no_skip_failure_error=not audit['final_junit_bad_nodes'],
    fixtures_unchanged=audit['fixture_count'] == 62 and not audit['changed_or_missing_fixtures'],
    full_nodes_match_collection=audit['final_junit_nodes'] == audit['current_collected_nodes'] and not audit['final_junit_missing_collected_nodes'],
    head_unchanged=git('rev-parse', '--short', 'HEAD').stdout.strip() == 'c194dbb',
    branch_unchanged=git('branch', '--show-current').stdout.strip() == 'codex-work',
    diff_check_clean=git('diff', '--check').returncode == 0,
    report_status_honest=report.strip().splitlines()[-1] == expected,
    report_local_links_valid=not bad_links,
)
result = dict(status='PASS' if all(checks.values()) else 'FAIL', checks=checks,
              performance_target_met=run['wall_seconds'] <= 900,
              final_last_line=run['last_nonempty_line'], wall_seconds=run['wall_seconds'],
              bad_links=bad_links, changed_files_manifest='changed_files_sha256.json',
              boundary='Read-only git checks and hashes; no commit/worktree. This audit does not claim six-lane G6 or audit writes by unrelated processes outside this workspace.')
(E/'final_artifact_audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(result['status'] != 'PASS')
