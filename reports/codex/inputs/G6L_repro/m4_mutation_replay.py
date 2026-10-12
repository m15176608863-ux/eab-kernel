"""Replay the three M4 real-path mutations without editing repository files."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tools'), str(ROOT / 'tests')]
import test_m4_bdda_shadow as gate
import m4_bdda_shadow as shadow
from eab.adapters import bdda2d
from eab.readers import bdda_df

original_enum = bdda2d.covers.enumerate_covers
original_classify = shadow.classify_extra
original_read = bdda_df._read_csv


def drop_window(A, B, **kwargs):
    kwargs['cone_tol'] = 0.0
    return original_enum(A, B, **kwargs)


def wrong_category(key, sg, window):
    value = original_classify(key, sg, window)
    return 'ANGULAR_WINDOW_COVER_NOT_SELECTED' if value == 'EXACT_LOCAL_COVER_NOT_SELECTED' else value


def shift_column(path):
    records = original_read(path)
    if path.name == 'bdda_debug_contacts.csv':
        for row in records:
            if row['mtype'] == '0':
                row['p1'] = row['p2']
    return records


files = [ROOT / f for f in ('src/eab/adapters/bdda2d.py', 'src/eab/readers/bdda_df.py',
                            'src/eab/kernel2d/covers.py', 'tools/m4_bdda_shadow.py')]
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
before = {str(p.relative_to(ROOT)): digest(p) for p in files}
results = []
for name, module, attribute, replacement, expected in [
        ('drop_domain_window', bdda2d.covers, 'enumerate_covers', drop_window, 'unclassified differences'),
        ('misclassify_difference', shadow, 'classify_extra', wrong_category, 'pinned shadow tally'),
        ('legacy_p1_column_shift', bdda_df, '_read_csv', shift_column, 'legacy p1 column misread')]:
    gate._gate_case('bb52_N3')
    original = getattr(module, attribute)
    try:
        setattr(module, attribute, replacement)
        try:
            gate._gate_case('bb52_N3')
        except AssertionError as error:
            assert expected in str(error), ('wrong killing assertion', name, str(error))
            results.append(dict(name=name, status='KILLED', verified_assertion=str(error)))
        else:
            raise AssertionError(('mutation survived', name))
    finally:
        setattr(module, attribute, original)
    gate._gate_case('bb52_N3')
    results[-1]['restored_baseline'] = 'PASS'
after = {str(p.relative_to(ROOT)): digest(p) for p in files}
assert before == after, 'source bytes changed'
result = dict(mutations=results, source_sha256_before=before, source_sha256_after=after)
(ROOT / 'review/m4/mutation_replay.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
