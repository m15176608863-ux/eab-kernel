"""Read-only Git/fixture audit and machine-readable evidence completeness check."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode('utf-8')


def main():
    initial = json.loads((OUT / 'initial_manifest.json').read_text(encoding='utf-8'))
    fixtures = {p: sha for p, sha in initial['sha256'].items() if p.startswith('fixtures/')}
    fixture_changes = [p for p, sha in fixtures.items()
                       if not (ROOT / p).is_file() or hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != sha]
    changed = git('diff', '--name-only').splitlines()
    staged = git('diff', '--cached', '--name-only').splitlines()
    untracked = git('ls-files', '--others', '--exclude-standard').splitlines()
    expected = {f"{x['file']}:{x['line']}" for x in json.loads((OUT / 'selected_findings.json').read_text(encoding='utf-8'))}
    dispositions_file = OUT / 'g6e_dispositions.json'
    dispositions = json.loads(dispositions_file.read_text(encoding='utf-8')) if dispositions_file.exists() else {}
    report = dict(head=git('rev-parse', 'HEAD').strip(), branch=git('branch', '--show-current').strip(),
                  baseline_head_unchanged=git('rev-parse', 'HEAD').strip() == initial['head'],
                  tracked_fixture_count=len(fixtures), fixture_changes=fixture_changes,
                  changed_tracked=changed, staged=staged, untracked=untracked,
                  g6e_expected=sorted(expected), g6e_missing=sorted(expected - dispositions.keys()),
                  g6e_extra=sorted(dispositions.keys() - expected),
                  diff_check=git('diff', '--check'))
    (OUT / 'scope_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('baseline_head_unchanged', 'tracked_fixture_count',
                                           'fixture_changes', 'staged', 'g6e_missing', 'g6e_extra')}, ensure_ascii=False))
    assert report['baseline_head_unchanged'] and not fixture_changes and not staged
    assert not report['g6e_missing'] and not report['g6e_extra']


if __name__ == '__main__':
    main()
