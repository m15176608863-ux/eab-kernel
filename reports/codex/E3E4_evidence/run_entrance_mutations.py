"""D1-D4 one-shot source mutations; root must run serially, never concurrently with pytest.
Usage: PYTHONDONTWRITEBYTECODE=1 python -X utf8 reports/codex/E3E4_evidence/run_entrance_mutations.py
Every mutation restores the original source bytes in finally and checks SHA-256.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'src/eab/kernel2d/entrance.py'
OUT = ROOT / 'reports/codex/E3E4_evidence/mutations_entrance'
TEST = 'tests/test_kernel2d_entrance_e3.py'


def replace_once(source, before, after):
    assert source.count(before) == 1, (before, source.count(before))
    return source.replace(before, after, 1)


def mutate_d1(source):
    # Restore float translation + float overlap/ctol inside the actual concave adjudicator.
    start = source.index('def _first_entrance_concave(')
    end = source.index('\n\ndef shortest_exit', start)
    fragment = source[start:end]
    fragment = replace_once(fragment, 'return polygons_overlap_exact(A, B, _at(X, D, t))',
        'from .geom import polygons_overlap, translate\n        return polygons_overlap(translate(A, tuple(map(float, _at(X, D, t)))), B, ctol)')
    return source[:start] + fragment + source[end:]


def mutate_d2(source):
    return replace_once(source, 'return (-g / slope,)', 'return (Fraction(-float(g) / float(slope)),)')


def mutate_d3(source):
    before = '''        for tp in probes:
            if state(tp) >= 0:
                raise RuntimeError(f"first_entrance: bodies already touch at t = {tp!r} < candidate {t!r} ({label}); "
                                   "the cover candidate set missed an earlier entrance")'''
    return replace_once(source, before, '        # MUTATION D3: deleted exact pre-contact selfcheck')


def mutate_d4(source):
    return replace_once(source, 'best_distance, label = min(candidates, key=lambda q: q[0])',
        'best_distance, label = max(candidates, key=lambda q: q[0])')


CASES = [
    ('D1', mutate_d1, [TEST+'::test_concave_first_entrance_keeps_sub_roundoff_translation_and_tiny_velocity']),
    ('D2', mutate_d2, [TEST+'::test_concave_fraction_time_is_not_replaced_by_rounded_float_candidate', TEST+'::test_concave_rotated_translated_and_scaled_ray_matches_independent_piecewise_sat']),
    ('D3', mutate_d3, [TEST+'::test_missing_earlier_concave_contact_is_caught_by_exact_selfcheck', TEST+'::test_exact_selfcheck_catches_an_earlier_narrow_contact_interval_not_just_the_last_step']),
    ('D4', mutate_d4, [TEST+'::test_shortest_exit_compares_exact_signed_distance_not_rounded_gap']),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    backup = ROOT / 'reports/codex/E3E4_evidence/tmp/mutation_backups'
    backup.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['TEMP'] = env['TMP'] = str(ROOT / 'reports/codex/E3E4_evidence/tmp')
    results = []
    for name, mutate, tests in CASES:
        original = SOURCE.read_bytes()
        digest = hashlib.sha256(original).hexdigest()
        (backup / (name+'_entrance.py')).write_bytes(original)
        started = time.perf_counter()
        try:
            changed = mutate(original.decode('utf-8')).encode('utf-8')
            SOURCE.write_bytes(changed)
            xml = OUT / (name+'.xml')
            command = [sys.executable,'-X','utf8','-m','pytest','-q','-p','no:cacheprovider',*tests,'--junitxml='+str(xml)]
            proc = subprocess.run(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            log = proc.stdout.decode('utf-8', errors='replace')
            (OUT/(name+'.log')).write_text(log,encoding='utf-8')
            failures=[]
            if xml.exists():
                for case in ET.parse(xml).iter('testcase'):
                    failure=case.find('failure')
                    if failure is not None:
                        failures.append({'name':case.attrib['name'], 'assertion':failure.attrib.get('message'), 'traceback':failure.text})
            result={'id':name,'returncode':proc.returncode,'command':command,'elapsed_s':time.perf_counter()-started,
                    'source_before_sha256':digest,'source_mutated_sha256':hashlib.sha256(changed).hexdigest(),
                    'last_line':log.rstrip().splitlines()[-1], 'failures':failures}
        finally:
            SOURCE.write_bytes(original)
            restored=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
            assert restored==digest
        result['source_restored_sha256']=restored
        results.append(result)
        print(name,result['last_line'],flush=True)
        (OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__ == '__main__':
    main()
