"""Read-only workspace/status checks and a clickable WO-M3b artifact index."""
from pathlib import Path
import json
import subprocess
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'reports/codex/M3b_evidence'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode('utf-8')


def main():
    assert str(ROOT).lower() == r'd:\eab-wt\cx-m4'
    names = sorted(set(filter(None, git('ls-files', '-m', '-o', '--exclude-standard', '-z').split('\0'))))
    bad_encoding, oversized_logs, rows = [], [], []
    for name in names:
        path = ROOT / name
        if not path.is_file():
            continue
        raw = path.read_bytes()
        if raw.startswith((b'\xef\xbb\xbf', b'\xff\xfe', b'\xfe\xff')):
            bad_encoding.append(name)
        try:
            raw.decode('utf-8')
        except UnicodeDecodeError:
            bad_encoding.append(name)
        if len(raw) > 1_000_000 and name.startswith('reports/codex/M3b'):
            oversized_logs.append(name)
        rows.append(dict(path=name, bytes=len(raw), uri=path.as_uri()))
    current_provenance = (ROOT/'fixtures/PROVENANCE.json').read_bytes()
    head_provenance = subprocess.check_output(['git', 'show', 'HEAD:fixtures/PROVENANCE.json'], cwd=ROOT)
    head = git('rev-parse', 'HEAD').strip()
    branch = git('symbolic-ref', '--short', 'HEAD').strip()
    raw_whitespace = subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True)
    # The tracked M4c summary already uses CRLF; retain that byte convention.
    # cr-at-eol recognizes CRLF, while real trailing blanks/EOF errors still fail.
    whitespace = subprocess.run(['git', '-c', 'core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol', 'diff', '--check'], cwd=ROOT, capture_output=True)
    index = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=ROOT)
    links = sorted(set(re.findall(r'file:///[^)\s]+', (ROOT/'reports/codex/M3b_report.md').read_text(encoding='utf-8'))))
    link_checks = [dict(uri=uri, exists=Path(unquote(urlsplit(uri).path).lstrip('/')).exists()) for uri in links]
    good = (all(row['exists'] for row in link_checks) and head == '3bf5e955d8ea669846a088f50223e17e76475947' and branch == 'm4-seam'
            and not bad_encoding and not oversized_logs and current_provenance == head_provenance
            and whitespace.returncode == index.returncode == 0)
    report = dict(status='PASS' if good else 'FAIL', head=head, branch=branch,
                  index_unchanged=index.returncode == 0, diff_check_exit=whitespace.returncode,
                  default_diff_check_exit=raw_whitespace.returncode,
                  diff_check_policy='blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol (command-only; no Git config write)',
                  provenance_unchanged=current_provenance == head_provenance,
                  report_file_links=link_checks,
                  utf8_or_bom_failures=sorted(set(bad_encoding)),
                  over_one_mb_new_deliverable_logs=oversized_logs,
                  changed_or_new_files=rows,
                  boundaries=['Read-only Git queries, no Git state changes.',
                              'Ignored tmp holds large raw records and downloaded originals.',
                              'Existing large construction-policy configuration is not a run log.',
                              'This checks the workspace snapshot, not a forensic audit of the entire machine.'])
    (OUT/'scope_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    lines = ['# WO-M3b 文件交付索引', '',
             '本清单列当前 Git 可见的本单改动及新成果；大记录/下载原件/副本位于 ignored tmp，不列入提交成果。', '',
             '- [主报告]('+ (ROOT/'reports/codex/M3b_report.md').as_uri()+')',
             '- [最终机器审计]('+ (OUT/'final_audit.json').as_uri()+')',
             '- [范围与编码检查]('+ (OUT/'scope_audit.json').as_uri()+')', '',
             '## 全部可见改动与成果', '']
    for row in rows:
        lines.append('- ['+row['path']+']('+row['uri']+') — '+str(row['bytes'])+' bytes')
    (OUT/'artifact_index.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(report['status'], 'UTF8/BOM failures', len(bad_encoding),
          'oversized new logs', len(oversized_logs), 'visible files', len(rows))
    return 0 if good else 1


if __name__ == '__main__':
    raise SystemExit(main())
