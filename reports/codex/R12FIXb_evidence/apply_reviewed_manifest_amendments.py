"""One-time explicit amendments to the initial R12FIXb migration, not renewal.

Only reviewed Expr-wrapper extraction errors and enumerated metadata corrections
are accepted. No new waiver, source edit, scope hash update, or fresh scan-to-
waiver conversion is possible. Keep the original decision history intact.
"""
import collections
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def write(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='')


def main():
    destination = HERE / 'local_review_decisions_final.json'
    assert not destination.exists(), 'Amendment is one-time; do not overwrite decision history'
    ledger_path = HERE / 'local_review_decisions.json'
    assert hashlib.sha256(ledger_path.read_bytes()).hexdigest() == '48bc7cc77cea05d9592b6fad32e0e7c3ba2e8d1d68923e4265b1174ad15633a4'
    ledger = read('local_review_decisions.json')
    rows = copy.deepcopy(ledger['decisions'])
    by_id = {r['id']: r for r in rows}
    fingerprints = read('fingerprint_extraction_corrections.json')
    assert len(fingerprints) == 165
    for correction in fingerprints:
        row = by_id[correction['id']]
        assert row['node'] == correction['before_node'] == 'Expr(value=' + correction['after_node'] + ')'
        assert all(row[k] == correction[k] for k in ('path', 'function', 'rule', 'source', 'context'))
        row['node'] = correction['after_node']
        row['binding_amendment'] = 'fingerprint_extraction_corrections.json'
    amendments = ['suggested_metadata_corrections.json']
    extra = HERE / 'src_final_reason_metadata_corrections.json'
    if extra.exists():
        amendments.append(extra.name)
    metadata_ids = []
    for filename in amendments:
        for correction in read(filename)['corrections']:
            row = by_id[correction['id']]
            assert row['category'] == correction['old_category'] and row['reason'] == correction['old_reason']
            assert correction['metadata_only'] and not correction['may_change_node_or_context']
            for old, new in [('category', 'new_category'), ('reason', 'new_reason'), ('review_disposition', 'new_review_disposition')]:
                row[old] = correction[new]
            row['review_evidence'] = 'reports/codex/R12FIXb_evidence/' + filename
            row['metadata_amendment'] = filename
            metadata_ids.append(row['id'])
    assert len(metadata_ids) == len(set(metadata_ids))
    # Compare every pin with the original. The only change is the explicit
    # Expr->actual-child binding; enclosing source hashes must all be identical.
    originals = {r['id']: r for r in ledger['decisions']}
    assert len(rows) == 2365
    assert all(all(r[k] == originals[r['id']][k] for k in ('path','function','rule','context')) for r in rows)
    raw = read('raw_actual_fingerprints.json')
    key = lambda r: tuple(r[k] for k in ('path','function','rule','node','context'))
    assert {key(r) for r in rows} == {key(r) for r in raw}
    assert len({key(r) for r in rows}) == 2365
    spec = importlib.util.spec_from_file_location('amendment_pin_check', ROOT / 'tools/exact_construction_subset.py')
    subset = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(subset)
    contexts = {}
    for row in rows:
        if row['path'] not in contexts:
            contexts[row['path']] = subset.site_contexts((ROOT / row['path']).read_text(encoding='utf-8-sig'))
        assert contexts[row['path']][row['function']] == row['context'], 'Source changed: do not renew'
    policy_path = ROOT / 'tools/exact_construction_policy.json'
    policy = json.loads(policy_path.read_text(encoding='utf-8'))
    assert hashlib.sha256(policy_path.read_bytes()).hexdigest() == '5f119aecdc9e51d8af3a168d9854c32e415078225547fa33ef77a54defb49ed5'
    final = {**ledger, 'decisions': rows, 'amends': ledger_path.name,
             'amendment_files': ['fingerprint_extraction_corrections.json', *amendments],
             'scope_hashes_refreshed': 0, 'new_waivers': 0,
             'root_decision': 'Explicitly adopt enumerated binding/metadata corrections; no numerical proof or reviewer approval is claimed.'}
    write(destination.name, final)
    policy['waivers'] = [{k: r[k] for k in ('id','path','function','rule','node','context','category','reason','review_evidence')} for r in rows]
    policy_path.write_text(json.dumps(policy, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='')
    counts = dict(collections.Counter(r['category'] for r in rows))
    stats = {'waivers': len(rows), 'original_waivers': 16936, 'within_200': False,
             'unique_ast_sites': len({(r['path'],r['function'],r['node']) for r in rows}),
             'scope_count': len({(r['path'],r['function']) for r in rows}),
             'by_category': counts, 'by_disposition': dict(collections.Counter(r['review_disposition'] for r in rows)),
             'by_rule': dict(collections.Counter(r['rule'] for r in rows)),
             'by_path': dict(collections.Counter(r['path'] for r in rows)),
             'representatives': {c: [r for r in rows if r['category'] == c][:2] for c in counts},
             'source_vs_tests': dict(collections.Counter(r['path'].split('/')[0] for r in rows)),
             'unreviewed_keys': 0, 'reviewer_approvals_claimed': 0,
             'extraction_binding_corrections': len(fingerprints), 'metadata_corrections': len(metadata_ids)}
    write('local_manifest_statistics_final.json', stats)
    result = {'waivers': len(rows), 'scope_hashes_refreshed': 0, 'new_waivers': 0,
              'binding_corrections': len(fingerprints), 'metadata_corrections': len(metadata_ids),
              'by_category': counts, 'policy_sha256': hashlib.sha256(policy_path.read_bytes()).hexdigest(),
              'ledger_sha256': hashlib.sha256(destination.read_bytes()).hexdigest()}
    write('local_manifest_amendments_applied.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
