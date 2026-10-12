"""Replay final K02 gates against the frozen baseline/current source and mutant."""
from pathlib import Path
import argparse
import hashlib
import inspect
import json
import os
import runpy
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TEST = ROOT / 'tests/test_r11fix_numeric_types.py'


def main():
    mode = argparse.ArgumentParser()
    mode.add_argument('mode', choices=('baseline', 'green', 'mutation'))
    name = mode.parse_args().mode
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if name == 'mutation':
        sys.path.insert(0, str(ROOT / 'src'))
        from eab.kernel2d import geom
        tests = runpy.run_path(str(TEST))
        source = inspect.getsource(geom.orient2d)
        old = 'any(type(v) is not float for p in (a, b, c) for v in p)'
        new = 'any(isinstance(v, Fraction) for p in (a, b, c) for v in p)'
        assert source.count(old) == 1
        namespace = dict(geom.__dict__)
        exec(compile(source.replace(old, new), '<R11 K02 internal type-gate rollback>', 'exec'), namespace)
        geom.orient2d = namespace['orient2d']
        rows = []
        for test in ('test_mixed_integer_orientation_keeps_exact_negative_sign',
                     'test_mixed_integer_orientation_keeps_exact_zero',
                     'test_all_3072_review_integer_float_orientations_have_exact_signs',
                     'test_mixed_nondegenerate_triangle_is_not_silently_triangulated_to_empty'):
            try:
                tests[test]()
            except AssertionError as exc:
                rows.append({'test': test, 'caught': True, 'assertion': str(exc),
                             'traceback': traceback.format_exc()})
            else:
                rows.append({'test': test, 'caught': False})
        assert all(row['caught'] for row in rows)
        result = {'mode': name, 'injection': 'replace production orient2d type guard in memory',
                  'source_files_written': False, 'semantic_failures': rows}
        (HERE / 'mutation.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    source = ROOT / ('reports/codex/R11FIX_evidence/baseline/src' if name == 'baseline' else 'src')
    command = [sys.executable, '-X', 'utf8', '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
               str(TEST), '-o', 'pythonpath=' + source.as_posix(),
               '--basetemp=' + str(HERE.parent / 'tmp' / ('k02_final_' + name))]
    if name == 'baseline':
        command += ['-k', 'not kills_reinstated']
    start = time.perf_counter()
    process = subprocess.run(command, cwd=ROOT, env=os.environ.copy(), stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, encoding='utf-8', errors='replace')
    elapsed = time.perf_counter() - start
    (HERE / ('final_' + name + '.log')).write_text(process.stdout, encoding='utf-8')
    result = {'mode': name, 'command': command, 'pytest_returncode': process.returncode,
              'seconds': elapsed, 'last_line': process.stdout.strip().splitlines()[-1],
              'test_sha256': hashlib.sha256(TEST.read_bytes()).hexdigest(),
              'source_sha256': {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in (source / 'eab/kernel2d/geom.py', source / 'eab/predicates.py')}}
    (HERE / ('final_' + name + '.json')).write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    assert process.returncode == (1 if name == 'baseline' else 0), process.stdout


if __name__ == '__main__':
    main()
