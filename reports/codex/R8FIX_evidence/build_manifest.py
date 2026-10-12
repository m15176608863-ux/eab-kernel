"""Index delivered changes and reproducible evidence without archiving test scratch."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, check=True, capture_output=True).stdout

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

changed = git('diff', '--name-only', '-z').decode('utf-8').split('\0')
new = ['docs/r8fix_design_sync.md', 'src/eab/kernel3d/entrance_topology.py',
       'tests/e5a_convex_oracle.py', 'reports/codex/R8FIX_report.md']
new.extend(p.relative_to(ROOT).as_posix() for p in sorted((ROOT/'tests').glob('test_r8fix_*.py')))
paths = {ROOT/p for p in changed+new if p}
exclude = {'ARTIFACTS.md', 'artifact_manifest.json'}
paths.update(p for p in OUT.rglob('*') if p.is_file()
             and 'tmp' not in p.relative_to(OUT).parts
             and '__pycache__' not in p.parts and p.name not in exclude)
records = [{'path':p.relative_to(ROOT).as_posix(), 'uri':p.as_uri(),
            'bytes':p.stat().st_size, 'sha256':sha(p)} for p in sorted(paths)]
tmp_files = [p for p in (OUT/'tmp').rglob('*') if p.is_file()]
result = dict(head=git('rev-parse','HEAD').decode().strip(),
              branch=git('branch','--show-current').decode().strip(),
              files=records, excluded_scratch=dict(uri=(OUT/'tmp').as_uri(),
                  file_count=len(tmp_files), bytes=sum(p.stat().st_size for p in tmp_files)),
              self_exclusion='ARTIFACTS.md and artifact_manifest.json avoid recursive hashes',
              reused_dependencies=(ROOT/'reports/codex/R7FIX_evidence/verification_deps').as_uri())
(OUT/'artifact_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
key = [('Main report', ROOT/'reports/codex/R8FIX_report.md'),
       ('Machine verification', OUT/'verification.json'), ('Full-suite log',OUT/'full_suite.log'),
       ('Full-suite metadata',OUT/'full_suite.json'), ('Design synchronization',ROOT/'docs/r8fix_design_sync.md'),
       ('Tracked changes patch',OUT/'working_tree.patch'), ('SHA256 manifest',OUT/'artifact_manifest.json'),
       ('Evidence and scratch directory',OUT)]
lines = ['# R8FIX delivery index', '', 'Uncommitted changes; original HEAD and branch are recorded in the JSON manifest.', '',
         '## Key files', '']
lines += ['- [%s](%s)' % (label,path.as_uri()) for label,path in key]
lines += ['', '## All source, documentation, and persistent evidence files', '',
          'The tracked patch does not contain untracked files; both are listed below.',
          'Scratch is intentionally indexed only as a directory, not as durable evidence.', '']
lines += ['- [%s](%s) (%d bytes)' % (r['path'],r['uri'],r['bytes']) for r in records]
lines += ['', '## Scratch and read-only inputs', '',
          '- [Test scratch](%s)' % (OUT/'tmp').as_uri(),
          '- [G6H source input report](%s)' % (ROOT/'reports/codex/inputs/G6H_report.md').as_uri(),
          '- [G6H findings](%s)' % (ROOT/'reports/codex/inputs/G6H_findings.json').as_uri(),
          '- [Original reproduction scripts](%s)' % (ROOT/'reports/codex/inputs/G6H_repro').as_uri()]
(OUT/'ARTIFACTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(dict(index=(OUT/'ARTIFACTS.md').as_uri(), durable_files=len(records),
                     scratch_files=len(tmp_files)),ensure_ascii=False))
