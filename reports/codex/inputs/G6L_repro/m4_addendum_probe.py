"""G6L M4 addendum: source citations, exception cells, exact key digest guard."""
from collections import Counter
import csv
import hashlib
import inspect
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tools'), str(ROOT/'tests')]
import m4_bdda_shadow as shadow
import test_m4_bdda_shadow as gate

source_file = Path('D:/b-DDA/df/df.c')
lines = source_file.read_text(encoding='utf-8', errors='replace').splitlines()
checks = {
    'mtype_assignment_3915': 'i1 = m[i][0];',
    'skipped_shear_branch_3994': 'if (i1==1 || m0[i][2]==0) goto c212;',
    'shear_assignment_4030': 'o[i][4] = s1+s2;',
    'jump_target_4063': 'c212:;',
    'csv_type_and_state_4073': 'nn, bdda_df22_iter, i, (long)m[i][0], (long)m0[i][0],',
    'csv_shear_4074': '(long)m0[i][1], (long)m0[i][2], o[i][3], o[i][4],',
}
for name, expected in checks.items():
    number = int(name.rsplit('_',1)[1])
    assert lines[number-1].strip() == expected, (name, lines[number-1])

manifest = json.loads((ROOT/'reports/codex/M4a_evidence/family_manifest.json').read_text(encoding='utf-8'))
counts = Counter()
for case in manifest['cases']:
    folder = ROOT/case['fixture']
    differences = case['repeat']['documented_differences']
    df22_lines = (folder/'bdda_debug_df22.csv').read_text(encoding='utf-8').splitlines()
    header = df22_lines[0].split(',')
    for diff in differences:
        counts[diff['file']] += 1
        if diff['file'] != 'bdda_debug_df22.csv':
            continue
        raw = dict(zip(header, df22_lines[diff['line']-1].split(',')))
        assert diff['column'] == 'o4' and raw['step'] == '1'
        assert raw['mtype'] == '1' or raw['m0_new'] == '0', (case['case'],diff,raw)
        assert raw['o4'] == diff['first'], (case['case'], 'stored first raw cell drift')
        assert diff['rule'] == 'df22_skipped_shear_update'
assert counts['bdda_debug_df22.csv'] == 570
assert counts['bdda_debug_contacts.csv'] == 975
assert counts['bdda_debug_df18.csv'] == 967

path = ROOT/'fixtures/bdda_df/bb52_N3'
baseline = shadow.compare_fixture(path)
gate._assert_baseline('bb52_N3', baseline)
original_compare = shadow.compare_step
original_classifier = shadow.classify_extra
code = inspect.getsource(original_compare)
needle = 'differences.append(dict(key=key, category=category,'
replacement = 'differences.append(dict(key=(key[0], *key[1:-1], key[-1]+1), category=category,'
assert code.count(needle) == 1
namespace = dict(original_compare.__globals__)
exec(compile(code.replace(needle,replacement), str(ROOT/'tools/m4_bdda_shadow.py')+'::key_mutation', 'exec'), namespace)
results = []
before = hashlib.sha256((ROOT/'tools/m4_bdda_shadow.py').read_bytes()).hexdigest()
try:
    shadow.compare_step = namespace['compare_step']
    changed = shadow.compare_fixture(path)
    assert [r['counts'] for r in changed] == [r['counts'] for r in baseline], 'same-count probe changed counts'
    shadow.assert_classified(changed)
    try:
        gate._assert_baseline('bb52_N3', changed)
    except AssertionError as error:
        assert str(error) == 'pinned row-by-row classification', error
        results.append(dict(name='internal_comparator_key_mutation_with_unchanged_counts',
                            assert_classified_only='PASS', complete_frozen_gate='KILLED',
                            assertion=str(error)))
    else:
        raise AssertionError('same-count wrong-key mutation survived frozen row digest')
finally:
    shadow.compare_step = original_compare
gate._gate_case('bb52_N3')
results[-1]['restored_baseline'] = 'PASS'

def unknown_category(key, sg, window):
    return 'NOT_A_REGISTERED_CATEGORY'
try:
    shadow.classify_extra = unknown_category
    try:
        gate._gate_case('bb52_N3')
    except AssertionError as error:
        assert 'unclassified differences' in str(error), error
        results.append(dict(name='actual_classify_extra_unknown_category', complete_frozen_gate='KILLED',
                            assertion=str(error)))
    else:
        raise AssertionError('unknown category from real classifier survived')
finally:
    shadow.classify_extra = original_classifier
gate._gate_case('bb52_N3')
results[-1]['restored_baseline'] = 'PASS'
after = hashlib.sha256((ROOT/'tools/m4_bdda_shadow.py').read_bytes()).hexdigest()
assert before == after
out = dict(source_citations_checked=checks, documented_difference_counts=dict(counts),
           all_570_df22_cells_match_first_value_and_specific_skip_branch=True,
           guards=results, source_sha256_before=before, source_sha256_after=after)
(ROOT/'review/m4/addendum_probe.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
