"""Read-only final documentation/manifest audit; writes H1 evidence only."""
import ast
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
H1 = OUT.parent
FILES = ['README.md', 'AGENTS.md', 'docs/shi_attribution.md', 'docs/canon_map.md',
         'docs/m3_global_entrance_design.md', 'docs/plan_20260921.md',
         'docs/m5d_c1_theory.md', 'reports/EVIDENCE_ARCHIVE.md']
changes = []
for filename in FILES:
    data = (ROOT / filename).read_bytes()
    old = subprocess.check_output(['git', 'show', '476c5d6:'+filename], cwd=ROOT)
    assert not data.startswith(b'\xef\xbb\xbf')
    text = data.decode('utf-8')
    assert b'\r' not in data
    delta = list(difflib.ndiff(old.decode('utf-8').splitlines(), text.splitlines()))
    changes.append(dict(path=filename, baseline='476c5d6',
                        before_sha256=hashlib.sha256(old).hexdigest(),
                        after_sha256=hashlib.sha256(data).hexdigest(),
                        removed_lines=sum(s.startswith('- ') for s in delta),
                        added_lines=sum(s.startswith('+ ') for s in delta)))

readme = (ROOT / 'README.md').read_text('utf-8')
table = (ROOT / 'docs/shi_attribution.md').read_text('utf-8')
rows = {line.split('|')[1].strip(): [cell.strip() for cell in line.strip('|').split('|')]
        for line in table.splitlines() if line.startswith('| A')}
assert len(rows) == 39
def refs(text):
    return set(re.findall(r'(test_\w+\.py::test_\w+)', text))
mapping = {'A01/A04': ['A01', 'A04'], 'A08': ['A08'], 'A10': ['A10'],
           'A12': ['A12'], 'A14': ['A14'], 'A16': ['A16'], 'A18': ['A18'],
           'A20': ['A20'], 'A25': ['A25'], 'A27': ['A27'], 'A29': ['A29'],
           'A30': ['A30'], 'A31–A33': ['A31', 'A32', 'A33']}
aligned = []
for line in readme.splitlines():
    if line.startswith('| ') and any('（'+key+'）' in line for key in mapping):
        key = next(key for key in mapping if '（'+key+'）' in line)
        wanted = set().union(*(refs(rows[item][5]) for item in mapping[key]))
        assert refs(line) == wanted, key
        aligned.append(key)
assert len(aligned) == 13
assert rows['A28'][5] == '无门（仅文档算例）'
assert rows['A36'][2] == '已有标准结果'
assert len(readme.splitlines()) <= 120
for node in refs(table):
    filename, name = node.split('::')
    assert any(isinstance(n, ast.FunctionDef) and n.name == name
               for n in ast.walk(ast.parse((ROOT / 'tests' / filename).read_text('utf-8')))), node

directories = []
for filename in ['archive_result.json', 'archive_additional_result.json']:
    directories.extend(json.loads((H1 / filename).read_text('utf-8'))['directories'])
assert len(directories) == 43
git_rows = subprocess.check_output(['git', 'ls-tree', '-rl', '1ce9a91', '--', 'reports'], cwd=ROOT).decode('utf-8')
git_sizes = {}
for line in git_rows.splitlines():
    metadata, filename = line.split('\t', 1)
    git_sizes[filename] = int(metadata.split()[-1])
tracked = []
manifest_hashes = []
for directory in directories:
    path = Path(directory['manifest'])
    with path.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    assert actual == directory['manifest_sha256'], path
    manifest_hashes.append(dict(path=str(path), sha256=actual))
    with path.open(encoding='utf-8') as stream:
        tracked.extend(json.loads(line) for line in stream if '"tracked":true' in line)
assert len(tracked) == 6047
git_bytes = sum(git_sizes[row['source']] for row in tracked)
archive_bytes = sum(row['bytes'] for row in tracked)
assert (git_bytes, archive_bytes) == (523273912, 523274109)
exception_name = 'reports/codex/M3_evidence/theory_audit.md'
original = subprocess.check_output(['git', 'show', '1ce9a91:'+exception_name], cwd=ROOT)
archived = (Path('D:/eab-evidence') / exception_name).read_bytes()
erratum, body = archived.split(b'\n', 1)
assert body == original and len(archived)-len(original) == 197
archive_doc = (ROOT / 'reports/EVIDENCE_ARCHIVE.md').read_text('utf-8')
assert erratum.decode('utf-8') in archive_doc
inputs = json.loads((H1 / 'frozen_inputs_manifest.json').read_text('utf-8'))['files']
families = Counter('/'.join(row['source'].split('/')[:3]) if row['source'].startswith('reports/codex/') else row['source'] for row in inputs)
assert len(inputs) == 137 and sum(families.values()) == 137
assert families['reports/codex/M5c_evidence'] == 4
for row in inputs:
    data = (ROOT / row['destination']).read_bytes()
    assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256']

result = dict(status='passed', files=changes, readme_lines=len(readme.splitlines()),
              readme_rows_aligned=aligned, attribution_rows=len(rows),
              attribution_categories=dict(Counter(row[2] for row in rows.values())),
              attribution_references=len(refs(table)), readme_named_tests=len(refs(readme)),
              archive=dict(manifests_checked=len(manifest_hashes), manifest_hashes=manifest_hashes,
                           tracked_files=len(tracked), git_original_bytes=git_bytes,
                           archive_tracked_bytes=archive_bytes, unique_exception_bytes=197,
                           theory_body_equal_git=True, erratum_full_text_in_tracked_doc=True,
                           fixture_files=len(inputs), fixture_families=dict(families),
                           external_archive_writes=False),
              note='Manifest hashes and theory exception freshly checked; this is not a repeat hash of all 274740 archived data files.')
(OUT / 'documentation_edits.json').write_text(json.dumps(changes, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
(OUT / 'documentation_audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({key:value for key,value in result.items() if key not in ('files', 'archive')}, ensure_ascii=False))
print('archive 43 manifests; tracked 6047; git bytes 523273912; exception +197; fixtures 137: PASS')
