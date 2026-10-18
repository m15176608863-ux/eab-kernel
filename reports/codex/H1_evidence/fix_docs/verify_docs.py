"""Run cited gates and acceptance mutants on a workspace-local byte copy."""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
SCRATCH = ROOT / 'reports/codex/H1_evidence/tmp/fix_docs'
COPY = SCRATCH / 'source'
assert not COPY.exists(), 'use a fresh evidence run; do not splice runs'
COPY.mkdir(parents=True)
for folder in ('src', 'tests', 'tools', 'fixtures', 'docs'):
    shutil.copytree(ROOT / folder, COPY / folder,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
for name in ('README.md', 'AGENTS.md', 'pyproject.toml'):
    shutil.copy2(ROOT / name, COPY / name)
TEMP = SCRATCH / 'temp'
TEMP.mkdir()
env = dict(os.environ, TEMP=str(TEMP), TMP=str(TEMP), PYTHONIOENCODING='utf-8',
           PYTHONDONTWRITEBYTECODE='1')
env.pop('PYTHONPATH', None)

readme = (COPY / 'README.md').read_text('utf-8')
nodes = sorted(set(re.findall(r'`(test_\w+\.py::test_\w+)`', readme)))
assert nodes
refs = sorted(set(re.findall(r'`(tests/test_\w+\.py::test_\w+)`',
                               (COPY / 'docs/shi_attribution.md').read_text('utf-8'))))
for node in refs:
    filename, name = node.split('::')
    assert any(isinstance(n, ast.FunctionDef) and n.name == name
               for n in ast.walk(ast.parse((COPY / filename).read_text('utf-8')))), node
assert len(readme.splitlines()) <= 120
assert '无门' not in readme.split('## 已证明清单', 1)[1].split('## 未证明', 1)[0]
results = []


def run(name, selected, expected_code, expected_counts, required_message=None):
    command = [sys.executable, '-X', 'utf8', '-m', 'pytest', '-q', '--runslow',
               '-p', 'no:cacheprovider', '--basetemp', str(SCRATCH / (name+'_pytest')),
               '--color=no'] + selected
    started = time.monotonic()
    log = OUT / (name+'.log')
    with log.open('wb') as stream:
        process = subprocess.run(command, cwd=COPY, env=env,
                                 stdout=stream, stderr=subprocess.STDOUT, timeout=900)
    output = log.read_text('utf-8', errors='replace')
    line = output.rstrip().splitlines()[-1]
    item = dict(name=name, command=command, exit_code=process.returncode,
                last_line=line, seconds=time.monotonic()-started,
                log=log.relative_to(ROOT).as_posix())
    results.append(item)
    (OUT / 'verification_progress.json').write_text(json.dumps(results, indent=2)+'\n', encoding='utf-8')
    assert process.returncode == expected_code, item
    for count in expected_counts:
        assert count in line, item
    assert ' skipped' not in line and ' error' not in line, item
    if required_message:
        assert required_message in output, item
    print(name+': '+line, flush=True)


run('readme_cited_pristine', ['tests/'+node for node in nodes], 0, ['passed'])
M3 = ['tests/test_m3_theory.py::test_m3_tight_fit_distinguishes_body_relation_from_entrance_topology',
      'tests/test_m3_global3d.py::test_zero_clearance_contact_is_not_silently_regularized_to_open_union',
      'tests/test_m3_theory.py::test_m3_open_pair_sum_union_is_not_the_interior_of_closed_union',
      'tests/test_m3_theory.py::test_m3_closed_separation_depth_and_nonpenetration_depth_are_different']
M4 = ['tests/test_m3_global2d.py::test_clipped_covers_are_exactly_boundary_and_cover_oracle_ray_exits',
      'tests/test_m3_global2d.py::test_local_clipping_covers_the_independently_built_cell_boundary',
      'tests/test_m3b_2d.py::test_nonstrict_flat_collinear_local_covers_weakly_cover_boundary']
run('m3_pristine', M3, 0, ['24 passed'])
run('m4_pristine', M4, 0, ['15 passed'])


def poison(text, names):
    lines = text.splitlines(keepends=True)
    tree = ast.parse(text)
    starts = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in names:
            body = node.body
            first = body[1] if isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str) else body[0]
            starts.append((first.lineno-1, first.col_offset))
    assert starts
    for index, indent in sorted(starts, reverse=True):
        lines.insert(index, ' '*indent+'raise RuntimeError("H1-fix M3 production path poisoned")\n')
    return ''.join(lines)


saved = {}
try:
    for filename, names in [('src/eab/kernel2d/exact.py', {'polygons_overlap_exact', 'entrance_membership_exact'}),
                            ('src/eab/kernel3d/global_entrance.py', {'classify'})]:
        path = COPY / filename
        saved[path] = path.read_bytes()
        path.write_text(poison(saved[path].decode('utf-8'), names), encoding='utf-8', newline='')
    run('m3_production_poison', M3, 1, ['22 failed', '2 passed'], 'H1-fix M3 production path poisoned')
finally:
    for path, data in saved.items():
        path.write_bytes(data)

path = COPY / 'src/eab/kernel2d/global_entrance.py'
saved = path.read_bytes()
try:
    text = saved.decode('utf-8')
    before = 'exposed = (states[0] >= 0) != (states[1] >= 0)'
    assert text.count(before) == 1
    path.write_text(text.replace(before, 'exposed = True'), encoding='utf-8', newline='')
    run('m4_no_clipping', M4, 1, ['6 failed', '9 passed'], 'cover clipping exposure mismatch')
finally:
    path.write_bytes(saved)

result = dict(status='passed', source='workspace byte copy, not Git worktree',
              readme_lines=len(readme.splitlines()),
              readme_distinct_named_tests=len(nodes), attribution_distinct_references=len(refs),
              mutations='only scratch production paths; all source bytes restored',
              results=results)
(OUT / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print('documentation verification complete', flush=True)
