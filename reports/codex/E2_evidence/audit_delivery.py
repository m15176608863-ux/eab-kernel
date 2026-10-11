"""Read-only git/data audit and deliverable index for WO-E2. Writes only local evidence."""
from pathlib import Path
import ast
import hashlib
import json
import os
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
os.environ['GIT_OPTIONAL_LOCKS'] = '0'

def git(*args):
    return subprocess.check_output(['git', '--no-optional-locks', *args], cwd=ROOT)

def sha(data):
    return hashlib.sha256(data).hexdigest()

names = ('ve_cover', 'ev_cover', 'vv_cover', 'enumerate_covers')
old = git('show', 'HEAD:src/eab/kernel2d/covers.py').decode('utf-8')
new = (ROOT / 'src/eab/kernel2d/covers.py').read_text(encoding='utf-8')
def local_functions(text):
    return {n.name: ast.get_source_segment(text, n) for n in ast.parse(text).body
            if isinstance(n, ast.FunctionDef) and n.name in names}
original, current = local_functions(old), local_functions(new)
unchanged = {name: original[name] == current[name] for name in names}
assert all(unchanged.values()), unchanged

# Compare raw tracked fixture blobs against the index, without filters or writes.
fixture_lines = git('ls-files', '-s', '--', 'fixtures').decode('utf-8').splitlines()
fixture_files, fixture_expected = [], []
for line in fixture_lines:
    meta, name = line.split('\t', 1)
    name = name.strip('"')
    fixture_files.append(name)
    fixture_expected.append(meta.split()[1])
hashes = subprocess.check_output(['git', '--no-optional-locks', 'hash-object', '--no-filters', '--stdin-paths'],
                                cwd=ROOT, input=('\n'.join(fixture_files) + '\n').encode('utf-8')).decode().splitlines()
fixture_changed = [name for name, want, got in zip(fixture_files, fixture_expected, hashes) if want != got]
assert len(hashes) == len(fixture_files) and not fixture_changed, fixture_changed

mutations = json.loads((HERE / 'mutations/results.json').read_text(encoding='utf-8'))
restored = all(m['original_sha256'] == m['restored_sha256'] == sha((ROOT / m['path']).read_bytes()) for m in mutations)
assert restored
files = git('diff', '--name-only').decode('utf-8').splitlines()
tracked = {f: sha((ROOT / f).read_bytes()) for f in files}
for p in sorted((ROOT / 'tests').glob('test_kernel2d_*')):
    if p.name in ('test_kernel2d_convex_ray_exact.py', 'test_kernel2d_report_band.py'):
        tracked[p.relative_to(ROOT).as_posix()] = sha(p.read_bytes())
record = dict(branch=git('branch', '--show-current').decode().strip(), head=git('rev-parse', 'HEAD').decode().strip(),
              local_legacy_functions_text_unchanged=unchanged, tracked_fixture_files=len(fixture_files),
              changed_fixture_files=fixture_changed, mutations_original_restored_and_current_equal=restored,
              modified_deliverable_sha256=tracked)
(HERE / 'scope_audit.json').write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding='utf-8')
(HERE / 'working_tree.diff').write_bytes(git('diff', '--binary'))
(HERE / 'final_status.txt').write_bytes(git('status', '--short', '--untracked-files=all'))

lines = ['# WO-E2 交付索引', '', '所有成果位于本工作树；以下链接为文件/目录，可直接打开。', '',
         '- [中文执行报告](file:///D:/eab-wt/cx-e2/reports/codex/E2_report.md)',
         '- [未提交差异（已跟踪文件）](working_tree.diff)',
         '- [范围与哈希审计](scope_audit.json)',
         '- [全部原始失败与处置](failure_inventory.md)',
         '- [最终全套机读结果](final_full_result.json)',
         '- [突变结果](mutations/results.json)',
         '', '## 改动文件', '']
for name in tracked:
    lines.append(f'- [{name}](file:///D:/eab-wt/cx-e2/{name})')
lines += ['', '## 证据文件', '', '原始 PowerShell 重定向日志使用 UTF-16 BOM；最终全套日志及 JSON 为 UTF-8。',
          'draft / prepare / apply 文件是基线期间的临时草稿，不是最终源码，不应重新应用。', '']
for p in sorted(HERE.iterdir()):
    if p.is_file():
        lines.append(f'- [{p.name}]({p.name})')
lines += ['', '突变子目录包含每项原字节、日志、JUnit和修改片段；tmp仅是本树内pytest临时输出。', '']
(HERE / 'INDEX.md').write_text('\n'.join(lines), encoding='utf-8')
print(json.dumps({k: v for k, v in record.items() if k != 'modified_deliverable_sha256'}, ensure_ascii=False, indent=2))
